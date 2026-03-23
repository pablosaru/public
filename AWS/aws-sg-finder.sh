#!/bin/bash

# Validación de argumentos
if [ -z "$1" ]; then
  echo "Uso: $0 <sg-id>"
  echo "Ejemplo: $0 sg-0123456789abcdef0"
  exit 1
fi

SG_ID="$1"

echo "=== EC2 Instances ==="
aws ec2 describe-instances \
  --filters Name=instance.group-id,Values=$SG_ID \
  --query 'Reservations[*].Instances[*].[InstanceId, Tags[?Key==`Name`]|[0].Value]' \
  --output text

echo "=== RDS Instances ==="
aws rds describe-db-instances \
  --query "DBInstances[?contains(VpcSecurityGroups[*].VpcSecurityGroupId, '$SG_ID')].[DBInstanceIdentifier]" \
  --output text

echo "=== ELB (ALB/NLB) ==="
aws elbv2 describe-load-balancers \
  --output json | python3 -c "
import json, sys
data = json.load(sys.stdin)
sg = '$SG_ID'
for lb in data['LoadBalancers']:
    sgs = lb.get('SecurityGroups') or []  # maneja null y campo ausente
    if sg in sgs:
        print(lb['LoadBalancerName'], '-', lb['Type'])
"

echo "=== Lambda ==="
aws lambda list-functions \
  --query "Functions[?VpcConfig.SecurityGroupIds && contains(VpcConfig.SecurityGroupIds, '$SG_ID')].[FunctionName]" \
  --output text

echo "=== ECS Tasks ==="
aws ecs list-clusters --output text | awk '{print $1}' | while read cluster; do
  aws ecs list-tasks --cluster $cluster --output text | awk '{print $2}' | while read task; do
    aws ecs describe-tasks --cluster $cluster --tasks $task \
      --output json | python3 -c "
import json, sys
data = json.load(sys.stdin)
sg = '$SG_ID'
for t in data['tasks']:
    for a in t.get('attachments', []):
        for d in a.get('details', []):
            if d['name'] == 'securityGroups' and sg in d['value']:
                print(t['taskArn'])
"
  done
done 
 
echo "=== Network Interfaces (catch-all) ==="
aws ec2 describe-network-interfaces \
  --filters Name=group-id,Values=$SG_ID \
  --query 'NetworkInterfaces[*].[NetworkInterfaceId, Description, Attachment.InstanceId]' \
  --output text