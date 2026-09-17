# Relatório de Qualidade e Proposta de Conformidade — v1

**Squad 1 · Estudante 3 (Giovana Dodero) · MINERA Goiás · 17/09/2026**

Escopo desta entrega: analisar outliers e dados faltantes, organizar e definir a estratégia para
dados faltantes, e propor a uniformização de quantidades e unidades entre as fontes do Squad 1,
como passo para consolidar tudo em uma única base. Todos os números abaixo vêm de
`analise_qualidade_lucas_v1.py`, rodado sobre a v17 e as três planilhas "CORRIGIDA LUCAS V1", e do
`relatorio_qualidade.md` do Estudante 1.

## 1. O que já existia e não foi refeito aqui

A base v17 do Estudante 1 (Eliel) já tem um relatório de qualidade completo — faltantes,
duplicidades, divergências entre fontes e unidades — em
`Squad 1/Bases consolidadas/documentacao/relatorio_qualidade.md`. Este documento não repete esse
trabalho; ele cobre o que ainda faltava: as três planilhas do Estudante 2 (Lucas), que chegaram ao
repositório em 03/09 sem documentação do que foi "corrigido", e a consistência entre as duas
frentes.

## 2. Matriz de completude

`matriz_completude_v17_eliel.csv` traz os 439 campos da aba `14_dicionario_dados` da v17 (aba,
campo, % vazio, tipo, descrição) — a base para a matriz de completude da base do Estudante 1.
Achados que valem destaque para a estratégia de dados faltantes (seção 5):

- Vazios **de propósito**, já documentados pelo Eliel: `capacidade_t_ano`, `capex_brl` e
  `ano_previsto_entrada` da aba `04_dim_projetos` (100% vazios — dependem do Radar de Projetos do
  Estudante 2); `energy_mwh` e `energy_intensity_mwh_t` da aba `11` (100% vazios — dependem do
  pareamento com a CCEE, que é a parte que cabe a mim); `operation_id`/`latitude`/`longitude` da
  aba `12`, vazios em 457 das 4.856 linhas do nível `operacao` (9,4%, ver nota do Eliel).
- Os arquivos do Lucas (produção beneficiada, bruta e arrecadação) **não têm dicionário nem
  relatório de qualidade próprio** — a matriz de completude deles está nas seções 3 e 4 abaixo.

## 3. Outliers e problemas de qualidade encontrados nas planilhas do Lucas

Nenhum destes itens está documentado em `Squad 1/PROPOSTA_ORGANIZACAO_DADOS.md` nem em nenhum
outro lugar do repositório — são achados novos desta análise.

### 3.1 Arrecadação CFEM — 17,9% de linhas duplicadas

`ARRECADAÇÃO CORRIGIDA LUCAS V1.xlsx` tem 38.854 linhas (já só Goiás); **6.950 (17,9%) são
duplicatas exatas** — todas as colunas iguais, incluindo processo, mês e valor. Exemplo: o
processo 1475 (Águas Caldas Novas) tem a mesma linha de janeiro/2026 repetida 4 vezes. Antes de
usar este arquivo em qualquer consolidação, essas linhas precisam ser removidas (`drop_duplicates`
simples resolve, mas fica registrado aqui para não ser feito silenciosamente).

### 3.2 Produção bruta (ROM) — mesmo padrão de dupla categoria que o Eliel já sinalizou

