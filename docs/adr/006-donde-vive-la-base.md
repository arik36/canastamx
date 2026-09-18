# ADR 006 · Dónde vive la base desplegada

- **Fecha:** 17 de septiembre de 2026
- **Estado:** propuesta
- **Participantes:** Ari Adair (B), Ariadne (A)

## Contexto

En la reunión del 11 se citó Supabase como la plataforma, pero el protocolo
especifica PostgreSQL 16 en contenedor sobre máquina virtual, y desde la semana 1
hay una cuenta de Oracle Cloud registrada para eso.

## Decisión

[La plataforma elegida y su configuración]
La plataforma elegida es Oracle Cloud en conjunto con PostgreSQL. La máquina virtual Ampere 1 que se creará en Oracle Cloud será quien albergue la base de datos usando PostgreSQL mediante una instalación local en la VM, de está manera evitando migrar toda la planificación de la BD a una nueva arquitectura y evitando los límites impuestos por el uso de servicios en la nube, como Supabase.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Supabase, plan gratuito | 500 MB contra ~1,373 MB que pesa el recorte. Y no está en el protocolo |
| Oracle Autonomous Database | Caben los 20 GB, pero no es PostgreSQL: habría que cambiar el adaptador de dbt y el protocolo lo especifica |

## Consecuencias

- La memoria, no el disco, es la restricción real: 12 GB para toda la pila ·
  responsable B · se verifica en la semana 9
- El laboratorio nacional de A deja de ser un punto único de falla · B · semana 9