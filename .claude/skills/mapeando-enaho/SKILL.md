---
name: mapeando-enaho
description: Hace un mapa coroplético de la pobreza monetaria de la ENAHO del INEI por departamento del Perú, uniendo por código de ubigeo con el GeoJSON de límites departamentales. Úsala cuando pidan un mapa, mapear o ver la pobreza por departamento o región.
---
# Mapear la pobreza por departamento

1. Si no existe `salidas/hogares_2024.parquet`, usa primero la skill `limpiando-enaho`.
2. Si falta `datos/peru_departamental_simple.geojson`, pide al usuario bajarlo de https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson
3. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py`
4. Si el script falla por departamentos faltantes o sin dato, no entregues el mapa: revisa la unión.
5. Reporta el departamento más y menos pobre y la ruta `mapas/pobreza_departamento.png`, y advierte que el orden no es un ranking exacto (ver «Precisión» abajo).

## Reglas del mapa
- Une por código: `ubigeo[:2]` con `FIRST_IDDP`, ambos como texto de 2 dígitos. Nunca por nombre: «APURIMAC» no es «Apurímac», y un código convertido a número pierde el cero de «01».
- Exige 25 departamentos y ninguno sin dato.
- Lima (15) y Callao (07) van separados.
- Una escala secuencial de un color, de claro a oscuro, desde 0; nunca arcoíris.
- Leyenda con la unidad: «% de personas en pobreza».
- Tasas con la base de hogares ponderada por `peso` (método oficial INEI).

Resultado esperado para validar: Cajamarca 45.0 % (más pobre), Ica 6.0 % (menos pobre).

## Precisión: el mapa no es un ranking
Cada tasa departamental se estima con entre 603 y 1,611 hogares (Lima, 4,544), con un
margen de error de varios puntos. El INEI no publica un orden sino grupos de
departamentos con pobreza estadísticamente similar.

Por eso: reporta el más y el menos pobre, pero no presentes la lista como un ranking ni
digas que un departamento «supera» a otro por pocos puntos. En 2024 hay empates exactos
que lo muestran: Pasco y Huánuco en 39.0 %, Cusco y Junín en 18.5 %, Apurímac y Tacna en
24.0 %.
