# Base consolidada do Squad 1 — Estudante 1 (Eliel)

Base Mineral de Goiás — versão 1: minerais, empresas, processos e projetos da ANM, municípios, ocorrências geológicas do SGB,
produção mineral e CFEM de Goiás, com ID estável, fonte e unidade em cada número, como pede o Contrato de Dados.

| O quê | Onde |
|---|---|
| **Entregável** (25 abas, versão 15) | `documentacao/prototipo_bases_consolidadas_v15.xlsx` — comece pela aba `00_LEIA-ME` |
| Entrega ao Squad 2 | aba `12_interface_squad1_squad2` |
| Catálogo de fontes (link oficial, sha256, período) | aba `07_dim_fontes` e `dados/LEIA-ME.md` |
| Dicionário de dados e validações automáticas | abas `14_dicionario_dados` e `14b_validacoes_governanca` |
| Código que gera a planilha e os mapas | `base_consolidada_work/scripts/` (instruções no `LEIA-ME.md` de lá) |
| Modelo da planilha (entrada do pipeline) | `documentacao/modelo_demo/prototipo_bases_consolidadas_v0.xlsx` |

## O que não está aqui, e por quê

- **Dados brutos** (`dados/`, cerca de 300 MB): o GitHub do projeto é para código e documentação, não fonte de dado, e
  alguns arquivos da ANM trazem CPF dentro do nome de titulares. Cada arquivo, com link oficial e sha256, está listado em
  `dados/LEIA-ME.md` e na aba 07. Para rodar o pipeline, coloque os arquivos em `dados/` (a pasta é ignorada pelo git) ou
  aponte a variável de ambiente `MINERA_BASE` para uma pasta que os tenha.
- **Camadas de mapa** (`outputs/mapas/`, cerca de 200 MB) e as planilhas intermediárias `v1_base1` … `v5d_fato`: são
  geradas de novo a cada execução do pipeline.

## Site e importador

O importador da VPS (`ingestion/`) carrega os CSV e XLSX do `main` no banco do site; a planilha v15 entra como fonte
`source_unvalidated` (as versões anteriores ficam só no histórico do git, para não serem carregadas em dobro). O modelo v0 fica em `modelo_demo/` para não ser carregado: ele só tem dados ilustrativos. O atlas do
site (`data/atlas/`) é um retrato separado e não é atualizado por esta pasta.

## LGPD

O CPF que aparece dentro do nome de um titular (empresário individual) sai mascarado na planilha (`***456789**`), e a aba
14b confere a cada geração que não há CPF completo em nenhum campo de texto. Os nomes de titulares pessoa física continuam,
como a ANM os publica.

## Como rodar

A partir da raiz do repositório, com Python 3.11:

```bash
pip install -r "Squad 1/dados/base_consolidada_estudante1/base_consolidada_work/requirements.txt"
python "Squad 1/dados/base_consolidada_estudante1/base_consolidada_work/scripts/rodar_pipeline.py"
```

Leva cerca de 12 minutos e precisa dos dados brutos (veja acima). A aba 14b da planilha gerada mostra se algo saiu do esperado.
