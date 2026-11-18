# Contribuindo

As alterações devem ser auditáveis e pequenas. Não reescreva nem retrodate commits históricos.

1. Crie uma branch `feat/`, `fix/`, `docs/` ou `test/` a partir de `master`.
2. Faça uma alteração por unidade lógica e documente qualquer interpretação nova da métrica.
3. Execute `python -m pytest tests/ -q` e `node --check dashboard/app.js`.
4. Para UI, teste teclado, foco, estados vazio/erro, 390 px e 1366 px com dados sintéticos de teste.
5. Examine `git status`, `git diff --check`, arquivos rastreados e segredos antes do commit.
6. Abra PR com objetivo, evidências, limitações e estratégia de rollback. Só faça merge após CI verde.

Não comite ZIPs/Excel brutos baixados, variáveis de ambiente, arquivos de cliente, perfis ou dados privados. Os CSVs em `data/processed` são derivadas de dados públicos do INEP; mantenha origem e versão verificáveis.
