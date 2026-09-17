# Modelo econômico-energético da Squad 2

## Objetivo

Este diretório contém o modelo econômico-energético desenvolvido pela Squad 2 para o projeto MINERA Goiás.

O modelo estima a demanda de energia elétrica associada à produção mineral de Goiás entre 2027 e 2040. Ele parte das séries históricas consolidadas pela Squad 1, aplica cenários explícitos de crescimento e eficiência energética e produz resultados por mineral, ano e cenário.

O objetivo desta versão é disponibilizar um componente técnico funcional, reproduzível e integrado aos dados disponíveis. Ela não pretende ser uma previsão definitiva da mineração goiana. Os resultados devem ser interpretados como cenários condicionais às hipóteses e aos dados atualmente disponíveis.

A demonstração inicial da plataforma permanece preservada no repositório como referência. Este diretório contém um modelo separado, criado especificamente para trabalhar com os dados reais consolidados no projeto.

## O que o modelo faz

A versão atual do modelo realiza quatro funções separadas:

1. Lê e valida a produção mineral histórica consolidada pela Squad 1.
2. Executa um backtest histórico para verificar como uma projeção baseada em tendência se comporta em anos conhecidos.
3. Gera cenários futuros de produção e de demanda estimada de energia para 2027–2040.
4. Executa uma análise de sensibilidade das intensidades energéticas, preparada para integração interativa na plataforma.

Essas quatro funções são executadas por scripts diferentes. O backtest, os cenários futuros e a análise de sensibilidade possuem outputs separados para evitar confusão entre validação histórica, projeção e teste de hipóteses.

## Cobertura da versão atual

O modelo cobre cinco minerais cujas séries de produção e parâmetros energéticos puderam ser conciliados de forma consistente:

| Mineral | Base de produção usada no modelo | Intensidade energética base |
|---|---|---:|
| Cobre | Conteúdo mineral | 11,20 MWh/t |
| Alumínio (Bauxita) | Produção beneficiada | 1,40 MWh/t |
| Níquel | Produção beneficiada | 45,551351 MWh/t |
| Fosfato | Produção beneficiada | 0,15 MWh/t |
| Amianto | Produção beneficiada | 0,32 MWh/t |

O nióbio não é incluído nesta versão. As bases disponíveis apresentam unidades e conceitos de produção que não puderam ser conciliados com segurança com o coeficiente energético disponível. A sua inclusão sem essa conciliação poderia produzir resultados incorretos.

As toneladas dos minerais não são agregadas entre si, porque o cobre utiliza conteúdo mineral e os demais minerais utilizam produção beneficiada. A agregação realizada pelo modelo é a demanda estimada de energia, expressa em MWh.

## Estrutura do diretório

```text
modello_reale/
├── parameters/
│   ├── energy_intensity.csv
│   └── scenarios.csv
├── src/
│   ├── common.py
│   ├── run_backtest.py
│   ├── run_future_scenarios.py
│   └── run_intensity_sensitivity.py
├── outputs/
│   ├── backtest/
│   ├── future/
│   └── sensitivity/
├── requirements.txt
└── README.md
```

Os arquivos dentro de `outputs/` são gerados automaticamente pelos scripts e publicados como artefatos na GitHub Actions.

## Dados de entrada e rastreabilidade

### Produção mineral histórica

O modelo lê diretamente os outputs consolidados pela Squad 1. Não são criadas cópias da base de produção dentro deste diretório.

| Uso | Arquivo de origem |
|---|---|
| Bauxita, níquel, fosfato e amianto | `Squad 1/Bases consolidadas/documentacao/pacote_squad2/interface_squad1_squad2.csv` |
| Cobre | `Squad 1/Bases consolidadas/documentacao/prototipo_bases_consolidadas_v17.xlsx`, aba `08_fato_producao_energia` |

O cobre é lido diretamente da planilha consolidada porque a métrica compatível, `contido_beneficiada`, não está disponível no arquivo de interface utilizado para os outros minerais.

Durante a leitura, o modelo preserva e utiliza campos importantes para rastreabilidade, como:

- `mineral_id`
- `mineral_name`
- `production_basis`
- `source_id`
- `status_validacao`
- `periodo_referencia`

O script interrompe a execução caso encontre observações duplicadas, produção ausente ou produção negativa.

### Intensidades energéticas

Os coeficientes de intensidade energética estão em:

```text
parameters/energy_intensity.csv
```

A intensidade energética representa quantos MWh são necessários, em hipótese, para produzir uma tonelada do mineral na base de produção correspondente.

Os parâmetros utilizados possuem o identificador de fonte `SRC_FGV_EPGE_001`. Nesta versão, eles devem ser interpretados como **benchmarks ou proxies operacionais**, e não como uma medição observada do consumo elétrico de toda a mineração de Goiás.

Portanto, a saída energética do modelo deve ser interpretada como:

