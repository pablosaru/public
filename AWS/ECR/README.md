# 📦 Análisis de Imágenes Docker en ECR

Este documento describe el proceso para inspeccionar y analizar imágenes Docker almacenadas en Amazon ECR, con foco en:

* Identificación de la imagen base (OS)
* Análisis de capas (history)
* Evaluación de superficie de ataque
* Preparación para análisis de vulnerabilidades
* Analisis de vulnerabilidadaes escaneadas

---

## 🔐 1. Autenticación en AWS

Exportar el perfil y autenticarse mediante SSO:

```bash
export AWS_PROFILE=StrixFlotasProd          # Ej: StrixConsumerProd / StrixDataLake2
aws sso login
```

Validar identidad:

```bash
aws sts get-caller-identity
```

---

## 🌎 2. Configuración de variables

Obtener automáticamente Account ID y región:

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=$(aws configure get region)
```

Definir repositorio e imagen:

```bash
export ECR_REPO_NAME=twin_service
export ECR_IMAGE_TAG=0.19.23-debian

ECR_IMAGE=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:$ECR_IMAGE_TAG
```

---

## 🔑 3. Login a ECR

Autenticarse contra el registry:

```bash
aws ecr get-login-password --region $AWS_REGION \
  | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

---

## ⬇️ 4. Descargar la imagen

```bash
docker pull $ECR_IMAGE
```

---

## 🧱 5. Análisis de capas (Docker history)

Exportar el historial completo:

```bash
docker history --no-trunc $ECR_IMAGE > /tmp/dockerfile
```

### 🔍 Limpieza del output (más legible)

```bash
cat /tmp/dockerfile \
  | cut -b89- \
  | sed -E 's/ {2,}/ /g' \
  | sed -E 's/#.*/ /g' \
  | sed -E 's/0B .*/ /g'
```

### 📌 ¿Qué permite ver esto?

* Instrucciones tipo `RUN`, `COPY`, `CMD`
* Paquetes instalados (`apt-get install`)
* Tamaño de cada capa
* Posibles fuentes de vulnerabilidades

---

## 🧬 6. Identificación del sistema operativo base

```bash
docker run --rm $ECR_IMAGE cat /etc/os-release
```

### 📌 Resultado esperado

Ejemplo:

```
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
```

### 🧠 ¿Por qué es importante?

Permite:

* Identificar la imagen base real (aunque no haya `FROM`)
* Relacionar vulnerabilidades con el OS
* Detectar imágenes pesadas vs minimalistas

---

## 🧪 7. Buenas prácticas

* Usar `--rm` en `docker run` para evitar contenedores residuales
* Evitar imágenes con:

  * `apt-get install` innecesarios
  * herramientas de debug en runtime (bash, curl, etc.)
* Preferir:

  * imágenes slim
  * Alpine o distroless
* Mantener trazabilidad del `FROM` en el Dockerfile

---

## 🚨 8. Observaciones de seguridad

Durante el análisis se pueden detectar:

* Librerías vulnerables (ej: `libncurses`, `nghttp2`)
* Superficie de ataque innecesaria
* Imágenes base desactualizadas
* Falta de hardening

---

## 🚀 9. Resumen de vulnerabilidades escaneadas en ECR

```bash
aws ecr describe-image-scan-findings \\n  --repository-name twin_service \\n  --image-id imageDigest=sha256:77140137bd5528fe156b4cfb70f330b4a0e7c7baeec41695a832ab1a9687f9ee
```

---

## 📌 TL;DR

Este proceso permite:

✔ Entender qué hay dentro de una imagen
✔ Detectar riesgos de seguridad
✔ Identificar mejoras en el Dockerfile
✔ Preparar la imagen para producción segura

---

## 🧰 Comandos clave (resumen)

```bash
# Login AWS
aws sso login

# Variables
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=$(aws configure get region)

# Login ECR
aws ecr get-login-password --region $AWS_REGION \
  | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Pull
docker pull $ECR_IMAGE

# History
docker history --no-trunc $ECR_IMAGE > /tmp/dockerfile

# OS
docker run --rm $ECR_IMAGE cat /etc/os-release
```

---