10 linhas em Goiás (todas da substância "Gemas", categoria "Gemas e Diamantes") aparecem em pares
para o mesmo ano — o mesmo fenômeno que o relatório de qualidade do Eliel já registra na aba `08`
como `alerta_producao_repetida` (164 linhas: "co-produto, mineral separado por teor ou mesma
declaração em duas categorias"). Não é um problema novo do Lucas; é a mesma característica da fonte
ANM aparecendo de novo. Tratamento recomendado: somar as duas linhas por (ano, substância), como o
Eliel já faz na aba `09`.

### 3.3 Valores nulos na arrecadação

`QuantidadeComercializada`: 7 nulos; `QTD KG`: 1.176 nulos (linhas cuja unidade original não é de
massa — m³, l — e por isso não têm conversão para kg, o mesmo caso já descrito na aba `09b` do
Eliel para a mesma fonte); `VALOR CORRIGIDO`: 3 nulos. Nenhum caso de `ValorRecolhido = 0` com
`VALOR CORRIGIDO` preenchido (a correção não inventa valor onde não havia).

### 3.4 A coluna "Correção" / "VALOR CORRIGIDO" não está documentada

Todas as três planilhas do Lucas trazem uma coluna de correção monetária aplicada aos valores em
R$. Na arrecadação, o fator (`VALOR CORRIGIDO ÷ ValorRecolhido`) varia por ano **e dentro do
mesmo ano** (ex.: 2022 vai de 1,19 a 1,25; 2026 vai de 1,00 a 1,03), decrescendo com o tempo — o
padrão é compatível com uma correção monetária mês a mês (o valor de um mês antigo pesa mais que o
de um mês recente), mas **o repositório não diz qual índice foi usado, a data de referência, nem a
fórmula**. Isso já estava listado como pendência no `STATUS_SQUAD1_ENTREGA1.md` ("o repositório não
documenta que correções foram feitas"). Recomendação: pedir ao Lucas a metodologia antes de usar
essa coluna na base consolidada; sem isso, ela não pode ser tratada como "observada".

## 4. Verificação cruzada: os números do Lucas batem com os da v17?

Comparei a produção e a arrecadação de Goiás nas planilhas do Lucas com os mesmos totais na aba
`09_cons_mineral_ano` da v17 (que veio de um pipeline independente, a partir dos brutos da ANM).

| Comparação | Pares comparáveis (mineral × ano) | Divergentes (>5%) |
|---|---:|---:|
| Produção bruta (ROM) | 421 | **0** |
| Produção beneficiada | 311 | **0** |
| CFEM nominal, por ano (2022–2026) | 5 | **0** (razão = 1,000 em todos os anos) |

**As duas fontes batem.** Isso é uma boa notícia para a consolidação: não há conflito de dado entre
o que o Eliel processou e o que o Lucas "corrigiu" — a diferença entre os dois é só a correção
monetária (seção 3.4) e o recorte (Lucas trouxe o Brasil inteiro; a v17 já vem só de Goiás).

**Achado de meio-de-caminho, corrigido durante a análise** — vale registrar porque quase virou um
falso alarme: a primeira comparação de produção beneficiada mostrou divergências de até 5.000.000×.
A causa não era um erro do Lucas nem do Eliel: é que o campo `production_beneficiada` da aba `09`
**muda de unidade por mineral** (t para a maioria, kg para Ouro/Prata/Estanho/Gemas, ct para
Diamante) sem uma coluna de valor já normalizado — só a coluna `production_beneficiada_unit` avisa
qual é. Isso é, em si, um problema de conformidade de unidades (ver seção 5).

## 5. Proposta de conformidade de unidades

### 5.1 O problema

- Na aba `09` da v17, `production_beneficiada` é um único campo numérico que representa t, kg ou ct
  dependendo do mineral — quem for somar ou comparar essa coluna sem olhar
  `production_beneficiada_unit` mineral a mineral vai errar por até 6 ordens de grandeza (como
  quase aconteceu nesta análise).
- Nas planilhas do Lucas, a mesma informação já vem com uma coluna auxiliar em kg
  (`Quantidade Produção KG`, `Quantidade Produção - Minério ROM KG` etc.) ao lado da quantidade na
  unidade original — ou seja, o Lucas já resolveu esse problema à sua maneira, mas em arquivos
  separados, sem chave (`mineral_id`) nem `municipality_id`, e para o Brasil inteiro.
- CFEM: `QuantidadeComercializada` mistura t, m³, l, kg, ct, quilate; a v17 já converte só a parte
  de massa para t (aba `09`, `cfem_qtd_comercializada_t`) e separa o resto em
  `cfem_qtd_outras_unidades` — mesma limitação física está nas planilhas do Lucas.

### 5.2 Proposta

1. **Adotar como padrão da base consolidada**: massa sempre em toneladas (t); valores monetários
   sempre com duas colunas lado a lado — nominal (R$ na data da declaração) e corrigido (R$ na data
   de referência), com a metodologia da correção documentada antes de entrar na base (depende do
   Lucas, seção 3.4); volume (m³) e área (m²) nunca somados com massa, como já é feito na aba `09`.
2. **Adicionar uma coluna `production_t_normalizada`** em qualquer aba que hoje exponha
   `production_beneficiada` (ou equivalente) sem normalizar por unidade — calculada a partir de
   `production_beneficiada_unit` com a tabela de conversão (t×1000=kg, ct×0,2=g), do jeito que este
   relatório teve que fazer manualmente para poder comparar. Isso evita que o próximo consumidor da
   base (Squad 2) cometa o mesmo erro.
3. **Antes de somar/consolidar dado do Lucas com o da v17**: remover as duplicatas exatas da
   arrecadação (3.1), somar os pares de "Gemas" na produção bruta (3.2) e não usar `VALOR CORRIGIDO`
   até a metodologia estar documentada (3.4).

## 6. Estratégia para dados faltantes (aplicação do fluxo do `SQUAD1_PLANEJAMENTO.md`, §16)

```
Dado ausente → existe fonte adicional? → sim: extrair e validar
                                        → não: existe proxy defensável?
                                                 → sim: registrar como estimativa (método + erro)
                                                 → não: manter ausente, nunca inventar
```

Aplicado às três lacunas materiais que cabem à S1-E3 (`QUADRO_ENTRADAS_SAIDAS.md`):

| Lacuna | Fonte adicional existe? | Proxy defensável | Situação |
|---|---|---|---|
| Produção sem coordenadas (457 linhas / 112 processos, aba 12) | Não (processos fora do SIGMINE) | Município de arrecadação da CFEM, já presente nessas linhas — já sugerido pelo Eliel | A aplicar |
| Capacidade dos projetos (aba 04) | Depende do Radar do Lucas, ainda não publicado | Benchmark por mineral, só depois que houver ao menos alguns valores observados | Bloqueada até o Radar |
| Pareamento CCEE ↔ operação mineral | A demonstrar (exigência separada do guia, não é uma "variável" a escolher) | — | Próximo passo |

Machine learning não entra aqui: nenhuma das três lacunas tem amostra que justifique ML sem risco
de overfitting, e o `SQUAD1_PLANEJAMENTO.md` já veda ML automático sem justificativa.

## 7. Próximos passos

1. Rodar o mesmo diagnóstico sobre a base de arrecadação já deduplicada e sobre a produção bruta já
   somada por (ano, substância), para ter os números "limpos" antes de qualquer consolidação.
2. Pedir ao Lucas a metodologia da coluna de correção monetária (índice, data de referência).
3. Consolidar: v17 (GO, já tratada) + planilhas do Lucas (filtradas para GO, deduplicadas, com
   `mineral_id` já mapeado pelo crosswalk `01b` — este script já faz o mapeamento) em uma única
   tabela, usando os nomes de campo do Contrato de Dados (`production_t`, `valor_observado_estimado`,
   `metodo_estimacao`, `erro_estimativa_intervalo`) em vez de nomes novos.
4. Tratar a lacuna de coordenadas (457 linhas) com o proxy do município de CFEM, documentando erro
   e método na própria linha.
5. Demonstrar o pareamento CCEE ↔ operação mineral (arquivos em `Squad 1/dados/CCEE/`).
