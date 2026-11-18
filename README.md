# Análises de Dados

Projetos de **análise exploratória, tratamento de dados e visualização**, desenvolvidos em Python. O repositório reúne estudos com notebooks Jupyter e um dashboard interativo sobre indicadores da educação brasileira.

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-Análise%20de%20dados-150458?logo=pandas&logoColor=white)

## Atlas Educação — Indicador de Esforço Docente

O **Atlas Educação** permite explorar o Indicador de Esforço Docente (IED) publicado pelo INEP para 2022. A aplicação reúne informações nacionais, estaduais e municipais em um painel com filtros e gráficos.

![Dashboard Atlas Educação](docs/dashboard-desktop.png)

### O que você pode explorar

- **Panorama nacional:** percentual de docentes nas categorias 1 e 2 do indicador, por etapa de ensino.
- **Comparação entre estados:** visualização das 27 unidades federativas e referência nacional.
- **Regiões:** médias dos percentuais estaduais, indicadas como comparação exploratória.
- **Municípios:** busca por nome, filtro por estado e consulta dos registros disponíveis.
- **Exportação CSV:** download dos municípios do recorte selecionado.
- **Layout responsivo:** interface de alto contraste para desktop e celular.

Os resultados usam as planilhas do **INEP 2022**. A metodologia do indicador, os filtros aplicados e as limitações das comparações estão descritos em [Metodologia](docs/METODOLOGIA.md).

### Executar o dashboard

Clone o repositório e inicie um servidor HTTP na raiz da pasta:

```powershell
git clone https://github.com/JackNoArms/Analises-de-dados.git
cd Analises-de-dados
python -m http.server 8000
```

Acesse **http://localhost:8000/dashboard/**.

Os CSVs processados necessários para visualizar o painel já acompanham o projeto.

## Pipeline de dados

O projeto inclui um pipeline em Python que baixa os arquivos públicos de 2022, valida as fontes e transforma os dados para uso no dashboard.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.inep_pipeline
```

A transformação gera:

| Arquivo | Conteúdo |
| --- | --- |
| `data/processed/geografias.csv` | Brasil, regiões e unidades federativas |
| `data/processed/municipios.csv` | Dados municipais por etapa de ensino |
| `data/processed/manifest.json` | Fonte, versão e verificações dos arquivos |

O pipeline trabalha com quatro etapas de ensino e preserva as métricas oficiais por geografia. A validação confere a integridade dos arquivos por SHA-256 e identifica dados ausentes ou inválidos.

## Outros estudos

A pasta `notebooks/` contém análises em Jupyter Notebook:

| Tema | Conteúdo |
| --- | --- |
| **Vendas de consoles** | Exploração e comparação de dados de vendas |
| **Índice Global da Paz** | Análise exploratória de indicadores por país |
| **Churn bancário** | Modelagem de classificação com SVC |
| **Esforço docente** | Investigação do indicador educacional do INEP |

Alguns notebooks utilizam conjuntos de dados externos e podem precisar dos arquivos originais para execução.

## Tecnologias

**Python**, **Pandas**, **Jupyter Notebook**, **HTML**, **CSS** e **JavaScript**. O tratamento das planilhas utiliza **OpenPyXL**, e os testes são executados com **Pytest**.

## Estrutura do projeto

```text
dashboard/       Aplicação web interativa
src/             ETL e validação dos dados do INEP
data/processed/  Dados tratados para visualização
notebooks/       Estudos e análises em Jupyter
tests/           Testes automatizados
docs/            Metodologia e imagens
```

## Testes

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

**Fonte:** [INEP — Indicadores Educacionais](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais).
