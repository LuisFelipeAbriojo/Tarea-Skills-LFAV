---
name: graficando-enaho
description: Hace gráficos de barras de la pobreza monetaria de la ENAHO del INEI por área (urbano/rural), sexo o grupo de edad, ponderados y con formato de publicación. Úsala cuando pidan graficar, visualizar o comparar la pobreza de la ENAHO entre grupos.
argument-hint: [area|sexo|edad]
---
# Graficar la pobreza de la ENAHO

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho`.
2. Identifica el corte pedido: `area` (urbano/rural), `sexo` o `edad`. Si el pedido trae varios, corre uno por cada uno.
3. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por <corte>`
4. Reporta las cifras que imprime el script y la ruta del PNG en `figuras/`.

## Reglas del gráfico (el script ya las cumple; si haces uno nuevo, respétalas)
- Pondera siempre: área con la base de hogares (`peso`), sexo y edad con `facpob07`. Sin ponderar la cifra es de la muestra, no del país.
- Barras que empiezan en cero y ordenadas de mayor a menor (la edad conserva su orden natural); un eje truncado exagera las diferencias.
- Un solo color y el valor escrito en cada barra.
- El título dice qué y cuándo: «Pobreza monetaria por área de residencia, Perú 2024».
- Nota al pie: «Fuente: INEI, ENAHO 2024».
- PNG a 200 dpi en `figuras/`.

Resultado esperado para validar: urbano 24.8 %, rural 39.3 %.