> estimativa de demanda de energia sob parâmetros de intensidade energética baseados nos benchmarks disponíveis.

Ela não representa uma medição direta do consumo total efetivamente observado em todas as operações do estado.

### Cenários

As hipóteses de cenário estão em:

```text
parameters/scenarios.csv
```

| Cenário | Ajuste sobre o crescimento histórico | Melhoria anual de eficiência energética |
|---|---:|---:|
| Conservador | -2,0 pontos percentuais | 0,4% |
| Referência | 0,0 pontos percentuais | 0,9% |
| Expansão | +2,0 pontos percentuais | 1,4% |

Essas hipóteses são identificadas como `illustrative`. Elas não são previsões oficiais. O seu objetivo é permitir comparação transparente entre diferentes trajetórias possíveis.

## Método de projeção

Para cada mineral, o modelo calcula uma taxa média anual de crescimento a partir da sua série histórica de produção.

A projeção futura de produção é calculada como:

```text
produção projetada =
produção no último ano observado
× (1 + crescimento histórico + ajuste do cenário)^n
```

Em que `n` representa o número de anos entre o último dado observado e o ano projetado.

A intensidade energética diminui ao longo do tempo de acordo com a hipótese de eficiência do cenário:

```text
intensidade projetada =
intensidade base
× (1 - melhoria anual de eficiência)^n
```

Por fim, a demanda estimada de energia é calculada para cada mineral, ano e cenário:

```text
demanda de energia em MWh =
produção projetada em toneladas
× intensidade energética em MWh/t
```

Os cenários futuros cobrem o período de 2027 a 2040.

## Backtest histórico

O backtest verifica o comportamento do modelo em dados já conhecidos.

Para cada mineral, os dois últimos anos disponíveis são separados como período de teste. O modelo calcula o crescimento histórico apenas com os anos anteriores e projeta os anos reservados. Em seguida, compara a previsão com a produção efetivamente observada.

O indicador utilizado é o erro percentual absoluto médio, ou MAPE.

| Mineral | Anos testados | MAPE |
|---|---:|---:|
| Fosfato | 2 | 2,3% |
| Cobre | 2 | 3,0% |
| Níquel | 2 | 7,8% |
| Amianto | 2 | 8,6% |
| Alumínio (Bauxita) | 2 | 44,3% |

O resultado da bauxita merece uma interpretação específica. Até 2023, a série apresentava crescimento histórico positivo e o modelo prolongou essa tendência. Contudo, a produção observada caiu de forma relevante em 2024 e recuperou-se apenas parcialmente em 2025.

O erro elevado da bauxita não indica necessariamente um erro de programação. Ele mostra o limite de uma projeção baseada apenas em tendência histórica: o modelo não consegue antecipar interrupções operacionais, decisões empresariais, condições de mercado, licenciamento ou outras mudanças estruturais sem dados adicionais.

Os resultados da bauxita devem, portanto, ser usados com maior cautela.

Os outputs do backtest são:

| Arquivo | Conteúdo |
|---|---|
| `outputs/backtest/backtest_detail.csv` | Previsões e valores observados por mineral e ano testado |
| `outputs/backtest/backtest_summary.csv` | MAPE por mineral |

## Cenários futuros

Os outputs de cenários futuros são:

| Arquivo | Conteúdo |
|---|---|
| `outputs/future/future_projection_by_mineral.csv` | Produção projetada, intensidade energética e demanda de energia por mineral, ano e cenário |
| `outputs/future/future_energy_summary.csv` | Demanda total estimada de energia dos cinco minerais cobertos, por ano e cenário |

No cenário de referência, a demanda estimada de energia dos cinco minerais cobertos evolui de aproximadamente 10,87 TWh em 2027 para 19,30 TWh em 2040.

Esse valor não deve ser apresentado como consumo observado ou previsão oficial de toda a mineração de Goiás. Ele é o resultado do modelo sob as hipóteses atuais de produção, eficiência e intensidade energética.

## Análise de sensibilidade

A análise de sensibilidade é um módulo separado do backtest e dos cenários futuros.

Ela não altera a produção projetada. O seu objetivo é testar o impacto de mudanças nos coeficientes de intensidade energética, que constituem uma fonte importante de incerteza nesta versão do modelo.

O intervalo de teste vai de -10% a +10%, com passos de 1%.

A fórmula aplicada é:

```text
energia ajustada do mineral =
energia base do mineral
× (1 + ajuste percentual / 100)
```

A energia total ajustada é a soma dos resultados ajustados de todos os minerais.

A análise gera os seguintes outputs:

| Arquivo | Conteúdo |
|---|---|
| `outputs/sensitivity/intensity_global_range.csv` | Variação igual da intensidade de todos os minerais |
| `outputs/sensitivity/intensity_one_way.csv` | Variação de um mineral por vez, mantendo os demais fixos |
| `outputs/sensitivity/intensity_sensitivity_contract.json` | Contrato de dados para integração interativa |
| `outputs/sensitivity/custom_intensity_result.json` | Resultado de uma combinação específica de ajustes |

