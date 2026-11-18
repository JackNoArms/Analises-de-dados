"""INEP 2022 · Indicador de Esforço Docente (IED), níveis 1 e 2.

Fonte: arquivos públicos XLSX do Inep; os dados oficiais NÃO são sintéticos.
Métrica: soma dos percentuais das categorias 1 e 2, por etapa,
geografia, dependência e localização. Não agregue municípios com
média simples para estimar a UF/Brasil: os arquivos oficiais já fornecem
seus próprios totais, que usamos diretamente.

Reproduza com: python -m src.inep_pipeline
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import unicodedata
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

BASE_URL = "https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2022"
ARCHIVES = {
    "estados": ("IED_2022_BRASIL_REGIOES_UFS.zip", "IED_BRASIL_REGIOES_UFS_2022.xlsx",
                "e37ebf07c4aabf77d712556e84baa130f44563b2ee80959d72c9dbf3f5b3843d"),
    "municipios": ("IED_2022_MUNICIPIOS.zip", "IED_MUNICIPIOS_2022.xlsx",
                   "6072d642479beb75fdf579905e4480f615cb40eff646eb8af68f99d303b51788"),
}
ETAPAS = {
    "Ensino fundamental": "FUN_CAT",
    "Anos iniciais": "FUN_AI_CAT",
    "Anos finais": "FUN_AF_CAT",
    "Ensino médio": "MED_CAT",
}
# Nome, código IBGE e região. Não confundir a UF e a região com município.
UF = {
    "AC": ("Acre", 12, "Norte"), "AL": ("Alagoas", 27, "Nordeste"),
    "AP": ("Amapá", 16, "Norte"), "AM": ("Amazonas", 13, "Norte"),
    "BA": ("Bahia", 29, "Nordeste"), "CE": ("Ceará", 23, "Nordeste"),
    "DF": ("Distrito Federal", 53, "Centro-Oeste"),
    "ES": ("Espírito Santo", 32, "Sudeste"), "GO": ("Goiás", 52, "Centro-Oeste"),
    "MA": ("Maranhão", 21, "Nordeste"), "MT": ("Mato Grosso", 51, "Centro-Oeste"),
    "MS": ("Mato Grosso do Sul", 50, "Centro-Oeste"),
    "MG": ("Minas Gerais", 31, "Sudeste"), "PA": ("Pará", 15, "Norte"),
    "PB": ("Paraíba", 25, "Nordeste"), "PR": ("Paraná", 41, "Sul"),
    "PE": ("Pernambuco", 26, "Nordeste"), "PI": ("Piauí", 22, "Nordeste"),
    "RJ": ("Rio de Janeiro", 33, "Sudeste"),
    "RN": ("Rio Grande do Norte", 24, "Nordeste"),
    "RS": ("Rio Grande do Sul", 43, "Sul"), "RO": ("Rondônia", 11, "Norte"),
    "RR": ("Roraima", 14, "Norte"), "SC": ("Santa Catarina", 42, "Sul"),
    "SP": ("São Paulo", 35, "Sudeste"), "SE": ("Sergipe", 28, "Nordeste"),
    "TO": ("Tocantins", 17, "Norte"),
}


def sem_acentos(value: object) -> str:
    clean = unicodedata.normalize("NFD", str(value))
    return "".join(char for char in clean if unicodedata.category(char) != "Mn").casefold().strip()


NAME_TO_UF = {sem_acentos(value[0]): abbr for abbr, value in UF.items()}
# Variante encontrada em um notebook histórico do projeto.
NAME_TO_UF["tocantis"] = "TO"


def obtain_archive(cache: Path, source: str, allow_download: bool = True) -> tuple[bytes, str]:
    """Return verified ZIP bytes. Never silently accept modified source archives."""
    archive, _, expected = ARCHIVES[source]
    cache.mkdir(parents=True, exist_ok=True)
    archive_path = cache / archive
    if not archive_path.exists():
        if not allow_download:
            raise FileNotFoundError(f"Arquivo não encontrado: {archive_path}. Execute sem --offline.")
        url = f"{BASE_URL}/{archive}"
        req = urllib.request.Request(url, headers={"User-Agent": "portfolio-inep-2022/1.0"})
        with urllib.request.urlopen(req, timeout=90) as response:
            payload = response.read()
        tmp = archive_path.with_suffix(".part")
        tmp.write_bytes(payload)
        tmp.replace(archive_path)
    payload = archive_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected:
        raise ValueError(f"Checksum SHA256 incorreto para {archive}: {digest} (esperado {expected})")
    return payload, digest


def read_official_excel(payload: bytes, source: str) -> pd.DataFrame:
    _, expected_file, _ = ARCHIVES[source]
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        paths = [name for name in archive.namelist() if name.endswith("/" + expected_file) or name == expected_file]
        if len(paths) != 1:
            raise ValueError(f"Planilha oficial {expected_file} não encontrada de modo único no ZIP")
        with archive.open(paths[0]) as stream:
            content = stream.read()
    return pd.read_excel(io.BytesIO(content), skiprows=10, skipfooter=5)


def _pct_sum(df: pd.DataFrame, prefix: str) -> pd.Series:
    names = [f"{prefix}_1", f"{prefix}_2"]
    missing = [col for col in names if col not in df.columns]
    if missing:
        raise ValueError(f"Faltam colunas oficiais: {missing}")
    parts = [pd.to_numeric(df[col].replace("--", pd.NA), errors="coerce") for col in names]
    total = parts[0] + parts[1]  # não transforme dados ausentes em zero
    valid = parts[0].between(0, 100) & parts[1].between(0, 100) & total.between(0, 100.2)
    return total.where(valid).round(2)


def reshape(df: pd.DataFrame, source: str) -> tuple[pd.DataFrame, dict]:
    """Normalize only official Total/Total cuts, avoiding duplicate aggregation."""
    expected = {"NU_ANO_CENSO", "NO_CATEGORIA", "NO_DEPENDENCIA"}
    expected |= {"UNIDGEO"} if source == "estados" else {"SG_UF", "CO_MUNICIPIO", "NO_MUNICIPIO"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Campos obrigatórios ausentes no {source}: {sorted(missing)}")
    cut = df.loc[
        df["NO_CATEGORIA"].map(sem_acentos).eq("total")
        & df["NO_DEPENDENCIA"].map(sem_acentos).eq("total")
        & pd.to_numeric(df["NU_ANO_CENSO"], errors="coerce").eq(2022)
    ].copy()
    if cut.empty:
        raise ValueError("Fonte não contém recorte 2022: Total / Total")
    frames = []
    for etapa, prefix in ETAPAS.items():
        series = _pct_sum(cut, prefix)
        base = cut[["NU_ANO_CENSO"]].copy()
        base["etapa"] = etapa
        base["percentual_n1_n2"] = series
        if source == "estados":
            base["geografia"] = cut["UNIDGEO"].astype(str).str.strip()
            base["uf"] = base["geografia"].map(lambda value: NAME_TO_UF.get(sem_acentos(value), ""))
            base["regiao"] = base["uf"].map(lambda uf: UF[uf][2] if uf else "")
            base["nivel"] = base["geografia"].map(
                lambda value: "Brasil" if sem_acentos(value) == "brasil"
                else ("UF" if sem_acentos(value) in NAME_TO_UF else "Região")
            )
            base = base.loc[(base["nivel"] != "UF") | base["uf"].ne("")]
            columns = ["NU_ANO_CENSO", "nivel", "geografia", "uf", "regiao", "etapa", "percentual_n1_n2"]
        else:
            base["uf"] = cut["SG_UF"].astype(str)
            base["municipio"] = cut["NO_MUNICIPIO"].astype(str).str.strip()
            base["codigo_ibge"] = pd.to_numeric(cut["CO_MUNICIPIO"], errors="coerce")
            base["regiao"] = base["uf"].map(lambda uf: UF[uf][2] if uf in UF else "")
            base = base.loc[base["uf"].isin(UF) & base["codigo_ibge"].notna()]
            columns = ["NU_ANO_CENSO", "uf", "regiao", "codigo_ibge", "municipio", "etapa", "percentual_n1_n2"]
        frames.append(base[columns])
    result = pd.concat(frames, ignore_index=True)
    invalid = int(result["percentual_n1_n2"].isna().sum())
    result = result.dropna(subset=["percentual_n1_n2"]).copy()
    if source == "municipios":
        result["codigo_ibge"] = result["codigo_ibge"].astype(int)
    if result.empty:
        raise ValueError("Nenhuma observação válida após a validação dos percentuais")
    key = ["nivel", "geografia", "etapa"] if source == "estados" else ["codigo_ibge", "etapa"]
    if result.duplicated(key).any():
        raise ValueError(f"Chaves duplicadas em {source}; confira o filtro de localização e dependência")
    result.rename(columns={"NU_ANO_CENSO": "ano"}, inplace=True)
    return result, {"origem_linhas": len(df), "total_total_linhas": len(cut), "faltantes_removidos": invalid,
                    "linhas_validas": len(result)}


def build(cache: Path, out: Path, offline: bool = False) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    stats: dict = {}
    for source in ARCHIVES:
        payload, digest = obtain_archive(cache, source, not offline)
        frame, validation = reshape(read_official_excel(payload, source), source)
        target = out / ("geografias.csv" if source == "estados" else "municipios.csv")
        frame.to_csv(target, index=False, encoding="utf-8")
        stats[source] = {"arquivo": ARCHIVES[source][0], "sha256": digest, **validation}
    geo = pd.read_csv(out / "geografias.csv")
    if geo.loc[geo["nivel"].eq("UF"), "uf"].nunique() != 27:
        raise ValueError("Esperávamos 27 unidades federativas; verifique a fonte")
    if geo.loc[geo["nivel"].eq("Brasil"), "etapa"].nunique() != 4:
        raise ValueError("Totais nacionais incompletos")
    info = {
        "titulo": "Indicador de Esforço Docente · 2022",
        "fonte": "INEP — Indicadores Educacionais, IED 2022",
        "urls": {key: f"{BASE_URL}/{data[0]}" for key, data in ARCHIVES.items()},
        "metrica": "Soma percentual das categorias 1 e 2 (N1 + N2) por etapa",
        "filtros": "Localização Total; Dependência administrativa Total",
        "aviso": "Percentuais publicados por geografia; não inferir UF ou Brasil de médias municipais.",
        "ano": 2022,
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validacao": stats,
    }
    (out / "manifest.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=Path(".cache/inep/2022"))
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    parser.add_argument("--offline", action="store_true", help="Use apenas arquivos ZIP já baixados")
    args = parser.parse_args()
    result = build(args.cache, args.output, offline=args.offline)
    print(json.dumps(result["validacao"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
