# Squad 2 — Motor Econômico-Energético

## Objetivo

A Squad 2 desenvolve o componente econômico-energético do projeto MINERA Goiás.

O objetivo final é estimar, para cada mineral e para Goiás como um todo, a produção mineral e a demanda associada de energia elétrica entre 2027 e 2040. O componente deverá combinar:

- produção histórica observada;
- operações existentes;
- projetos e expansões futuros, quando houver dados estruturados;
- hipóteses de crescimento, utilização e eficiência energética;
- cenários conservador, referência e expansão;
- conversão de produção mineral em demanda estimada de energia.

O repositório contém atualmente dois componentes distintos:

| Componente | Função | Natureza dos dados |
|---|---|---|
| Demo do motor | Demonstra a arquitetura completa de um pipeline físico de operações e projetos | Dados integralmente sintéticos |
| Modelo real | Usa os dados históricos efetivamente disponíveis da Squad 1, executa backtest, cenários futuros e sensibilidade | Dados consolidados da Squad 1 e parâmetros de benchmark |

A demo não é substituída pelo modelo real. Ela permanece como referência de arquitetura para a futura integração de projetos físicos. O modelo real é o componente utilizado para produzir resultados baseados nos dados atualmente disponíveis.

## Estado atual

### 1. Demo do motor econômico-energético

A versão demo é executável e reproduzível. Ela utiliza dados identificados como `estimated_demo` e simula uma arquitetura completa com:

- produção existente;
- entrada de projetos futuros;
- capacidade, utilização e atrasos;
- captura de mercado;
- intensidade energética;
- cenários conservador, referência e expansão;
- análise de sensibilidade para atraso, utilização e eficiência;
- validações automáticas via GitHub Actions.

Os dados demo não representam valores reais de empresas, minas, produção, capacidade ou consumo energético. A sua função é demonstrar como o motor poderá operar quando a estrutura completa de dados reais estiver disponível.

### 2. Modelo real

O diretório `modello_reale/` contém o novo modelo baseado nos dados consolidados efetivamente disponíveis no projeto.

Essa versão:

- lê diretamente os outputs consolidados da Squad 1;
- cobre cobre, bauxita, níquel, fosfato e amianto;
- valida dados de produção antes da execução;
- executa um backtest histórico;
- gera cenários futuros de 2027 a 2040;
- converte produção projetada em demanda estimada de energia;
- executa análise de sensibilidade das intensidades energéticas;
- publica outputs separados como artefatos da GitHub Actions;
- disponibiliza um contrato JSON para futura integração interativa pela Squad 3.

O modelo real ainda não inclui projetos e expansões físicos. Os dados atualmente disponíveis não contêm, de forma estruturada e validada, capacidade, ano de início e grau de certeza dos projetos futuros. Por isso, esta versão utiliza projeção de tendência histórica com cenários explícitos, sem inventar uma carteira de projetos inexistente.

A documentação completa do modelo real está em:

```text
Squad 2/modello_reale/README.md
```

## Estrutura

```text
Squad 2/
├── data/
│   └── demo/                         # dados sintéticos da demonstração
├── notebooks/
│   └── Motor_Economico_Energetico_MINERA_Goias.ipynb
├── outputs/
│   └── demo/                         # resultados da demonstração
├── modello_reale/
│   ├── parameters/
│   │   ├── energy_intensity.csv
│   │   └── scenarios.csv
│   ├── src/
│   │   ├── common.py
│   │   ├── run_backtest.py
│   │   ├── run_future_scenarios.py
│   │   └── run_intensity_sensitivity.py
│   ├── outputs/
│   │   ├── backtest/
│   │   ├── future/
│   │   └── sensitivity/
│   ├── requirements.txt
│   └── README.md
└── README.md
```

## Como funciona a demo

A demo apresenta a lógica física que será utilizada quando houver dados completos de operações e projetos.

1. Usa uma produção-base por mineral e base de produção.
2. Projeta operações existentes com uma taxa de crescimento.
3. Inclui projetos conforme estágio, cenário, ano de início e atraso.
4. Calcula a produção dos projetos:

   ```text
   capacidade × utilização × captura de mercado
   ```

5. Calcula a demanda de energia:

   ```text
   produção projetada × intensidade energética
   ```

6. Agrega os resultados por mineral para obter o total anual de Goiás.

A camada futura de demanda e elasticidade deverá complementar essa lógica como explicação macroeconômica ou restrição de mercado. Ela não deve substituir o pipeline físico de oferta.

## Como funciona o modelo real

O modelo real foi construído para aproveitar os dados já consolidados, mantendo separadas as etapas de validação, projeção e sensibilidade.

### Produção histórica

O modelo lê diretamente os seguintes outputs da Squad 1:

| Uso | Origem |
|---|---|
| Bauxita, níquel, fosfato e amianto | `Squad 1/Bases consolidadas/documentacao/pacote_squad2/interface_squad1_squad2.csv` |
| Cobre | `Squad 1/Bases consolidadas/documentacao/prototipo_bases_consolidadas_v17.xlsx`, aba `08_fato_producao_energia` |

