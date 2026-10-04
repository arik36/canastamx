# Sistema de Diseño - CanastaMX

## 1. Colores y Reglas Semánticas
Están declarados como variables en `index.css`:
- **Turquesa (Principal):** `#23BBB7`
- **Crema (Fondo base):** `#F0EADF`
- **Tinta (Texto):** `#2F2F2F`
- **Verde (Éxito):** `#00A859`
- **Rojo (Peligro):** Uso estricto SOLO para incidentes y fallos del sistema.
- **Naranja (Advertencia):** Uso estricto SOLO para anomalías de mercado (ej. variaciones de precio).

## 2. Tipografía
- **Familia:** `Inter`, sans-serif.
- **Tamaños base:** Títulos grandes a `24px`, subtítulos a `18px`/`14px`, y metadatos a `11px`.

## 3. Radios y Espaciado
- **Radios:** Tarjetas a `16px`, modales a `24px`, botones a `12px` o totalmente redondos (píldoras).
- **Espaciado:** Escala basada en múltiplos de `4px` (ej. padding de `16px` o `20px`).

## ENLACE A FIGMA: 
https://www.figma.com/make/yUK7s2m2NoGCHGk6vAkSTZ/CanastaMX-3.0?t=5QeO3L2hmrAGrZqX-1

## Puntos de Quiebre (App y Web)
- **Móvil:** Hasta 768 px
- **Tableta:** 769 px a 1024 px
- **Escritorio:** Desde 1025 px

## Semántica de Colores (Alertas y Estados)
El sistema utiliza la siguiente paleta alineada a los estados del contrato (*Nota para C2 / Renato: favor de replicar estos valores en `clients/mobile/theme/design-system.ts`*):
- **OK:** Verde `#16A34A`
- **Aviso:** Naranja `#F59E0B`
- **Bloquea / Incidente:** Rojo `#DC2626`