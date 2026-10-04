# Prototipo y Puntos de Quiebre

**Enlace al prototipo cerrado en Figma:** [Prototipo CanastaMX 3.0](https://www.figma.com/make/yUK7s2m2NoGCHGk6vAkSTZ/CanastaMX-3.0)

## Definición de Puntos de Quiebre
El sistema se adapta mediante tres puntos de quiebre principales:
- **Teléfono (Móvil):** Hasta 768 px.
- **Tableta:** 769 px a 1024 px.
- **Escritorio (Web):** Desde 1025 px.

*Nota sobre consolas (pantallas menores a 1025 px):* Las consolas de Operador y Analista son exclusivas de escritorio. En resoluciones menores a 1025 px, el sistema muestra un aviso de ancho mínimo requerido y habilita el desplazamiento horizontal.

## Comportamiento por Vista

### 1 · Acceso (Web y Móvil)
- **Comportamiento:** Se adapta a los tres anchos (carrusel dividido en web, capas en móvil).
- **Nota:** La barra superior de perfiles (Operador, Analista, App) existe únicamente para facilitar la navegación en el prototipo. El sistema final no cuenta con selectores de rol visibles.

### 2 · Tablero analítico (Web)
- **Comportamiento:** Exclusivo para escritorio (desde 1025 px). Gráficos y filtros en panel completo.

### 3 · Detalle de artículo (Web)
- **Comportamiento:** Exclusivo para escritorio. Despliegue de histórico a 12 meses y tabla comparativa.

### 4 · Consola de observabilidad (Web)
- **Comportamiento:** Exclusivo para escritorio. 

### 5 · Cola de reconciliación (Web)
- **Comportamiento:** Exclusivo para escritorio. Tabla de diccionario en formato ancho.

### 6 · Búsqueda y Catálogos (Móvil)
- **Comportamiento:** Exclusivo móvil (hasta 768 px).
- **Detalle de artículo (App):** Se abre como pantalla dentro de esta misma vista. Despliega el ícono de su catálogo (ADR 010 · 6). El interruptor de monitoreo abre el umbral de precio dentro del rango histórico (CU-10) y la alerta se dispara cuando el precio es menor o igual.

### 7 · Mi canasta (Móvil)
- **Comportamiento:** Exclusivo móvil. La lista de artículos se divide por cadena comercial.

### 8 · Cuenta y Alertas (Móvil)
- **Comportamiento:** Exclusivo móvil.