(.venv) mlizz@GAMINGARI:~/projects/canastamx$ python docs/datos/perfilado/verificar-precios.py
==============================================================================
El alcance que el contrato declara · cinco catálogos del ADR 005
==============================================================================
  Recorte territorial (lo que mide medir-decisiones.py) :  4,384,962
  Dentro de los cinco catálogos (lo que ingiere)        :  2,658,906  (60.64%)
  Fuera del alcance                                     :  1,726,056  (39.36%)

  Las 77,670 colisiones del yaml están medidas sobre la primera
  cifra, no sobre la segunda. Lo que sigue las vuelve a medir sobre
  el alcance de verdad.

── Los supuestos del yaml sobre `precio`, dentro del alcance
   filas                                : 2,658,906
   nulos  (yaml dice: ninguno permitido): 0
   en cero                              : 0
   negativos                            : 0
   por debajo de 0.01 (yaml: `minimo`)  : 0

==============================================================================
El REVISAR de `precio.maximo` · qué techo aguanta
==============================================================================
           catalogo   filas  minimo  mediano   p99   p999  maximo
pescados y mariscos   42955    27.9    153.0 670.0 1300.0  1775.0
           mercados  104409     3.5     50.0 400.0  650.0   850.0
            basicos 2105019     1.5     44.9 404.0  584.0   769.9
 frutas y legumbres  237440     3.0     38.0 180.0  399.9   498.0
              pacic  169083     3.5     26.5 204.0  252.9   299.0

  Si el máximo de un catálogo está muy arriba de su p999, ese máximo
  es un caso aislado y no sirve de frontera. Si están pegados, el
  catálogo de verdad llega hasta ahí.

── Cuántas filas rechazaría cada techo, hoy
                                filas_que_rechaza
1775 · el máximo exacto medido                  0
2000 · redondeado hacia arriba                  0
2041 · el medido +15%                           0
2663 · el medido +50%                           0

  Todos rechazan 0 o casi 0 sobre lo ya medido: es el pasado. La
  ventana está abierta (`hasta: null`), así que el techo tiene que
  aguantar las quincenas que faltan, no las que ya están.

── Los quince máximos mensuales más altos
    mes            catalogo  maximo
2026-03 pescados y mariscos  1775.0
2026-06 pescados y mariscos  1775.0
2026-04 pescados y mariscos  1775.0
2026-01 pescados y mariscos  1775.0
2026-05 pescados y mariscos  1775.0
2026-02 pescados y mariscos  1775.0
2026-07 pescados y mariscos  1775.0
2025-06 pescados y mariscos  1690.0
2025-07 pescados y mariscos  1690.0
2025-10 pescados y mariscos  1690.0
2025-08 pescados y mariscos  1690.0
2025-04 pescados y mariscos  1690.0
2025-09 pescados y mariscos  1690.0
2025-11 pescados y mariscos  1690.0
2025-03 pescados y mariscos  1690.0

  Si 1775 aparece un solo mes, no calibres el techo con él.

==============================================================================
Las colisiones, medidas sobre lo que el contrato sí ingiere
==============================================================================
        clase  grupos  filas_sobrantes  diferencia_promedio  diferencia_maxima
  de centavos   72629          72631.0                 0.00               0.95
  de $1 a $50    2089           2105.0                17.68              50.00
de más de $50     256            256.0                72.25             200.00

  Suma de filas_sobrantes: 74,992
  El yaml dice 77,670, medido sobre 4,384,962 filas.
  Este número está medido sobre 2,658,906. Es el que va al contrato,
  junto con sus porcentajes recalculados para `que_se_hace`.

==============================================================================
El bucket de «más de $50», abierto por catálogo
==============================================================================
          catalogo  en_alcance  grupos  diferencia_promedio  diferencia_maxima
 electrodomesticos       False      98              1525.59           15100.00
  utiles escolares       False       9               486.49            1000.00
      medicamentos       False     121               152.17             724.99
          juguetes       False       8               153.50             314.00
frutas y legumbres        True      90                83.19             200.00
           basicos        True     151                65.75             144.00
          mercados        True      15                72.00             140.00

  En los cinco catálogos del ADR 005 el precio máximo es 1775, así
  que ahí ninguna diferencia puede pasar de 1775. Toda diferencia por
  encima de eso viene de un catálogo que el contrato NO ingiere.

── Las veinte colisiones más grandes, fila por fila
         catalogo  en_alcance                producto                                                                                                                 presentacion     marca  precio_min  precio_max  diferencia  razon sospecha
