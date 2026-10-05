# Pliego de correcciones del protocolo

> **Qué es.** Lo que el protocolo entregado dice y ya no es cierto, porque una
> decisión posterior lo cambió. El protocolo vive en Drive, en Word. Estas
> correcciones se aplican ahí **en una sola pasada antes del 9 de octubre**, y aquí
> se marcan como aplicadas, con la fecha.
>
> Lo citan `docs/datos/informe-perfilado-v1.md` y el ADR 014.

| # | Dónde | Dice | Debe decir | Por qué | Estado |
|---|---|---|---|---|---|
| 1 | §8 · Alcances | «Recorte geográfico a Guanajuato y tres entidades vecinas» | «Recorte a siete entidades: Aguascalientes, Guanajuato, Jalisco, Michoacán, Querétaro, San Luis Potosí y Zacatecas» | Contrato 1.3.3 · `alcance.entidades` | Por aplicar |
| 2 | §8 · Alcances, mismo párrafo | «con ventana temporal de 2024 a 2026» | «con ventana del 1 de enero de 2025 al 31 de julio de 2026» | Contrato · `alcance.ventana`. La fuente no publica después de julio de 2026 | Por aplicar |
| 3 | §8 · Alcances, mismo párrafo | «un volumen estimado entre dos y cuatro millones de registros» | «2,658,906 registros, medidos en la ingesta a la capa cruda» | Consolidado de la ingesta (T020), 2 de octubre | Por aplicar |
| 4 | §4 · Diferenciación, tabla, fila «Histórico» | «Serie 2024–2026» | «Serie de enero de 2025 a julio de 2026» | La misma que la 2 | Por aplicar |

## Lo que se revisó y no necesita corrección

- **H3.** Se mide como está enunciada en el protocolo: cobertura del 85% y precisión
  del 90% sobre 200 pares (ADR 014). El ADR 013, que la reenunciaba, quedó retirado,
  así que no hay nada que reenunciar.
- **H5.** Nunca entró al protocolo.

## Cuando se apliquen

Cambia «Por aplicar» por «Aplicada el …» en cada fila, en un PR. La entrega del 9 se
arma con el protocolo ya corregido.
