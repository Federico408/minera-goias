# `dados/` — Bases úteis do MINERA Goiás (Squad 1 / Estudante 1)

Seleção das bases de dados que serão efetivamente usadas na **Base Mineral de Goiás — v1**,
organizadas **por fonte**. Os arquivos aqui são **cópias** dos originais (sem alteração);
os originais permanecem em `../Bases prontas para o GIT/` e em `../minera-goias/Squad 1/Dados/`.
A exceção é `SGB_GeoSGB/recmin/`, baixado direto do WFS oficial do SGB.

Escopo: fontes **prioritárias e complementares do Estudante 1** conforme o documento
*Squads / Entrega Avaliativa 1* — ANM (AMB/RAL, Cadastro Mineiro, SIGMINE), SGB/GeoSGB,
CFEM, IBGE (malhas) e IMB. **Energia (CCEE, EPE, ANEEL, ONS) não entra aqui** — é escopo do Squad 2.

Recorte territorial: **Goiás**. Onde o arquivo é nacional (Cadastro Mineiro, Água Mineral,
Investimento em Pesquisa), o filtro `UF = GO` é feito na etapa de processamento, preservando o bruto.

O catálogo **calculado** destes arquivos (sha256, tamanho, período coberto e abas que usam cada fonte)
é a aba `07_dim_fontes` da planilha `../documentacao/prototipo_bases_consolidadas_v15.xlsx`. Todo arquivo desta pasta tem
`source_id` ali, exceto a documentação das fontes (este LEIA-ME, os metadados `.ods`, o dicionário do SCM e os metadados do download do RECMIN).

---

## Estrutura

```
dados/
├── ANM/
│   ├── producao_amb_ral/      Produção mineral (Anuário Mineral Brasileiro / RAL)
│   ├── cfem/                   Arrecadação da CFEM em Goiás
│   ├── cadastro_mineiro/       Títulos e requerimentos minerários (SCM) — nacional, filtrar GO
│   ├── sigmine/                Shapefile dos processos minerários de GO (geometria)
│   ├── agua_mineral/           Produção de água mineral e potável de mesa
│   └── investimento_pesquisa/  Investimento declarado em pesquisa mineral por UF
├── ANM_derivados_analises/     Planilhas já consolidadas a partir de dados ANM (cross-check)
├── SGB_GeoSGB/
│   ├── geoquimica_tabular/     Geoquímica em planilha (dado estruturado)
│   ├── recmin/                 Ocorrências de recursos minerais (RECMIN) de GO — WFS oficial do SGB, baixado em 12/09/2026
│   ├── sig_vetorial/           Pacotes SIG (shapefiles) de GO / Faixa Brasília / Oeste de Goiás
│   └── mapas_referencia_GO/    Mapas e relatórios RECMIN/favorabilidade de GO (PDF, referência)
├── IBGE/                       Malha municipal de GO + PIB e população municipal
└── IMB/                        Goiás em Dados — séries do estado e dos municípios (produção mineral e energia)
```

---

## Catálogo de fontes

### ANM — Agência Nacional de Mineração

