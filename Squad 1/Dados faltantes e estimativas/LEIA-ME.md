# Squad 1 / Estudante 3 — Dados faltantes e estimativas (Giovana Dodero)

Entrega em andamento para o prazo de 21/09/2026 (`STATUS_SQUAD1_ENTREGA1.md`, seção 3.3).

| Arquivo | Conteúdo |
|---|---|
| `matriz_completude_v17_eliel.csv` | os 439 campos da aba `14_dicionario_dados` da v17, com % vazio, tipo e descrição |
| `analise_qualidade_lucas_v1.py` | script reproduzível: compara as três planilhas "CORRIGIDA LUCAS V1" com a aba `09` da v17 (recorte Goiás), mede duplicidade, nulos e divergência de unidade |
| `RELATORIO_QUALIDADE_E_CONFORMIDADE_v1.md` | relatório de qualidade das planilhas do Lucas (não coberto pelo relatório do Eliel), proposta de conformidade de unidades e estratégia de dados faltantes |

## Como rodar

Da raiz do repositório, com `pandas` e `openpyxl` instalados:

```bash
python "Squad 1/Dados faltantes e estimativas/analise_qualidade_lucas_v1.py"
```

## Entrada e saída (regra 1 da Entrega Avaliativa)

- **Entrada:** abas `14` e `12` e as planilhas "CORRIGIDA LUCAS V1", de `Squad 1/Bases consolidadas/`
  e `Squad 1/dados/` (Estudantes 1 e 2); consumo da CCEE em `Squad 1/dados/CCEE/`.
- **Saída esperada:** base consolidada com flags `valor_observado_estimado`, `metodo_estimacao` e
  erro/intervalo, para o Squad 2 — ainda a publicar (ver `RELATORIO_QUALIDADE_E_CONFORMIDADE_v1.md`,
  seção 7).

## O que ainda falta (v1 é diagnóstico, não a entrega final)

- Deduplicar a arrecadação e somar os pares de "Gemas" na produção bruta.
- Confirmar com o Lucas a metodologia da coluna de correção monetária.
- Consolidar numa única base com os nomes de campo do Contrato de Dados.
- Tratar a lacuna de coordenadas (457 linhas da aba 12) com o proxy do município de CFEM.
- Demonstrar o pareamento CCEE ↔ operação mineral.
