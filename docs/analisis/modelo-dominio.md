# Modelo de dominio

<!-- Lo escribe C1 (Liseth) en T012 · viernes 4 de septiembre.

     Los TRES agregados ya están nombrados en el protocolo: Usuario, Canasta y
     Alerta. No inventes otros. Tu trabajo es decidir qué hay DENTRO de cada uno.

     La pregunta que separa entidad de objeto de valor:
     ¿tiene identidad propia que persiste aunque cambien sus atributos?
       Sí  → entidad          (dos usuarios con el mismo nombre son distintos)
       No  → objeto de valor  (dos precios de $24.50 MXN son el mismo)

     Las dos reglas de los agregados:
       1. Una transacción toca un solo agregado
       2. Entre agregados se referencia por identificador, no por objeto -->

**Autora:** C1 · **Fecha:** _______ · **Estado:** borrador

---

## Agregado 1 · Usuario

**Raíz:** Usuario

| Elemento | Tipo | Por qué |
|---|---|---|
| Usuario | Entidad | |
| CorreoElectronico | Objeto de valor | |
|  |  |  |

**Reglas dentro del agregado:**

<!-- Cada regla tiene que poder ser un método de una clase, probable sin
     levantar Spring. Si no, está en el lugar equivocado. -->

- 
- 

---

## Agregado 2 · Canasta

**Raíz:** Canasta

| Elemento | Tipo | Por qué |
|---|---|---|
| Canasta | Entidad | |
| ItemDeCanasta | Entidad local | Identidad solo dentro de la canasta; no se accede desde afuera |
| Cantidad | Objeto de valor | |
| UsuarioId | Referencia | Se referencia por identificador, no por objeto |
|  |  |  |

**Reglas dentro del agregado:**

- No puede haber dos ítems del mismo producto; se suma la cantidad
- 
- 

---

## Agregado 3 · Alerta

**Raíz:** Alerta

| Elemento | Tipo | Por qué |
|---|---|---|
| Alerta | Entidad | |
| UmbralDePrecio | Objeto de valor | |
|  |  |  |

**Reglas dentro del agregado:**

<!-- La central: "una alerta se dispara cuando el precio observado cae por
     debajo del umbral". Es un método de Alerta, no una consulta SQL. -->

- 
- 

---

## Objetos de valor compartidos

| Objeto de valor | Qué encapsula | Por qué no es un tipo primitivo |
|---|---|---|
| Dinero | Monto y moneda | Evita sumar pesos con dólares, y centraliza el redondeo |
| CorreoElectronico | Cadena validada | La validación vive en el tipo, no repartida en cada controlador |
|  |  |  |

---

## Cobertura de los casos de uso

<!-- Verifica que el modelo cubre CU-08 a CU-12. Si un caso de uso no se puede
     expresar con estos agregados, falta algo. -->

| Caso de uso | Agregado que lo soporta | ¿Cubierto? |
|---|---|---|
| CU-08 Registrar cuenta e iniciar sesión | Usuario | |
| CU-09 Crear y editar una canasta | Canasta | |
| CU-10 Configurar una alerta de precio | Alerta | |
| CU-11 Notificar cuando la alerta se dispara | Alerta | |
| CU-12 Buscar producto y comparar | — (consulta a la interfaz analítica) | |

---

## Lo que C2 necesita saber de esto

<!-- Lo que decidas aquí es lo que la app móvil va a consumir. Si defines que
     una canasta tiene máximo de ítems, Oscar lo necesita para la pantalla.
     Coméntaselo antes del lunes. -->

- 

---

## Dudas para la reunión del lunes

1. 
