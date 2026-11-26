# T072 · Versión final móvil (#215)

Estado: implementación revisada y aceptada por el responsable para preparar el
PR. La aceptación comunicada es **un teléfono Android y BlueStacks**. El issue
original solicita dos teléfonos distintos; se registra la variación aceptada
sin presentar el emulador como un segundo teléfono físico.

## Resultado

- Registro de consumidor desde Acceso mediante `POST /api/v1/cuentas`;
  validación, confirmación de contraseña y mensaje de correo duplicado.
- Sesión real, perfil consultado en el dominio y token guardado con SecureStore.
- Inicio con selección de artículos y búsqueda por entidad/catálogo; comparación
  por establecimiento, marca, fecha y quincena.
- Canastas persistentes: crear, seleccionar, renombrar, eliminar con confirmación,
  agregar/quitar artículos y editar cantidades. Recuperación antes de repetir
  una escritura cuya respuesta se perdió.
- Descubrir conserva su pestaña y muestra que no está disponible. La ruta de
  alertas redirige a Cuenta, conforme al recorte aprobado.
- Interfaz nativa adaptada a App_Karen, selección directa de las 32 entidades,
  paneles desplazables con teclado, controles de cantidad y botón fijo del detalle.
- Imágenes locales ilustrativas por producto y presentación; variantes sin una
  correspondencia segura muestran un recurso neutro. No representan una marca
  ni envase exactos. [Fuentes y prompts](../assets/README.md).

La referencia App_Karen no se modifica. Precios, cuentas y canastas vienen de
los servicios; los datos ficticios del prototipo no se incorporan a la app.

## Servicios públicos y compilación

- Dominio: https://dominio.canastamx.duckdns.org
- Analítica: https://analitica.canastamx.duckdns.org

Las direcciones están versionadas en `servidores-publicos.json`. Con Node 20,
JDK 21 y SDK Android configurados:

```powershell
npm.cmd ci
npm.cmd run typecheck
npm.cmd test
npm.cmd run build:android -- -ServidoresPublicos
```

El guion genera `artifacts/canastamx-servidores.apk`, con recursos y JavaScript
incluidos, y usa una copia temporal corta si la ruta de Windows es larga.
La app necesita internet y servidores disponibles; funciona sin los procesos
locales del equipo. HTTP sin cifrar está desactivado.

El modo `-ValidacionLocal` conserva la prueba aislada con servicios locales.
EAS es otra opción documentada en el [README](../README.md); ni #215 ni ADR 006
exigen usar ese proveedor ni publicar en una tienda.

## APK validado

| Dato | Valor |
|---|---|
| Archivo entregado | `artifacts/canastamx-servidores-v10.apk` |
| SHA-256 | `D3A7E1587559257251A88F9E312BE544A5752CEC10E22FDA461598B52B034940` |
| Tamaño | 67 124 517 bytes |
| Paquete / versión | `mx.tecnm.canastamx` · 1.0.0 (1) |
| Android / arquitecturas | mínimo 24 · ARM64 y x86_64 |
| Firma | Android Debug, misma identidad de las revisiones anteriores |
| Certificado SHA-256 | `fac61745dc0903786fb9ede62a962b399f7348f0bb6f899b8332667591033b9c` |

Apksigner verifica el APK. El archivo extraído de BlueStacks coincide por
SHA-256 con v10. La firma debe conservarse para actualizar estas instalaciones;
una identidad posterior de distribución debe decidirse explícitamente.

## Verificación del 25 de noviembre de 2026

- Ejecución final de preparación del PR: **67/67 pruebas pasan** con Node 20.
  Cubren acceso/registro, sesión, contratos, canastas, protección entre cuentas,
  simulador, configuración de build y clasificación de imágenes.
- TypeScript sin errores y APK Android compilado.
- Health de Dominio y Analítica: HTTP 200, `UP`.
- Funciones reales del cliente contra los servicios públicos, con validación de
  respuesta: búsqueda de leche/Básicos/Guanajuato en 0.90 s (32 coincidencias);
  comparación en 1.76 s (45 registros); costo de una línea sin guardar en 1.76 s
  (11 cadenas). Datos no simulados, quincena 2026-07-Q2.
- Revisión del Android abierto: Inicio con imágenes diferenciadas, comparación
  con precios reales y botón Agregar completo. Se volvió a Inicio sin modificar
  las canastas del responsable.
- El responsable confirmó registro, inicio de sesión, búsqueda, comparación y
  canasta en su teléfono y en BlueStacks y solicitó dar esas pruebas por válidas.

La auditoría de servicios no creó cuentas ni modificó canastas públicas. Las
pruebas optativas `t072-real.cjs` y `t056-real.cjs` se ejecutan sólo contra una
base local aislada; su ejecución anterior no se presenta como prueba de la VM.

## Evidencia y criterio de aceptación

[Capturas Android y procedencia](evidencia/t072-final/README.md):

- [Inicio v10](evidencia/t072-final/01-inicio-v10.png).
- [Detalle v10 y botón visible](evidencia/t072-final/02-detalle-v10.png).
- Portada, acceso, registro, Cuenta y Descubrir: capturas aportadas durante la
  revisión visual previa, etiquetadas como tales en el índice.

No se dispone de captura/modelo del teléfono para adjuntar. La conformidad con
teléfono + emulador es una aceptación expresa del responsable; queda expuesta
a quien revise el PR para no atribuir evidencia de dos teléfonos físicos.

## Alcance y observaciones

- Inicio ofrece una selección por varias búsquedas, no un catálogo exhaustivo.
  Orden y rango de precios se aplican a los artículos cargados, como indica la UI.
- La búsqueda admite hasta cinco minutos; detalle/costo conservan ocho segundos.
  En la auditoría respondieron en menos de dos, pero la carga del servidor puede
  variar. Se conserva cancelación al cambiar criterios.
- No hay cobertura de todas las entidades ni una foto para cada variante
  desconocida. Los avisos de falta de datos permanecen.
- Los costos por cadena son independientes; un faltante no se cuenta como cero
  ni se suman cadenas para inventar un total.
- Falta completar revisión del PR e integración para cerrar #215. La aceptación
  del responsable y las verificaciones no equivalen a probar todos los modelos
  Android.

El historial local de iteraciones se conserva fuera del diff de entrega, junto
a los APK anteriores, en `artifacts/`.
