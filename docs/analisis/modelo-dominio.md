# Modelo de dominio

<!-- Lo escribe C1 (Liseth) en T022 y T030 · viernes 18 de septiembre. -->

**Autora:** C1 · **Fecha:** 19 Sep 2026 · **Estado:** borrador

---

## Agregado 1 · Usuario

**Raíz:** Usuario

| Elemento | Tipo | Por qué |
|---|---|---|
| Usuario | Entidad | Tiene identidad propia que permanece aunque cambien sus atributos. |
| CorreoElectronico | Objeto de valor | Representa un correo electrónico validado y no tiene identidad propia. |
| ContraseñaCifrada | Objeto de valor | No tiene identidad propia, se compara por su valor y se reemplaza cuando cambia. |

**Reglas dentro del agregado:**

<!-- Cada regla tiene que poder ser un método de una clase, probable sin
     levantar Spring. Si no, está en el lugar equivocado. -->

- El correo electrónico debe tener un formato válido.
- La contraseña debe cumplir las condiciones de seguridad definidas por el sistema. **Pendiente de acordar las condiciones específicas.**

---

## Agregado 2 · Canasta

**Raíz:** Canasta

| Elemento | Tipo | Por qué |
|---|---|---|
| Canasta | Entidad | Tiene identidad propia y es la raíz del agregado. |
| LineaDeCanasta | Entidad local | Representa un artículo y su cantidad dentro de la canasta; no se accede desde afuera. |
| Cantidad | Objeto de valor | Representa la cantidad de unidades de un artículo, se valida por su valor y no tiene identidad propia. |
| UsuarioId | Referencia | Se referencia por identificador, no por objeto. |
| ReferenciaDeArticulo | Referencia | Identifica un artículo mediante producto + presentación, sin incluir la marca ni el objeto completo del catálogo. |

**Reglas dentro del agregado:**

- La canasta pertenece a exactamente un usuario y no puede cambiar de dueño.
- No puede haber dos líneas del mismo artículo; al agregar un artículo existente se suma la cantidad.
- La cantidad de cada línea debe ser un número entero mayor que cero.
- El costo estimado de la canasta se calcula y no se almacena.
- Las líneas de la canasta solo pueden modificarse a través de la raíz Canasta.

---

## Agregado 3 · Alerta

**Raíz:** Alerta

| Elemento | Tipo | Por qué |
|---|---|---|
| Alerta | Entidad | Tiene identidad propia porque representa una alerta específica que puede mantenerse y cambiar de estado. |
| UmbralDePrecio | Objeto de valor | Representa el precio límite que debe cumplirse para activar la alerta y no tiene identidad propia. |
| ReferenciaDeArticulo | Referencia | Identifica el artículo al que pertenece la alerta mediante producto + presentación, sin incluir la marca ni el objeto completo del catálogo. |
| UsuarioId | Referencia | Identifica al usuario que configuró la alerta sin incluir el objeto Usuario completo. |

**Reglas dentro del agregado:**

<!-- La condición exacta de activación todavía está pendiente de acordar:
     si se dispara cuando el precio es menor (<) o menor o igual (<=) al umbral. -->

- El umbral de precio debe ser un valor válido. **Pendiente de acordar las condiciones específicas de validez.**
- La alerta se dispara cuando el precio observado del artículo cumple la condición de activación acordada: **menor (<) o menor o igual (<=) al umbral establecido.**

---

## Objetos de valor compartidos

| Objeto de valor | Qué encapsula | Por qué no es un tipo primitivo |
|---|---|---|
| Dinero | Monto y moneda | Evita sumar pesos con dólares, y centraliza el redondeo |
| CorreoElectronico | Cadena validada | La validación vive en el tipo, no repartida en cada controlador |
| Cantidad | Número entero validado | Evita manejar cantidades inválidas y concentra la regla de que cada cantidad debe ser mayor que cero. |

---

## Reglas generales del modelo

