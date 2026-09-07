| Tabela | Campo | Tipo | Descrição |
| :--- | :--- | :--- | :--- |
| `tb_fontes` | `source_id` | INT PK | Identificador único da fonte de dado |
| `tb_fontes` | `nome_fonte` | VARCHAR | Nome da fonte (ex: "ANM", "EPE") |
| `tb_fontes` | `source_url` | VARCHAR | Link para a base original |
| `tb_fontes` | `tipo_fonte` | ENUM | Oficial / Companhia / Setorial / Imprensa |
| `tb_municipios` | `municipality_id` | INT PK | Identificador único do município |
| `tb_municipios` | `nome_municipio` | VARCHAR | Nome oficial do município |
| `tb_municipios` | `latitude / longitude` | DECIMAL | Coordenadas decimais (fonte: IBGE) |
| `tb_minerais` | `mineral_id` | INT PK | Identificador único do mineral |
| `tb_minerais` | `mineral_name` | VARCHAR | Nome padronizado do mineral |
| `tb_minerais` | `sinonimos` | VARCHAR | Nomes alternativos vindos de planilhas de origem |
| `tb_empresas` | `company_id` | INT PK | Identificador único da empresa |
| `tb_projetos` | `project_id` | INT PK | Identificador único do projeto/mina (também usado como operation_id — ver decisão acima) |
| `tb_projetos` | `valor_observado_estimado` | ENUM | Real / Projetado |
| `tb_intensidade_energetica` | `intensidade_mwh_t` | DECIMAL | Energia gasta por tonelada produzida |
| `tb_intensidade_energetica` | `production_basis` | ENUM | ROM (minério bruto) ou Beneficiado |
| `tb_projecoes` | `scenario` | ENUM | conservador / referencia / expansao |
| `tb_projecoes` | `year` | INT | Ano da projeção (2027–2040) |
