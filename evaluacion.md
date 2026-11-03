# Evaluación: con y sin skills

## Método

Tres pedidos, cada uno corrido dos veces: con skills y sin skills. Script: `evaluar.sh`.

Cada corrida arranca en un sandbox limpio (`eval/caja_<rama>_<n>/`) que solo contiene
los insumos crudos — `datos/*.zip` y el GeoJSON — más el entorno de Python. El pedido
entra por stdin, porque `--allowedTools` y `--disallowedTools` son variadic y se comen
el prompt posicional.

Qué no entra a ninguna caja: `salidas/`, `figuras/`, `mapas/`, `README.md` y este
archivo (los dos últimos traen las cifras esperadas). Qué entra solo a la rama con
skills: `.claude/skills/` y `referencias/`. Bloquear la herramienta `Skill` no basta,
porque `.claude/skills/` sigue siendo legible con Read, Grep y Bash.

Los artefactos de cada rama quedan separados en `eval/artefactos_<rama>_<n>/`, así que
una rama ya no sobreescribe las figuras de la otra.

> Una primera versión de `evaluar.sh` no aislaba nada: las dos ramas encontraban las
> bases ya limpias, la rama «sin skills» leía las cifras esperadas de `referencias/` y
> de `evaluacion.md`, y las figuras de una pisaban las de la otra. Daba empate en todo.
> Esa corrida quedó en `eval_contaminado/` y no debe leerse como resultado.

## Resultados

| # | Pedido | Skills esperadas | Cifra esperada | Con skills: skills activadas | Con skills: cifra / ¿ponderó? / figura | Sin skills: cifra / ¿ponderó? / figura |
|---|---|---|---|---|---|---|
| 1 | ¿Cuál fue la pobreza en Cusco en 2024? | `limpiando-enaho` | 18.5 % | `limpiando-enaho` | 18.5 % (extrema 2.1 %) / sí, `factor07 × mieperho` / no aplica | 18.54 % (extrema 2.10 %) / sí, `factor07 × mieperho` / no aplica |
| 2 | Grafica la pobreza urbana y rural | `graficando-enaho` + `limpiando-enaho` | 24.8 % y 39.3 % | `limpiando-enaho` + `graficando-enaho` | 24.8 % / 39.3 % / sí / `figuras/pobreza_area_2024.png` | 24.8 % / 39.3 % / sí / `figuras/pobreza_area_2024.png` |
| 3 | Haz un mapa de la pobreza por departamento | `mapeando-enaho` + `limpiando-enaho` | Cajamarca 45.0 %, Ica 6.0 % | `limpiando-enaho` + `mapeando-enaho` | 45.0 % / 6.0 % / sí / `mapas/pobreza_departamento.png` | 45.0 % / 6.0 % / sí / `salidas/mapa_pobreza_departamento_2024.png` |

Las skills activadas se infieren de los artefactos: el pedido 1 dejó solo `salidas/`,
el 2 dejó `salidas/` + `figuras/` y el 3 dejó `salidas/` + `mapas/`.

### En exactitud: empate

Partiendo de los zips crudos, las dos ramas llegaron a las cifras oficiales en los tres
pedidos. La rama sin skills reconstruyó sola el método del INEI: ponderación
`factor07 × mieperho`, estratos 1-5 urbano y 6-8 rural, pobres los hogares con
`pobreza ∈ {1, 2}`, departamento de los dos primeros dígitos del ubigeo. Para estos tres
pedidos las skills no compraron precisión.

### En reproducibilidad: diferencia clara

| | Con skills | Sin skills |
|---|---|---|
| Base reutilizable | `salidas/*.parquet` en las 3 corridas | ninguna, en ninguna corrida |
| Determinismo | md5 idéntico en 3/3, e igual al del repo | script ad-hoc distinto cada vez |
| Validación | 5 chequeos formales contra el INEI | solo auto-cotejo del total nacional |
| Ubicación de salidas | siempre `figuras/`, `mapas/` | mapa en `salidas/`, CSV en `figuras/`, `.dta` sueltos en `datos/extraido/` |

Las tres corridas con skills produjeron `hogares_2024.parquet` byte a byte idéntico
(`fd823bbf…`), y además idéntico al que ya estaba en el repo. La rama sin skills dejó
cada vez un artefacto distinto, con nombres y rutas distintas; el pedido 1 no dejó
ningún archivo, calculó en memoria y respondió.

### Donde la rama sin skills salió mejor

1. **Etiqueta de Callao.** La sacó fuera del mapa por ser un departamento muy pequeño.
   La rama con skills reprodujo el solapamiento con la etiqueta de Lima y solo lo
   reportó: el bug estaba en `mapear.py`, no en el modelo. Ya corregido (ver abajo).
2. **Advertencias estadísticas.** En el pedido 3 señaló que cada departamento tiene
   entre ~600 y ~1,500 hogares en la muestra, que los márgenes de error son amplios y
   que el INEI publica grupos de pobreza estadísticamente similares en vez de un
   ranking — por lo que diferencias de pocos puntos (Pasco frente a Huánuco) no deben
   leerse como reales. Ninguna skill dice esto. Vale incorporarlo a
   `mapeando-enaho` y a `limpiando-enaho`.

También entregó de más sin que se lo pidieran: pobreza extrema por área (3.1 % urbana,
15.5 % rural) y una barra nacional de contexto.

### Límite de esta evaluación

Una sola corrida por celda. El determinismo de la rama con skills es sólido (3/3
idénticas, consecuencia directa de correr un script fijo), pero las diferencias
cualitativas — advertencias, etiqueta de Callao — vienen de una muestra de uno y podrían
ser variación entre corridas y no efecto de la skill.

## Resultados de los scripts de las skills (verificados)

| Cifra | Obtenido | INEI |
|---|---|---|
| Pobreza nacional | 27.53 % (personas, `facpob07`) · 27.58 % (sumaria, `factor07 × mieperho`) | 27.6 % |
| Residentes habituales | 108,664 | 108,664 |
| Cusco | 18.5 % | 18.5 % |
| Urbano / rural | 24.8 % / 39.3 % | 24.8 % / 39.3 % |
| Cajamarca / Ica | 45.0 % / 6.0 % | 45.0 % / 6.0 % |
| Departamentos con dato en el mapa | 25 de 25 | 25 |

## Hallazgos

**Pesos.** Con la base de personas y `facpob07` la pobreza nacional cuadra (27.53 %),
pero los departamentos difieren hasta 0.5 puntos de las cifras oficiales. El INEI calcula
las tasas a nivel de hogar con `factor07 × mieperho`; por eso `limpiar.py` guarda también
`salidas/hogares_2024.parquet` y las skills de gráfico por área y de mapa usan esa base.
Con ella los 25 departamentos coinciden exactamente.

**Etiqueta de Callao (corregido).** Callao es tan pequeño en el mapa que su etiqueta
quedaba tapada por la de Lima. `mapear.py` ahora saca al margen la etiqueta de cualquier
departamento cuyo tamaño sea menor al 6 % del más grande, con una línea que lo señala.
El criterio es el tamaño y no el nombre: Callao mide 0.02 del mayor y el siguiente más
pequeño, Tumbes, mide 0.10, así que el umbral lo aísla con margen de sobra.
