# ADR 006 · Dónde vive la base desplegada

- **Fecha:** 17 de septiembre de 2026
- **Estado:** propuesta
- **Participantes:** Ari Adair (B), Ariadne (A)

## Contexto

En la reunión del 11 se citó Supabase como la plataforma, pero el protocolo
especifica PostgreSQL 16 en contenedor sobre máquina virtual, y desde la semana 1
hay una cuenta de Oracle Cloud registrada para eso.

## Decisión

Oracle Cloud es un proveedor de servicios en la nube para productos Oracle. Uno de sus servicios, es el provisionamiento de hardware a través de la nube, que permite la creación de máquinas virtuales bajo demanda y bajo especificaciones dadas por el usuario. Se ofertan distintos planes, contando con un plan gratuito que permite el uso de 200 GB de espacio, 12 GB de memoria RAM y una selección básica de arquitecturas. 

Tanto el plan gratuito como los planes ofertados son restringidos por el uso de hardware, es decir, no está restringido por número de llamadas a APIs, conexiones de tiempo medido o uso de espacio. Si se requiere de más potencia computacional se actualiza a un plan superior. 

A continuación se muestran las ofertas del plan gratuito.

| Forma de Cómputo y Arquitectura | Procesador | Límite de Asignación (Siempre Gratis) | Descripción y Detalles de Configuración |
| --- | --- | --- | --- |
| **Microinstancia AMD** | (`VM.Standard.E2.1.Micro`) | AMD | Hasta **2 instancias** por arrendamiento | Cada instancia cuenta con **1/8 de OCPU** y **1 GB de RAM**. Ideal for tareas ligeras, microservicios o pequeños bots. |
| **Instancia de Cómputo Ampere A1** | (`VM.Standard.A1.Flex`) | Arm (Ampere Altra) | Hasta **1,500 horas de OCPU** y **9,000 horas de GB** por mes | Equivalente a un total de **4 OCPUs y 24 GB de RAM** por arrendamiento. Se puede configurar como una sola máquina virtual potente (ej. 4 OCPUs / 24 GB) o dividirse en varias máquinas virtuales más pequeñas (ej. 4 VMs con 1 OCPU / 6 GB cada una). |

Se ha seleccionado Oracle CLoud VM en su plan gratuito como plataforma a utilizar para alojar los servicios requeridos por el proyecto. El plan gratuito cubre las necesidades planteadas para el desarrollo del proyecto, además de contar con la flexibilidad de restricción de uso mencionadas anteriormente. Para esto, se trabajará con la Instancia de Cómputo Ampere A1, 12 GB RAM asignadas, 150GB de espacio en disco, 1 OCPU, y un sistema Operativo Ubuntu 26.04.

En conjunto, se ha seleccionado PostegreSQL como el administrador de base de datos en sustitución de Supabase, que se había planteado en el protocolo, debido a sus restricciones de uso en un plan gratuito. De está manera, evitamos perder tiempo migrando la arquitectura planteada a un nuevo sistema, así manteniendo el plan original sin sacrificar funcionalidades.


## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Supabase, plan gratuito | 500 MB contra ~1,373 MB que pesa el recorte. Y no está en el protocolo |
| Oracle Autonomous Database | Caben los 20 GB, pero no es PostgreSQL: habría que cambiar el adaptador de dbt y el protocolo lo especifica |
| Microinstancia AMD | Está más restringida en cuánto a configuración de la VM, se le permite menos potencia a comparación de la Ampere A1 | 

## Consecuencias

- La memoria, no el disco, es la restricción real: 12 GB para toda la pila ·
  responsable B · se verifica en la semana 9
- El laboratorio nacional de A deja de ser un punto único de falla · B · semana 9
- Si la VM deja de estar disponible por motivos de mantenimiento o algún error en la plataforma de Oracle, todo el sistema dejará de estar disponible. (fallo fatal de QoS)