O cobre é tratado separadamente porque a métrica compatível, `contido_beneficiada`, não está disponível no arquivo de interface utilizado para os outros minerais.

### Cenários futuros

Para cada mineral, o modelo calcula o crescimento médio anual a partir da série histórica disponível. A produção futura é projetada a partir do último ano observado, com um ajuste específico de cada cenário.

A intensidade energética também varia ao longo do tempo conforme a hipótese de eficiência do cenário.

Os cenários utilizados são:

| Cenário | Ajuste sobre o crescimento histórico | Melhoria anual de eficiência |
|---|---:|---:|
| Conservador | -2,0 pontos percentuais | 0,4% |
| Referência | 0,0 pontos percentuais | 0,9% |
| Expansão | +2,0 pontos percentuais | 1,4% |

As hipóteses são explícitas e parametrizadas. Elas devem ser interpretadas como cenários ilustrativos, não como previsões oficiais.

### Intensidade energética

A demanda estimada de energia é calculada por mineral:

```text
demanda de energia em MWh =
produção projetada em toneladas
× intensidade energética em MWh/t
```

Os coeficientes de intensidade energética utilizados no modelo real são benchmarks identificados por `SRC_FGV_EPGE_001`.

Eles não representam uma medição observada de toda a demanda elétrica da mineração de Goiás. Portanto, os resultados devem ser interpretados como uma estimativa de demanda de energia sob hipóteses de intensidade baseadas nos benchmarks disponíveis.

### Backtest

O backtest é executado separadamente dos cenários futuros.

Para cada mineral, os dois últimos anos disponíveis são reservados como teste. O modelo estima esses anos apenas com os dados anteriores e compara a previsão com os valores efetivamente observados.

| Mineral | MAPE do backtest |
|---|---:|
| Fosfato | 2,3% |
| Cobre | 3,0% |
| Níquel | 7,8% |
| Amianto | 8,6% |
| Alumínio (Bauxita) | 44,3% |

A bauxita apresenta erro mais alto porque a produção observada caiu de forma relevante em 2024, enquanto a série histórica anterior apresentava crescimento. Esse resultado mostra uma limitação esperada de projeções baseadas apenas em tendência: mudanças operacionais ou de mercado não podem ser antecipadas sem variáveis e dados adicionais.

### Sensibilidade

A análise de sensibilidade também é separada dos cenários futuros.

Ela testa como a demanda de energia muda quando as intensidades energéticas variam entre -10% e +10%, com intervalos de 1%.

O modelo produz:

- variação simultânea da intensidade de todos os minerais;
- variação de um mineral por vez, mantendo os demais fixos;
- um contrato JSON que permite à plataforma testar ajustes independentes por mineral.

Assim, a interface poderá permitir combinações como:

```text
Cobre: +3%
Bauxita: 0%
Níquel: -5%
Fosfato: +1%
Amianto: 0%
```

A plataforma não precisa pré-calcular todas as combinações possíveis. Ela pode aplicar os ajustes diretamente aos valores base fornecidos pelo contrato de sensibilidade.

## Outputs do modelo real

| Grupo | Arquivo | Conteúdo |
|---|---|---|
| Backtest | `backtest_detail.csv` | Previsões e valores observados por mineral e ano testado |
| Backtest | `backtest_summary.csv` | Erro percentual absoluto médio por mineral |
| Cenários futuros | `future_projection_by_mineral.csv` | Produção, intensidade e energia por mineral, ano e cenário |
| Cenários futuros | `future_energy_summary.csv` | Demanda total estimada de energia por ano e cenário |
| Sensibilidade | `intensity_global_range.csv` | Variação igual das intensidades de todos os minerais |
| Sensibilidade | `intensity_one_way.csv` | Variação de uma intensidade por vez |
| Sensibilidade | `intensity_sensitivity_contract.json` | Contrato de integração para a Squad 3 |
| Sensibilidade | `custom_intensity_result.json` | Resultado de uma combinação específica de ajustes |

No cenário de referência, a demanda estimada dos cinco minerais cobertos passa de aproximadamente 10,87 TWh em 2027 para 19,30 TWh em 2040.

Esse resultado não representa consumo observado ou previsão oficial de todo o setor mineral de Goiás.

## Dados necessários para a futura integração física

A demo define o contrato que permitirá integrar uma versão futura do motor com operações e projetos reais. Os dados podem ser fornecidos em CSV, banco de dados ou API, desde que preservem os campos e significados abaixo.

### Catálogo de minerais

| Campo | Obrigatório | Descrição |
|---|---:|---|
| `mineral_id` | Sim | Identificador estável e único do mineral |
| `mineral_name` | Sim | Nome padronizado usado nas projeções |
| `source_mineral_name` | Sim | Nome como aparece na fonte original |
| `production_basis` | Sim | Base física: `rom`, `beneficiada` ou `conteudo_mineral` |
| `catalog_status` | Sim | Situação da classificação no catálogo |
| `notes` | Não | Observações e limitações |

