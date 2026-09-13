# Dicionário de dados

Atualizado em 13/09/2026. Ao mudar uma coluna no `schema.sql`, atualize esta tabela na mesma alteração.

| Tabela | Campo | Tipo | Descrição |
| :--- | :--- | :--- | :--- |
| `tb_fontes` | `source_id` | VARCHAR PK | Identificador da fonte (ex.: `ANM_CADASTRO`) |
| `tb_fontes` | `titulo` | VARCHAR | Nome do conjunto de dados de origem |
| `tb_fontes` | `instituicao` | VARCHAR | Quem publica (ANM, EPE, CCEE…) |
| `tb_fontes` | `url_arquivo` | VARCHAR | Caminho ou endereço do arquivo usado |
| `tb_fontes` | `cobertura` | VARCHAR | Recorte territorial da fonte |
| `tb_fontes` | `notas_metodologicas` | VARCHAR | Limites conhecidos e o que não foi inferido |
| `tb_municipios` | `codigo_ibge` | VARCHAR PK | Código IBGE de sete dígitos |
| `tb_municipios` | `nome_municipio` | VARCHAR | Nome do município |
| `tb_minerais` | `mineral_id` | INT PK | Chave interna |
| `tb_minerais` | `id_substancia_anm` | INT UK | Identificador do dicionário da ANM (`Substancia.txt`) |
| `tb_minerais` | `mineral_name` | VARCHAR | Nome da substância como a ANM registra |
| `tb_minerais` | `sinonimos` | VARCHAR | Nomes alternativos vistos nas planilhas |
| `tb_empresas` | `empresa_id` | INT PK | Chave interna |
| `tb_empresas` | `nome_empresa` | VARCHAR | Nome do titular como veio da fonte |
| `tb_empresas` | `nome_empresa_normalizado` | VARCHAR UK | Nome em maiúsculas, sem acento — a chave de deduplicação |
| `tb_empresas` | `documento_cnpj_cpf` | VARCHAR UK NULL | CNPJ/CPF quando a fonte fornece; as atuais não fornecem |
| `tb_empresas` | `tipo_pessoa` | VARCHAR | Física ou jurídica, quando declarado |
| `tb_projetos` | `processo_anm` | VARCHAR PK | Número do processo minerário (ex.: `860366/2014`) |
| `tb_projetos` | `empresa_id` | INT FK NULL | Titular; nulo quando a fonte não o nomeia |
| `tb_projetos` | `titular_nome` | VARCHAR | Nome do titular como veio da origem, sem normalização |
| `tb_projetos` | `ultimo_evento` | VARCHAR | Último evento registrado no cadastro |
| `tb_projetos` | `uf` | VARCHAR(2) | Unidade federativa do processo |
| `tb_projetos` | `poligonos` | INT | Quantos polígonos o processo tem no shapefile |
| `tb_projetos` | `substancia_anm` | VARCHAR | Substância como texto da origem (inclui `DADO NÃO CADASTRADO`) |
| `tb_projetos` | `mineral_id` | INT FK NULL | Substância resolvida no dicionário; nulo quando não resolve |
| `tb_projetos` | `fase` | VARCHAR | Fase do processo (requerimento, concessão de lavra…) |
| `tb_projetos` | `uso` | VARCHAR | Classificação de uso declarada |
| `tb_projetos` | `area_ha` | DECIMAL NULL | Área **apenas** quando há um único polígono; com vários fica nula |
| `tb_projetos` | `categoria` | VARCHAR | Categoria atribuída pela equipe |
| `tb_projetos` | `source_id` | VARCHAR FK | De qual fonte a linha veio |
| `tb_projetos` | `data_acesso` | DATE | Quando a fonte foi lida |
| `tb_projetos` | `valor_observado_estimado` | ENUM | Real ou Projetado |
| `tb_projetos` | `status_validacao` | VARCHAR | `nao_validado` até revisão técnica |
| `tb_projeto_poligono` | `poligono_id` | INT PK | Chave interna do polígono |
| `tb_projeto_poligono` | `processo_anm` | VARCHAR FK | Processo a que o polígono pertence |
| `tb_projeto_poligono` | `id_poligono_origem` | VARCHAR | Identificador do shapefile; **repete** na origem, por isso não é chave |
| `tb_projeto_poligono` | `area_ha` | DECIMAL | Área declarada daquele polígono |
| `tb_projeto_municipio` | `processo_anm` + `codigo_ibge` | PK composta | Em que municípios o processo incide |
| `tb_intensidade_energetica` | `intensidade_mwh_t` | DECIMAL | Energia por tonelada produzida |
| `tb_intensidade_energetica` | `production_basis` | ENUM | ROM (bruto) ou Beneficiado — nunca misturar as duas |
| `tb_projecoes` | `processo_anm` | VARCHAR FK | Processo projetado |
| `tb_projecoes` | `year` | INT | Ano da projeção (2027–2040) |
| `tb_projecoes` | `scenario` | ENUM | conservador / referencia / expansao |
| `tb_projecoes` | `projected_production` | DECIMAL | Produção projetada |
| `tb_projecoes` | `unidade_producao` | VARCHAR | Unidade da produção projetada (`t`, `kg`…) |
| `tb_projecoes` | `energy_demand_mwh` | DECIMAL | Demanda de energia correspondente |

## Campos que existem para não mentir

`status_validacao` nasce `nao_validado`: importar não é validar. `substancia_anm` guarda o texto cru mesmo quando não resolve no dicionário — 381 processos de Goiás vêm marcados `DADO NÃO CADASTRADO` na própria origem. `area_ha` fica nula quando o processo tem vários polígonos, porque somá-los pode contar duas vezes a mesma superfície.
