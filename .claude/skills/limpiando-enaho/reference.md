# Referencia de variables · ENAHO 2024

## Bases que produce `limpiar.py`

| Base | Una fila por | Filas | Peso |
|---|---|---|---|
| `salidas/personas_2024.parquet` | residente habitual | 108,664 | `facpob07` |
| `salidas/hogares_2024.parquet` | hogar | 33,691 | `peso` = `factor07 × mieperho` |

## Variables

| Variable | Origen | Significado |
|---|---|---|
| `conglome`, `vivienda`, `hogar` | ambos | Llave de hogar (texto) |
| `codperso` | 02 | Número de persona dentro del hogar |
| `ubigeo` | 34 | Código de distrito, 6 dígitos (texto) |
| `departamento` | construida | `ubigeo[:2]`; Lima = 15, Callao = 07 |
| `dominio` | 34 | 1-7 costa/sierra/selva urbano-rural; 8 = Lima Metropolitana |
| `estrato` | 34 | 1-5 urbano, 6-8 rural |
| `urbano` | construida | `estrato <= 5` |
| `pobreza` | 34 | 1 pobre extremo, 2 pobre no extremo, 3 no pobre |
| `pobre` / `pobre_extremo` | construida | `pobreza <= 2` / `pobreza == 1` |
| `p203` | 02 | Parentesco con el jefe del hogar |
| `p204`, `p205`, `p206` | 02 | Miembro del hogar / ausente 30 días o más / presente 30 días o más |
| `p207`, `mujer` | 02 | Sexo (1 hombre, 2 mujer) |
| `edad` (`p208a`) | 02 | Edad en años cumplidos |
| `mieperho` | 34 | Miembros del hogar |
| `factor07` | 34 | Factor de expansión del hogar |
| `facpob07` | 02 | Factor de expansión de la persona |

## Residente habitual
`(p204 == 1 & p205 == 2) | (p204 == 2 & p206 == 1)`: miembro que no estuvo ausente 30 días o más, o no miembro que estuvo presente 30 días o más.

## Cifras oficiales 2024 para validar
Pobreza 27.6 %, extrema 5.5 %, urbano 24.8 %, rural 39.3 %, Lima Metropolitana 28.2 %. Por departamento: `referencias/pobreza_departamento_2024.csv`.

## Por qué dos pesos
El INEI calcula la pobreza a nivel de hogar expandida por `factor07 × mieperho`. Con personas y `facpob07` la nacional da 27.53 % (dentro de tolerancia), pero los departamentos pueden diferir hasta 0.5 puntos. Por eso las tasas territoriales usan la base de hogares.

## Precisión de las estimaciones
Las cifras salen de una muestra, no de un censo. Hogares en la muestra por departamento:
mínimo 603 (Madre de Dios), mediana 1,244, máximo 4,544 (Lima); los demás caen entre 842
y 1,611. Con esos tamaños el margen de error departamental es de varios puntos, así que
una diferencia chica entre dos departamentos no es real. El INEI publica grupos de
departamentos con pobreza estadísticamente similar, no un ranking.

Los scripts no calculan intervalos de confianza. Hacerlo exige el diseño muestral complejo
(`conglome` como conglomerado y `estrato` como estrato), no basta con el factor de
expansión.

