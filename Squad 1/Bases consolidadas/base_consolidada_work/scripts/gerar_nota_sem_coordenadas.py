# -*- coding: utf-8 -*-
"""Nota ao Squad 2: produção estimada por operação que não tem coordenadas (aba 12), com a lista processo a processo.

    python base_consolidada_work/scripts/gerar_nota_sem_coordenadas.py                 # usa a planilha mais recente de documentacao/
    python base_consolidada_work/scripts/gerar_nota_sem_coordenadas.py <planilha.xlsx>

Grava documentacao/nota_squad2_operacoes_sem_coordenadas.md e documentacao/operacoes_sem_coordenadas.csv. Todos os números saem
da planilha (abas 12, 03 e 07); rodar de novo depois de uma versão nova atualiza a nota.
"""
import csv
import glob
import os
import re
import sys
from collections import Counter, defaultdict

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")
from caminhos import BASE  # caminhos relativos ao projeto — ver caminhos.py

if len(sys.argv) > 1:
    PLANILHA = sys.argv[1]
else:
    PLANILHA = max((int(m.group(1)), p) for p in glob.glob(os.path.join(BASE, "documentacao", "prototipo_bases_consolidadas_v*.xlsx"))
                   if (m := re.search(r"_v(\d+)\.xlsx$", p)))[1]
VERSAO = "v" + re.search(r"_v(\d+)\.xlsx$", PLANILHA).group(1)
PASTA = os.path.dirname(PLANILHA)
wb = openpyxl.load_workbook(PLANILHA, read_only=True)


def ler(aba):
    it = wb[aba].iter_rows(min_row=4, values_only=True)
    cab = [c for c in next(it) if c is not None]
    return [dict(zip(cab, r)) for r in it if r and r[0] is not None]


mi = lambda t: f"{t / 1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
pct = lambda x: f"{x:.1f}".replace(".", ",")
inteiro = lambda x: f"{x:,}".replace(",", ".")
sem_coord = lambda r: r.get("latitude") in (None, "")

R = [r for r in ler("12_interface_squad1_squad2") if r["nivel_agregacao"] == "operacao"]
S = [r for r in R if sem_coord(r)]
na_03 = {r["processo_anm"] for r in ler("03_dim_operacoes")}
DATA_SIGMINE = next((str(r.get("data_arquivo_local") or "") for r in ler("07_dim_fontes") if r["source_id"] == "SRC_ANM_SIGMINE"), "")
anos = sorted({r["year"] for r in R})

# parcela por ano e base (soma entre minerais) e por mineral-ano
tot, sem = defaultdict(float), defaultdict(float)
tot_m, sem_m = defaultdict(float), defaultdict(float)
for r in R:
    t = r["production_t"] or 0
    tot[(r["production_basis"], r["year"])] += t
    tot_m[(r["production_basis"], r["mineral_name"], r["year"])] += t
    if sem_coord(r):
        sem[(r["production_basis"], r["year"])] += t
        sem_m[(r["production_basis"], r["mineral_name"], r["year"])] += t

# processo a processo
P = defaultdict(lambda: dict(rom=0.0, benef=0.0, minerais=set(), anos=set(), titulares=set(), municipios=set(), cfem=0.0))
for r in S:
    e = P[r["processo_anm"]]
    e["rom" if r["production_basis"] == "ROM" else "benef"] += r["production_t"] or 0
    e["minerais"].add(r["mineral_name"])
    e["anos"].add(r["year"])
    e["titulares"].add(str(r["company_id"] or "—"))
    if r.get("municipality_id"):
        e["municipios"].add(str(r["municipality_id"]))
    if r["production_basis"] == "ROM":
        e["cfem"] += r.get("cfem_brl_operacao") or 0
serie = Counter(str(p)[:2] for p in P)
com_mun = sum(1 for r in S if r.get("municipality_id"))

with open(os.path.join(PASTA, "operacoes_sem_coordenadas.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["processo_anm", "minerais", "anos", "production_t_rom_estimada", "production_t_beneficiada_estimada", "company_ids",
                "municipality_ids", "na_aba_03_sigmine", "versao_planilha"])
    for p, e in sorted(P.items(), key=lambda kv: -kv[1]["rom"]):
        w.writerow([p, "; ".join(sorted(e["minerais"])), f"{min(e['anos'])}-{max(e['anos'])}", round(e["rom"], 3), round(e["benef"], 3),
                    "; ".join(sorted(e["titulares"])), "; ".join(sorted(e["municipios"])), "sim" if p in na_03 else "não", VERSAO])

