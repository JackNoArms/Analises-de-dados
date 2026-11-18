"""Tests use synthetic records only, never inferred official statistics."""
from pathlib import Path
import pandas as pd
import pytest

from src.inep_pipeline import ETAPAS, reshape, sem_acentos, obtain_archive, UF


def sample_frame(source="estados"):
    base = {
        "NU_ANO_CENSO": [2022, 2022, 2022],
        "NO_CATEGORIA": ["Total", "Total", "Urbana"],
        "NO_DEPENDENCIA": ["Total", "Total", "Total"],
        "UNIDGEO": ["Brasil", "Piauí", "Piauí"],
        "SG_UF": ["PI", "PI", "PI"],
        "CO_MUNICIPIO": [2200103, 2200103, 2200103],
        "NO_MUNICIPIO": ["Água Branca", "Água Branca", "Água Branca"],
    }
    for prefix in ETAPAS.values():
        base[prefix + "_1"] = [10.0, 30.0, 99.0]
        base[prefix + "_2"] = [20.0, 40.0, 99.0]
    if source == "estados":
        base["UNIDGEO"][1] = "Piauí"
    return pd.DataFrame(base)


def test_normalization_and_total_total_filter():
    rows, stats = reshape(sample_frame(), "estados")
    assert len(rows) == 8
    assert stats["total_total_linhas"] == 2
    assert sorted(rows["percentual_n1_n2"].unique().tolist()) == [30.0, 70.0]
    assert rows.loc[rows["nivel"].eq("UF"), "uf"].unique().tolist() == ["PI"]
    assert not rows["percentual_n1_n2"].eq(198).any()


def test_municipal_codes_are_preserved_without_aggregating():
    rows, _ = reshape(sample_frame("municipios").iloc[[0]], "municipios")
    assert len(rows) == 4
    assert set(rows["codigo_ibge"]) == {2200103}
    assert all(rows["percentual_n1_n2"] == 30.0)


def test_missing_values_are_excluded_not_zeroed():
    df = sample_frame().iloc[[0]].copy()
    df["FUN_CAT_1"] = df["FUN_CAT_1"].astype(object)
    df["FUN_CAT_1"] = "--"
    df.loc[:, "FUN_AI_CAT_2"] = 101.0
    rows, stats = reshape(df, "estados")
    assert set(rows["etapa"]) == {"Anos finais", "Ensino médio"}
    assert stats["faltantes_removidos"] == 2


def test_required_columns_fail_clearly():
    with pytest.raises(ValueError, match="Campos obrigatórios"):
        reshape(sample_frame().drop(columns=["UNIDGEO"]), "estados")


def test_ambiguous_duplicate_keys_fail():
    df = pd.concat([sample_frame().iloc[[0]], sample_frame().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicadas"):
        reshape(df, "estados")


def test_utf8_normalization_and_dictionary():
    assert sem_acentos("  PIAUÍ  ") == "piaui"
    assert len(UF) == 27
    assert UF["PI"][1] == 22


def test_offline_requires_cached_source(tmp_path):
    with pytest.raises(FileNotFoundError, match="não encontrado"):
        obtain_archive(tmp_path, "estados", allow_download=False)


def test_rejects_wrong_checksum(tmp_path):
    (tmp_path / "IED_2022_BRASIL_REGIOES_UFS.zip").write_bytes(b"not an INEP zip")
    with pytest.raises(ValueError, match="Checksum"):
        obtain_archive(tmp_path, "estados", allow_download=False)
