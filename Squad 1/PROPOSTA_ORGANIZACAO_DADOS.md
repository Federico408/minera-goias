# Proposta — organização do que sobrou em `Squad 1/dados/`

**Squad 1 · proposta do Estudante 1 para o squad decidir · 14/09/2026 · nada foi movido**

Em 14/09, as cópias idênticas de brutos que estavam em `Squad 1/dados/` (AMB, CFEM, investimento, SIGMINE, Panorama e Mineradoras) foram
para `Squad 1/Dados brutos/`, uma pasta por fonte. Restam 13 arquivos, cerca de 26 MB. Esta nota diz o que é cada um, quem usa hoje e o que
propomos. Três conjuntos são lidos pelo código do Squad 3 e ficam onde estão.

## O que é cada arquivo

| Arquivo | Tamanho | Entrou em | O que é | Quem usa hoje | Proposta |
|---|---:|---|---|---|---|
| `CCEE/parcela_carga_consumo_2024_GO.csv`, `_2025_GO.csv` e `_2026_GO.csv` | 0,8 / 1,4 / 1,5 MB | 03/09 (Eliel) | consumo mensal por parcela de carga em Goiás (CCEE), de todos os ramos de atividade | painel do site (`Squad 3/backend/dashboard.py`), `tests/test_web.py` e a consulta de exemplo de `ingestion/README.md`; é insumo do E3 | **Manter.** Completar o `CCEE/Read.me` com link, período e data de acesso. |
| `CCEE/Read.me` | 15 bytes | 03/09 (Eliel) | só o texto "dados da CCEE" | — | Completar (ver a linha acima). |
| `ResultadoRodadaDisponibilidade (1).csv` | 3,5 MB | 10/09 (conta compartilhada) | resultado das rodadas de disponibilidade de áreas da ANM, todas as UFs (cerca de 31,8 mil linhas), com nome e CPF/CNPJ mascarado dos vencedores, como a ANM publica | radar do site (`Squad 3/backend/radar_api.py`, que filtra Goiás) | **Manter.** Registrar link e data de acesso. Se um dia mudar de lugar, trocar `ROUNDS_PATH` no mesmo commit. |
| `Substancia.txt` | 17 KB | 10/09 (conta compartilhada) | dicionário de substâncias da ANM (código e nome, em Windows-1252) | `Squad 3/database/load_anm.py` | **Manter.** Se mudar de lugar, trocar `SUBSTANCES` e rodar `test_load_anm`. |
| `PRODUCAO CORRIGIDA LUCAS V1.xlsx`, `PRODUCAO BRUTA CORRIGIDA LUCAS V1.xlsx` e `ARRECADAÇÃO CORRIGIDA LUCAS V1.xlsx` | 0,6 / 0,8 / 3,5 MB | 03/09 (conta compartilhada) | AMB (beneficiada e bruta) e CFEM 2022–2026 "corrigidas" pelo Estudante 2, uma aba cada; o repositório não diz o que foi corrigido | banco do site, pelo importador (regra `*CORRIGIDA*.xlsx` em `ingestion/policy.json`) | **Decisão do Lucas.** Proposta: pasta do Estudante 2, com um LEIA-ME que diga de qual arquivo da ANM cada planilha partiu e o que mudou. |
| `Base_Mineracao_Goias_Producao_Energia_2023_2026.xlsx` | 0,8 MB | 28/08 (Eliel) | primeira base exploratória, anterior à base consolidada (abas Resumo, Base_consolidada, Producao_empresas, CFEM_detalhe, CCEE_consumo, Projetos_existentes, Fontes e QA) | banco do site, pelo importador (três regras próprias em `ingestion/policy.json`) | Manter até o Squad 3 confirmar se o site ainda usa. Depois, mover para uma pasta de versões exploratórias, junto com as regras do importador. |
| `Panorama Mineracao Goias.html` | 3,4 MB | 27/08 (Eliel) | painel exploratório em HTML | nenhum código | Mover para a pasta de versões exploratórias. |
| `GO.kmz` | 10,3 MB (um `doc.kml` de 88,5 MB) | 10/09 (conta compartilhada) | exportação KMZ da ANM (documento "Dados ANM"), provavelmente as poligonais do SIGMINE em Goiás | nenhum código | Confirmar origem e data com quem enviou. A base usa o shapefile `GO.zip`, que já está em `Dados brutos/ANM - SIGMINE/`; se o KMZ for a mesma camada, registrar como redundante e decidir em grupo se continua no repositório. |
| `SQUAD1_PLANEJAMENTO.md` | 19 KB | 27/08 (Eliel) | planejamento e roadmap do Squad 1 | citado no `STATUS_SQUAD1_ENTREGA1.md` | Mover para `Squad 1/`, ao lado do quadro de entradas e saídas e do STATUS. |

## Estrutura proposta

```
Squad 1/
├── Bases consolidadas/               Estudante 1 — base consolidada (pronto)
├── Dados brutos/                     Estudante 1 — arquivos das fontes, uma pasta por fonte (pronto)
├── dados/                            só o que o código do Squad 3 lê: CCEE/, ResultadoRodadaDisponibilidade (1).csv e Substancia.txt
├── Radar de Projetos/                Estudante 2 — planilhas "LUCAS V1" com LEIA-ME e o radar v1 (proposta)
├── Dados faltantes e estimativas/    Estudante 3 — matriz de completude e método (proposta)
├── Versões exploratórias/            base de 28/08 e painel HTML (proposta)
├── QUADRO_ENTRADAS_SAIDAS.md
├── STATUS_SQUAD1_ENTREGA1.md
└── SQUAD1_PLANEJAMENTO.md            (proposta)
```

## Como mover, quando o grupo decidir

1. Um commit por conjunto de arquivos, com `git mv`, para manter o histórico.
2. No mesmo commit, atualizar tudo o que cita o caminho antigo: procurar o nome do arquivo no repositório inteiro (código do Squad 3,
   testes, `ingestion/`, READMEs e o STATUS).
3. Se o arquivo é lido pelo Squad 3, rodar `test_web`, `test_radar_api` e `test_load_anm` e esperar o CI "Validar plataforma web" passar
   numa branch antes de levar ao `main`.
4. Depois do `main`, conferir em `/api/public/summary` que o importador recarregou os arquivos. O banco do site guarda o caminho de cada
   arquivo (ver a consulta de exemplo em `ingestion/README.md`), então mover muda o caminho registrado lá.

## Quem decide

| Ponto | Quem |
|---|---|
| Planilhas "LUCAS V1" e a pasta do Estudante 2 | Lucas (Estudante 2) |
| Base exploratória de 28/08 e as regras do importador | Squad 3, com o Eliel |
| `GO.kmz` | quem enviou, com o grupo |
| Pasta do Estudante 3, versões exploratórias e `SQUAD1_PLANEJAMENTO.md` | Squad 1 |
