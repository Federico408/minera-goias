# -*- coding: utf-8 -*-
"""Aba 04 -- Projetos: CAMADA ANM do Radar de Projetos (evidência jurídico-minerária de projetos que ainda não produzem).

O Radar de Projetos completo é entrega do Squad 1 / Estudante 2 (guia: ANM Cadastro Mineiro/SIGMINE são fonte
obrigatória de "situação jurídica/minerária e sinais de pesquisa/desenvolvimento"; capacidade, CAPEX, cronograma e as
classes definido/construção/expansão dependem de RI, CVM e SEMAD). Esta aba entrega a parte que sai das fontes do
Squad 1, com IDs estáveis e campos corporativos VAZIOS de propósito ("a ausência de informação deve permanecer explícita").

Pente fino que definiu as regras (12/09/2026):
  - universo: processos de GO que não produzem mas estão em estágio de desenvolvimento (categorias da Base 4):
    2_lavra_sem_cfem_recente (2.131), 4_pre_lavra (1.440), 6_requerimento_licenc_garimpeira (1.944). Pesquisa (9.167)
    fica fora -- processo de pesquisa não é projeto (guia, seção 9) -- e operação ativa já está na 03;
  - 'Situação' do Cadastro Mineiro é "Sim" (ativo) em 100% das linhas dos 12 arquivos que têm o campo: os dados
    abertos só publicam processos ativos, então ela não separa projeto vivo de morto;
  - o último evento do SIGMINE separa: 294 tipos nos candidatos, muitos TERMINAIS (indeferimento, desistência, baixa
    da transcrição, caducidade, renúncia, área apta para disponibilidade, plano de fechamento de mina). Cada tipo é
    classificado na aba 04b; processo com evento terminal não vira projeto;
  - processos contíguos (<= 100 m) do mesmo titular e mineral são o mesmo empreendimento (5.515 -> ~4.300 com os
    terminais); o project_id vem do processo-âncora (o de estágio mais avançado);
  - só o último evento está nos dados abertos: o histórico completo (licença ambiental já obtida, PAE analisado) está
    nos microdados do SCM (ProcessoEvento.txt), não baixados.
"""
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

import geopandas as gpd
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
from caminhos import BASE, TMP, arquivo, data_acesso  # caminhos relativos ao projeto — ver caminhos.py
GPKG = f"{BASE}/outputs/mapas/minera_goias_mapas_v1.gpkg"
CRS_AREA = "+proj=aea +lat_0=-32 +lon_0=-60 +lat_1=-5 +lat_2=-42 +x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs"
TOL_M = 100      # processos do mesmo titular e mineral a até 100 m viram um projeto
ADJ_M = 500      # operação ativa do mesmo titular e mineral a até 500 m -> candidato a expansão (brownfield)
JANELA_ANOS = 3  # evento na ANM mais antigo que isto -> processo parado

FONTES = {  # url_recurso e arquivos iguais aos da 07 (a governança confere linha a linha)
    "SRC_ANM_SIGMINE": ("https://dadosabertos.anm.gov.br/SIGMINE/PROCESSOS_MINERARIOS/GO.zip", ["dados/ANM/sigmine/GO.zip"]),
    "SRC_ANM_CADASTRO": ("https://dadosabertos.anm.gov.br/SCM/<arquivo>.csv — 13 arquivos (Alvara_de_Pesquisa, Cessoes_de_Direitos, Guia_de_Utilizacao_Autorizada, "
                         "Licenciamento, PLG, Portaria_de_Lavra, …)", ["dados/ANM/cadastro_mineiro/*.csv"]),
    "SRC_ANM_CFEM": ("https://dadosabertos.anm.gov.br/CFEM/CFEM_Arrecadacao_2022_2026.csv", ["dados/ANM/cfem/CFEM_Arrecadacao_2022_2026_GO.csv"]),
    "SRC_IBGE_MALHA_2025": ("https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/UFs/GO/GO_Municipios_2025.zip",
                            ["dados/IBGE/GO_Municipios_2025.zip"]),
}
DATA = {sid: data_acesso(pads)
        for sid, (_, pads) in FONTES.items()}
