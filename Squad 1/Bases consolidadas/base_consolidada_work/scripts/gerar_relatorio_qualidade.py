# -*- coding: utf-8 -*-
"""Relatório de qualidade da base consolidada, num documento só: faltantes, duplicidades, divergências e unidades.

    python base_consolidada_work/scripts/gerar_relatorio_qualidade.py                 # usa a planilha mais recente de documentacao/
    python base_consolidada_work/scripts/gerar_relatorio_qualidade.py <planilha.xlsx>

Lê só a planilha (abas 14b, 14, 08, 09b, 09c, 01b, 02b, 05b, 06b e 13b) e grava documentacao/relatorio_qualidade.md. Nenhum número é
digitado: rodar de novo depois de gerar uma versão nova da planilha atualiza o relatório. As divergências são registradas, não corrigidas.
"""
import glob
import os
import re
import sys
from collections import Counter, defaultdict

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")
from caminhos import BASE  # caminhos relativos ao projeto — ver caminhos.py

HDR = 4
if len(sys.argv) > 1:
    PLANILHA = sys.argv[1]
else:
    versoes = [(int(m.group(1)), p) for p in glob.glob(os.path.join(BASE, "documentacao", "prototipo_bases_consolidadas_v*.xlsx"))
               if (m := re.search(r"_v(\d+)\.xlsx$", p))]
    PLANILHA = max(versoes)[1]
VERSAO = "v" + re.search(r"_v(\d+)\.xlsx$", PLANILHA).group(1)
SAIDA = os.path.join(os.path.dirname(PLANILHA), "relatorio_qualidade.md")

wb = openpyxl.load_workbook(PLANILHA, read_only=True)


def ler(aba):
    it = wb[aba].iter_rows(min_row=HDR, values_only=True)
    cab = [c for c in next(it) if c is not None]
    return [dict(zip(cab, r)) for r in it if r and r[0] is not None]


def celula(v, n=180):
    s = re.sub(r"\s+", " ", str("" if v is None else v)).replace("|", "/").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


num = lambda x: f"{x:,}".replace(",", ".")


def limite(v):
    if not v:
        return "—"
    return num(round(v)) if v >= 10 else f"{v:.3f}".replace(".", ",")


V = ler("14b_validacoes_governanca")
D = ler("14_dicionario_dados")
F = ler("08_fato_producao_energia")
Q9B = ler("09b_auditoria_cfem_quantidade")
Q9C = ler("09c_alertas_cfem_processo")
X01, X02, X05, X06 = ler("01b_crosswalk_pente_fino"), ler("02b_crosswalk_empresas"), ler("05b_crosswalk_municipios"), ler("06b_crosswalk_recmin")
A13 = ler("13b_auditoria_mapas")


def validacao(padrao):
    return next((v for v in V if re.search(padrao, str(v["verificacao"]), re.I)), None)


st = Counter(v["status"] for v in V)
L = [f"# Relatório de qualidade — Base Mineral de Goiás ({VERSAO})", "",
     f"Gerado por `gerar_relatorio_qualidade.py` a partir de `{os.path.basename(PLANILHA)}`. Todos os números saem da planilha; o detalhe "
     "de cada item está na aba citada. Regra do projeto: **divergências são registradas, não corrigidas** — nada aqui foi apagado ou "
     "ajustado na fonte.", "",
     "## 1. Resumo", "",
     f"- **Validações automáticas (aba 14b):** {len(V)} checagens — {st.get('OK', 0)} OK e {st.get('ALERTA', 0)} ALERTA. Os alertas são de dado, "
     "sinalizados de propósito; a lista completa está na seção 7.",
     f"- **Fato longo (aba 08):** {num(len(F))} linhas, uma por célula numérica da fonte; status: "
     + "; ".join(f"{k} {num(n)}" for k, n in Counter(r["status_validacao"] for r in F).most_common()) + ".",
     f"- **Quantidades da CFEM fora da soma de toneladas (aba 09b):** {num(len(Q9B))} linhas (o R$ continua somado).",
     f"- **Processos com quantidade implausível na CFEM (aba 09c):** {num(len(Q9C))} processo-anos, mantidos na soma e sinalizados.", ""]
for v in V:
    if v["status"] != "OK":
        L.append(f"  - ALERTA — {celula(v['verificacao'], 140)}: n = {v['n']}.")
L.append("")

