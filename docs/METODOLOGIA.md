# Metodologia — Indicador de Esforço Docente (INEP, 2022)

## Fonte e rastreabilidade

Dados obtidos diretamente dos arquivos públicos de Indicadores Educacionais do INEP, ano-base 2022:

- [IED 2022 Brasil, regiões e UFs](https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2022/IED_2022_BRASIL_REGIOES_UFS.zip)
- [IED 2022 Municípios](https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2022/IED_2022_MUNICIPIOS.zip)

As planilhas XLSX são lidas a partir dos ZIPs, sem modificação das origens. O código confere os hashes SHA-256 fixados em `src/inep_pipeline.py`, registrados também em `data/processed/manifest.json`. Se a fonte mudar, o ETL interrompe a execução, exigindo uma revisão consciente. Os ZIPs e XLSX não são versionados; a saída CSV transformada, sim.

## Métrica

Para cada etapa de ensino e unidade geográfica:

```text
percentual_n1_n2 = percentual_categoria_1 + percentual_categoria_2
```

Etapas: ensino fundamental, anos iniciais, anos finais e ensino médio.

**Atenção:** os números descrevem uma composição percentual do indicador, não quantidade de professores, carga horária individual ou uma medida direta de qualidade educacional. Não inferir causalidade.

## Recortes e validação

- Ano 2022; `NO_CATEGORIA == Total` (localização); `NO_DEPENDENCIA == Total` (dependência administrativa).
- Conversão explícita de percentuais para número; marcadores `--` e valores inválidos não viram zero.
- Percentuais dos dois componentes precisam estar entre 0 e 100 e sua soma dentro de 0 a 100,2 para tolerar arredondamento.
- As 27 UFs são conferidas contra o cadastro de siglas; os 5.570 códigos municipais são preservados como IBGE.
- Chaves duplicadas interrompem a transformação.
- Brasil e UF são **dados originais publicados**: jamais recalculados por média ou soma municipal.

A tela de regiões usa exclusivamente **média simples dos percentuais de UFs**, rotulada como exploração, e **não** deve ser confundida com a medida oficial agregada da região. Mesmo o ranking de municípios deve ser interpretado com atenção a contextos populacionais, não como uma competição entre escolas ou professores.

## Qualidade e limitações

Em 2022, a transformação com os dois arquivos originais registrou:

- Geografias: 586 linhas originais, 33 geografias no recorte Total/Total, 132 observações válidas.
- Municípios: 66.266 linhas originais, 5.570 no recorte Total/Total, 22.273 observações válidas e 7 combinações sem percentual válido.

O tratamento é reprodutível ao obter as mesmas fontes com hashes correspondentes. Conclusões são específicas a 2022; não se deve desenhar tendência temporal sem novas bases verificadas.

## Testes realizados

- Testes unitários com dados sintéticos verificam filtros, somas, dados ausentes, chaves duplicadas e validação SHA-256.
- Testes do dataset verificam 27 UFs, Brasil com quatro etapas, 5.570 municípios, unicidade e valores entre 0 e 100.
- Teste Playwright headless: carregamento, filtro de etapa, região/UF, busca, exportação e layout mobile.
- Não foi realizada auditoria estatística externa independente; isto é um projeto educacional e de portfólio.