IDS_FONTE = list(FONTES)
REF = pd.Timestamp(DATA["SRC_ANM_SIGMINE"])  # recência medida contra a data do arquivo do SIGMINE, não contra "hoje"
RESPONSAVEL = "Squad 1 / Estudante 1 — checagens automáticas do pipeline (ver 14b)"

CAND = {"2_lavra_sem_cfem_recente", "4_pre_lavra", "6_requerimento_licenc_garimpeira"}
ESTAGIO = {  # fase atual no SIGMINE -> (estágio, ordem de avanço)
    "CONCESSÃO DE LAVRA": ("lavra_autorizada_sem_producao", 4), "LICENCIAMENTO": ("lavra_autorizada_sem_producao", 4),
    "LAVRA GARIMPEIRA": ("lavra_autorizada_sem_producao", 4), "REGISTRO DE EXTRAÇÃO": ("lavra_autorizada_sem_producao", 4),
    "REQUERIMENTO DE LAVRA": ("requerimento_de_lavra", 3),
    "DIREITO DE REQUERER A LAVRA": ("direito_de_requerer_lavra", 2),
    "REQUERIMENTO DE LICENCIAMENTO": ("requerimento_de_licenciamento_ou_lavra_garimpeira", 1),
    "REQUERIMENTO DE LAVRA GARIMPEIRA": ("requerimento_de_licenciamento_ou_lavra_garimpeira", 1),
    "REQUERIMENTO DE REGISTRO DE EXTRAÇÃO": ("requerimento_de_licenciamento_ou_lavra_garimpeira", 1),
}
# classificação do tipo de evento, na ordem (a primeira regra que casa vence); a lista de tipos com a classe está na 04b
REGRAS_EVENTO = [
    # exceções revistas uma a uma na 04b: desfazem uma decisão ou não atingem o direito principal do processo
    ("andamento", r"TORNA S/EFEITO"), ("andamento", r"RECURSO PROVIDO"), ("andamento", r"OPÇÃO REGIME"), ("andamento", r"GUIA UTILIZAÇÃO"),
    ("andamento", r"DESISTÊNCIA PARCIAL"), ("andamento", r"ARQUIVAMENTO AUTO DE EMBARGO"),
    ("encerramento", r"RECONSIDERAÇÃO NEGAD"), ("disputa", r"INSTAURA PROC ADM|SANCIONADOR"),
    ("encerramento", r"INDEFER"), ("encerramento", r"DESIST"), ("encerramento", r"BAIXA TRANSCRI"), ("encerramento", r"CADUC"),
    ("encerramento", r"RENÚNCIA|RENUNCIA"), ("encerramento", r"NÃO CONHECE"), ("encerramento", r"RECURSO NEGADO"),
    ("encerramento", r"APTA PARA DISPONIBILIDADE|LIBERADA PARA EDITAL|ÁREA DESCARTADA"), ("encerramento", r"FECHAMENTO DE MINA"),
    ("encerramento", r"EXTIN|NULIDADE|CANCELAMENTO"), ("encerramento", r"ARQUIVAMENTO"),
    ("disputa", r"RECURSO|RECONSIDERA|DEFESA|DECISÃO JUDICIAL|IMPUGNA|(?<!EVENTUAL )CONTESTA"),
    ("licenciamento_ambiental", r"LICENÇA AMBIENTAL|ÓRGÃO AMBIENTAL"),
]


def tipo_evento(txt):
    """Descrição do evento sem o código numérico e sem a data ('365 - REQ LAV/CUMPRIMENTO EXIGÊNCIA PROTOC EM 08/09/2026')."""
    t = re.sub(r"^\d+\s*-\s*", "", str(txt))
    return re.sub(r"\s+(EM|PUBL?|PROTOC|HOM|EFETUADO)\b.*$", "", t).strip()


