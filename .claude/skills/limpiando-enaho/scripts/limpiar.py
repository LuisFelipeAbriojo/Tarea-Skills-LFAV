"""Limpia la ENAHO (módulos 34 sumaria y 02 miembros) y arma una base de personas.

Uso: uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024

Pipeline fijo: leer -> normalizar -> filtrar residentes -> unir m:1 -> construir -> validar -> guardar.
Si una validación falla, el script termina con error y no guarda la base.
"""

import argparse
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

CODIGOS = {2024: "966"}  # código de la ENAHO anual en el portal de microdatos del INEI
OFICIAL = {2024: {"pobreza": 27.6, "extrema": 5.5, "hogares": 33_691, "residentes": 108_664}}
LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVES_PERSONA = LLAVES_HOGAR + ["codperso"]
TOLERANCIA = 0.1  # puntos porcentuales


def leer_dta(zip_path: Path, patron: str, columnas: list[str]) -> pd.DataFrame:
    """Lee el .dta del zip cuyo nombre coincide con `patron`, sin etiquetas y con llaves como texto."""
    with zipfile.ZipFile(zip_path) as z:
        nombre = next(n for n in z.namelist() if Path(n).name.lower() == patron)
        df = pd.read_stata(io.BytesIO(z.read(nombre)), convert_categoricals=False)
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(columns={c: "anio" for c in df.columns if c.startswith("a") and c.endswith("o") and len(c) == 3})
    for k in LLAVES_PERSONA:
        if k in df.columns:
            df[k] = df[k].astype(str).str.strip()
    df["ubigeo"] = df["ubigeo"].astype(str).str.zfill(6)
    return df[[c for c in columnas if c in df.columns]]


def pct(serie: pd.Series, peso: pd.Series) -> float:
    return 100 * (serie * peso).sum() / peso.sum()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anio", type=int, default=2024)
    ap.add_argument("--datos", type=Path, default=Path("datos"))
    ap.add_argument("--salidas", type=Path, default=Path("salidas"))
    a = ap.parse_args()
    cod = CODIGOS[a.anio]
    of = OFICIAL[a.anio]

    zip34, zip02 = a.datos / f"{cod}-Modulo34.zip", a.datos / f"{cod}-Modulo02.zip"
    for z in (zip34, zip02):
        if not z.exists():
            sys.exit(f"Falta {z}. Bájalo de https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/{z.name}")

    # 1-2. Leer y normalizar
    hog = leer_dta(zip34, f"sumaria-{a.anio}.dta",
                   LLAVES_HOGAR + ["ubigeo", "dominio", "estrato", "pobreza", "mieperho", "factor07"])
    per = leer_dta(zip02, f"enaho01-{a.anio}-200.dta",
                   LLAVES_PERSONA + ["p203", "p204", "p205", "p206", "p207", "p208a", "facpob07"])
    filas_02 = len(per)

    # 3. Filtrar residentes habituales (definición del INEI)
    res = ((per.p204 == 1) & (per.p205 == 2)) | ((per.p204 == 2) & (per.p206 == 1))
    per = per[res].copy()

    # 4. Unir personas con hogares (muchas personas -> un hogar)
    assert not hog.duplicated(LLAVES_HOGAR).any(), "Llaves de hogar duplicadas en la sumaria"
    assert not per.duplicated(LLAVES_PERSONA).any(), "Llaves de persona duplicadas en el módulo 02"
    base = per.merge(hog, on=LLAVES_HOGAR, how="left", validate="m:1", indicator=True)
    assert len(base) == len(per), "La unión cambió el número de filas"
    assert (base["_merge"] == "both").all(), "Hay personas sin hogar en la sumaria"
    base = base.drop(columns="_merge")

    # 5. Construir variables
    base["departamento"] = base["ubigeo"].str[:2]
    base["urbano"] = base["estrato"] <= 5
    base["pobre"] = base["pobreza"] <= 2
    base["pobre_extremo"] = base["pobreza"] == 1
    base["mujer"] = base["p207"] == 2
    base = base.rename(columns={"p208a": "edad"})
    base["anio"] = a.anio

    # 6. Validar contra las cifras oficiales
    w = base["facpob07"]
    pob = pct(base.pobre, w)
    ext = pct(base.pobre_extremo, w)
    pob_hog = pct(hog.pobreza <= 2, hog.factor07 * hog.mieperho)
    wh = hog.factor07 * hog.mieperho  # método oficial INEI para tasas por grupo
    pobre_h, urb_h = hog.pobreza <= 2, hog.estrato <= 5
    urb = pct(pobre_h[urb_h], wh[urb_h])
    rur = pct(pobre_h[~urb_h], wh[~urb_h])
    lima = pct(pobre_h[hog.dominio == 8], wh[hog.dominio == 8])
    n_dep = base.departamento.nunique()

    chequeos = [
        ("Hogares en la sumaria", len(hog), of["hogares"], len(hog) == of["hogares"]),
        ("Residentes habituales", len(base), of["residentes"], len(base) == of["residentes"]),
        ("Pobreza (personas, facpob07) %", f"{pob:.2f}", of["pobreza"], abs(pob - of["pobreza"]) <= TOLERANCIA),
        ("Pobreza extrema %", f"{ext:.2f}", of["extrema"], abs(ext - of["extrema"]) <= TOLERANCIA),
        ("Departamentos", n_dep, 25, n_dep == 25),
    ]
    lineas = [
        f"VALIDACIÓN ENAHO {a.anio} (código INEI {cod})",
        "=" * 52,
        f"Filas del módulo 02: {filas_02:,}  ->  residentes habituales: {len(base):,}",
        "Llaves únicas: OK   Unión m:1 sin pérdidas ni duplicados: OK",
        "",
        f"{'Chequeo':<34}{'Obtenido':>10}{'INEI':>8}  Estado",
    ]
    for nombre, obt, ref, ok in chequeos:
        lineas.append(f"{nombre:<34}{obt:>10}{ref:>8}  {'OK' if ok else 'FALLA'}")
    lineas += [
        "",
        "Cifras complementarias (sumaria, factor07 x mieperho = método INEI):",
        f"  Pobreza nacional: {pob_hog:.2f} %",
        f"  Urbano (estrato <= 5): {urb:.1f} %   Rural: {rur:.1f} %",
        f"  Lima Metropolitana (dominio == 8): {lima:.1f} %",
    ]
    texto = "\n".join(lineas)
    sys.stdout.reconfigure(encoding="utf-8")
    print(texto)

    a.salidas.mkdir(parents=True, exist_ok=True)
    (a.salidas / "validacion.txt").write_text(texto + "\n", encoding="utf-8")
    if not all(ok for *_, ok in chequeos):
        sys.exit("ERROR: la validación falló; no se guardó la base.")

    # 7. Guardar
    destino = a.salidas / f"personas_{a.anio}.parquet"
    base.to_parquet(destino, index=False)
    print(f"\nGuardado: {destino} ({len(base):,} personas, {base.shape[1]} columnas)")

    # Base de hogares: método oficial del INEI para tasas por área y departamento (peso factor07 x mieperho)
    hog = hog.assign(departamento=hog.ubigeo.str[:2], urbano=hog.estrato <= 5, pobre=hog.pobreza <= 2,
                     pobre_extremo=hog.pobreza == 1, peso=hog.factor07 * hog.mieperho, anio=a.anio)
    destino_h = a.salidas / f"hogares_{a.anio}.parquet"
    hog.to_parquet(destino_h, index=False)
    print(f"Guardado: {destino_h} ({len(hog):,} hogares, peso = factor07 x mieperho)")


if __name__ == "__main__":
    main()