# 2) faltantes
L += ["## 2. Faltantes", "",
      "Campos das abas de dados com metade ou mais das linhas vazias (aba 14, coluna `pct_vazio`). Vazio não é zero: significa que a fonte "
      "não informa ou que o campo não se aplica à linha — a descrição de cada campo explica.", "",
      "| Aba | Campo | % vazio | O que o campo é |", "|---|---|---:|---|"]
for r in sorted((r for r in D if r.get("status_aba") != "auditoria" and r.get("aba") != "07_dim_fontes"
                 and isinstance(r.get("pct_vazio"), (int, float)) and r["pct_vazio"] >= 50),
                key=lambda r: (r["aba"], -r["pct_vazio"])):
    L.append(f"| `{r['aba']}` | `{r['campo']}` | {str(r['pct_vazio']).replace('.', ',')} | {celula(r.get('descricao'), 160)} |")
L += ["", "Vazios esperados: `capacidade_t_ano`, `capex_brl` e `ano_previsto_entrada` da aba 04 dependem de evidência corporativa (Estudante 2); "
      "`metodo_estimacao` fica vazio nas linhas observadas; na aba 06, a maioria dos campos descritivos do RECMIN vem vazia da própria fonte.", ""]

# 3) duplicidades
L += ["## 3. Duplicidades", "", "Cada linha de dimensão tem um ID único:", "", "| Aba | ID | Linhas | Valores distintos |", "|---|---|---:|---:|"]
for aba, chave in [("01_dim_minerais", "mineral_id"), ("02_dim_empresas", "company_id"), ("03_dim_operacoes", "operation_id"),
                   ("04_dim_projetos", "project_id"), ("05_dim_municipios", "municipality_id"), ("06_dim_ocorrencias_geologicas", "occurrence_id"),
                   ("07_dim_fontes", "source_id")]:
    ids = [r.get(chave) for r in ler(aba)]
    L.append(f"| `{aba}` | `{chave}` | {num(len(ids))} | {num(len(set(ids)))} |")
L += [f"| `08_fato_producao_energia` | `fato_id` | {num(len(F))} | {num(len({r['fato_id'] for r in F}))} |", ""]
for padrao, rotulo in [(r"^IDs fora do padrão", "IDs no padrão do Contrato de Dados"), (r"^Integridade referencial", "Chaves das consultas → dimensões"),
                       (r"mesma tonelagem", "Produção repetida no AMB"), (r"mesma célula da fonte", "Células da fonte no fato longo")]:
    v = validacao(padrao)
    if v:
        L.append(f"- **{rotulo}** ({v['status']}, n = {v['n']}): {celula(v['verificacao'], 160)} — {celula(v['resultado'], 420)}")
tipos02 = Counter(r["tipo_correspondencia"] for r in X02)
L += [f"- **Titulares (aba 02b):** " + "; ".join(f"{celula(k, 90)}: {n}" for k, n in tipos02.most_common()) + ". Nomes iguais com raízes de CNPJ "
      "diferentes NÃO são fundidos.", ""]

# 4) divergências entre fontes
L += ["## 4. Divergências entre fontes", ""]
v = validacao(r"^Plausibilidade")
if v:
    L += [f"- **Quantidade comercializada da CFEM × produção do AMB** ({v['status']}, {v['n']} mineral-anos fora de 0,05–2×): a quantidade da CFEM "
          "não serve como proxy de produção. " + celula(v["resultado"], 500), ""]
sev = Counter(r["severidade"] for r in Q9C)
L += [f"- **Processos da aba 09c:** {len(Q9C)} processo-anos ({'; '.join(f'{k}: {n}' for k, n in sev.most_common())}). Os de maior razão:", "",
      "| Mineral | Ano | Processo | CFEM (t) | Limite do AMB (t) | Razão | Critério | Severidade |", "|---|---:|---|---:|---:|---:|---|---|"]
for r in sorted(Q9C, key=lambda r: -(r.get("razao") or 0))[:12]:
    razao = f"{r['razao']:,.1f}×".replace(",", "X").replace(".", ",").replace("X", ".") if r.get("razao") else "—"
    L.append(f"| {r['mineral_name']} | {r['year']} | {r['processo_anm']} | {num(round(r['cfem_t_processo'] or 0))} | "
             f"{limite(r.get('amb_total_uf_t'))} | {razao} | {celula(r.get('criterio'), 60)} | {r['severidade']} |")
