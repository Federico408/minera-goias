# Metodologia de medição

Este documento fixa **o que o Minera Goiás mede, a partir de qual fonte, em qual unidade e em qual período** — e, com o mesmo cuidado, o que ele ainda não mede. Vale para o painel CCEE, o atlas mineral, o perfil de município, a carga das tabelas de negócio e o radar de notícias.

Atualizado em 13/09/2026. Ao mudar uma regra de cálculo, atualize este arquivo na mesma alteração.

---

## 1. Cinco princípios que valem para tudo

**Contagem não é consumo, nem produção.** Um registro é uma linha de uma fonte. Quando o painel mostra "8.072 registros", isso é o número de linhas da CCEE no recorte — não é número de empresas, nem de minas, nem de MWh.

**Unidade nunca é convertida por inferência.** A CFEM declara quantidade em sete unidades diferentes (t, m³, kg, l, g, m², ct). Nada é somado entre unidades e nada é convertido sem regra revisada. Ouro aparece em kg; energia em MWh ou GWh; coeficientes em kWh/t.

**Fontes sobrepostas não se somam.** As planilhas corrigidas e as originais descrevem o mesmo fenômeno. O acervo guarda as duas como fontes separadas; somar suas linhas produziria dupla contagem.

**Importar não é validar.** Toda linha carregada nasce com `status_validacao = nao_validado`. A validação técnica é ato humano, registrado em `responsavel_validacao`.

**Quando a fonte não diz, o sistema não inventa.** Sem CNPJ na origem, o titular fica sem documento. Sem detalhamento anual, o município fica sem série. Sem substância cadastrada, o campo guarda o texto cru `DADO NÃO CADASTRADO`.

---

## 2. Unidade de observação, por fonte

| Fonte | Uma linha é… | Volume | Período |
|---|---|---|---|
| CCEE — parcelas de carga | Uma parcela de carga de um agente, em um mês, município e ramo | 4.241 (2024) · 8.072 (2025) · 8.245 (2026) | 2024–2026 |
| CFEM — arrecadação | Um recolhimento por processo, substância, município e mês | 38.854 | 2022–2026 |
| Cadastro mineiro (shapefile) | Um polígono de um processo minerário | 17.428 polígonos em 16.656 processos | Data de extração não informada |
| Rodadas de disponibilidade | Uma área oferecida em uma rodada | 31.841 no Brasil · **3.632 em Goiás** | Rodadas 1 a 8 |
| Dicionário de substâncias | Uma substância da ANM | 862 | Sem data declarada |
| Atlas (artefato recebido) | Retrato consolidado de terceiros | 246 municípios · 17.402 polígonos · 23 barragens | Ver §5 |

O acervo importado hoje soma **189.785 linhas em 14 arquivos**, cada uma rastreável até arquivo, aba, linha de origem e commit.

---

## 3. Como cada indicador é calculado

### 3.1 Painel CCEE (visão geral)

Mede **cobertura do acervo**, não energia.

- **Registros no recorte** — contagem de linhas da CCEE do ano selecionado, filtradas por ramo de atividade quando escolhido.
- **Municípios representados** — contagem de valores distintos de `CIDADE` no recorte.
- **Meses com registros** — contagem de valores distintos de `MES_REFERENCIA`.
- **Cobertura ao longo do ano** e **municípios com mais registros** — as mesmas contagens, agrupadas.

**O que existe e deliberadamente não é usado:** o arquivo traz `CONSUMO_ACL`, `CONSUMO_CATIVO_PARC_LIVRE` e `CONSUMO_TOTAL` em MWh. Somados, dariam 6,84 milhões de MWh em 2024, 11,63 em 2025 e 11,33 em 2026. **O painel não publica esses totais** porque a base mistura 16 ramos de atividade — alimentícios, comércio, serviços — e um recorte "mineral" confiável exige critério de classificação revisado, não o campo autodeclarado `RAMO_ATIVIDADE`. Publicar MWh hoje sugeriria uma medição de consumo mineral que a base ainda não sustenta.

### 3.2 Atlas mineral

Cada camada tem unidade própria e período próprio; elas **não** se comparam entre si.

| Camada | Unidade | Período |
|---|---|---|
| CFEM por município | R$ | Acumulado 2022–jul/2026, ou ano escolhido |
| Quantidade comercializada | t (ou kg, para ouro) | 2025 |
| Energia da cadeia mineral | GWh | 2025 |
| Intensidade energética | kWh/t (MWh/kg para ouro) | 2025 |
| Polígonos de processos | ha declarados | Extração sem data |
| Barragens | Classificação categórica | Extração sem data |

**Escala de cores:** faixas de quantis dos valores positivos. Cinza significa **sem registro ou zero** — e são coisas distintas que a fonte não separa.

**A CFEM anual só existe para 8 municípios.** Ao escolher um ano, os outros 238 ficam cinza por ausência de detalhamento, não por arrecadação zero. O acumulado cobre os 246.

**Reconciliação feita:** a soma dos acumulados municipais bate com o total dos cinco anos em R$ 867.578.398,91.

### 3.3 Perfil do município

- **Processos minerários** — contagem de polígonos do artefato naquele município.
- **CFEM acumulada** — valor do artefato, 2022 a julho de 2026.
- **Participação no estado** — CFEM acumulada do município ÷ soma dos 246 municípios, em %.
- **Energia · 2025** — MWh do artefato convertidos para GWh (divisão por 1.000, única operação aritmética aplicada).
- **Substâncias declaradas · 2025** — quantidade, CFEM e número de empresas por substância, como no artefato.
- **Evolução ao longo do tempo** — CFEM por ano **apenas** para os 8 municípios detalhados. Para os outros 238 o painel declara a ausência em vez de desenhar série.

