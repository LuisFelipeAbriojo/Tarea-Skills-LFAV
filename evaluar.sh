#!/usr/bin/env bash
# Evalua las skills contra una linea base sin skills, en sandboxes aislados.
#
# Cada corrida arranca en una caja limpia que solo tiene los insumos crudos
# (datos/*.zip, geojson) y el entorno de Python. Asi ninguna rama puede
# reutilizar bases ya limpias ni leer las respuestas esperadas.
#
# Lo que NO entra a ninguna caja: salidas/, figuras/, mapas/, README.md y
# evaluacion.md (los dos ultimos traen las cifras esperadas: 18.5 %, 24.8/39.3,
# Cajamarca 45.0 / Ica 6.0).
# Lo que entra solo a la rama "con": .claude/skills/ y referencias/.
# Bloquear la herramienta Skill no basta, porque .claude/skills/ sigue siendo
# legible con Read/Grep/Bash.
#
# El pedido va por stdin: --allowedTools/--disallowedTools son variadic y se
# comerian el prompt posicional.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Reusa el venv del repo: instalar geopandas 6 veces no es lo que estamos midiendo.
export UV_PROJECT_ENVIRONMENT="$RAIZ/.venv"
HERR="Bash,Read,Write,Edit,Glob,Grep"

pedidos=(
  "¿Cuál fue la pobreza en Cusco en 2024? Usa la ENAHO."
  "Grafica la pobreza urbana y rural con la ENAHO 2024"
  "Haz un mapa de la pobreza por departamento con la ENAHO 2024"
)

prepara_caja() {  # $1 = ruta de la caja, $2 = con|sin
  local caja="$1" modo="$2"
  rm -rf "$caja"
  mkdir -p "$caja/datos"
  cp "$RAIZ/datos/"*.zip "$RAIZ/datos/"*.geojson "$caja/datos/"
  cp "$RAIZ/pyproject.toml" "$RAIZ/uv.lock" "$caja/"
  [ -f "$RAIZ/.python-version" ] && cp "$RAIZ/.python-version" "$caja/"
  if [ "$modo" = con ]; then
    mkdir -p "$caja/.claude"
    cp -r "$RAIZ/.claude/skills" "$caja/.claude/"
    cp -r "$RAIZ/referencias" "$caja/"
  fi
}

mkdir -p "$RAIZ/eval"
for i in 0 1 2; do
  n=$((i + 1))
  for modo in con sin; do
    caja="$RAIZ/eval/caja_${modo}_$n"
    arte="$RAIZ/eval/artefactos_${modo}_$n"
    prepara_caja "$caja" "$modo"
    rm -rf "$arte"; mkdir -p "$arte"

    if [ "$modo" = con ]; then
      flags=(--allowedTools "$HERR,Skill")
    else
      flags=(--allowedTools "$HERR" --disallowedTools "Skill")
    fi

    echo ">>> pedido $n, rama $modo"
    ( cd "$caja" && printf '%s' "${pedidos[$i]}" | claude -p "${flags[@]}" ) \
      > "$RAIZ/eval/${modo}_skills_$n.txt" 2> "$RAIZ/eval/${modo}_skills_$n.err"

    # Cada rama deja sus artefactos en su propia carpeta, sin pisar a la otra.
    for sub in salidas figuras mapas; do
      [ -d "$caja/$sub" ] && cp -r "$caja/$sub" "$arte/"
    done
    rm -rf "$caja"   # son ~22 MB de zips por caja
  done
done
echo "=== EVALUACION COMPLETA ==="
