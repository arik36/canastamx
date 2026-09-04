# Plantilla de ficha de tarea

Copia esto para cada tarea de la semana que empieza. **Se llenan en la reunión semanal**, con todos presentes, en los últimos diez minutos. Escribirlas es parte de cerrar la reunión.

Una ficha bien escrita toma cinco minutos y ahorra medio día. La parte que más cuesta escribir —«antes de empezar, verifica»— es la que más rinde: es la que evita que alguien trabaje dos días sobre un insumo que no existe.

---

```markdown
## T0__ · [A / B / C1 / C2 / D / Equipo] · [Título en imperativo]

**Tiempo estimado:** __ horas

### Qué entregas

[El artefacto concreto, con su ruta exacta en el repositorio. No «avanzar en X»:
 «existe el archivo Y con la tabla Z llena».]

### Antes de empezar, verifica

- [ ] [Insumo 1 — qué tiene que existir ya, y quién lo produce]
- [ ] [Insumo 2 — herramienta instalada, con el comando que lo comprueba]
- [ ] [Insumo 3 — decisión tomada, con dónde está escrita]

### Depende de · Bloquea a

**Depende de:** T0__ ([qué tarea y de quién])
**Bloquea a:** T0__ ([a quién dejas detenido si no terminas])

**Cuando termines, avísale a:** [nombre], porque [qué destraba].

### Lo que necesitas saber

[Los conceptos, explicados AQUÍ. No un enlace a documentación de 400 páginas.
 Si algo ya está definido en el protocolo o en otro documento del equipo,
 TRANSCRÍBELO, no lo cites: quien lee la ficha a las once de la noche no va
 a ir a buscarlo.]

[Si hay una ambigüedad conocida —dos formas de entender la tarea— resuélvela
 aquí de forma explícita. Es lo que más tiempo ahorra.]

### Paso a paso

1. [Acción concreta, con el comando exacto si aplica]
2. [...]
3. [Cómo se verifica que ese paso quedó]

### Cómo se ve terminado

[El esqueleto del archivo, la salida esperada de un comando, o la captura que
 hay que subir al issue. Algo que otra persona pueda contrastar sin discutir.]

### Errores frecuentes

| Qué pasa | Por qué | Salida |
|---|---|---|
| [Mensaje o síntoma exacto] | [Causa] | [Qué hacer] |
```

---

## Las seis preguntas que la ficha tiene que contestar

Si al terminar de escribirla no puedes contestar estas seis, la ficha está incompleta:

1. **¿Cuándo sé que terminé?** — un hecho verificable por otra persona, no una sensación.
2. **¿Qué necesito que exista antes?** — con nombre de quién lo produce.
3. **¿A quién dejo detenido si no termino?** — para que sepa a quién avisar.
4. **¿Qué tengo que entender para hacerlo?** — explicado en la ficha, no afuera.
5. **¿Cómo se ve el resultado?** — un esqueleto, una salida, una captura.
6. **¿Qué me va a salir mal?** — los dos o tres errores que sabemos que aparecen.

## Reglas al escribirlas

**Transcribe, no cites.** Si los seis indicadores están en el protocolo, van copiados en la ficha. Un enlace a un documento de treinta páginas es una barrera, no una ayuda.

**Resuelve las ambigüedades por escrito.** «Las tres capas» puede significar dos cosas distintas. La ficha dice cuál, y por qué. Esa línea vale más que el resto de la ficha.

**Nombra a las personas.** «Pregúntale a A» sirve más que «consulta la documentación», porque en un equipo remoto el problema nunca es que la información no exista: es no saber a quién preguntarle.

**No la escribas sola.** La ficha de una tarea de C1 la escribe C1, en la reunión, con los demás oyendo. Quien va a hacer el trabajo es quien sabe qué le falta.
