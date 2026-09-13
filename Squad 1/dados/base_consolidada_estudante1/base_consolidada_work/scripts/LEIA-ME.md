# Pipeline da planilha consolidada — MINERA Goiás (Squad 1 / Estudante 1)

Gera `documentacao/prototipo_bases_consolidadas_v14.xlsx` e as camadas de mapa em `outputs/mapas/` a partir dos arquivos
em `dados/`. Nenhum número é digitado: tudo sai destes scripts.

## O que precisa existir

A pasta do projeto — a que contém este `base_consolidada_work/` — com:

```
<projeto>/
├── dados/                                              fontes (catálogo em dados/LEIA-ME.md e na aba 07)
├── documentacao/modelo_demo/prototipo_bases_consolidadas_v0.xlsx   modelo da planilha: é ENTRADA, não apagar (também vale direto em documentacao/)
└── base_consolidada_work/
    ├── requirements.txt
    └── scripts/                                        este pipeline
```

`outputs/mapas/` é criada na primeira execução.

## Como rodar

Python 3.11 (a planilha atual foi gerada com 3.11.3, no Windows 11). A partir da pasta do projeto:

```bash
pip install -r base_consolidada_work/requirements.txt
```

```bash
python base_consolidada_work/scripts/rodar_pipeline.py
```

O comando funciona a partir de qualquer pasta (use o caminho do script). Leva cerca de 12 minutos; a etapa de mapas
sozinha leva uns 4. Cada etapa roda num processo separado. Se uma falhar, o script mostra o fim do log e para: corrija e
retome com `--de <etapa>`. `--lista` mostra os nomes das etapas.

## Caminhos

`caminhos.py` calcula tudo a partir da própria posição — não há caminho de máquina nos scripts:

- `BASE` = dois níveis acima de `scripts/`, ou seja, a pasta do projeto — ou a pasta indicada na variável de ambiente
  `MINERA_BASE`, para rodar a cópia do GitHub usando um `dados/` guardado em outro lugar (os dados brutos não são versionados);
- `TMP` = JSONs intermediários entre as etapas, em `<pasta temporária do sistema>/minera_goias_pipeline` (fora do OneDrive
  e do git). Para usar outra pasta, defina a variável de ambiente `MINERA_TMP`.

O log de cada etapa fica em `<TMP>/logs/`.

## Etapas

| # | Script | O que faz |
|---|---|---|
| 1 | `build_base1_mineral_ano` | mineral × ano: AMB, CFEM, Cadastro Mineiro e SIGMINE; crosswalk de minerais, rochas por tipo de uso, tratamento da quantidade da CFEM |
| 2 | `build_base2_municipio_ano` | município × ano: malha, população e PIB do IBGE, CFEM, Cadastro Mineiro |
| 3 | `build_base3_empresa_mineral_ano` | empresa × mineral × ano: identidade do titular pela raiz do CNPJ, ponte CFEM → processo, máscara de CPF |
| 4 | `build_base4_mapas` | camadas de mapa (GeoPackage, GeoJSON, PMTiles) e a tabela de processos da aba 03 |
| 5 | `build_fato_08` | fato longo: uma linha por célula numérica do AMB e da CFEM |
| 6 | `build_interface_12` | entrega ao Squad 2, nos níveis estado e operação |
| 7 | `build_projetos_04` | projetos: camada ANM do Radar de Projetos |
| 8 | `build_ocorrencias_06` | ocorrências minerais do RECMIN |
| 9–16 | `write_base1` … `write_fato_08` | montam a planilha aba por aba a partir do modelo v0, passando pelos arquivos intermediários `v1_base1`, `v3`, `v4`, `v5`, `v5a_ocorrencias`, `v5b_projetos`, `v5c_interface` e `v5d_fato` em `documentacao/` |
| 17 | `write_governanca_into_workbook` | nomes do Contrato de Dados, catálogo de fontes (07), dicionário (14), validações (14b), 00_LEIA-ME e o arquivo final |

## Conferir o resultado

Abra a aba `14b_validacoes_governanca`. Hoje ela tem 3 ALERTAs esperados, que são alertas de dado sinalizados de
propósito: plausibilidade CFEM × AMB, processos com quantidade implausível na CFEM (09c) e produção repetida no AMB. Qualquer outro
ALERTA indica problema.

A ANM republica os arquivos com frequência, e um `dados/` diferente gera números diferentes. Para reproduzir exatamente
uma planilha, os arquivos precisam ter o sha256 registrado na aba 07 dela.

## Cuidados ao mexer nos scripts

- Os scripts executam trechos uns dos outros com `exec`: as Bases 2 e 3, a 06 e a governança usam as definições da
  Base 1 até o marcador `# 2) Carregar as fontes`; a Base 4 e a 08 executam a Base 3 inteira.
- Ordene antes de cortar ou juntar conjuntos (`sorted(...)[:n]`) e não use `hash()` do Python em IDs: a ordem de um `set`
  de texto e o `hash()` mudam a cada execução.
- Nome de aba do Excel tem no máximo 31 caracteres. Ao renomear um cabeçalho, renomeie também a coluna da Tabela do Excel.
- Aba nova precisa de descrição em `ABA_DESC` (governança) e as colunas novas, em `D`/`DA`: a governança acusa o que faltar.
