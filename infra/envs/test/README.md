# CANASTAMX - TEST

En este directorio se encuentran los archivos necesarios para levantar el entorno de pruebas. 

> **NOTA**
> ---
> Consulte la [📖 **GUÍA DE ARRANQUE**](../../../docs/infra/arranque.md) para tener un mejor entendimiento del proceso.  

## GUÍA RÁPIDA

### Método A

1. Ubique el directorio de trabajo de su terminal en `canastamx/infra/envs/test`

2. Haga una copia de `.env.example` con el nombre de `.env` en el mismo directorio

3. Rellene los campos indicados en `.env` (Consulte **Guía de arranque** para recordar este procedimiento)

4. Ejecute `docker compose up -d`

### MÉTODO B

1. Siga pasos del 1 al 3 del [método A](#método-a)

2. Posicione el directorio de trabajo de su terminal en la raíz (`canastamx/`)

3. Ejecute el siguiente comando en su terminal

```bash
docker compose -f infra/envs/test/docker-compose.yml --env-file infra/envs/test/.env up -d
```

> **NOTA**
> ---
> El llenado de .env solo es necesario hacerlo una vez. Tras realizarlo, puede omitir esos pasos y ejecutar directamente docker compose de acuerdo al método elegido.

**RESULTADO ESPERADO**
Un entorno de canastamx bajo el nombre de canastamx-test, que pueda ser ejecutado en conjunto a canastamx (dev)