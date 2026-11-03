# ENAHO 2024 con skills de Claude Code

Tres skills de Claude Code que limpian, grafican y mapean la pobreza monetaria de la ENAHO 2024 del INEI, siempre de la misma forma y validadas contra las cifras oficiales. Sesión 16 · Data Science con Python.

| Skill | Entra | Sale |
|---|---|---|
| `limpiando-enaho` | Zips de los módulos 34 y 02 | `salidas/personas_2024.parquet`, `salidas/hogares_2024.parquet`, `salidas/validacion.txt` |
| `graficando-enaho` | Base limpia + corte (área, sexo, edad) | `figuras/pobreza_<corte>_2024.png` |
| `mapeando-enaho` | Base limpia + GeoJSON | `mapas/pobreza_departamento.png` |

Las skills de gráfico y mapa llaman primero a `limpiando-enaho` si la base no existe, así un solo pedido activa dos skills seguidas.

## 1. Bajar los datos

Descárgalos a `datos/` (no se sube a git):

```bash
mkdir -p datos
curl -L -o datos/966-Modulo34.zip https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip
curl -L -o datos/966-Modulo02.zip https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip
curl -L -o datos/peru_departamental_simple.geojson https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson
```

`966` es el código de la ENAHO 2024 en el portal de microdatos del INEI.

## 2. Instalar

```bash
uv sync
```

## 3. Correr

Con Claude Code, en lenguaje natural:

```bash
claude -p "Haz un mapa de la pobreza por departamento con la ENAHO 2024"
```

O los scripts directamente:

```bash
uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024
uv run .claude/skills/graficando-enaho/scripts/graficar.py --por area
uv run .claude/skills/mapeando-enaho/scripts/mapear.py
```

## Validación

`salidas/validacion.txt`: pobreza 27.53 % (oficial 27.6 %), extrema 5.5 %, 33,691 hogares, 108,664 residentes habituales de 117,721 filas, 25 departamentos. Las tasas por departamento coinciden con `referencias/pobreza_departamento_2024.csv`. Detalle en `evaluacion.md`.

## Estructura

```text
.claude/skills/
  limpiando-enaho/   SKILL.md, reference.md, scripts/limpiar.py
  graficando-enaho/  SKILL.md, scripts/graficar.py
  mapeando-enaho/    SKILL.md, scripts/mapear.py
salidas/validacion.txt
figuras/  mapas/  referencias/
evaluacion.md  evaluar.sh  README.md  pyproject.toml
```