- Una transacción toca un solo agregado.
- Entre agregados se referencia mediante identificadores, no mediante objetos completos.
- La identidad de un artículo está determinada por **producto + presentación**.
- Dos presentaciones diferentes del mismo producto corresponden a artículos diferentes.
- La `ReferenciaDeArticulo` representa esa identidad de producto + presentación, sin incluir la marca.
- El catálogo de productos y artículos vive fuera de estos tres agregados.

---

## Cobertura de los casos de uso

<!-- Verifica que el modelo cubre CU-08 a CU-12. Si un caso de uso no se puede
     expresar con estos agregados, falta algo. -->

| Caso de uso | Agregado que lo soporta | ¿Cubierto? |
|---|---|---|
| CU-08 Registrar cuenta e iniciar sesión | Usuario | Parcial |
| CU-09 Crear y editar una canasta | Canasta | Sí |
| CU-10 Configurar una alerta de precio | Alerta | Parcial |
| CU-11 Notificar cuando la alerta se dispara | Alerta | Pendiente |
| CU-12 Buscar producto y comparar | — (consulta a la interfaz analítica / catálogo externo) | Sí |

---

## Lo que C2 necesita saber de esto

<!-- Lo que decidas aquí es lo que la app móvil va a consumir. Si defines que
     una canasta tiene máximo de ítems, Oscar lo necesita para la pantalla.
     Coméntaselo antes del lunes. -->

- Los agregados Usuario, Canasta y Alerta son independientes entre sí.
- Las referencias entre agregados se realizan mediante identificadores (`UsuarioId` y `ReferenciaDeArticulo`), no mediante objetos completos.
- Una `ReferenciaDeArticulo` representa un artículo identificado por producto + presentación, sin incluir la marca.
- El catálogo de productos y artículos se encuentra fuera de estos tres agregados.
- La cantidad de cada línea debe ser un número entero mayor que cero.
- No se permiten artículos duplicados dentro de una canasta; al agregar un artículo existente se suma su cantidad.
- Una canasta pertenece a exactamente un usuario y no puede cambiar de dueño.
- El costo estimado de la canasta se calcula y no se almacena.
- La condición exacta para activar una alerta está pendiente de acordar entre `<` y `<=`.

## Diagrama de clases

```mermaid
classDiagram

    class Usuario {
        -String id
        -CorreoElectronico correo
        -Instant fechaDeRegistro
        -String contrasenaCifrada
        -String nombre
        +Usuario(String id, CorreoElectronico correo, String contrasenaCifrada, String nombre, Instant fechaDeRegistro)
        +cambiarContrasena(String yaCifrada) void
        +renombrar(String nuevo) void
        +id() String
        +correo() CorreoElectronico
        +nombre() String
        +fechaDeRegistro() Instant
        +contrasenaCifrada() String
    }

    class CorreoElectronico {
        <<record>>
        +String valor
    }

    class Canasta {
        -String id
        -String usuarioId
        -List~LineaDeCanasta~ lineas
        -String nombre
        +Canasta(String id, String usuarioId, String nombre)
        +renombrar(String nuevo) void
        +agregar(ReferenciaDeArticulo articulo, Cantidad cantidad) void
        +quitar(ReferenciaDeArticulo articulo) void
        +lineas() List~LineaDeCanasta~
        +id() String
        +usuarioId() String
        +nombre() String
    }

    class LineaDeCanasta {
        <<record>>S
        +ReferenciaDeArticulo articulo
        +Cantidad cantidad
        +sumar(Cantidad extra) LineaDeCanasta
    }

    class ReferenciaDeArticulo {
        <<record>>
        +String producto
        +String presentacion
    }

    class Cantidad {
        <<record>>
        +int unidades
        +mas(Cantidad otra) Cantidad
    }

    Usuario --> CorreoElectronico
    Canasta "1" --> "*" LineaDeCanasta
    LineaDeCanasta --> ReferenciaDeArticulo
    LineaDeCanasta --> Cantidad
    Canasta --> Usuario : usuarioId
  ```