L = [f"# Nota ao Squad 2 — produção estimada sem coordenadas (aba 12, {VERSAO})", "",
     "Gerada por `gerar_nota_sem_coordenadas.py` a partir da planilha; a lista completa está em `operacoes_sem_coordenadas.csv`, na mesma pasta.", "",
     "## O que é", "",
     f"No nível `operacao` da aba `12_interface_squad1_squad2`, a produção observada do AMB em Goiás é aberta por processo pela participação na "
     f"CFEM recolhida. Das {inteiro(len(R))} linhas desse nível, **{inteiro(len(S))} ({pct(100 * len(S) / len(R))}%) não têm `operation_id`, "
     f"`latitude` nem `longitude`**. Elas vêm de {len(P)} processos que recolhem CFEM mas não têm poligonal no SIGMINE de Goiás "
     f"({', '.join(f'{n} da série {k}xxxx' for k, n in serie.most_common())}); "
     + (f"{n_03} deles estão na aba 03." if (n_03 := sum(1 for p in P if p in na_03)) else "nenhum está na aba 03.") + "", "",
     "A produção dessas linhas **não se perde**: o total de cada mineral e ano continua igual ao do estado. Só a localização da operação fica "
     "desconhecida." + (f" {inteiro(com_mun)} das {inteiro(len(S))} linhas trazem o município de arrecadação da CFEM (`municipality_id`)." if com_mun else ""), "",
     "## Quanto pesa", "",
     "Parcela da produção estimada por operação que fica sem coordenadas (soma entre minerais; co-produtos, como ouro e cobre, contam nos dois):", "",
     "| Base | " + " | ".join(str(a) for a in anos) + " |", "|---|" + "---:|" * len(anos)]
for base in ("ROM", "beneficiada"):
    L.append(f"| {base} | " + " | ".join(f"{pct(100 * sem[(base, a)] / tot[(base, a)])}%" if tot[(base, a)] else "—" for a in anos) + " |")
L += ["", "Minerais mais afetados (produção bruta, ROM):", "", "| Mineral | Ano | Sem coordenadas | % do mineral no ano |", "|---|---:|---:|---:|"]
for (base, m, a), v in sorted(((k, v) for k, v in sem_m.items() if k[0] == "ROM"), key=lambda kv: -kv[1])[:14]:
    L.append(f"| {m} | {a} | {mi(v)} Mt | {pct(100 * v / tot_m[(base, m, a)])}% |")
L += ["", "## Maiores processos", "", "| Processo | Minerais | Anos | ROM estimada no período | Titular |", "|---|---|---|---:|---|"]
for p, e in sorted(P.items(), key=lambda kv: -kv[1]["rom"])[:15]:
    L.append(f"| {p} | {', '.join(sorted(e['minerais']))} | {min(e['anos'])}–{max(e['anos'])} | {mi(e['rom'])} Mt | {', '.join(sorted(e['titulares']))} |")
L += ["", "## Por que acontece", "",
      "- Esses processos aparecem na CFEM, mas não no SIGMINE nem no Cadastro Mineiro de Goiás usados na base (arquivo do SIGMINE de "
      f"{DATA_SIGMINE}). Sem poligonal não há coordenada nem município pela geometria, e sem Cadastro não há titular: "
      f"{sum(1 for e in P.values() if e['titulares'] == {'COM_NAO_IDENTIFICADO'})} dos {len(P)} processos ficam em `COM_NAO_IDENTIFICADO`.",
      "- A base não inventa coordenada nem titular (Contrato de Dados: nada é preenchido sem fonte).", "",
      "## Sugestões de uso (a decidir com o Squad 2)", "",
      "1. Para totais do estado por mineral e ano, use o nível `estado` da aba 12, que é observado e não depende de coordenada.",
      "2. Em cálculos por operação ou por território, trate essa parcela como **não localizada**; não a distribua para operações vizinhas.",
      "3. Se precisar de território, use o município de arrecadação da CFEM (aba 08) como localização aproximada, marcada como estimada.",
      "4. No ouro, os processos da série 96xxxx concentram a maior parte: vale confirmar a localização em fonte oficial da ANM antes de atribuir "
      "coordenada.", ""]
with open(os.path.join(PASTA, "nota_squad2_operacoes_sem_coordenadas.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(L))
print(f"SALVO: {os.path.join(PASTA, 'nota_squad2_operacoes_sem_coordenadas.md')} e operacoes_sem_coordenadas.csv "
      f"({len(P)} processos, {len(S)} linhas; com município: {com_mun})")