### 3.4 Carga das tabelas de negócio (`load_anm.py`)

- **Substância** resolvida contra o dicionário da ANM por nome normalizado (maiúsculas, sem acento). Todos os nomes reais resolvem; 381 processos trazem `DADO NÃO CADASTRADO` na origem e ficam sem `mineral_id`.
- **Titular** chaveado pelo nome normalizado, porque nenhuma fonte atual fornece documento utilizável.
- **Área do processo** preenchida **somente** quando há um único polígono. Com mais de um, a área fica por polígono e nenhum total é declarado: polígonos podem se sobrepor e a soma criaria superfície inexistente.
- **Polígono** tem chave própria. O identificador do shapefile se repete entre processos e até dentro de um mesmo processo, então é atributo de origem.

### 3.5 Radar de notícias (protótipo)

Mede **o que a imprensa está dizendo**, não preço.

- Uma frase que cite uma substância **e** traga palavra de direção vira um sinal, guardando a frase como evidência.
- `score = (altas − baixas) ÷ total de sinais`, por substância e semana ISO.
- Veredito só com **3 ou mais matérias distintas**; abaixo disso fica `evidencia_insuficiente`, por mais extremo que seja o score.
- Preço citado no texto é extraído com moeda, unidade e escala — e permanece um **preço citado**, não cotação de mercado.

---

## 4. O que ainda não é medido

Declarar isto é parte da metodologia.

- **Consumo de energia da mineração em MWh.** Depende de um critério revisado para separar carga mineral das demais na base CCEE (§3.1).
- **Intensidade energética por operação.** Os coeficientes do atlas são razões municipais — energia do município ÷ produção do município —, não medidas de planta.
- **Projeções.** `tb_projecoes` está vazia. O motor da Squad 2 roda sobre dados sintéticos identificados como `estimated_demo` e não alimenta o portal.
- **Série temporal municipal fora dos 8 municípios.** A base CCEE do banco é mensal e cobre todos os municípios; ligá-la ao perfil municipal é o caminho natural, e ainda não foi feito.
- **Produção mineral física por empresa.** As fontes dão quantidade comercializada declarada para fins de CFEM, que não equivale a produção.

---

## 5. Precisão e incerteza declaradas

- **Geometrias do atlas** vêm de caminhos SVG convertidos por transformação linear e de matrizes quantizadas em UInt16, com coordenadas arredondadas a seis casas. Servem para localizar e comparar; **não são limites cadastrais**.
- **Identificadores em notação científica:** 34.212 registros da CFEM trazem CPF/CNPJ como número em notação científica. Dígitos perdidos na origem não são recuperados por aproximação — são sinalizados como alerta.
- **CPF de pessoa física** vem mascarado da ANM (`***370285**`). CNPJ de pessoa jurídica vem íntegro, e é dado público.
- **Fórmulas de planilha** não são recalculadas: 2.358 células da base consolidada estão sem valor em cache e aparecem como alerta, não como zero.
- **Barragens** trazem classificação de risco, dano potencial e nível de emergência como categorias de uma extração sem data. **Não servem para avaliar condição atual.**

---

## 6. Divergência aberta

**Período da CFEM de 2026.** O arquivo `CFEM_Arrecadacao_2022_2026_GO.csv` contém registros nos meses 1 a **8** de 2026. O artefato do atlas rotula o mesmo conjunto — 9.569 registros — como "janeiro a julho". As duas coisas não podem estar certas ao mesmo tempo.

Hipótese a verificar: o campo `Mês` pode ser o mês do recolhimento, e não o da competência, o que deslocaria o rótulo em um mês. Até que alguém confirme na ANM, **o portal exibe "2022–jul/2026" por ser o rótulo mais conservador**, e este item fica registrado como pendência. Quem for verificar: comparar `Mês` com `DataCriacao` em uma amostra e confrontar com a documentação da CFEM.

---

## 7. Reprodutibilidade

Toda medição do portal pode ser refeita a partir do repositório:

```sh
# Acervo: reconstrói as tabelas de origem a partir dos arquivos
python3 ingestion/import_repository.py --root . --sqlite /tmp/acervo.sqlite --report /tmp/acervo.json

# Tabelas de negócio: carga direta das fontes da ANM, sem tocar no MySQL
python3 "Squad 3/database/load_anm.py" --root . --sqlite /tmp/negocio.sqlite

# Atlas: reextrai o pacote a partir do artefato recebido
python3 scripts/extract_atlas.py /caminho/do/artefato.html

# Radar: executa sem rede, sobre as fixtures
python3 news/radar.py --db /tmp/radar.sqlite --offline-dir tests/fixtures/news
```

Cada arquivo importado guarda hash do conteúdo, commit de origem e versão das regras de leitura. Uma alteração cria versão nova e preserva a anterior; um arquivo removido é desativado sem apagar o histórico.

---

## 8. Como mudar esta metodologia

Uma regra de cálculo só muda junto com três coisas: o código que a implementa, o teste que a fixa e este documento. Os testes que hoje travam decisões metodológicas:

| Decisão | Teste |
|---|---|
| Nenhum polígono se perde pela chave do processo | `tests/test_load_anm.py` |
| Área não é somada quando polígonos podem se sobrepor | `tests/test_load_anm.py` |
| Documento de titular não é inventado | `tests/test_load_anm.py` |
| Nome de pessoa não sai no endpoint público | `tests/test_load_anm.py` · `tests/test_web.py` |
| Semana sem matérias suficientes não recebe veredito | `tests/test_news.py` |
| Preço citado preserva moeda, unidade e escala | `tests/test_news.py` |
| Demos e mocks ficam fora da carga | `tests/test_ingestion.py` |
| Versão anterior sobrevive a uma importação que falha | `tests/test_ingestion.py` |
