# Squad 2 — Modelo Econômico-Energético

## Objetivo

Desenvolver o Motor Econômico-Energético do projeto MINERA Goiás, com projeções anuais de produção mineral e demanda de energia elétrica para o período de 2027 a 2040.

## Lógica do modelo

O modelo utiliza uma estrutura física e auditável:

`demanda de energia (MWh) = produção projetada (t) × intensidade energética (MWh/t)`

A produção projetada combina:

* produção das operações existentes;
* entrada de novos projetos;
* capacidade, utilização e ano de entrada dos projetos;
* regras para os cenários `conservador`, `referencia` e `expansao`.

## Estado atual

Foi construída uma versão demonstrativa do motor com dados sintéticos, incluindo:

* projeções anuais por mineral e cenário;
* agregação do total de Goiás;
* parâmetros externos ao código;
* análise de sensibilidade para atraso de projetos, utilização e eficiência energética;
* verificações de consistência e arquivos de saída rastreáveis.

Os dados demo são identificados como `estimated_demo` e serão substituídos pelos dados reais quando disponíveis.

## Dependências

* **Squad 1:** produção histórica, operações, projetos, capacidades, localização e fontes;
* **Squad 2:** intensidades energéticas e parâmetros de cenários;
* **Squad 3:** integração dos outputs com banco de dados, API e interface.

## Estrutura prevista

* `notebooks/` — execução e documentação do modelo;
* `data/demo/` — dados sintéticos para testes;
* `data/processed/` — dados tratados e prontos para o motor;
* `outputs/demo/` — resultados da versão demonstrativa;
* `docs/` — metodologia, premissas e fontes.

## Princípios

* IDs, nomes de campos e unidades seguem o Contrato de Dados do projeto;
* dados originais não devem ser sobrescritos;
* valores estimados devem ser identificados e rastreáveis;
* produção e intensidade energética devem utilizar a mesma `production_basis`.