electrodomesticos       False        Centro de Lavado                                                 7 Mwgt 4027 Hw0 o Hw1. 20 Kgs. Agitador. Secado y Centrifugado. Color Blanco Whirlpool    26999.00    42099.00    15100.00   1.56
electrodomesticos       False        Centro de Lavado                                                 7 Mwgt 4027 Hw0 o Hw1. 20 Kgs. Agitador. Secado y Centrifugado. Color Blanco Whirlpool    27129.00    42049.00    14920.00   1.55
electrodomesticos       False        Centro de Lavado                                                 7 Mwgt 4027 Hw0 o Hw1. 20 Kgs. Agitador. Secado y Centrifugado. Color Blanco Whirlpool    29699.00    42099.00    12400.00   1.42
electrodomesticos       False      Bocinas Port?tiles                                                                                                 Srs-ult1000. Usb y Bluetooth      Sony    19599.00    26699.00     7100.00   1.36
electrodomesticos       False          Refrigeradores                                              Vs 27 Bxqp (silver). 789 L. 2 Puertar Verticales. Deshielo Automático Ajustable        Lg    25599.36    31999.20     6399.84   1.25
electrodomesticos       False          Refrigeradores                                 Lt 57 Bpsx (plata). 572 Dm3. 2 Puertas, Horizontal y Vertical. Deshielo Automático Ajustable        Lg    13499.00    19799.00     6300.00   1.47
electrodomesticos       False                 Estufas                                                       Wfr 5200 D00. 30 Plgs. 6 Quemadores Encendido Electrónico. Color Acero Whirlpool     8499.00    13699.00     5200.00   1.61
electrodomesticos       False               Lavadoras                                                                 7 Mwtw 1904 Lm0. 19 Kg. Agitador. Centrifugado. Color Blanco Whirlpool    11999.00    17199.00     5200.00   1.43
electrodomesticos       False               Lavadoras                                                                 7 Mwtw 1904 Lm0. 19 Kg. Agitador. Centrifugado. Color Blanco Whirlpool    11999.00    17199.00     5200.00   1.43
electrodomesticos       False               Lavadoras                                                                        Wt 18 Mv6. 18 Kg. Impulsor. Centrifugado. Color Negro        Lg    11199.20    15999.00     4799.80   1.43
electrodomesticos       False Computadoras Portátiles Ideapad Slim 3 15amn8. 82xq0009lm. Laptop (azul). Amd Ryzen 5/windows 11. Disco Duro 512 Gb Ssd/memoria Ram 8 Gb. 15.6 Plgs.    Lenovo     7499.00    11799.00     4300.00   1.57
electrodomesticos       False                 Estufas                                               Wfr 3100 B00. Frente 30 Plgs. 6 Quemadores. Encendido Electrónico. Color Acero Whirlpool     7699.00    10299.00     2600.00   1.34
electrodomesticos       False               Lavadoras                                                                8 Mwtw 2224 Wjm0. 22 Kg. Agitador. Centrifugado. Color Blanco Whirlpool     9999.00    12299.00     2300.00   1.23
electrodomesticos       False               Pantallas                                                                                 55a65nv. 55 Plgs. Led. Puerto Usb. Smart Tv.   Hisense     5999.00     8299.00     2300.00   1.38
electrodomesticos       False                  Tablet                                                         Tab M11. Tb330fu. 11 Plgs. Memoria Interna 128 Gb. Memoria Ram 8 Gb.    Lenovo     3499.00     5699.00     2200.00   1.63
electrodomesticos       False                 Estufas                                                       Aw 5300 D01. 20 Plgs. 4 Quemadores. Encendido Manual. Color Gris/acero     Acros     4699.00     6799.00     2100.00   1.45
electrodomesticos       False   Electrónicos de Video                                                             Switch Oled. White. Mario Kart 8. 64 Gb. Mario Kart 8 (descarga)  Nintendo     6999.00     8999.00     2000.00   1.29
electrodomesticos       False          Refrigeradores                                 Lt 57 Bpsx (plata). 572 Dm3. 2 Puertas, Horizontal y Vertical. Deshielo Automático Ajustable        Lg    13999.00    15799.00     1800.00   1.13
electrodomesticos       False               Lavadoras                                        Lma 74215 Wbab0 o Wbab00 o Wbab1 o Wbab10. 24 Kg. Agitador. Centrifugado Color Blanco      Mabe    11219.32    12863.52     1644.20   1.15
electrodomesticos       False               Lavadoras                                                                 7 Mwtw 1904 Lm0. 19 Kg. Agitador. Centrifugado. Color Blanco Whirlpool    12036.94    13641.86     1604.92   1.13

  `razon` = precio_max / precio_min. En 10, 100 o 1000 clavado es
  error de captura. En 1.4 es precio. Esta tabla es la que se anexa
  al PR: quien revise mira filas, no promedios.

==============================================================================
Qué hacer con estas cifras
==============================================================================
  · `colisiones_conocidas` y los porcentajes de `que_se_hace` se
    reemplazan por los de aquí, con nota de que los anteriores eran
    del recorte territorial.
  · `precio.maximo` se cierra con el techo elegido y su razón, y deja
    de decir REVISAR.
  · Si el ADR 005 no se ratifica el 16, estas cifras cambian: están
    atadas a los cinco catálogos. Fecharlas.