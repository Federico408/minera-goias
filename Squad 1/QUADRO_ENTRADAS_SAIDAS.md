# Squad 1 — Quadro de entradas e saídas

**MINERA Goiás · Entrega Avaliativa 1 (21/09/2026)**

A regra 1 da entrega pede que cada estudante indique **uma entrada recebida** de outro estudante ou squad e **uma saída usada** por
outro. O fluxo do Contrato de Dados é Squad 1 → Squad 2 → Squad 3. Situação levantada em 13/09/2026 no repositório
`mineragoias-rgb/minera-goias`.

## Chaves que todos os componentes do Squad 1 devem usar

Todas as chaves saem da base consolidada do Estudante 1 (`Squad 1/Bases consolidadas/`). Nome e formato estão no Contrato de Dados e na
aba `14_dicionario_dados`.

| Chave | Formato | Aba de origem |
|---|---|---|
| `mineral_id` | `MIN_###` | `01_dim_minerais` (lista oficial de minerais, com sinônimos na 01b) |
| `company_id` | `COM_CNPJ_<raiz de 8 dígitos>`, `COM_NOME_<hash>` ou `COM_NAO_IDENTIFICADO` | `02_dim_empresas` |
| `operation_id` | `OPE_<número>_<ano do processo>` | `03_dim_operacoes` |
| `project_id` | `PRJ_<processo-âncora>` | `04_dim_projetos` |
| `municipality_id` | código IBGE de 7 dígitos | `05_dim_municipios` |
| `occurrence_id` | `OCC_<id do SGB>` | `06_dim_ocorrencias_geologicas` |
| `source_id` | `SRC_*` | `07_dim_fontes` |

## Quadro por componente

### S1-E1 — Base Mineral de Goiás (Eliel) · pronta

| | O quê | De / para quem | Onde |
|---|---|---|---|
| **Entrada** | Contrato de Dados V1 e lista oficial de minerais (IDs, nomes de campo, unidades) | Gestor do projeto | `📄 MINERA Goiás — Contrato de Dados.txt`, aplicado nas abas 01–14 |
| **Entrada** | Arquivos oficiais da ANM, do IBGE e do SGB | Fontes públicas | `Squad 1/Dados brutos/` |
| **Saída** | Produção (`production_t`) por mineral e ano, observada no estado e estimada por operação, com coordenadas | **Squad 2** — intensidade energética (Sarah) e motor 2027–2040 (Federico) | aba `12_interface_squad1_squad2` |
| **Saída** | Camada ANM do Radar de Projetos: `project_id`, estágio, classificação por evidência na ANM, brownfield | **S1-E2** (Lucas) | aba `04_dim_projetos` e camada `projetos_futuros` |
| **Saída** | Campos com vazio por aba e flags de estimativa (`valor_observado_estimado`, `metodo_estimacao`, `erro_estimativa_intervalo`) | **S1-E3** | abas `14_dicionario_dados` e `12_interface_squad1_squad2` |
| **Saída** | Planilha carregada no banco do site; atlas com municípios, processos, projetos, ocorrências e gráficos | **Squad 3** — banco/API (Kayo) e mapa/painéis | tabelas `ingest_*` da VPS; `data/atlas/` |

### S1-E2 — Radar de Projetos Minerais (Lucas Maia) · pendente no GitHub

| | O quê | De / para quem | Onde |
|---|---|---|---|
| **Entrada** | `project_id`, estágio na ANM, brownfield e chaves de mineral, titular e município | S1-E1 | aba `04_dim_projetos` (3.377 projetos) |
| **Entrada** | Licenças, pareceres e RIMA; FRE, IPE, DFP e ITR; relatórios de RI | SEMAD, CVM, empresas | a coletar |
| **Saída esperada** | Radar com capacidade, ano previsto, CAPEX, evidências com fonte e data, classificação completa (operação … sinal) | **Squad 2** — motor (entrada de projetos até 2040); **Squad 3** — listagem e mapa | a publicar em `Squad 1/` |

### S1-E3 — Dados faltantes e estimativas (responsável a confirmar) · pendente no GitHub

| | O quê | De / para quem | Onde |
|---|---|---|---|
| **Entrada** | % de vazio por campo, flags de estimativa e produção por operação | S1-E1 | abas `14` e `12` |
| **Entrada** | Radar de projetos (capacidade, ano previsto) | S1-E2 | a publicar |
| **Entrada** | Consumo horário por agente e ativo de carga | CCEE | `Squad 1/dados/CCEE/` (2024–2026) |
| **Saída esperada** | Valores estimados com valor original, método, erro ou intervalo e flag observado/estimado | **Squad 2** — intensidade e motor | a publicar em `Squad 1/` |

## O que ainda precisa ser combinado

1. **Squad 2 × aba 12:** confirmar que o formato atende a intensidade e o motor — base física (`production_basis`), unidades e o
   tratamento da parte sem coordenadas (ver `nota_squad2_operacoes_sem_coordenadas.md`). O pacote `Bases consolidadas/documentacao/pacote_squad2/` traz a aba em CSV,
   o dicionário, a correspondência com o `production_history` do motor e os cinco pontos a confirmar.
2. **S1-E2 × aba 04:** usar `project_id` da 04 como chave do radar, para não criar outro identificador para o mesmo projeto.
3. **S1-E3:** escolher a variável material a estimar (produção sem coordenadas, capacidade dos projetos ou intensidade por operação) e
   registrar o método com erro.
4. **Squad 3:** confirmar se o banco e a API consomem a planilha pelo importador ou por uma carga própria das abas.