def classe_evento(tipo):
    for classe, padrao in REGRAS_EVENTO:
        m = re.search(padrao, tipo.upper())
        if m:
            return classe, m.group(0)
    return "andamento", ""


def data_evento(txt):
    m = re.search(r"EM (\d{2}/\d{2}/\d{4})\s*$", str(txt))
    return pd.to_datetime(m.group(1), format="%d/%m/%Y", errors="coerce") if m else pd.NaT


def maturidade(estagio, recente, disputa, ambiental):
    """Teto da camada ANM = provável; definido/construção/expansão exigem RI, CVM ou SEMAD (Estudante 2)."""
    if disputa:
        return "sinal", "último evento do processo-âncora é recurso, defesa ou reconsideração: situação em disputa"
    if not recente:
        return "sinal", f"nenhum evento na ANM nos {JANELA_ANOS} anos anteriores ao arquivo do SIGMINE"
    if estagio == "lavra_autorizada_sem_producao":
        return "provável", "título de lavra concedido, sem CFEM em 2024–2026 e com evento recente na ANM"
    if estagio in ("requerimento_de_lavra", "direito_de_requerer_lavra"):
        return "possível", "pesquisa aprovada e lavra requerida ou a requerer, com evento recente na ANM"
    if ambiental:
        return "possível", "requerimento de licenciamento/lavra garimpeira recente com evento de licenciamento ambiental"
    return "sinal", "requerimento de licenciamento/lavra garimpeira recente, sem evento de licenciamento ambiental"


md = json.load(open(f"{TMP}/_min_def.json", encoding="utf-8"))
_ordem = sorted(md.items(), key=lambda kv: (kv[1][1], kv[1][0]))
NOME2ID = {v[0]: f"MIN_{i + 1:03d}" for i, (k, v) in enumerate(_ordem)}


def canon(p):
    a, b = str(p).split("/", 1)
    return (re.sub(r"\D", "", a).lstrip("0") or "0") + "/" + re.sub(r"\D", "", b)[:4]


rp = pd.read_csv(arquivo("dados/ANM/cadastro_mineiro/Relatorio_de_Pesquisa_Aprovado.csv"), sep=",", encoding="cp1252", encoding_errors="replace",
                 dtype=str, keep_default_na=False, engine="python", on_bad_lines="skip")
RELATORIO_APROVADO = {canon(p) for p in rp["Processo"]}

# ---------------------------------------------------------------------------
# 1) universo e classificação dos eventos
# ---------------------------------------------------------------------------
g = gpd.read_file(GPKG, layer="processos_minerarios_go", engine="pyogrio").to_crs(CRS_AREA)
g["chave_titular"] = [c if c else "NOME:" + re.sub(r"\s+", " ", str(t)).strip().upper() for c, t in zip(g["company_id"], g["titular_sigmine"])]
g["chave"] = g["chave_titular"] + "|" + g["mineral_principal"].fillna("").astype(str)
cand = g[g["categoria_mapa"].isin(CAND)].copy()
faltam = set(cand["fase_atual"]) - set(ESTAGIO)
if faltam:
    raise SystemExit(f"fases sem estágio definido: {faltam}")
cand["tipo_evento"] = cand["ultimo_evento"].map(tipo_evento)
cand[["classe_evento", "palavra_chave"]] = [classe_evento(t) for t in cand["tipo_evento"]]
cand["data_evento"] = cand["ultimo_evento"].map(data_evento)
cand["estagio"] = cand["fase_atual"].map(lambda f: ESTAGIO[f][0])
cand["ordem"] = cand["fase_atual"].map(lambda f: ESTAGIO[f][1])
vivos = cand[cand["classe_evento"] != "encerramento"].reset_index(drop=True)
print(f"universo: {len(cand)} processos; com evento terminal: {len(cand) - len(vivos)}; vivos: {len(vivos)}")

# ---------------------------------------------------------------------------
# 2) agrupamento: processos contíguos do mesmo titular e mineral = um projeto
# ---------------------------------------------------------------------------
pai = list(range(len(vivos)))