| Pasta / arquivo | Conteúdo | Granularidade | Período | Uso na base v1 |
|---|---|---|---|---|
| `producao_amb_ral/Producao_Bruta.csv` | Produção bruta (minério ROM), venda, transformação | UF × classe × substância × ano | 2010–2025 | Produção física (ROM) — `production_basis = ROM` |
| `producao_amb_ral/Producao_Beneficiada.csv` | Produção beneficiada, venda, unidade de medida | UF × classe × substância × ano | 2010–2025 | Produção beneficiada — `production_basis = beneficiada` |
| `producao_amb_ral/metadados-amb.ods` | Dicionário do Anuário Mineral | — | — | Documentação |
| `cfem/CFEM_Arrecadacao_2022_2026_GO.csv` | Compensação Financeira pela Exploração Mineral — **já filtrado GO** | mês × processo × substância × município × titular | 2022-01 a 2026-08 (2026 parcial) | Validação econômica/municipal; `commercialized_quantity` (não é produção) |
| `cfem/metadados-cfem.ods` | Dicionário da CFEM | — | — | Documentação |
| `cadastro_mineiro/*.csv` | 13 arquivos do Sistema Cadastro Mineiro: alvará de pesquisa, cessões, guia de utilização, licenciamento, PLG, portaria de lavra, registro de extração, relatório de pesquisa aprovado, requerimentos (lavra, licenciamento, PLG, pesquisa, registro de extração) | processo/título (nacional) | vigente | Titular, município(s), substância(s), fase, situação, tipo de uso → dimensões `company` e `operation` |
| `cadastro_mineiro/mer-microdados-scm.pdf`, `metadados*.ods` | Dicionários do SCM | — | — | Documentação |
| `sigmine/GO.zip` | Shapefile dos processos minerários de Goiás | polígono por processo | vigente | **Espinha das operações** + centróide (lat/long), fase, área (ha), último evento |
| `agua_mineral/Agua_Mineral_Producao.csv` | Produção de água mineral e potável de mesa (litros, valor, embalagem) | UF × ano (nacional) | 2010–2025 | Substância "água mineral" (Caldas Novas etc.) |
| `investimento_pesquisa/InvestimentoPesquisaMineralUf.csv` | Investimento declarado em pesquisa mineral por rubrica | UF × substância × ano | 2001–2025 | Contexto/indicador de pipeline exploratório |

**Links oficiais:** ANM – Bases de Dados (AMB/RAL, Cadastro Mineiro, CFEM, SIGMINE): <https://dados.gov.br/dados/organizacoes/visualizar/agencia-nacional-de-mineracao-anm> · SIGMINE: <https://geo.anm.gov.br/> · CFEM: <https://sistemas.anm.gov.br/arrecadacao/extra/relatorios/arrecadacao_cfem.aspx>

**Atenção metodológica:** AMB/RAL é declaratório — a própria ANM alerta para inconsistências.
Divergências devem ser **registradas, não corrigidas silenciosamente**. Processo minerário existente
≠ mina em operação. Quantidade comercializada da CFEM **não** é produção.

**LGPD:** o Cadastro Mineiro e o SIGMINE trazem o CPF completo no nome de alguns titulares
(empresário individual). Os arquivos brutos daqui ficam como vieram; na planilha e nos mapas
esse CPF sai mascarado (`***456789**`, o mesmo padrão que a ANM usa na coluna de documento).

### ANM — derivados / análises já prontas

| Arquivo | Conteúdo | Uso |
|---|---|---|
| `ANM_derivados_analises/Panorama_Mineracao_Goias_ANM.xlsx` | 62 abas: CFEM por ano/município/substância/empresa, produção bruta e beneficiada, barragens (SIGBM), estoque de processos por fase/substância/município, REPEM, investimento em pesquisa, **empresas produtoras com CNPJ**, direito de lavra, titulares de pesquisa. Extração ANM de 04/08/2026. | Cross-check dos agregados; **entity resolution** (lista de CNPJ); diagnóstico |
| `ANM_derivados_analises/Mineradoras_Goias_operacao_e_potencial.xlsx` | Aba `Operacao_atual`: 753 registros (406 empresas) com evidência de **operação atual**; aba `Potencial_futuro`: 10.366 registros (2.092 empresas) de **potencial/futuro** — já classificados com critério e confiança, com processo/número/ano/área | Insumo para o Radar de Projetos (Estudante 2) e para separar operação de projeto |

> São produtos derivados (não fontes primárias). Usar como apoio e sempre rastrear ao dado ANM original.

### SGB — Serviço Geológico do Brasil (GeoSGB / RECMIN)