O arquivo `intensity_sensitivity_contract.json` foi preparado para que a plataforma permita um ajuste independente por mineral. Por exemplo:

```text
Cobre: +3%
Bauxita: 0%
Níquel: -5%
Fosfato: +1%
Amianto: 0%
```

Não é necessário pré-calcular todas as combinações possíveis. A interface pode aplicar a fórmula de sensibilidade diretamente aos valores base do contrato JSON, permitindo respostas imediatas ao utilizador.

## Integração entre squads

### Squad 1

A Squad 1 consolida e documenta os dados de produção. Este modelo lê diretamente os seus outputs e preserva identificadores de fonte, base de produção e status de validação.

Uma evolução futura poderá incorporar uma camada física de oferta caso sejam disponibilizados dados estruturados de projetos, como capacidade, ano de entrada em operação, produção esperada e grau de certeza.

### Squad 2

Este diretório contém o componente econômico-energético da Squad 2. Ele recebe produção histórica, aplica cenários, produz projeções, executa backtest e calcula a demanda estimada de energia.

### Squad 3

A Squad 3 pode utilizar:

- os arquivos em `outputs/future/` para gráficos e tabelas;
- o arquivo `intensity_sensitivity_contract.json` para controles interativos de sensibilidade.

O fluxo de integração esperado é:

```text
Squad 1: dados históricos consolidados
    ↓
Squad 2: projeção, backtest e sensibilidade
    ↓
Squad 3: visualização e interação do utilizador
```

## Execução local

A partir da raiz do repositório, instalar as dependências:

```bash
python -m pip install -r "Squad 2/modello_reale/requirements.txt"
```

Validar a leitura dos dados da Squad 1:

```bash
python "Squad 2/modello_reale/src/common.py"
```

Executar o backtest histórico:

```bash
python "Squad 2/modello_reale/src/run_backtest.py"
```

Executar os cenários futuros:

```bash
python "Squad 2/modello_reale/src/run_future_scenarios.py"
```

Executar a análise de sensibilidade:

```bash
python "Squad 2/modello_reale/src/run_intensity_sensitivity.py"
```

## Automação e verificação

O workflow abaixo executa o modelo automaticamente quando há alterações nos arquivos relevantes:

```text
.github/workflows/validate-modelo-real.yml
```

O workflow:

1. instala as dependências;
2. valida a leitura dos dados da Squad 1;
3. executa o backtest;
4. executa os cenários futuros;
5. executa a análise de sensibilidade;
6. publica os três grupos de outputs como artefatos da GitHub Actions.

## Limitações da versão atual

As principais limitações são:

- os coeficientes energéticos são benchmarks, não medições completas de todas as operações minerais de Goiás;
- o modelo ainda não incorpora capacidade, novos projetos, expansões, encerramentos ou atrasos operacionais;
- a versão atual não inclui uma camada macroeconômica ou de elasticidade entre demanda global e produção de Goiás;
- não foi realizado backtest de consumo elétrico observado pela CCEE porque ainda não há uma série compatível por operação e com o mesmo perímetro dos dados de produção;
- mudanças estruturais, como a queda da produção de bauxita em 2024, não podem ser antecipadas apenas com tendência histórica;
- a cobertura atual é limitada a cinco minerais.

## Próximas evoluções recomendadas

1. Incorporar dados estruturados de projetos futuros.
2. Separar cenários de oferta física e cenários de demanda ou contexto macroeconômico.
3. Estimar uma camada de elasticidade entre demanda global dos minerais e produção de Goiás.
4. Substituir ou complementar benchmarks por intensidades observadas por operação e etapa produtiva.
5. Integrar dados compatíveis da CCEE para validar a demanda energética.
6. Incluir nióbio e outros minerais após conciliação clara de produto, unidade e base de produção.
7. Conectar os outputs e o contrato de sensibilidade à plataforma da Squad 3.

## Evidências para avaliação

| Critério de avaliação | Evidência disponível neste componente |
|---|---|
| Produto técnico | Scripts funcionais para leitura, backtest, cenários e sensibilidade |
| Qualidade e consistência | Validações de colunas, duplicidades, valores ausentes e produção negativa |
| Rastreabilidade | Fontes identificadas, parâmetros separados e campos de origem preservados |
| Integração | Leitura direta dos outputs da Squad 1 e contrato JSON para a Squad 3 |
| Organização e GitHub | Estrutura separada da demonstração, dependências declaradas e workflow automatizado |

## Status

O modelo está funcional para o escopo atual de dados. Os próximos passos prioritários são a integração dos outputs na plataforma e o enriquecimento gradual da camada de oferta e dos parâmetros energéticos quando novas bases estruturadas estiverem disponíveis.
