# Relatório de qualidade — Base Mineral de Goiás (v17)

Gerado por `gerar_relatorio_qualidade.py` a partir de `prototipo_bases_consolidadas_v17.xlsx`. Todos os números saem da planilha; o detalhe de cada item está na aba citada. Regra do projeto: **divergências são registradas, não corrigidas** — nada aqui foi apagado ou ajustado na fonte.

## 1. Resumo

- **Validações automáticas (aba 14b):** 36 checagens — 33 OK e 3 ALERTA. Os alertas são de dado, sinalizados de propósito; a lista completa está na seção 7.
- **Fato longo (aba 08):** 153.855 linhas, uma por célula numérica da fonte; status: valido 152.904; alerta_processo_09c 698; alerta_producao_repetida 164; quantidade_excluida_da_soma_09b 89.
- **Quantidades da CFEM fora da soma de toneladas (aba 09b):** 89 linhas (o R$ continua somado).
- **Processos com quantidade implausível na CFEM (aba 09c):** 45 processo-anos, mantidos na soma e sinalizados.

  - ALERTA — Plausibilidade: CFEM comercializada (t) ÷ produção do AMB na base mais próxima (bruta ou beneficiada), por mineral e ano em GO, fora de 0,0…: n = 33.
  - ALERTA — Processos com quantidade na CFEM implausível frente ao AMB do estado (acima do total ou, em metais, R$/t incompatível; mantidos na soma, si…: n = 45.
  - ALERTA — 08: mesma tonelagem de produção em linhas diferentes da mesma UF e ano no AMB (co-produto, mineral separado por teor ou mesma declaração em…: n = 164.

## 2. Faltantes

Campos das abas de dados com metade ou mais das linhas vazias (aba 14, coluna `pct_vazio`). Vazio não é zero: significa que a fonte não informa ou que o campo não se aplica à linha — a descrição de cada campo explica.

| Aba | Campo | % vazio | O que o campo é |
|---|---|---:|---|
| `01_dim_minerais` | `mineral_grupo_pai` | 95,5 | mineral_id do mineral-pai quando o item é subtipo (ex.: Calcário Calcítico → Calcário). |
| `02_dim_empresas` | `metodo_estimacao` | 100 | Método quando o valor não é observado; vazio nas linhas observadas. |
| `02_dim_empresas` | `nomes_alternativos` | 99,7 | Outras grafias do titular vistas nas fontes (até 3). |
| `02_dim_empresas` | `cnpj_raiz` | 55 | 8 primeiros dígitos do CNPJ: identificam a empresa (o restante é o estabelecimento). |
| `03_dim_operacoes` | `metodo_estimacao` | 100 | Método quando o valor não é observado; vazio nas linhas observadas. |
| `03_dim_operacoes` | `cfem_2024_2026_brl` | 94,9 | CFEM recolhida pelo processo em 2024–2026 (2026 parcial, até 08/2026). |
| `03_dim_operacoes` | `cfem_2022_2026_brl` | 94,1 | CFEM recolhida pelo processo em 2022–2026 (2026 parcial). |
| `04_dim_projetos` | `capacidade_t_ano` | 100 | Capacidade anunciada. VAZIA de propósito: nenhuma fonte do Squad 1 publica capacidade (vem de RI, CVM ou SEMAD — Estudante 2). |
| `04_dim_projetos` | `capex_brl` | 100 | CAPEX anunciado. VAZIO de propósito: vem de RI ou CVM (Estudante 2). |
| `04_dim_projetos` | `ano_previsto_entrada` | 100 | VAZIO de propósito: a ANM não publica cronograma; vem de RI, CVM ou SEMAD (Estudante 2). |
| `04_dim_projetos` | `operacao_adjacente` | 95,5 | Operações ativas (03) do mesmo titular e mineral a até 500 m do projeto. |
| `04_dim_projetos` | `observacao` | 93,1 | Nota da linha: vários municípios, titular sem CNPJ, processo sem substância ou candidato a expansão. |
| `05_dim_municipios` | `metodo_estimacao` | 100 | Método quando o valor não é observado; vazio nas linhas observadas. |
| `06_dim_ocorrencias_geologicas` | `metodo_estimacao` | 100 | Vazio: a 06 só tem valores observados na fonte. |
| `06_dim_ocorrencias_geologicas` | `substancias_sem_categoria_anm` | 99,8 | Substâncias sem categoria ANM (sem mineral_id), guardadas pelo nome — ver 06b. |
| `06_dim_ocorrencias_geologicas` | `observacao` | 98,4 | Nota da linha: município ou UF divergente, coordenada repetida, motivo do garimpo diferente, substância sem categoria ANM. |
| `06_dim_ocorrencias_geologicas` | `motivo_inatividade` | 98,1 | Motivo da inatividade na data do cadastro (exaurido, paralisado, intermitente). |
| `06_dim_ocorrencias_geologicas` | `descricao` | 96,2 | Descrição do afloramento no RECMIN (preenchida em poucas ocorrências). |
| `06_dim_ocorrencias_geologicas` | `rochas_afloramento` | 96 | Rochas descritas no afloramento. |
| `06_dim_ocorrencias_geologicas` | `projeto_sgb` | 92,1 | Projeto de mapeamento do SGB que cadastrou a ocorrência; vazio na maioria. |
| `06_dim_ocorrencias_geologicas` | `folha_sgb` | 92,1 | Folha cartográfica do SGB. |
| `06_dim_ocorrencias_geologicas` | `numero_campo` | 92,1 | Número de campo do ponto no projeto do SGB. |
| `06_dim_ocorrencias_geologicas` | `situacao_explotacao` | 91,5 | Ativo(a) ou Inativo(a) na data do cadastro (situacao_mina; situacao_garimpo é cópia idêntica na fonte). |
| `06_dim_ocorrencias_geologicas` | `tipos_alteracao` | 90,9 | Alterações hidrotermais/intempéricas associadas. |
| `06_dim_ocorrencias_geologicas` | `tipo_afloramento` | 90 | Tipo de afloramento (pedreira, mina, corte de estrada…); vazio na maioria. |
| `06_dim_ocorrencias_geologicas` | `project_ids_sobrepostos` | 87,6 | Projetos da 04 que contêm esses processos. |
| `06_dim_ocorrencias_geologicas` | `rochas_encaixantes` | 51,5 | Rochas encaixantes da mineralização. |
| `08_fato_producao_energia` | `project_id` | 100 | Vazio: nenhuma fonte do Squad 1 / Estudante 1 identifica projeto (vem do Radar de Projetos). |
| `08_fato_producao_energia` | `metodo_estimacao` | 100 | Vazio: a 08 só tem valores observados na fonte. |
| `08_fato_producao_energia` | `erro_estimativa_intervalo` | 100 | Erro ou intervalo de referência da estimativa (obrigatório quando o dado não é observado). |
| `08_fato_producao_energia` | `tratamento` | 91,1 | O que foi feito entre valor_original e valor_tratado. Vazio = só a leitura do número (vírgula decimal). |
| `08_fato_producao_energia` | `notas` | 89,7 | Notas de rastreabilidade da linha. |
| `08_fato_producao_energia` | `production_basis` | 70,6 | Base física da quantidade (campo do contrato): ROM (produção bruta), beneficiada ou conteudo_mineral (contido). Vazio para valores em R$ e para a CFEM, que não… |
| `08_fato_producao_energia` | `operation_id` | 53,2 | Só na CFEM, quando o processo tem poligonal no SIGMINE de GO (03_dim_operacoes). Vazio no AMB (grão UF). |
| `09_cons_mineral_ano` | `metodo_estimacao` | 100 | Método quando o valor não é observado; vazio nas linhas observadas. |
| `09_cons_mineral_ano` | `cfem_qtd_outras_unidades` | 97,3 | Quantidade comercializada em unidades sem conversão para t (m³, l, m²), somada por unidade. |
| `09_cons_mineral_ano` | `cfem_qtd_comercializada_t` | 89,7 | Quantidade comercializada declarada na CFEM, só unidades de massa convertidas para t (kg, g, quilate), sem as linhas corrompidas ou implausíveis (ver 09b). NÃO… |
| `09_cons_mineral_ano` | `cfem_qtd_linhas_excluidas` | 89,4 | Linhas da CFEM do mineral no ano cuja quantidade saiu da soma (o R$ foi mantido). Detalhe linha a linha na aba 09b. |
| `09_cons_mineral_ano` | `cfem_recolhido_brl` | 89,4 | CFEM recolhida em GO para o mineral no ano (vazia nas linhas BR: só temos CFEM de GO). |
| `09_cons_mineral_ano` | `qtd_titulares_cfem` | 62,8 | Titulares distintos que recolheram CFEM para o mineral (2022–2026). ATENÇÃO: contado pelo CPF_CNPJ da CFEM, que está corrompido (notação científica) — CNPJs di… |
| `09_cons_mineral_ano` | `qtd_processos_cadastro_mineiro` | 62,8 | Processos distintos em GO com título citando o mineral — fotografia atual, repetida em todas as linhas do mineral. |
| `09_cons_mineral_ano` | `qtd_titulares_cadastro_mineiro` | 62,8 | Titulares distintos com título — fotografia atual, repetida em todas as linhas. |
| `09_cons_mineral_ano` | `qtd_processos_sigmine` | 62,8 | Processos com polígono no SIGMINE — fotografia atual. |
| `10_cons_municipio_ano` | `observacao` | 100 | Nota metodológica ou de rastreabilidade da linha. |
| `10_cons_municipio_ano` | `metodo_estimacao` | 100 | Método quando o valor não é observado; vazio nas linhas observadas. |
| `10_cons_municipio_ano` | `populacao` | 74,3 | População residente estimada; preenchida só na linha do ano de referência (populacao_ano). |
| `10_cons_municipio_ano` | `pib_total_brl` | 74,3 | PIB a preços correntes, convertido de mil reais (SIDRA) para R$; só na linha do ano de referência. |
| `11_cons_empresa_ano_mineral` | `production_t` | 100 | VAZIO de propósito: a ANM não publica produção por empresa (gap QC07). Nome fixado no contrato. |
| `11_cons_empresa_ano_mineral` | `energy_mwh` | 100 | VAZIO de propósito: depende do pareamento com a CCEE (Squad 2). Nome fixado no contrato. |
| `11_cons_empresa_ano_mineral` | `energy_intensity_mwh_t` | 100 | VAZIO de propósito: energy_mwh / production_t na mesma production_basis. Nome fixado no contrato. |
| `11_cons_empresa_ano_mineral` | `observacao` | 100 | Nota metodológica ou de rastreabilidade da linha. |
| `11_cons_empresa_ano_mineral` | `metodo_estimacao` | 100 | Método quando o valor não é observado; vazio nas linhas observadas. |
| `11_cons_empresa_ano_mineral` | `year` | 79,8 | Ano da CFEM (contrato). Vazio = mineral citado nos títulos do titular, sem CFEM. |
| `11_cons_empresa_ano_mineral` | `cfem_recolhido_brl` | 79,8 | CFEM do titular para o mineral no ano, ligada pela ponte do número do processo. A soma da coluna bate com o arquivo bruto (R$ 867.578.398,91). |
| `12_interface_squad1_squad2` | `project_id` | 100 | Vazio: depende do Radar de Projetos (Squad 1 / Estudante 2). |
| `12_interface_squad1_squad2` | `observacao` | 74,8 | Nota da linha: por que não há abertura, subitens somados, processo sem poligonal ou titular não identificado. |

Vazios esperados: `capacidade_t_ano`, `capex_brl` e `ano_previsto_entrada` da aba 04 dependem de evidência corporativa (Estudante 2); `metodo_estimacao` fica vazio nas linhas observadas; na aba 06, a maioria dos campos descritivos do RECMIN vem vazia da própria fonte.

## 3. Duplicidades

Cada linha de dimensão tem um ID único:

| Aba | ID | Linhas | Valores distintos |
|---|---|---:|---:|
| `01_dim_minerais` | `mineral_id` | 67 | 67 |
| `02_dim_empresas` | `company_id` | 5.045 | 5.045 |
| `03_dim_operacoes` | `operation_id` | 16.656 | 16.656 |
| `04_dim_projetos` | `project_id` | 3.377 | 3.377 |
| `05_dim_municipios` | `municipality_id` | 246 | 246 |
| `06_dim_ocorrencias_geologicas` | `occurrence_id` | 1.796 | 1.796 |
| `07_dim_fontes` | `source_id` | 20 | 20 |
| `08_fato_producao_energia` | `fato_id` | 153.855 | 153.855 |

- **IDs no padrão do Contrato de Dados** (OK, n = 0): IDs fora do padrão — nenhum
- **Chaves das consultas → dimensões** (OK, n = 0): Integridade referencial (chaves das abas consolidadas → dimensões) — 0 órfãos
- **Produção repetida no AMB** (ALERTA, n = 164): 08: mesma tonelagem de produção em linhas diferentes da mesma UF e ano no AMB (co-produto, mineral separado por teor ou mesma declaração em duas categorias) — … — 74 grupos, 164 linhas (com status alerta_producao_repetida: 164). Numa soma contam a mais 97,774 t dentro do mesmo mineral (infla a linha BR da 09) e 294,862,785 t entre minerais. Goiás: producao_rom 2023: 5526825,440000 t em Nióbio + Bário; producao_beneficiada 2011: 395 t em Rochas Ornamentais + Rochas Ornamentais - Outras. A fonte não tem linha 100% duplicada — as linhas diferem na substância, na categoria ou no …
- **Células da fonte no fato longo** (OK, n = 0): 08: campos de governança por linha — source_url, data_acesso e tipo_fonte iguais à 07; não observado sem método; mesma célula da fonte em duas linhas — divergentes da 07: 0; não observado sem metodo_estimacao: 0; células repetidas: 0. valor_observado_estimado: {'observado': 153855}; status_validacao: {'valido': 152904, 'alerta_producao_repetida': 164, 'alerta_processo_09c': 698, 'quantidade_excluida_da_soma_09b': 89}
- **Titulares (aba 02b):** nome do SIGMINE sem titular equivalente no Cadastro Mineiro: 40; processo do CFEM sem titular correspondente no Cadastro Mineiro: 30; AMBIGUO: mesmo nome, raizes de CNPJ diferentes (NAO fundidas): 6; mesma_raiz_cnpj_varias_grafias (fundidas): 1. Nomes iguais com raízes de CNPJ diferentes NÃO são fundidos.

## 4. Divergências entre fontes

- **Quantidade comercializada da CFEM × produção do AMB** (ALERTA, 33 mineral-anos fora de 0,05–2×): a quantidade da CFEM não serve como proxy de produção. Diamante 2024: 0.00× (bruta); Amianto 2024: 0.00× (bruta); Gemas 2024: 0.00× (bruta); Amianto 2025: 0.00× (beneficiada); Amianto 2022: 0.00× (beneficiada); Amianto 2023: 0.00× (beneficiada); Gemas 2023: 0.00× (bruta); Monazita e Terras-Raras 2024: 0.00× (beneficiada); Gemas 2025: 0.00× (bruta); Gemas 2022: 0.00× (bruta); Prata 2025: 1,488.36× (beneficiada); Titânio 2025: 411.39× (beneficiada); Rochas Ornamentais - Outras 2024: 363.39× (bruta); Rochas Ornamentais - Outras 2025: 87.97× (bruta); T…

- **Processos da aba 09c:** 45 processo-anos (alta: 27; moderada: 18). Os de maior razão:

| Mineral | Ano | Processo | CFEM (t) | Limite do AMB (t) | Razão | Critério | Severidade |
|---|---:|---|---:|---:|---:|---|---|
| Prata | 2025 | 960658/1987 | 64 | 0,043 | 1.488,4× | tonelagem acima do total estadual; R$/t mais de 10× abaixo … | alta |
| Titânio | 2025 | 861559/2021 | 17.660 | 43 | 410,7× | tonelagem acima do total estadual | alta |
| Rochas Ornamentais - Outras | 2024 | 860633/2014 | 534.065 | 1.750 | 305,1× | tonelagem acima do total estadual | alta |
| Rochas Ornamentais - Outras | 2025 | 860633/2014 | 745.162 | 13.690 | 54,4× | tonelagem acima do total estadual | alta |
| Titânio | 2024 | 861559/2021 | 2.607 | 52 | 50,1× | tonelagem acima do total estadual | alta |
| Rochas Ornamentais - Outras | 2024 | 860529/2006 | 66.839 | 1.750 | 38,2× | tonelagem acima do total estadual | alta |
| Rochas Ornamentais - Outras | 2025 | 860529/2006 | 449.386 | 13.690 | 32,8× | tonelagem acima do total estadual | alta |
| Nióbio | 2023 | 803343/1973 | 129.472.247 | 5.526.825 | 23,4× | tonelagem acima do total estadual | alta |
| Rochas Ornamentais - Outras | 2024 | 860330/2007 | 31.036 | 1.750 | 17,7× | tonelagem acima do total estadual | alta |
| Rochas Ornamentais - Outras | 2022 | 860633/2014 | 423.562 | 33.704 | 12,6× | tonelagem acima do total estadual | alta |
| Rochas Ornamentais - Outras | 2023 | 860633/2014 | 441.332 | 36.505 | 12,1× | tonelagem acima do total estadual | alta |
| Manganês | 2023 | 860162/2005 | 4.479 | 503 | 8,9× | tonelagem acima do total estadual | alta |

- **Municípios de outro estado em processos de fronteira (aba 05b):** 46 municípios citados no Cadastro Mineiro junto com municípios de Goiás; ficam fora da dimensão de municípios, e a linha do processo é mantida pelo município goiano.
- **Titulares sem correspondência entre fontes (aba 02b):** nome do SIGMINE sem titular equivalente no Cadastro Mineiro: 40; processo do CFEM sem titular correspondente no Cadastro Mineiro: 30.
- **Mapas (aba 13b):** verificações com ocorrência:

  - `municipios_go` — Ponto 'centro da caixa envolvente' (usado nas versões anteriores da Base 2) cai fora do próprio município (n = 20): Substituído por representative_point (garantido dentro do polígono) na camada e na Base 2.
  - `municipios_go` — Área total: soma AREA_KM2 do IBGE vs. calculada em Albers equivalente (n = 246): Diferença residual de generalização da malha; mantidas as duas colunas.
  - `processos_minerarios_go` — Polígonos inválidos (autointerseção de anel) (n = 27): Reparados com make_valid; flag geometria_reparada = verdadeiro.
  - `processos_minerarios_go` — Processos fragmentados em várias feições (n = 176): Dissolvidos em 1 geometria por processo; AREA_HA somada; qtd_feicoes_originais preservada.
  - `processos_minerarios_go` — Área calculada vs. AREA_HA declarada no SIGMINE (n = 16.656): Mantidas as duas colunas; divergências > 5% ficam para revisão.
  - `processos_minerarios_go` — Processos que atravessam mais de um município (n = 3.898): municipality_id = município de MAIOR área; lista completa em municipios_intersectados.
  - `processos_minerarios_go` — Campo UF do SIGMINE como recorte territorial (n = 16.656): UF NÃO usado como filtro; recorte pela geometria, com fracao_area_em_go por processo.
  - `processos_minerarios_go` — Processos com menos de 50% da área em Goiás (n = 375): Mantidos (a parte goiana existe); filtrar por fracao_area_em_go se a análise exigir.
  - `processos_minerarios_go` — Simplificação da geometria para a web (teste com tolerância de 10 m) (n = 16.656): REJEITADA: são poligonais legais de título minerário. A web usa arquivos sem simplificação divididos por grupo de categoria e vector tiles (PMTiles); a generalização por zoom dos tiles é só visual.
  - `processos_minerarios_go` — Município espacial vs. município textual do Cadastro Mineiro (n = 15.354): Vale a junção espacial (limites municipais atuais); o texto do Cadastro guarda o município da época do registro.
  - `processos_minerarios_go` — Discordância espacial x Cadastro: 25 processos (ex.: 806139/1973, 808538/1970, 808539/1970, 808540/1970, 808541/1970, 809032/1968). Padrão compatível com desmembramento municipal posterior ao registro (ex.: Jussara → Santa Fé de Goiás); confirmar no histórico territorial do IBGE.
  - `processos_minerarios_go` — Processos sem município no Cadastro Mineiro (junção espacial é a única fonte) (n = 1.302): municipality_id atribuído pela geometria.
  - `processos_minerarios_go` — Atribuição de company_id (n = 16.656): Processo tem prioridade; nome só quando o processo não existe no Cadastro Mineiro.
  - `processos_minerarios_go` — Processos com CFEM mas sem polígono no SIGMINE (n = 149): Não aparecem no mapa; o valor continua na Base 3 (COM_NAO_IDENTIFICADO).
  - `amostras_geoquimicas_sgb_go` — Geologia e Metalogenia do Oeste de Goiás (2017): pontos com análise química (junção por NUM_LAB) (n = 1.932): Várias análises da mesma amostra: mantido o MAIOR teor quantificado; n_analises registra quantas havia.
  - `amostras_geoquimicas_sgb_go` — Geologia e Metalogenia do Oeste de Goiás (2017): ouro (Au) (n = 564): Au padronizado em ppb. Sem nenhum valor quantificado, a coluna não indica anomalia — e os LDs das campanhas diferem em 1.000×, então 'abaixo do LD' não é comparável entre elas.
  - `amostras_geoquimicas_sgb_go` — Geologia e Metalogenia do Oeste de Goiás (2017): separador decimal misto (n = 576): Normalizado para ponto antes da conversão numérica.
  - `amostras_geoquimicas_sgb_go` — Noroeste de Goiás - Folha Bonópolis (2007): pontos com análise química (junção por NUM_LAB) (n = 710): Várias análises da mesma amostra: mantido o MAIOR teor quantificado; n_analises registra quantas havia.
  - `amostras_geoquimicas_sgb_go` — Noroeste de Goiás - Folha Bonópolis (2007): ouro (Au) (n = 219): Au padronizado em ppb. Sem nenhum valor quantificado, a coluna não indica anomalia — e os LDs das campanhas diferem em 1.000×, então 'abaixo do LD' não é comparável entre elas.
  - `amostras_geoquimicas_sgb_go` — Noroeste de Goiás - Folha Bonópolis (2007): separador decimal misto (n = 219): Normalizado para ponto antes da conversão numérica.
  - `amostras_geoquimicas_sgb_go` — Folha Goiás - PLGB (1991): pontos com análise química (junção por NUM_LAB) (n = 647): Várias análises da mesma amostra: mantido o MAIOR teor quantificado; n_analises registra quantas havia.
  - `amostras_geoquimicas_sgb_go` — Amostras fora do território de Goiás (junção espacial) (n = 82): Mantidas sem municipality_id.
  - `projetos_futuros` — Camada exportada: ponto dentro da malha de Goiás e no mesmo município da aba 04 (n = 214): Coordenada e município mantidos como na aba 04 (não recalculados aqui). Ponto: ponto representativo da união dos processos do projeto (fica dentro dos polígonos). Conferido nos polígonos: 73 de 73 pontos fora de GO são …

## 5. Unidades

Nada é somado entre unidades diferentes. Massa (kg, g e quilate) vira t pela regra escrita na linha da aba 08; volume (m³, l) e área (m²) ficam à parte (`cfem_qtd_outras_unidades` na aba 09). Unidades na fonte (aba 08, `unidade_original`):

| Unidade | Linhas |
|---|---:|
| `t` | 70.369 |
| `R$` | 69.739 |
| `m3` | 5.702 |
| `kg` | 4.523 |
| `l` | 1.591 |
| `g` | 644 |
| `m2` | 580 |
| `ct` | 421 |
| `-` | 286 |

`-` é a unidade que o AMB usa no contido quando ela não se aplica: as 286 linhas com valor diferente de zero ficam na 08 como estão na fonte (as iguais a zero não viram linha).

Quantidades da CFEM excluídas da soma de toneladas (aba 09b): 89 linhas — quantidade implausível: R$ por unidade mais de 1.000× abaixo da mediana do mesmo mineral e unidade: 81; quantidade em notação científica (valor corrompido na exportação): 8. Por mineral: Água Mineral 39, Ouro 28, Calcário 6, Rochas (Britadas) e Cascalho 4, Areia 3, Minerais Industriais (Outros) 3, Vermiculita e Perlita 3, Calcário Dolomítico 1, Níquel 1, Dolomito e Magnesita 1.

## 6. Padronização de nomes

- **Substâncias (aba 01b):** 365 grafias das fontes → mineral da ANM; identico: 124; fusao_mineralogica_ou_grupo: 112; rocha_categoria_pelo_tipo_de_uso_ver_01c: 67; fusao_minerio_forma_pura: 61; excluido_nao_mineral: 1.
- **Municípios (aba 05b):** 476 grafias → código IBGE; identico_apos_remover_sufixo_GO: 246; identico_por_codigo: 184; outro_estado_em_processo_de_fronteira: 46.
- **Substâncias do RECMIN (aba 06b):** 79 nomes; crosswalk_base1: 49; sinonimo_recmin: 28; sem_categoria_anm: 2.

## 7. Todas as validações automáticas (aba 14b)

| Status | Verificação | n | Resultado |
|---|---|---:|---|
| OK | Cabeçalhos renomeados para o padrão (contrato + unificação entre abas) | 33 | ano → year; arquivo_geojson (web) → arquivo; atribuído a → atribuido_a; camada_gpkg (QGIS) → camada_gpkg; cnpj_raiz (8 díg.) → cnpj_raiz; consumo_energia_mwh → energy_mwh; decisão → decisao; identificacao (como o ID foi atribuído) → identificacao_empresa; ide… |
| OK | Nomes de coluna fora do padrão snake_case ASCII (abas reais, auditorias e 07) | 0 | nenhum |
| OK | Nomes de coluna duplicados dentro da mesma aba | 0 | nenhum |
| OK | Campos do Contrato de Dados presentes com o nome fixado | 16 | company_id, energy_intensity_mwh_t, energy_mwh, latitude, longitude, mineral_id, mineral_name, municipality_id, municipality_name, operation_id, production_basis, production_t, project_id, source_id, source_ids, year |
| OK | Campos do fluxo Squad 1 → Squad 2 sem nenhum valor preenchido nas abas reais | 0 | nenhum |
| OK | Mesma coluna com tipo diferente entre abas | 0 | nenhuma |
| OK | Colunas sem descrição no dicionário | 0 | nenhuma |
| OK | Valores em source_ids que não são ID de fonte (texto livre) | 0 | nenhum |
| OK | Fontes citadas em source_ids sem registro no catálogo 07 | 0 | nenhuma |
| OK | Fontes catalogadas que nenhuma aba real cita | 10 | SRC_ANM_AGUA_MINERAL (disponível em dados/, ainda não usada); SRC_ANM_INVEST_PESQUISA (disponível em dados/, ainda não usada); SRC_IMB_GOIAS_EM_DADOS (usada só como validação cruzada (14b: produção do estado × AMB)); SRC_ANM_PANORAMA_DERIVADO (usada só como v… |
| OK | Arquivos de dados/ sem source_id no catálogo 07 (fora a documentação: LEIA-ME, metadados .ods, dicionário do SCM, metadados do download do RECMIN) | 0 | nenhum (46 arquivos catalogados, 8 de documentação) |
| OK | IDs fora do padrão | 0 | nenhum |
| OK | LGPD: CPF completo em campo de texto (11 dígitos com dígito verificador válido) | 0 | nenhum. Titulares da 02 com CPF dentro do nome, mascarado na exibição (***456789**): 17; o company_id não muda. |
| OK | Integridade referencial (chaves das abas consolidadas → dimensões) | 0 | 0 órfãos |
| OK | Colunas 100% vazias em abas reais (placeholders declarados) | 19 | 02_dim_empresas.metodo_estimacao; 03_dim_operacoes.metodo_estimacao; 04_dim_projetos.capacidade_t_ano; 04_dim_projetos.capex_brl; 04_dim_projetos.ano_previsto_entrada; 05_dim_municipios.metodo_estimacao; 06_dim_ocorrencias_geologicas.metodo_estimacao; 08_fato… |
| OK | Quantidade comercializada da CFEM: unidades misturadas e valores corrompidos tratados | 89 | Na fonte: UNIDADES MISTURADAS no mesmo mineral — a soma não é fisicamente comparável: Amianto (kg, t); Areia (kg, m3, t); Argilas (kg, m3, t); Calcário (kg, m3, t); Calcário Calcítico (kg, t); Calcário Dolomítico (kg, t); Dolomito e Magnesita (kg, t); Manganê… |
| ALERTA | Plausibilidade: CFEM comercializada (t) ÷ produção do AMB na base mais próxima (bruta ou beneficiada), por mineral e ano em GO, fora de 0,05–2× | 33 | Diamante 2024: 0.00× (bruta); Amianto 2024: 0.00× (bruta); Gemas 2024: 0.00× (bruta); Amianto 2025: 0.00× (beneficiada); Amianto 2022: 0.00× (beneficiada); Amianto 2023: 0.00× (beneficiada); Gemas 2023: 0.00× (bruta); Monazita e Terras-Raras 2024: 0.00× (bene… |
| ALERTA | Processos com quantidade na CFEM implausível frente ao AMB do estado (acima do total ou, em metais, R$/t incompatível; mantidos na soma, sinalizados … | 45 | severidade alta: 27; moderada: 18. Alta: Prata 2025 proc. 960658/1987: 1,488.4×; Titânio 2025 proc. 861559/2021: 410.7×; Rochas Ornamentais - Outras 2024 proc. 860633/2014: 305.1×; Rochas Ornamentais - Outras 2025 proc. 860633/2014: 54.4×; Titânio 2024 proc. … |
| OK | Rochas na CFEM: de onde veio a categoria (% do R$ de CFEM de rochas) | 41 | uso_declarado: 75.7%; uso_majoritario_da_rocha_em_GO: 23.1%; rocha_fixa: 1.2% |
| OK | IMB (Goiás em Dados) × AMB: produção do estado por mineral nos anos em que as duas fontes têm valor (checagem cruzada, informativa) | 75 | 14 minerais comparados em 2010–2016; o IMB não traz produção mineral depois de 2016. Iguais à produção beneficiada do AMB em todos os anos (razão 0,99–1,01): Amianto, Saibro. Diferentes em algum ano (razão IMB ÷ AMB): Areia (IMB em m³, AMB em t): 2010 3.59×, … |
| OK | 08: cada célula numérica das fontes (AMB bruta, AMB beneficiada, CFEM) vira exatamente uma linha — contado de novo nos arquivos | 153855 | SRC_ANM_CFEM: 77,701 linhas × 77,701 células; SRC_ANM_PROD_BENEF: 29,679 linhas × 29,679 células; SRC_ANM_PROD_BRUTA: 46,475 linhas × 46,475 células. Fora: 6,206 células de contido com unidade '-' (não se aplica). Divergências: nenhuma |
| OK | 08 → 09/10/11: as abas consolidadas são somas de valor_tratado da 08 (produção bruta/beneficiada, venda e CFEM por mineral×UF×ano; CFEM por município… | 0 | 09: 0 divergências em 6,680 comparações; 10: 0 em 956; 11: 0 em 2,059 |
| OK | 08: campos de governança por linha — source_url, data_acesso e tipo_fonte iguais à 07; não observado sem método; mesma célula da fonte em duas linhas | 0 | divergentes da 07: 0; não observado sem metodo_estimacao: 0; células repetidas: 0. valor_observado_estimado: {'observado': 153855}; status_validacao: {'valido': 152904, 'alerta_producao_repetida': 164, 'alerta_processo_09c': 698, 'quantidade_excluida_da_soma_… |
| OK | §3 da Entrega: fonte, source_url, data_acesso, periodo_referencia, tipo_fonte, valor_observado_estimado, metodo_estimacao, status_validacao e respons… | 0 | 01: ok; 02: ok; 03: ok; 04: ok; 05: ok; 06: ok; 08: ok; 09: ok; 10: ok; 11: ok; 12: ok; 13: ok |
| ALERTA | 08: mesma tonelagem de produção em linhas diferentes da mesma UF e ano no AMB (co-produto, mineral separado por teor ou mesma declaração em duas cate… | 164 | 74 grupos, 164 linhas (com status alerta_producao_repetida: 164). Numa soma contam a mais 97,774 t dentro do mesmo mineral (infla a linha BR da 09) e 294,862,785 t entre minerais. Goiás: producao_rom 2023: 5526825,440000 t em Nióbio + Bário; producao_benefici… |
| OK | 12: nível estado = produção de GO na 08 (AMB); nível operação soma exatamente o total do estado (rateio conservativo) | 0 | estado: 745 linhas, 0 divergências com a 08; operação: 4,856 linhas em 156 totais rateados, 0 divergências de soma ou participação |
| OK | 12: cobertura da abertura por operação (2022–2025) — produção do estado com CFEM para ratear; parte estimada com operation_id e com coordenadas | 4856 | 2022: 99.5% das t abertas; 2023: 99.7% das t abertas; 2024: 99.7% das t abertas; 2025: 95.5% das t abertas. Da produção estimada: 81.7% com operation_id, 81.7% com coordenadas; 932 processos. Sem abertura (sem CFEM do mineral no ano): Areias Industriais 2022;… |
| OK | 12: governança por linha (Entrega Avaliativa §3) — estimado com método e intervalo, observado sem; fontes, URLs e datas iguais à 07 | 0 | nenhuma violação. valor_observado_estimado: {'observado': 745, 'estimado': 4856}; status_validacao: {'valido': 741, 'estimativa_conferida_no_total': 4786, 'estimativa_com_alerta_09c': 70, 'alerta_producao_repetida': 4} |
| OK | 04: cada processo vivo do universo (título de lavra sem CFEM, pré-lavra, requerimento de licenciamento/garimpeira) está em exatamente um projeto; os … | 0 | universo na 03: 5,515 processos; vivos 4,365 → 3,377 projetos; terminais 1,150. Vivos fora de projeto: 0; em dois projetos: 0; terminais em projeto: 0; fora do universo: 0; tipos de evento sem classe na 04b: 0 |
| OK | 04: classificação refeita a partir do estágio, da data do último evento, de disputa e de licenciamento ambiental (teto 'provável' sem evidência corpo… | 0 | 3,377 projetos: {'provável': 1106, 'possível': 704, 'sinal': 1567}; divergências com a regra: 0 |
| OK | 04: governança por linha — fontes, URLs e datas iguais à 07; capacidade, CAPEX e ano previsto vazios (não inventados); status, responsável e critério… | 0 | nenhuma violação. tipo_projeto: {'sem_operacao_adjacente': 3225, 'brownfield_adjacente_a_operacao': 152}; estágio: {'lavra_autorizada_sem_producao': 1475, 'requerimento_de_lavra': 754, 'direito_de_requerer_lavra': 143, 'requerimento_de_licenciamento_ou_lavra_… |
| OK | 06: recorte refeito do arquivo baixado — cada ponto do RECMIN dentro da malha de Goiás está na 06 uma vez, com o mesmo município; os de fora não | 0 | arquivo: 2,586 pontos, 1,796 dentro de GO; 06: 1,796 linhas (repetidas: 0). Faltando: 0; a mais: 0; município diferente: 0 |
| OK | 06: campos do RECMIN fora da aba por não terem informação (evidência recalculada no arquivo) | 6 | localizacao_mina = 'Mina subterrânea (GPS sem sinal)' em 92% dos pontos de GO (inclusive garimpo e não explotado); situacao_garimpo = situacao_mina em 100%; sureg: {'OUTROS': 1796}; origem: {'Oracle': 1796}; datum: {'WGS84': 1796}; geologo não usado. O arquiv… |
| OK | 13: toda camada do catálogo tem arquivo em outputs/mapas/; processos (CAM_02), ocorrências (CAM_05) e projetos (CAM_06) têm uma feição por linha da a… | 0 | 11 camadas com arquivo; CAM_02 = aba 03, CAM_05 = aba 06, CAM_06 = aba 04 |
| OK | 06: substâncias → mineral_ids refeito pela 06b (toda substância tem decisão; nenhum mineral novo, IDs MIN_### da 01) | 0 | 79 nomes na 06b: {'sem_categoria_anm': 2, 'sinonimo_recmin': 28, 'crosswalk_base1': 49}; sem categoria ANM: Índio, Arsênio. Substâncias da 06 sem linha na 06b: 0; ocorrências com mineral_ids diferente do crosswalk: 0 |
| OK | 06: governança por linha — fontes, URLs e datas iguais à 07; tudo observado na fonte. Cruzamento com a ANM (informativo) | 0 | nenhuma violação. status_validacao: {'valido': 1774, 'alerta_localizacao': 22}; categoria ANM do ponto: {'5_pesquisa': 886, 'fora_de_processo': 550, '2_lavra_sem_cfem_recente': 134, '4_pre_lavra': 80, '7_disponibilidade': 90, '1_operacao_ativa': 36, '6_requer… |
