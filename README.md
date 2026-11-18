# Atlas Educação — Análises de Dados

**Engenharia de dados + visualização com storytelling**, evoluindo um portfólio de notebooks criado em 2023. Os notebooks originais foram preservados para registrar a evolução técnica.

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white) ![Dados](https://img.shields.io/badge/Fonte-INEP%202022-8cd46b) ![CI](https://github.com/JackNoArms/Analises-de-dados/actions/workflows/checks.yml/badge.svg)

## O problema

O Indicador de Esforço Docente é publicado em planilhas por geografia, etapa e outros recortes. Interpretá-las exige cuidado: misturar localizações ou dependências pode duplicar registros, e uma média simples dos municípios **não reproduz** o indicador oficial de uma UF.

Este projeto transforma as planilhas públicas de 2022 em dados verificáveis e uma experiência interativa, com comparações claras, filtros, exportação e limites metodológicos explícitos.

## Explore o dashboard

![Dashboard Atlas Educação em desktop, com dados oficiais de 2022](docs/dashboard-desktop.png)

O painel tem design escuro, filtros por etapa/UF/região, estatísticas do Brasil, rankings estaduais, médias **exploratórias** das UFs por região, busca de municípios e exportação CSV. Disponível também em telas pequenas, com navegação por teclado e estados acessíveis.

**Execute o servidor local na raiz do repositório:**

```powershell
python -m http.server 8000
```

Abra **http://localhost:8000/dashboard/** no navegador. Não use `file://`: a leitura dos CSVs depende de HTTP. A interface usa CSS Bootstrap opcional por CDN e inclui estilos próprios para funcionar sem essa folha externa; os gráficos são nativos em HTML/CSS/JS, sem biblioteca adicional.

## Reproduza o ETL com dados oficiais

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m src.inep_pipeline
.\.venv\Scripts\python.exe -m pytest tests/ -q
```

Em Linux/macOS, substitua `.\.venv\Scripts\python.exe` por `.venv/bin/python`.

O pipeline baixa os dois ZIPs oficiais para `.cache/inep/2022`, verifica o SHA-256 antes de ler as planilhas XLSX e gera em `data/processed/` os arquivos `geografias.csv`, `municipios.csv` e `manifest.json`. Os arquivos brutos ficam **fora do Git**. Para reproduzir novamente usando os ZIPs já baixados: `python -m src.inep_pipeline --offline`.

### Evidência de qualidade dos dados (base 2022)

| Recorte | Origem | Saída normalizada |
| --- | ---: | ---: |
| Brasil, regiões e estados | 586 linhas | 132 observações válidas (33 geografias × 4 etapas) |
| Municípios | 66.266 linhas | 22.273 observações válidas (5.570 municípios, até 4 etapas) |
| Valores ausentes / inválidos no recorte municipal | — | 7 observações descartadas, sem trocar ausente por zero |

**Indicador exibido:** participação percentual nos níveis **1 + 2** do IED, não quantidade de professores. Os totais nacionais e estaduais vêm da própria planilha oficial, **não** de médias dos municípios. O painel utiliza *localização Total* e *dependência administrativa Total*. Não presume tendência histórica a partir de um único ano.

Leia o [guia de metodologia e proveniência](docs/METODOLOGIA.md) para as definições, limites e verificações.

## Estrutura

```text
dashboard/        Interface web e filtros (HTML, CSS, JavaScript)
src/              Pipeline Python reproduzível
data/processed/   Recortes oficiais transformados + manifesto SHA-256
tests/            Testes unitários e integridade do dataset
notebooks/        Quatro estudos históricos originais (preservados)
docs/             Metodologia, capturas e roteiro de evolução
```

## Outros estudos preservados

- **Vendas de consoles:** análise exploratória e estatística descritiva.
- **Índice Global de Paz:** estudo exploratório.
- **Churn bancário:** classificação supervisionada com SVC.
- **INEP Esforço Docente:** notebook original que motivou o pipeline estruturado atual.

Parte desses notebooks usa conjuntos de dados originalmente acessados pelo Kaggle. **As bases Kaggle não são distribuídas neste repositório**, e esses notebooks não foram reescritos nem apresentados como reproduzidos nesta rodada.

## Processo de desenvolvimento

Commits por mudança verificável, branches curtas, revisão em Pull Request e GitHub Actions para testes e sintaxe. Consulte [CONTRIBUTING.md](CONTRIBUTING.md).

### Próximos incrementos

- Adicionar novas séries anuais oficiais com definição compatível, sem extrapolar tendências.
- Expandir o storytelling regional usando as linhas oficiais de região, não médias de UF.
- Melhorar o fluxo de publicação do dashboard (hospedagem estática opcional) e experiência de leitura no celular.
- Revisar os notebooks legados individualmente com dados, licenças e testes apropriados.

**Crédito:** [Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP)](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais). Portfólio independente; não representa publicação oficial do INEP.
