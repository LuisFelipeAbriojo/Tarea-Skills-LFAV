"""Mapa coroplético de la pobreza 2024 por departamento.

Uso: uv run .claude/skills/mapeando-enaho/scripts/mapear.py [--anio 2024] [--geojson datos/peru_departamental_simple.geojson]

Une por código (ubigeo[:2] = FIRST_IDDP, como texto), nunca por nombre.
Exige 25 departamentos con dato. Usa la base de hogares (método oficial INEI: factor07 x mieperho).
"""

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

GEOJSON_URL = ("https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/"
               "06-geoespacial/lab/Data/peru_departamental_simple.geojson")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anio", type=int, default=2024)
    ap.add_argument("--geojson", type=Path, default=Path("datos/peru_departamental_simple.geojson"))
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    hogares = Path(f"salidas/hogares_{a.anio}.parquet")
    if not hogares.exists():
        sys.exit(f"Falta {hogares}: corre primero la skill limpiando-enaho.")
    if not a.geojson.exists():
        sys.exit(f"Falta {a.geojson}. Bájalo de {GEOJSON_URL}")

    h = pd.read_parquet(hogares)
    tasas = (h.assign(pw=h.pobre * h.peso).groupby("departamento")[["pw", "peso"]].sum()
             .pipe(lambda d: 100 * d.pw / d.peso).rename("pobreza_pct").reset_index())

    geo = gpd.read_file(a.geojson)
    geo["FIRST_IDDP"] = geo["FIRST_IDDP"].astype(str).str.zfill(2)
    mapa = geo.merge(tasas, left_on="FIRST_IDDP", right_on="departamento", how="left", validate="1:1")
    assert len(mapa) == 25, f"Se esperaban 25 departamentos y hay {len(mapa)}"
    sin_dato = mapa.loc[mapa.pobreza_pct.isna(), "NOMBDEP"].tolist()
    assert not sin_dato, f"Departamentos sin dato: {sin_dato}"

    fig, ax = plt.subplots(figsize=(7, 9))
    mapa.plot(column="pobreza_pct", cmap="Reds", vmin=0, vmax=50, edgecolor="white", linewidth=0.6, ax=ax,
              legend=True, legend_kwds={"label": "% de personas en pobreza", "shrink": 0.6})
    # Callao es tan chico que su etiqueta queda tapada por la de Lima: va al margen
    # con una linea que la senale. El criterio es el tamano, no el nombre.
    b = mapa.geometry.bounds
    tam = (b.maxx - b.minx) + (b.maxy - b.miny)
    chicos = tam < 0.06 * tam.max()  # solo Callao (0.02); el siguiente, Tumbes, es 0.10
    xmin, _, xmax, _ = mapa.total_bounds
    for (_, f), es_chico in zip(mapa.iterrows(), chicos):
        p = f.geometry.representative_point()
        if es_chico:
            ax.annotate(f"{f.NOMBDEP.title()} {f.pobreza_pct:.1f}", (p.x, p.y),
                        xytext=(xmin + 0.05 * (xmax - xmin), p.y), textcoords="data",
                        ha="left", va="center", fontsize=7, color="#222",
                        arrowprops={"arrowstyle": "-", "color": "#555", "linewidth": 0.6,
                                    "shrinkA": 2, "shrinkB": 1})
        else:
            ax.annotate(f"{f.pobreza_pct:.1f}", (p.x, p.y), ha="center", fontsize=7,
                        color="white" if f.pobreza_pct > 32 else "#222")
    ax.set_title(f"Pobreza monetaria por departamento, Perú {a.anio}", loc="left", fontsize=13,
                 fontweight="bold")
    ax.set_axis_off()
    fig.text(0.02, 0.02, f"Fuente: INEI, ENAHO {a.anio}. Lima (15) y Callao (07) por separado.", fontsize=8,
             color="#555")

    Path("mapas").mkdir(exist_ok=True)
    destino = Path("mapas/pobreza_departamento.png")
    fig.savefig(destino, dpi=200, bbox_inches="tight")

    orden = mapa.sort_values("pobreza_pct", ascending=False)[["FIRST_IDDP", "NOMBDEP", "pobreza_pct"]]
    print(orden.to_string(index=False, float_format=lambda v: f"{v:.1f}"))
    print(f"\n25 departamentos con dato. Guardado: {destino}")


if __name__ == "__main__":
    main()