fronteira = [r for r in X05 if r["tipo_correspondencia"] == "outro_estado_em_processo_de_fronteira"]
sem02 = Counter(r["tipo_correspondencia"] for r in X02 if "sem titular" in str(r["tipo_correspondencia"]) or "sem " in str(r["tipo_correspondencia"]))
L += ["", f"- **Municípios de outro estado em processos de fronteira (aba 05b):** {len(fronteira)} municípios citados no Cadastro Mineiro junto "
          "com municípios de Goiás; ficam fora da dimensão de municípios, e a linha do processo é mantida pelo município goiano.",
      f"- **Titulares sem correspondência entre fontes (aba 02b):** " + "; ".join(f"{celula(k, 90)}: {n}" for k, n in sem02.items()) + ".",
      "- **Mapas (aba 13b):** verificações com ocorrência:", ""]
grupos = defaultdict(list)  # as discordâncias processo a processo viram um item só
for r in A13:
    try:
        n = int(float(r["n"] or 0))
    except (TypeError, ValueError):
        n = 0
    if n:
        grupos[(r["camada"], str(r["verificacao"]).split(" — processo")[0])].append((n, r))
for (camada, verif), itens in grupos.items():
    r0 = itens[0][1]
    if len(itens) == 1:
        L.append(f"  - `{camada}` — {celula(verif, 120)} (n = {num(itens[0][0])}): {celula(r0['decisao'], 220)}")
    else:
        exemplos = ", ".join(str(r["verificacao"]).split(" — processo ")[-1] for _, r in itens[:6])
        L.append(f"  - `{camada}` — {celula(verif, 120)}: {len(itens)} processos (ex.: {exemplos}). {celula(r0['decisao'], 200)}")
L.append("")

# 5) unidades
unid = Counter(r["unidade_original"] for r in F)
motivos = Counter(r["motivo"] for r in Q9B)
por_min = Counter(r["mineral_name"] for r in Q9B)
L += ["## 5. Unidades", "",
      "Nada é somado entre unidades diferentes. Massa (kg, g e quilate) vira t pela regra escrita na linha da aba 08; volume (m³, l) e área (m²) ficam à parte "
      "(`cfem_qtd_outras_unidades` na aba 09). Unidades na fonte (aba 08, `unidade_original`):", "",
      "| Unidade | Linhas |", "|---|---:|"]
L += [f"| `{k}` | {num(n)} |" for k, n in unid.most_common()]
L += ["", f"`-` é a unidade que o AMB usa no contido quando ela não se aplica: as {num(unid.get('-', 0))} linhas com valor diferente de zero "
          "ficam na 08 como estão na fonte (as iguais a zero não viram linha).", "",
      f"Quantidades da CFEM excluídas da soma de toneladas (aba 09b): {len(Q9B)} linhas — "
          + "; ".join(f"{celula(k, 110)}: {n}" for k, n in motivos.most_common()) + ". Por mineral: "
          + ", ".join(f"{k} {n}" for k, n in por_min.most_common()) + ".", ""]

# 6) padronização
L += ["## 6. Padronização de nomes", "",
      f"- **Substâncias (aba 01b):** {len(X01)} grafias das fontes → mineral da ANM; " + "; ".join(f"{k}: {n}" for k, n in Counter(r['tipo_correspondencia'] for r in X01).most_common()) + ".",
      f"- **Municípios (aba 05b):** {len(X05)} grafias → código IBGE; " + "; ".join(f"{k}: {n}" for k, n in Counter(r['tipo_correspondencia'] for r in X05).most_common()) + ".",
      f"- **Substâncias do RECMIN (aba 06b):** {len(X06)} nomes; " + "; ".join(f"{k}: {n}" for k, n in Counter(r['tipo_correspondencia'] for r in X06).most_common()) + ".",
      ""]

# 7) todas as validações
L += ["## 7. Todas as validações automáticas (aba 14b)", "", "| Status | Verificação | n | Resultado |", "|---|---|---:|---|"]
for v in V:
    L.append(f"| {v['status']} | {celula(v['verificacao'], 150)} | {v['n']} | {celula(v['resultado'], 260)} |")
L.append("")
with open(SAIDA, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(L))
print(f"SALVO: {SAIDA} ({len(L)} linhas; {len(V)} validações, {len(Q9C)} processos na 09c, {len(Q9B)} linhas na 09b)")
