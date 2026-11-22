# CANASTAMX - ENTORNO PROD (EL DESPLIEGUE)

El sistema completo en la máquina virtual de Oracle Cloud del [ADR 008](../../../docs/adr/008-donde-vive-la-base.md), con Docker Compose, como en [`docs/arquitectura/05-despliegue.dot`](../../../docs/arquitectura/05-despliegue.dot). Es la versión que pide la entrega del 18 de noviembre (T074) y la tarjeta T054 (#201).

El despliegue se hace **a mano**, con los pasos de este archivo. Con el recorte del 5 de noviembre, el despliegue continuo (T065) salió del producto: hasta el 29, cada solicitud que entre a `main` se vuelve a desplegar como dice [Volver a desplegar](#8-volver-a-desplegar).

## QUÉ SE DESPLIEGA

| Servicio | Imagen | Se alcanza en | Dockerfile · lo revisa |
|---|---|---|---|
| `traefik` | `traefik:v3.6.2` | 80 y 443 de la VM: es lo **único** abierto hacia fuera | — · B |
| `web` | se construye | `https://<DIRECCION_PUBLICA>` | `clients/web/Dockerfile` · D |
| `domain-service` | se construye | `https://dominio.<DIRECCION_PUBLICA>` | `services/domain-service/Dockerfile` · C1 |
| `analytics-api` | se construye | `https://analitica.<DIRECCION_PUBLICA>` | `services/analytics-api/Dockerfile` · A |
| `dagster-webserver` | se construye | `127.0.0.1:3000` **de la VM**, por un túnel SSH | `services/data-platform/Dockerfile` · A |
| `dagster-daemon` | la misma | nada: corre el sensor y la cola de corridas | la misma |
| `postgres-oltp` | `postgres:16-alpine` | sólo la red interna de Compose | — |
| `postgres-analytics` | `postgres:16-alpine` | sólo la red interna de Compose | — |
| `minio` | `canastamx/minio` (ADR 012) | sólo la red interna de Compose | — |
| `minio-init` | `canastamx/mc` (ADR 012) | crea el bucket y se apaga | — |

- **Los certificados** son de Let's Encrypt. Traefik los pide y los renueva solo, y los guarda en el volumen `certificados`.
- **Las imágenes se construyen en la propia VM**, que es arm64 (Ampere A1), así que no hay que emular nada. El trabajo «Imágenes del despliegue (arm64)» de la CI construye las mismas imágenes en cada solicitud, para que un Dockerfile roto salga ahí y no en la VM.
- **Los secretos** viven sólo en `infra/envs/prod/.env`, en la VM. En el repositorio está su ejemplo sin valores, [`.env.example`](.env.example).

> **IMPORTANTE · Docker siempre desde una terminal sin ningún `.env` cargado**
> ---
> Docker Compose toma las variables de la terminal antes que las del `--env-file`. Si en la terminal hay un `.env` cargado con `set -a; source …`, Compose usa esos valores, como pasó el 15 de noviembre en #187. Antes de cada `up`:
>
> ```bash
> env | grep -E '^(OLTP|ANALYTICS|S3|JWT|DIRECCION|ACME|CARPETA)_' || echo "terminal limpia"
> ```

Todos los comandos se corren **desde la raíz del repositorio**. Para no repetir la línea de Compose, defina en cada terminal de la VM:

```bash
alias prod='docker compose -f infra/envs/prod/docker-compose.yml --env-file infra/envs/prod/.env'
```

---

## 1. LA MÁQUINA VIRTUAL

### 1.1 Crear la instancia

En la consola de Oracle Cloud: **Compute → Instances → Create instance**.

- **Imagen:** Ubuntu (la del ADR 008).
- **Forma:** `VM.Standard.A1.Flex` (Ampere, arm64), con la memoria y los OCPU del ADR 008, dentro de la capa gratuita.
- **Red:** una VCN con subred pública y **una IP pública** asignada.
- **SSH:** suba su llave pública y guarde la privada. Ese mismo acceso sirve para el túnel de Dagster.

Si Oracle contesta que no hay capacidad para A1 (`Out of host capacity`), intente con otro *availability domain* o más tarde: es una limitación conocida de la capa gratuita.

### 1.2 Abrir el 80 y el 443 en la red de Oracle

**Networking → Virtual Cloud Networks → la VCN → Security Lists → Default Security List → Add Ingress Rules**. Agregue dos reglas, las dos con origen `0.0.0.0/0` y protocolo TCP: una con puerto de destino **80** y otra con **443**.

Let's Encrypt comprueba el nombre entrando por el 80, así que sin ese puerto no hay certificado. **No abra ningún otro puerto**: ni el de las bases, ni el de MinIO, ni el de Dagster.

### 1.3 Abrir el 80 y el 443 en el firewall de Ubuntu

Las imágenes de Ubuntu de Oracle traen `iptables` con todo cerrado menos el 22. En la VM:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

### 1.4 Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
exit   # vuelva a entrar por SSH para que el grupo aplique
docker compose version
```

---

## 2. EL NOMBRE PÚBLICO

Let's Encrypt da certificados a **nombres**, no a direcciones IP. Con [DuckDNS](https://www.duckdns.org), que es gratis:

1. Entre con su cuenta de GitHub y cree un subdominio, por ejemplo `canastamx`. Eso da `canastamx.duckdns.org`.
2. En **current ip**, escriba la IP pública de la VM y pulse **update ip**.
3. DuckDNS también resuelve los nombres de debajo, así que `dominio.canastamx.duckdns.org` y `analitica.canastamx.duckdns.org` apuntan a la misma IP sin hacer nada más.

Compruébelo desde la VM y desde su computadora:

```bash
getent hosts canastamx.duckdns.org dominio.canastamx.duckdns.org analitica.canastamx.duckdns.org
```

Si la IP de la VM cambia, porque la instancia se detuvo y se volvió a crear, actualícela en DuckDNS.

---

## 3. EL REPOSITORIO Y EL `.env`

```bash
git clone https://github.com/arik36/canastamx.git
cd canastamx
cp infra/envs/prod/.env.example infra/envs/prod/.env
chmod 600 infra/envs/prod/.env
nano infra/envs/prod/.env
```

| Variable | Qué poner | Cómo generarla |
|---|---|---|
| `DIRECCION_PUBLICA` | El nombre del paso 2, sin `https://` | — |
| `ACME_CORREO` | Un correo real del equipo | — |
| `ACME_SERVIDOR` | Vacía. Para ensayar, la de pruebas del ejemplo | — |
| `OLTP_PASSWORD`, `ANALYTICS_PASSWORD` | Una contraseña distinta cada una | `openssl rand -hex 16` |
| `S3_ACCESS_KEY` | Un nombre, por ejemplo `canastamx` | — |
| `S3_SECRET_KEY` | Mínimo 8 caracteres | `openssl rand -hex 16` |
| `JWT_SECRET` | Base64 de 32 bytes (ADR 020) | `openssl rand -base64 32` |
| `SEMILLA_CONTRASENA` | 8 caracteres o más, una mayúscula y un número | `echo "Cmx$(openssl rand -hex 6)"` |
| `CARPETA_DE_LOTES` | Ruta **absoluta**, fuera del repositorio | por ejemplo `/home/ubuntu/canastamx-lotes` |

No use `$` en ningún valor, y no los pegue en ningún chat. La contraseña de las cuentas semilla sólo la necesita quien vaya a iniciar sesión con ellas.

```bash
mkdir -p /home/ubuntu/canastamx-lotes          # la de CARPETA_DE_LOTES
python3 infra/scripts/revisar-env.py infra/envs/prod/.env
```

---

## 4. LEVANTAR

Desde una terminal **sin ningún `.env` cargado**:

```bash
env | grep -E '^(OLTP|ANALYTICS|S3|JWT|DIRECCION|ACME|CARPETA)_' || echo "terminal limpia"
prod up -d --build
prod ps
```

La primera vez construye cuatro imágenes en la VM y tarda: compila el dominio con Maven, la web con Next.js e instala Dagster. Las siguientes reutilizan la caché.

`prod ps` tiene que mostrar todo `Up`, las dos bases y MinIO `(healthy)`, y `minio-init` en `Exited (0)`, que es lo correcto.

Los certificados los pide Traefik al levantar. Para ver cómo va:

```bash
prod logs traefik | grep -i -E "acme|certific|error"
```

Si no aparece ningún error, los certificados ya están. En el navegador, `https://<DIRECCION_PUBLICA>` abre la web con candado y `https://analitica.<DIRECCION_PUBLICA>/health` contesta `{"status":"UP",…}`.

> **Ensayar sin gastar el límite de Let's Encrypt.** Con `ACME_SERVIDOR` en el servidor de pruebas, el certificado no es de confianza, pero comprueba que todo lo demás funciona. Para pasar a los certificados de verdad, vacíe `ACME_SERVIDOR` y borre los de prueba:
>
> ```bash
> prod rm -sf traefik
> docker volume rm canastamx_prod_certificados
> prod up -d
> ```

---

## 5. LAS CUENTAS SEMILLA

El dominio crea sus tablas al arrancar (Flyway). Cuando `prod logs domain-service` diga `Started`:

```bash
bash infra/scripts/sembrar-cuentas.sh --prod
```

Crea `analista@canastamx.mx` (ANALISTA) y `operador@canastamx.mx` (OPERADOR) con la contraseña de `SEMILLA_CONTRASENA`. Se puede correr las veces que haga falta: si ya existen, no las toca.

---

## 6. LOS LOTES Y LA PLATAFORMA DE DATOS

### 6.1 Copiar los lotes

Los 38 lotes del alcance los tiene A, con un archivo `SHA256SUMS`. Desde la computadora donde estén:

```bash
scp *.parquet SHA256SUMS ubuntu@<IP>:/home/ubuntu/canastamx-lotes/
```

Y en la VM, comprobar que llegaron completos:

```bash
cd /home/ubuntu/canastamx-lotes && sha256sum -c SHA256SUMS && cd -
```

Todos tienen que decir `OK`.

### 6.2 Procesarlos

Desde **su computadora**, abra un túnel a Dagster y déjelo abierto:

```bash
ssh -L 3000:localhost:3000 ubuntu@<IP>
```

En el navegador, `http://localhost:3000`:

1. **Automation →** encienda `archivo_nuevo`. En menos de 30 segundos pide una corrida por cada lote.
2. **Runs →** las corridas pasan de `Queued` a `Success` **de una en una**: la cola de `dagster.yaml` no deja que corran varias a la vez, para no llenar la memoria de la VM.
3. Cuando las 38 terminen, ve a **Assets →** `capa_consumo`, da **Materialize** y espera a que termine. `capa_consumo` arma la estrella desde la capa intermedia y el sensor no la corre.

El sensor se queda encendido: un lote nuevo que se copie a la carpeta se procesa solo.

### 6.3 Comprobar los datos

En la VM:

```bash
prod exec dagster-daemon python ingestion/operacion.py --contar
prod exec dagster-daemon python ingestion/estrella.py --contar
prod exec dagster-daemon python -c "
import os, boto3
s3 = boto3.client('s3', endpoint_url=os.environ['S3_ENDPOINT'], region_name='us-east-1',
                  aws_access_key_id=os.environ['S3_ACCESS_KEY'], aws_secret_access_key=os.environ['S3_SECRET_KEY'])
n = sum(len(p.get('Contents', [])) for p in s3.get_paginator('list_objects_v2').paginate(Bucket=os.environ['S3_BUCKET']))
print(os.environ['S3_BUCKET'], n, 'objetos')"
```

`operacion.py --contar` tiene que mostrar una corrida vigente por lote y sus cuatro comprobaciones con ✓. Las cifras se comparan con las del entorno de A: con los mismos lotes y el mismo contrato, tienen que salir iguales.

---

## 7. VERIFICAR DESDE FUERA

Desde una computadora que **no** sea la VM y desde una red que no sea la de nadie del equipo, por ejemplo con los datos del teléfono:

```bash
bash infra/envs/prod/verificar-desde-fuera.sh <DIRECCION_PUBLICA>
```

Revisa los criterios de #201 que se ven desde fuera:
- que los tres nombres apunten a la VM;
- que cada uno tenga un certificado válido, y que el 80 mande al 443;
- que la web, el dominio y la interfaz analítica contesten;
- que haya datos;
- que las dos cuentas semilla inicien sesión en el dominio y en la web;
- que ningún puerto de base, MinIO o Dagster conteste.

Pide la contraseña de las cuentas sin mostrarla, y termina con `OK` o con la lista de lo que falló. Su salida y la dirección pública van en #201.

---

## 8. VOLVER A DESPLEGAR

Cada vez que entre una solicitud a `main`, en la VM y desde una terminal limpia:

```bash
git switch main && git pull
prod up -d --build
prod ps
```

Sólo se reconstruye lo que cambió. Los datos, las cuentas y los certificados están en volúmenes y no se pierden.

**Nunca `prod down -v`**: borra las dos bases, el bucket y los certificados. Si se borran los certificados muchas veces, Let's Encrypt deja de dar nuevos durante una semana.

---

## 9. LA MEMORIA

El ADR 008 dice que la memoria, no el disco, es la restricción real. Con todo arriba y después de procesar los lotes:

```bash
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}'
free -h
```

Esa salida también va en #201.

---

## SI ALGO FALLA

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `curl -I http://<IP>` no contesta desde fuera | El 80 cerrado en la red de Oracle o en `iptables` | Repita 1.2 y 1.3 |
| `prod logs traefik` dice `acme` con `Timeout during connect` o `NXDOMAIN` | Let's Encrypt no llega al 80, o el nombre no apunta a la VM | Revise 1.2, 1.3 y el paso 2 |
| `prod logs traefik` dice `too many certificates` | El límite semanal de Let's Encrypt | Use `ACME_SERVIDOR` de pruebas y espere |
| `Bad Gateway` en una dirección | El contenedor de ese servicio no está arriba | `prod ps` y `prod logs <servicio>` |
| `domain-service` se reinicia una y otra vez | `JWT_SECRET` no es Base64 de 32 bytes, o la contraseña de la base no coincide | `prod logs domain-service` y `revisar-env.py` |
| La contraseña de una base cambió en el `.env` y ya no conecta | PostgreSQL guarda la primera contraseña en su volumen | Vuelva a poner la contraseña anterior en el `.env` |
| `sembrar-cuentas.sh` dice que no existe la tabla `usuario` | El dominio todavía no arranca | Espere a `Started` en `prod logs domain-service` |
| El sensor dice `ningún archivo nuevo` | La carpeta o los nombres de los lotes | `ls /home/ubuntu/canastamx-lotes`: los nombres son los del contrato, como `07-2026_Q2.parquet` |
| Una corrida falla en `capa_cruda` o en `capa_intermedia` | MinIO o la base analítica no responden | El log de esa corrida en Dagster; `prod ps` |
| `/api/v1/entidades` da 500 | Todavía no se procesan los lotes | Paso 6 |
| `permission denied` con `docker` | El grupo `docker` no aplicó | Salga y vuelva a entrar por SSH |
