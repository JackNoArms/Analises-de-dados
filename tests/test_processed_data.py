"""Integrity checks for the committed public derived dataset."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"


def test_manifest_provenance_and_year():
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["ano"] == 2022
    assert "INEP" in manifest["fonte"]
    assert len(manifest["validacao"]["estados"]["sha256"]) == 64
    assert len(manifest["validacao"]["municipios"]["sha256"]) == 64


def test_geographical_coverage_and_official_brazil():
    geos = pd.read_csv(OUT / "geografias.csv")
    assert geos.loc[geos.nivel == "UF", "uf"].nunique() == 27
    brazil = geos.loc[geos.nivel == "Brasil"]
    assert len(brazil) == 4
    assert brazil.loc[brazil.etapa == "Ensino fundamental", "percentual_n1_n2"].iloc[0] == 38.0
    assert geos["percentual_n1_n2"].between(0, 100).all()


def test_municipal_observations_and_uniqueness():
    cities = pd.read_csv(OUT / "municipios.csv")
    assert cities["codigo_ibge"].nunique() == 5570
    assert cities.duplicated(["codigo_ibge", "etapa"]).sum() == 0
    assert cities["percentual_n1_n2"].between(0, 100).all()
    assert cities["ano"].eq(2022).all()
    assert cities["percentual_n1_n2"].notna().all()
