---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI y arma bases de personas y hogares con pobreza monetaria y factor de expansión, validadas contra las cifras oficiales. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular la pobreza nacional, por departamento (Cusco, Lima, etc.), área, sexo o edad.
argument-hint: [año]
---
# Limpiar la ENAHO

El objetivo es que la base sea idéntica para cualquiera que la pida, por eso el pipeline vive en un script y no se reescribe.

1. Verifica que existan `datos/966-Modulo34.zip` y `datos/966-Modulo02.zip` (966 = ENAHO 2024). Si faltan, detente y pide al usuario bajarlos de https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip y ...966-Modulo02.zip; no inventes datos.
2. Si `salidas/personas_2024.parquet` y `salidas/hogares_2024.parquet` ya existen y `salidas/validacion.txt` no dice FALLA, reutilízalos. Si no, corre exactamente:
   `uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio $0` (si no te dan año, usa 2024)
3. Lee `salidas/validacion.txt`. Si algún chequeo dice FALLA o la pobreza difiere del 27.6 % oficial en más de 0.1 puntos, detente y reporta; una cifra que no cuadra con el INEI no se debe publicar.
4. Para responder cifras de pobreza:
   - Nacional, por departamento, área o dominio: usa `salidas/hogares_2024.parquet` ponderando con `peso` (= `factor07 × mieperho`). Es el método oficial del INEI y reproduce exactamente sus cifras (p. ej. Cusco 18.5 %).
   - Por sexo, edad u otra característica de la persona: usa `salidas/personas_2024.parquet` ponderando con `facpob07`.
   - Nunca reportes promedios sin ponderar.
   - Si la cifra es de un departamento o de cualquier subgrupo chico, di que es una estimación muestral y que el margen de error es de varios puntos: cada departamento tiene entre 603 y 1,611 hogares (Lima, 4,544). No la presentes como dato exacto ni compares dos subgrupos que difieren en pocos puntos. Detalle en [reference.md](reference.md).
5. Responde con la cifra a un decimal, la base y el peso usados, y «Fuente: INEI, ENAHO 2024».
6. Antes de usar una variable que no está en la base, lee [reference.md](reference.md).
