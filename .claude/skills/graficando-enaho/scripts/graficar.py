"""Gráfico de barras de la pobreza 2024 por área, sexo o grupo de edad.

Uso: uv run .claude/skills/graficando-enaho/scripts/graficar.py --por area|sexo|edad [--anio 2024]

Área usa la base de hogares (método oficial INEI: factor07 x mieperho).
Sexo y edad usan la base de personas ponderada con facpob07.
"""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

COLOR = "#2b5c8a"
EDADES = [(0, 14, "0-14"), (15, 29, "15-29"), (30, 44, "30-44"), (45, 64, "45-64"), (65, 200, "65+")]


def tasa(df: pd.DataFrame, peso: str) -> float:
    return 100 * (df.pobre * df[peso]).sum() / df[peso].sum()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--por", choices=["area", "sexo", "edad"], required=True)
    ap.add_argument("--anio", type=int, default=2024)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    personas = Path(f"salidas/personas_{a.anio}.parquet")
    hogares = Path(f"salidas/hogares_{a.anio}.parquet")
    if not personas.exists() or not hogares.exists():
        sys.exit(f"Falta {personas}: corre primero la skill limpiando-enaho.")

    if a.por == "area":
        h = pd.read_parquet(hogares)
        datos = {"Urbano": tasa(h[h.urbano], "peso"), "Rural": tasa(h[~h.urbano], "peso")}
        titulo = f"Pobreza monetaria por área de residencia, Perú {a.anio}"
    elif a.por == "sexo":
        p = pd.read_parquet(personas)
        datos = {"Mujeres": tasa(p[p.mujer], "facpob07"), "Hombres": tasa(p[~p.mujer], "facpob07")}
        titulo = f"Pobreza monetaria por sexo, Perú {a.anio}"
    else:
        p = pd.read_parquet(personas)
        datos = {et: tasa(p[p.edad.between(lo, hi)], "facpob07") for lo, hi, et in EDADES}
        titulo = f"Pobreza monetaria por grupo de edad, Perú {a.anio}"

    s = pd.Series(datos)
    if a.por != "edad":  # las edades conservan su orden natural
        s = s.sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    barras = ax.bar(s.index, s.values, color=COLOR, width=0.6)
    ax.bar_label(barras, labels=[f"{v:.1f} %" for v in s.values], padding=3, fontsize=11)
    ax.set_ylim(0, max(s.values) * 1.2)
    ax.set_ylabel("% de personas en pobreza")
    ax.set_title(titulo, loc="left", fontsize=13, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, f"Fuente: INEI, ENAHO {a.anio}. Cifras ponderadas con el factor de expansión.",
             fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))

    Path("figuras").mkdir(exist_ok=True)
    destino = Path(f"figuras/pobreza_{a.por}_{a.anio}.png")
    fig.savefig(destino, dpi=200)
    for k, v in s.items():
        print(f"{k}: {v:.1f} %")
    print(f"Guardado: {destino}")


if __name__ == "__main__":
    main()
