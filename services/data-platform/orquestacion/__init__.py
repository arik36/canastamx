"""CanastaMX · la orquestación de la plataforma de datos (ADR 016).

Este paquete es DELGADO a propósito. El ADR 016 le puso a Dagster fecha de
salida: si el 25 de octubre de 2026 no corren tres activos particionados con un
sensor, se cambia a guion más `cron`. Para que ese cambio cueste poco, aquí no
vive ninguna regla del contrato: las reglas están en `ingestion/compuerta.py`
(fila por fila) y en `ingestion/lote.py` (lote completo), que son funciones de
Python sin nada de Dagster. Este paquete sólo las llama en orden y les pone
linaje.

Si Dagster se va, se borra esta carpeta y las compuertas siguen funcionando.
"""
