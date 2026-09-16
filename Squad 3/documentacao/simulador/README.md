# Simulador de Demanda Energética e Rastreabilidade — versão 1

Squad 3 · Henrique Falci · entrega de 21/09

Página web que recalcula a demanda de energia do setor mineral de Goiás entre 2027 e 2040
conforme o cenário e a hipótese de eficiência energética escolhidos, mostrando a origem de
cada parâmetro usado. O simulador não consulta nenhuma fonte externa: ele lê um único
arquivo de parâmetros versionado do repositório.

## Arquivos

| Arquivo | Função |
|---|---|
| `public/simulador.html` | Estrutura da página |
| `public/simulador.css` | Estilo, seguindo o guia visual azul/dourado |
| `public/simulador-engine.js` | Cálculo, isolado da interface e sem acesso à tela |
| `public/simulador.js` | Controles, gráficos e painel de fontes |
| `public/data/simulador/parametros_v0.json` | Parâmetros de entrada, com campo `versao` |
| `tests/simulador.test.js` | 28 verificações do cálculo |
| `tests/test_simulador.py` | Contrato dos parâmetros, rastreabilidade e ausência de segredos |

O cálculo fica separado da interface de propósito: quando o motor do Squad 2 estiver com
dados reais, basta trocar `simulador-engine.js` (ou fazê-lo ler a saída do motor) sem
mexer na tela.

## Como rodar

O projeto não tem build. A página é servida como arquivo estático:

```sh
cd public
python3 -m http.server 8000
```

Abra `localhost:8000/simulador.html` no navegador.

Em produção a página já é servida pelo Nginx junto com o resto de `public/`, no caminho
`/simulador.html`.

## Como testar

```sh
python3 -m unittest discover -s tests -p test_simulador.py -v
node tests/simulador.test.js
```

Ambos rodam também no GitHub Actions, pelo workflow `validate-web.yml`.

## As fórmulas

O núcleo é o método do projeto — produção física × intensidade energética — sem nenhuma
camada estatística intermediária:

```
Energia(t)       = Produção(t) × Intensidade(t)
Intensidade(t)   = Intensidade_base × (1 − g)^(t − ano_base)
Produção(t)      = produção_baseline × fator_producao(cenário)
```

- `ano_base` = 2025, `t` vai de 2027 a 2040.
- `g` é o ganho anual de eficiência, controlado pelo usuário entre 0% e 3%.
- Como o horizonte começa dois anos depois do ano base, em 2027 o ganho já se aplica duas
  vezes. É a mesma convenção do notebook do Squad 2.
- As três curvas comparadas usam a **mesma** hipótese de eficiência, para que a diferença
  entre elas isole o efeito do cenário de produção.

## De onde vêm os dados

**Baseline (observado).** As sete operações vêm da tabela "Baseline energético já existente
no material da FGV Energia", da proposta MINERA Goiás, que indica ANM e CCEE como origem:
Anglo Barro Alto, Maraca, Anglo Níquel Minas, CMOC Fosfato, CMOC Nióbio, Sama e CBA.

**Conferência.** Produção × intensidade resulta em 4,4904 TWh, contra 4,60 TWh publicados
na mesma tabela — diferença de −2,38%, porque a produção aparece arredondada em Mt na
origem. A divergência fica registrada em `conferencia_baseline` e aparece no painel de
fontes. Ela não foi corrigida em silêncio.

**Ilustrativo.** Os fatores de produção por cenário (0,90 / 1,00 / 1,15) foram arbitrados
pelo Squad 3 apenas para demonstrar o recálculo. Os ganhos de eficiência padrão
(0,4% / 0,9% / 1,4%) vêm de `scenario_parameters_demo.csv` do Squad 2, que são sintéticos
(`estimated_demo`). Tudo isso está marcado como `ilustrativo` no arquivo e sinalizado na
tela.

## Integração

**Entrada recebida.** Do Squad 2 (Federico Castro): o contrato de dados descrito no
`Squad 2/README (1).md`, os identificadores `mineral_id` de `minerals_demo.csv` e as taxas
de eficiência por cenário do motor demo. O simulador reusa esses identificadores, e
`tests/test_simulador.py` falha se eles divergirem do catálogo do Squad 2.

**Saída entregue.** `public/data/simulador/parametros_v0.json` é o formato que o Squad 2
precisa preencher para que o simulador passe a mostrar números reais, e o registro de
fontes que o Squad 3 (Kayo) pode servir por API no lugar do arquivo estático. O motor de
cálculo é uma função pura e pode ser chamado por qualquer outra tela do painel.

## Como atualizar e versionar os parâmetros

O arquivo de parâmetros é a única entrada do simulador. Para publicar uma versão nova:

1. Edite `public/data/simulador/parametros_v0.json` mantendo a estrutura.
2. Suba o campo `versao` e ajuste `data_versao`.
3. Toda medida nova precisa de um `source_id` que exista em `fontes`, com
   `valor_observado_estimado` igual a `observado`, `estimado` ou `ilustrativo`. Quando for
   estimado, preencha `metodo_estimacao`. Os testes recusam a alteração se faltar fonte.
4. Rode os dois comandos de teste da seção acima.
5. Faça o commit e marque a versão no GitHub:

```sh
git tag params-v0.1 -m "Parâmetros do simulador v0.1.0"
git push origin params-v0.1
```

A tag congela o par arquivo + código que produziu um resultado, então qualquer número
apresentado pode ser reproduzido depois. A página mostra a versão carregada no canto
superior direito e no painel de fontes.

Quando o Squad 2 entregar parâmetros com dados reais, o arquivo passa a `versao` 1.0.0, o
aviso de dado ilustrativo sai da tela e os `valor_observado_estimado` mudam conforme a
natureza de cada medida.

## Limitações desta versão

- A produção é constante ao longo do horizonte: não há crescimento da produção existente
  nem entrada de projetos novos. Essas duas coisas são do motor do Squad 2 e entram quando
  ele publicar parâmetros reais.
- Os fatores de cenário não têm base empírica.
- O baseline não traz o ano de referência; 2025 foi adotado por coerência com o Squad 2.
- Sem exportação, log de execução ou API — fora do escopo desta entrega.