### Produção histórica

| Campo | Obrigatório | Descrição |
|---|---:|---|
| `mineral_id` | Sim | Mineral do catálogo |
| `company_id` | Sim | Identificador estável da empresa |
| `operation_id` | Sim | Identificador estável da operação |
| `year` | Sim | Ano de referência |
| `production_t` | Sim | Produção em toneladas |
| `production_basis` | Sim | Base física da produção |
| `data_nature` | Sim | Natureza do dado, por exemplo observado ou estimado |
| `source_id` | Sim | Fonte correspondente no catálogo |

### Projetos e expansões

| Campo | Obrigatório | Descrição |
|---|---:|---|
| `project_id` | Sim | Identificador estável e único do projeto |
| `mineral_id` | Sim | Mineral do catálogo |
| `company_id` | Sim | Empresa responsável |
| `capacity_tpy` | Sim | Capacidade anual em toneladas |
| `start_year` | Sim | Ano previsto de início |
| `project_stage` | Sim | `definido`, `provavel` ou `possivel` |
| `production_basis` | Sim | Base física da capacidade |
| `data_nature` | Sim | Natureza do dado |
| `source_id` | Sim | Fonte correspondente |

### Intensidade energética

| Campo | Obrigatório | Descrição |
|---|---:|---|
| `mineral_id` | Sim | Mineral do catálogo |
| `operation_id` | Sim | Operação ou identificador agregado |
| `year` | Sim | Ano de referência |
| `energy_intensity_mwh_t` | Sim | MWh por tonelada |
| `production_basis` | Sim | Base compatível com a produção |
| `data_nature` | Sim | Natureza do dado |
| `source_id` | Sim | Fonte correspondente |

### Regras de qualidade antes da integração

- Não misturar `rom`, `beneficiada` e `conteudo_mineral` sem conversão documentada.
- Não utilizar valores negativos de produção, capacidade ou intensidade energética.
- Preservar IDs estáveis entre atualizações.
- Manter valores desconhecidos como ausentes, sem substituí-los automaticamente por zero.
- Associar toda observação a uma fonte identificável por `source_id`.
- Integrar projetos físicos apenas após validação técnica e metodológica dos dados.

## Execução e validação automática

A demo é executada pelo workflow:

```text
.github/workflows/validate-squad2-model.yml
```

O modelo real é executado pelo workflow:

```text
.github/workflows/validate-modelo-real.yml
```

O workflow do modelo real:

1. instala as dependências;
2. valida a leitura dos dados da Squad 1;
3. executa o backtest;
4. executa os cenários futuros;
5. executa a análise de sensibilidade;
6. publica os três grupos de resultados como artefatos.

Os artefatos podem ser baixados na aba **Actions** e permanecem disponíveis por 30 dias.

## Integração entre squads

```text
Squad 1: consolidação e rastreabilidade dos dados
    ↓
Squad 2: backtest, projeções, cenários e sensibilidade
    ↓
Squad 3: visualização, filtros e interação do utilizador
```

A Squad 1 fornece as bases consolidadas. A Squad 2 transforma essas bases em outputs econômicos e energéticos. A Squad 3 utiliza os outputs e o contrato de sensibilidade para apresentação e interação na plataforma.

## Limitações atuais

- Os coeficientes energéticos são benchmarks, não medições completas de todas as operações minerais de Goiás.
- O modelo real ainda não incorpora projetos físicos, capacidade, expansão, encerramento ou atraso operacional.
- A versão atual não inclui uma camada macroeconômica ou de elasticidade entre demanda global e produção de Goiás.
- Ainda não foi realizado um backtest de consumo elétrico observado pela CCEE, pois não existe uma série compatível por operação e com o mesmo perímetro da produção utilizada.
- Mudanças estruturais de produção não podem ser previstas apenas com tendência histórica.
- A cobertura atual do modelo real é limitada a cinco minerais.

## Próximas etapas

1. Integrar os outputs do modelo real à plataforma da Squad 3.
2. Incluir dados estruturados de projetos futuros quando estiverem disponíveis.
3. Construir uma camada física de oferta sobre a arquitetura já demonstrada na demo.
4. Incorporar uma camada macroeconômica de demanda e elasticidade.
5. Complementar os benchmarks com intensidades energéticas observadas por operação.
6. Integrar dados compatíveis da CCEE para validação energética.
7. Incluir outros minerais após conciliação clara de unidade, produto e base de produção.

## Evidências para avaliação

| Critério | Evidência no repositório |
|---|---|
| Produto técnico | Demo executável e modelo real com scripts de validação, backtest, cenários e sensibilidade |
| Qualidade e consistência | Validações de dados, outputs separados e execução automatizada |
| Rastreabilidade | Fontes, parâmetros e campos de identificação preservados |
| Integração | Leitura direta dos outputs da Squad 1 e contrato JSON para a Squad 3 |
| Organização e GitHub | Componentes separados, dependências declaradas, documentação e workflows automatizados |
