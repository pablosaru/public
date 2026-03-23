# AWS Scripts

Colección de scripts de Bash para operaciones y auditoría en AWS.

## Scripts

### `sg-finder.sh` — Buscar recursos asociados a un Security Group

Identifica todos los recursos AWS que están utilizando un Security Group específico, útil para auditorías o antes de modificar/eliminar un SG.

**Recursos que analiza:** EC2, RDS, ALB/NLB, Lambda, ECS, Network Interfaces

**Requisitos:** AWS CLI configurado, python3

**Uso:**
```bash
chmod +x sg-finder.sh
./sg-finder.sh <sg-id>
```

**Ejemplo:**
```bash
./sg-finder.sh sg-0123456789abcdef0
```

**Permisos IAM necesarios:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeNetworkInterfaces",
        "rds:DescribeDBInstances",
        "elasticloadbalancing:DescribeLoadBalancers",
        "lambda:ListFunctions",
        "ecs:ListClusters",
        "ecs:ListTasks",
        "ecs:DescribeTasks"
      ],
      "Resource": "*"
    }
  ]
}
```

> La región se toma del perfil activo. Para apuntar a una región específica: `export AWS_DEFAULT_REGION=us-east-1`  
> Para usar con múltiples cuentas: `AWS_PROFILE=mi-perfil ./sg-finder.sh <sg-id>`

---

## Requisitos generales

- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- `python3`
- Credenciales configuradas (`aws configure` o variables de entorno)

## Licencia

MIT