| Pasta / arquivo | Conteúdo | Formato | Uso |
|---|---|---|---|
| `geoquimica_tabular/projeto_se_de_goias_fl_nazario_geoquimica.xlsx` | Geoquímica – Folha Nazário (SE de Goiás) | XLSX | Dado geoquímico estruturado |
| `recmin/ocorrencias_recursos_minerais_GO.geojson` (+ `.metadados.json`) | **Ocorrências de Recursos Minerais (RECMIN)** — camada `geosgb:ocorrencias_recursos_minerais` do WFS oficial do SGB, recortada pela caixa de Goiás com folga: 2.586 pontos, 1.796 dentro de GO pela malha do IBGE. Baixado em 12/09/2026 com autorização do Eliel; URL da requisição, data e sha256 no `.metadados.json` | GeoJSON (WGS84) | **Aba 06** — ocorrências e depósitos minerais |
| `sig_vetorial/sig_geologico_integ_centro_norte_faixa_brasilia_vr.zip` | SIG geológico integrado – Centro-Norte da Faixa Brasília | Shapefile | Camada geológica (não traz ocorrências minerais) |
| `sig_vetorial/sig_oeste_de_goias_integrado_vr.zip` | SIG integrado – Oeste de Goiás | Shapefile | Camada geológica — litologia, estruturas, afloramentos; **não** traz ocorrências minerais |
| `sig_vetorial/sig_barro_alto_vr.zip` | SIG – Barro Alto (níquel) | Shapefile | Distrito de Ni |
| `sig_vetorial/geoquimica_Fl_goias_PLGB_1999_vr1.zip` | Geoquímica – Folha Goiás (PLGB 1999) | Shapefile | Geoquímica |
| `sig_vetorial/geoquimica_metalogenia_oeste_de_goias_2017.zip` | Geoquímica e metalogenia – Oeste de Goiás (2017) | Shapefile | Metalogenia |
| `sig_vetorial/geoquimica_noroeste_de_goias.zip` | Geoquímica – Noroeste de Goiás | Shapefile | Geoquímica |
| `mapas_referencia_GO/*.pdf` | RECMIN Oeste de Goiás, mapa geológico RECMIN Faixa Brasília, favorabilidade Au Oeste de GO, província estanífera de GO, agrominerais GO/DF, geológico-geofísico Oeste de GO, metalogenético Faixa Brasília, geotécnico 1:500k GO/DF | PDF | **Evidência de ocorrências/depósitos** (RECMIN) — referência, não estruturado |

**Link oficial:** <https://geosgb.sgb.gov.br/> · RECMIN: <https://recmin.sgb.gov.br/> · WFS das ocorrências: <https://geoservicos.sgb.gov.br/geoserver/ows> (camada `geosgb:ocorrencias_recursos_minerais`)

**Atenção metodológica:** RECMIN reúne ocorrência, depósito, mina, garimpo etc. Serve para
**potencial geológico**, não é lista de projetos empresariais e não deve virar "projeto em implantação" automaticamente.

### IBGE

| Arquivo | Conteúdo | Uso |
|---|---|---|
| `GO_Municipios_2025.zip` | Malha municipal de Goiás 2025 (shapefile) | **Padronização territorial** (código e nome oficiais, centróide) — usada na consolidação |
| `ibge_malha_municipal_goias_2024.zip` | Malha municipal de Goiás 2024 | Alternativa / comparação de versões |
| `pib_municipal_goias_ultimo_ano.json` | PIB municipal de 2023 (o SIDRA publica em **mil reais**) | Contexto socioeconômico |
| `populacao_municipal_goias_ultimo_ano.json` | População municipal de 2025 | Contexto |
| `populacao_goias_ultimo_ano.json` | População do estado | Contexto |

**Link oficial:** Malhas – <https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/> · SIDRA – <https://sidra.ibge.gov.br/>

> Padronizar em **uma** versão da malha (recomendado: 2025, já usada no pipeline).

### IMB — Instituto Mauro Borges (Goiás em Dados)

Cada arquivo tem uma linha por localidade (Estado de Goiás e municípios) × variável e uma coluna por ano.