def raiz(i):
    while pai[i] != i:
        pai[i] = pai[pai[i]]
        i = pai[i]
    return i


buf = gpd.GeoDataFrame(geometry=vivos.geometry.buffer(TOL_M / 2), crs=CRS_AREA)
pares = gpd.sjoin(buf, buf, predicate="intersects")
for i, j in zip(pares.index, pares["index_right"]):
    if i < j and vivos.at[i, "chave"] == vivos.at[j, "chave"]:
        pai[raiz(i)] = raiz(j)
vivos["grupo"] = [raiz(i) for i in range(len(vivos))]
ativas = g[g["categoria_mapa"] == "1_operacao_ativa"][["operation_id", "chave", "geometry"]].reset_index(drop=True)

linhas, eventos_por_processo = [], {}
for _, grp in vivos.groupby("grupo"):
    grp = grp.sort_values(["ordem", "data_evento", "processo_anm"], ascending=[False, False, True])
    a = grp.iloc[0]
    uniao = grp.geometry.union_all()
    pt = gpd.GeoSeries([uniao.representative_point()], crs=CRS_AREA).to_crs(4674).iloc[0]
    adj = ativas[(ativas["chave"] == a["chave"]) & ativas.geometry.intersects(uniao.buffer(ADJ_M))]
    ult = grp.sort_values("data_evento", ascending=False).iloc[0]
    recente = pd.notna(grp["data_evento"].max()) and grp["data_evento"].max() >= REF - pd.DateOffset(years=JANELA_ANOS)
    disputa = a["classe_evento"] == "disputa"
    ambiental = bool((grp["classe_evento"] == "licenciamento_ambiental").any())
    classe, criterio = maturidade(a["estagio"], recente, disputa, ambiental)
    muns = sorted(set(grp["municipio_nome"].dropna()))
    razao = a["razao_social"] if isinstance(a["razao_social"], str) and a["razao_social"] else a["titular_sigmine"]
    mineral = a["mineral_principal"] or None
    obs = []
    if len(muns) > 1:
        obs.append("processos em mais de um município: " + ", ".join(muns))
    if not a["company_id"]:
        obs.append("titular sem ponte com o Cadastro Mineiro (nome do SIGMINE, sem company_id)")
    if not mineral:
        obs.append("processo sem substância no SIGMINE")
    if len(adj):
        obs.append(f"a até {ADJ_M} m de operação ativa do mesmo titular e mineral: candidato a expansão — confirmar com RI/SEMAD")
    linhas.append(dict(
        project_id="PRJ_" + a["processo_anm"].replace("/", "_"),
        nome_projeto=" — ".join(x for x in (mineral or "sem substância", razao, a["municipio_nome"]) if x),
        company_id=a["company_id"] or None, razao_social=razao, mineral_id=NOME2ID.get(mineral) if mineral else None, mineral_name=mineral,
        municipality_id=a["municipality_id"], municipality_name=a["municipio_nome"], latitude=round(pt.y, 6), longitude=round(pt.x, 6),
        tipo_projeto="brownfield_adjacente_a_operacao" if len(adj) else "sem_operacao_adjacente", estagio=a["estagio"],
        classificacao_maturidade=classe, criterio_classificacao=criterio,
        capacidade_t_ano=None, capex_brl=None, ano_previsto_entrada=None,
        processo_ancora=a["processo_anm"], qtd_processos=len(grp), processos_anm="; ".join(sorted(grp["processo_anm"])),
        operation_ids="; ".join(sorted(grp["operation_id"])), area_ha=round(float(grp["area_ha_calculada"].astype(float).sum()), 2),
        relatorio_final_aprovado="sim" if grp["processo_anm"].isin(RELATORIO_APROVADO).any() else "não",
        evento_licenciamento_ambiental="sim" if ambiental else "não", operacao_adjacente="; ".join(sorted(adj["operation_id"])) or None,
        data_evidencia=ult["data_evento"].strftime("%Y-%m-%d") if pd.notna(ult["data_evento"]) else None, ultimo_evento=ult["ultimo_evento"],
        valor_observado_estimado="calculado", status_validacao="pendente_evidencia_corporativa", responsavel_validacao=RESPONSAVEL,
        source_id="; ".join(IDS_FONTE), source_url="; ".join(FONTES[i][0] for i in IDS_FONTE), data_acesso="; ".join(DATA[i] for i in IDS_FONTE),
        periodo_referencia=f"situação dos processos no SIGMINE de {DATA['SRC_ANM_SIGMINE']}", tipo_fonte="oficial",
        observacao="; ".join(obs) or None))
