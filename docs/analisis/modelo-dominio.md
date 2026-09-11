# Modelo de dominio

<!-- Lo escribe C1 (Liseth) en T012 · martes 8 de septiembre.

     Los TRES agregados ya están nombrados en el protocolo: Usuario, Canasta y
     Alerta. No inventes otros. Tu trabajo es decidir qué hay DENTRO de cada uno.

     La pregunta que separa entidad de objeto de valor:
     ¿tiene identidad propia que persiste aunque cambien sus atributos?
       Sí  → entidad          (dos usuarios con el mismo nombre son distintos)
       No  → objeto de valor  (dos precios de $24.50 MXN son el mismo)

     Las dos reglas de los agregados:
       1. Una transacción toca un solo agregado
       2. Entre agregados se referencia por identificador, no por objeto -->

**Autora:** C1 · **Fecha:** 08 Sep 2026 · **Estado:** borrador

---

## Agregado 1 · Usuario

**Raíz:** Usuario
| Elemento | Tipo | Por qué |
|---|---|---|
| Usuario | Entidad | Tiene identidad propia que permanece aunque cambien sus atributos. |
| CorreoElectronico | Objeto de valor | Representa un correo electrónico validado y no tiene identidad propia. |
| Contraseña | Objeto de valor | Puede cambiar sin modificar la identidad del usuario. |
**Reglas dentro del agregado:**

<!-- Cada regla tiene que poder ser un método de una clase, probable sin
     levantar Spring. Si no, está en el lugar equivocado. -->

- El correo electrónico debe tener un formato válido.
- La contraseña debe cumplir las condiciones de seguridad definidas por el sistema.

---

## Agregado 2 · Canasta

**Raíz:** Canasta
| Elemento | Tipo | Por qué |
|---|---|---|
| Canasta | Entidad | Tiene identidad propia y es la raíz del agregado. |
| ItemDeCanasta | Entidad local | Identidad solo dentro de la canasta; no se accede desde afuera. |
| Cantidad | Objeto de valor | Representa la cantidad de unidades de un producto y debe ser válida. |
| UsuarioId | Referencia | Se referencia por identificador, no por objeto. |
| ProductoId | Referencia | Se referencia por identificador, no por objeto. |

**Reglas dentro del agregado:**

- No puede haber dos ítems del mismo producto; se suma la cantidad.
- La cantidad de un producto debe ser un número entero mayor que cero.
- Los ítems de la canasta solo pueden modificarse a través de la raíz Canasta.

---

## Agregado 3 · Alerta

**Raíz:** Alerta
| Elemento | Tipo | Por qué |
|---|---|---|
| Alerta | Entidad | Tiene identidad propia porque representa una alerta específica que puede mantenerse y cambiar de estado. |
| UmbralDePrecio | Objeto de valor | Representa el precio límite que debe cumplirse para activar la alerta y no tiene identidad propia. |
| ProductoId | Referencia | Identifica el producto al que pertenece la alerta sin incluir el objeto Producto completo. |
| UsuarioId | Referencia | Identifica al usuario que configuró la alerta sin incluir el objeto Usuario completo. |

**Reglas dentro del agregado:**

<!-- La central: "una alerta se dispara cuando el precio observado cae por
     debajo del umbral". Es un método de Alerta, no una consulta SQL. -->

- El umbral de precio debe ser un valor válido.
- La alerta se dispara cuando el precio observado del producto es menor o igual al umbral establecido.

---

## Objetos de valor compartidos

| Objeto de valor | Qué encapsula | Por qué no es un tipo primitivo |
|---|---|---|
| Dinero | Monto y moneda | Evita sumar pesos con dólares, y centraliza el redondeo |
| CorreoElectronico | Cadena validada | La validación vive en el tipo, no repartida en cada controlador |
|  |  |  |
| Cantidad | Número entero validado | Evita manejar cantidades inválidas y concentra la regla de que una cantidad debe ser mayor que cero. |
---

## Cobertura de los casos de uso

<!-- Verifica que el modelo cubre CU-08 a CU-12. Si un caso de uso no se puede
     expresar con estos agregados, falta algo. -->

| Caso de uso | Agregado que lo soporta | ¿Cubierto? |
|---|---|---|
| CU-08 Registrar cuenta e iniciar sesión | Usuario | Sí |
| CU-09 Crear y editar una canasta | Canasta | Sí |
| CU-10 Configurar una alerta de precio | Alerta | Sí |
| CU-11 Notificar cuando la alerta se dispara | Alerta | Sí |
| CU-12 Buscar producto y comparar | — (consulta a la interfaz analítica) | Sí |

---

## Lo que C2 necesita saber de esto

<!-- Lo que decidas aquí es lo que la app móvil va a consumir. Si defines que
     una canasta tiene máximo de ítems, Oscar lo necesita para la pantalla.
     Coméntaselo antes del lunes. -->

- - Los agregados Usuario, Canasta y Alerta son independientes entre sí.
- Las referencias entre agregados se realizan mediante identificadores (UsuarioId y ProductoId), no mediante objetos completos.
- La cantidad de productos en una canasta debe ser un número entero mayor que cero.
- No se permiten productos duplicados dentro de una canasta; al agregar un producto existente se suma su cantidad.
- Una alerta se activa cuando el precio observado es menor o igual al umbral configurado.

<!-- Por definirse -->
---

## Dudas para la reunión del lunes


1. ¿ Sesión es dominio o infraestructura? Si Spring Security la maneja, no debería vivir en el
paquete domain .
2. ¿ Producto y Establecimiento son "punto de
contacto con C2" que pide la ficha: si Dominio solo guarda un Productold , la app móvil
necesita otro sitio de dónde sacar el nombre/precio para mostrarlo. Coméntalo antes del
viernes.
3. ¿ Notificación tiene historial (pendiente/enviada/leída) o es un evento sin persistencia?
Decide si es Entidad o Evento de dominio.
4. Los flujos alternos completos de CU-08 a CU-12 (formato Cockburn) todavía no existen —
solo el título. Sin eso, las reglas de arriba son un primer borrador, no definitivas.