| Arquivo | Conteúdo | Período |
|---|---|---|
| `consulta.csv` | Energia elétrica: consumidores e consumo (MWh) — total, rural, comercial, industrial, consumo próprio e iluminação pública — e capacidade instalada (MW) | colunas 2005–2025; último ano com valor: 2025 |
| `consulta (1).csv` | Produção: ouro (kg), prata, quartzito e siltito para cerâmica branca, quartzo (kg), rochas ornamentais, saibro, talco, titânio, vermiculita | colunas 2005–2025; último ano com valor: 2025 |
| `consulta (2).csv` | Produção: alumínio, amianto, areia (m³), argilas (refratária, cerâmica, cerâmica branca e vermelha, cimento) | colunas 2005–2025; último ano com valor: 2025 |
| `consulta (3).csv` | Produção: calcário para rações, cascalho, caulim, cobalto, cobre, diamante (ct), esmeralda (kg), ferro para cimento, filito, fosfato, manganês, nióbio, níquel | colunas 2005–2025; último ano com valor: 2016 |

**Link oficial:** <https://www.imb.go.gov.br/> (Goiás em Dados)

> Encoding **latin-1 / cp1252**, separador `;`, decimal `,` e milhar `.`. Bom para **cross-check** do AMB/RAL,
> não como fonte primária de produção.

---

## O que ficou de fora (e por quê)

| Item | Onde está | Motivo |
|---|---|---|
| `Bases prontas para o GIT/Energia/*`, `minera-goias/Squad 1/Dados/CCEE`, `EPE`, `energia/` | originais | Escopo do **Squad 2** (economia e energia) |
| `microdados-scm.zip` (316 MB) | `Bases prontas para o GIT/Cadastro mineiro/` | Redundante — os 13 CSV já são a forma utilizável |
| `SEGMINE 2/` (BRASIL.zip, PROCESSOS_INATIVOS.zip, demais UFs, .kmz) | `Bases prontas para o GIT/SEGMINE 2/` | Nacional / outras UFs / KML redundante com o shapefile GO |
| Dumps nacionais em `minera-goias/Squad 1/Dados/AMN/` (`Sicop.csv` 211 MB, `Tah.csv` 97 MB, `CFEM_Distribuicao.csv` 317 MB, `PlanoPesquisaRepem.csv` 137 MB, `BRASIL.zip`, `PROCESSOS_INATIVOS.zip`, `EstoqueAreas.csv`, REPEM) | repo | Nacionais e não usados na base v1; muitos acima do limite do GitHub |
| PDFs GeoSGB de outras regiões (grafita BA/CE, urânio Lagoa Real, terras raras BA, bauxita NE-SP, Currais Novos, Serrita-Salgueiro, panoramas nacionais) e os IRM/relatórios > 100 MB (`irm_faixa_brasilia.pdf` 327 MB, `rel_oeste_de_goias.pdf` 105 MB, `Rel_Goiasdf.pdf` 73 MB, `irm_barro_alto.pdf` 50 MB) | `Bases prontas para o GIT/GEOsgb/` | Fora de Goiás ou arquivo grande demais; consultar no local original se necessário |

---

## Próximos passos sugeridos

1. Histórico completo de eventos dos processos (microdados do SCM) para melhorar a classificação dos projetos da aba 04,
   que hoje só vê o último evento do SIGMINE.
2. Definir `.gitignore` / Git LFS antes de versionar: esta pasta tem ~300 MB em 54 arquivos; nenhum passa de 100 MB
   (os maiores são PDFs do SGB de 18–27 MB e `cadastro_mineiro/Alvara_de_Pesquisa.csv`, 26 MB).

O pipeline que lê esta pasta está em `../base_consolidada_work/scripts/` e roda com
`python base_consolidada_work/scripts/rodar_pipeline.py` (instruções em `../base_consolidada_work/scripts/LEIA-ME.md`).

_Última atualização do catálogo: 2026-09-12 (v13: todos os arquivos de dados com `source_id` na aba 07)._