ORDEM_CLASSE = {"provável": 0, "possível": 1, "sinal": 2}
linhas.sort(key=lambda r: (ORDEM_CLASSE[r["classificacao_maturidade"]], -r["area_ha"], r["project_id"]))
ids = Counter(r["project_id"] for r in linhas)
if any(n > 1 for n in ids.values()):
    raise SystemExit(f"project_id repetido: {[k for k, n in ids.items() if n > 1][:5]}")

# ---------------------------------------------------------------------------
# 3) auditoria 04b: cada tipo de último evento, com a classe atribuída
# ---------------------------------------------------------------------------
aud = []
for (tipo, classe, chave), sub in cand.groupby(["tipo_evento", "classe_evento", "palavra_chave"]):
    aud.append(dict(tipo_evento=tipo, classe_evento=classe, palavra_chave=chave or None, processos=len(sub),
                    fases="; ".join(f"{f} ({n})" for f, n in Counter(sub["fase_atual"]).most_common(3)),
                    exemplo_processo=sorted(sub["processo_anm"])[0], vira_projeto="não" if classe == "encerramento" else "sim"))
ORDEM_EV = {"encerramento": 0, "disputa": 1, "licenciamento_ambiental": 2, "andamento": 3}
aud.sort(key=lambda r: (ORDEM_EV[r["classe_evento"]], -r["processos"], r["tipo_evento"]))

pesquisa = g[g["categoria_mapa"] == "5_pesquisa"]
resumo = dict(
    universo=len(cand), universo_por_categoria=Counter(cand["categoria_mapa"]), terminais=int((cand["classe_evento"] == "encerramento").sum()),
    processos_vivos=len(vivos), projetos=len(linhas), por_classe=Counter(r["classificacao_maturidade"] for r in linhas),
    por_estagio=Counter(r["estagio"] for r in linhas), brownfield=sum(1 for r in linhas if r["tipo_projeto"] == "brownfield_adjacente_a_operacao"),
    com_relatorio_aprovado=sum(1 for r in linhas if r["relatorio_final_aprovado"] == "sim"),
    com_licenciamento_ambiental=sum(1 for r in linhas if r["evento_licenciamento_ambiental"] == "sim"),
    tipos_evento=len(aud), tipos_por_classe=Counter(r["classe_evento"] for r in aud),
    pesquisa_fora=len(pesquisa), pesquisa_minerais=Counter(pesquisa["mineral_principal"]).most_common(6),
    data_sigmine=DATA["SRC_ANM_SIGMINE"], janela_anos=JANELA_ANOS, tol_m=TOL_M, adj_m=ADJ_M,
    provaveis_por_mineral=Counter(r["mineral_name"] for r in linhas if r["classificacao_maturidade"] == "provável").most_common(10),
    possiveis_por_mineral=Counter(r["mineral_name"] for r in linhas if r["classificacao_maturidade"] == "possível").most_common(10))
for nome, obj in (("_projetos_04.json", dict(colunas=list(linhas[0].keys()), linhas=[list(r.values()) for r in linhas])),
                  ("_projetos_04b.json", dict(colunas=list(aud[0].keys()), linhas=[list(r.values()) for r in aud])),
                  ("_projetos_04_resumo.json", resumo)):
    with open(f"{TMP}/{nome}", "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=None if nome != "_projetos_04_resumo.json" else 1, default=str)
print(json.dumps(resumo, ensure_ascii=False, default=str))
