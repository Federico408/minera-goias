# -*- coding: utf-8 -*-
"""Aba 06 -- Ocorrências e depósitos minerais de Goiás (RECMIN do SGB), com as chaves do projeto.

Fonte: camada geosgb:ocorrencias_recursos_minerais do WFS oficial do SGB, baixada em 12/09/2026 com autorização do
Eliel (dados/SGB_GeoSGB/recmin/, URL da requisição e sha256 no .metadados.json). Os pacotes GeoSGB que já estavam em
dados/ não têm ocorrências (só geoquímica, litologia, estruturas e afloramentos) -- conferido camada a camada.

Pente fino que definiu as regras (12/09/2026):
  - recorte: a caixa de download traz 2.586 pontos; 1.796 caem dentro de Goiás pela malha do IBGE (fora: MG 705, MT 57,
    DF 17, TO 10, MS 1). 2 pontos dentro de GO dizem UF TO/DF e 22 trazem município diferente da malha (municípios
    desmembrados depois do cadastro) -> vale a malha, a divergência fica registrada;
  - id_ocorrencia é único (1:1 com id_afloramento) -> occurrence_id = OCC_<id_ocorrencia> (ID externo estável do SGB);
  - campos sem informação, fora da aba (evidência recalculada abaixo e na 14b): localizacao_mina = 'Mina subterrânea
    (GPS sem sinal)' em 92% das linhas, inclusive garimpo e 'não explotado'; situacao_garimpo é cópia de situacao_mina em
    100%; sureg e origem têm valor único; geologo não serve ao projeto;
  - 60% têm status e importância 'Indeterminado'; data_cadastro é a data de carga no banco (82% em 2003), não a de
    descoberta -- 'Mina Ativo(a)' é a situação daquele cadastro (só 9 das 177 'minas' estão em operação ativa na ANM hoje);
  - 83% dos pontos foram posicionados em carta 1:250.000 (erro de centenas de metros);
  - substâncias: 79 nomes; 63 ocorrências com mais de uma, em ordem alfabética (o RECMIN não indica a principal) ->
    mineral_ids lista todas. 49 nomes casam com o crosswalk da Base 1; 28 viram sinônimo documentado; Índio e Arsênio
    não têm categoria ANM e ficam sem mineral_id (aba 06b). Nenhum mineral novo: MIN_### não é renumerado.
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
ARQ = "dados/SGB_GeoSGB/recmin/ocorrencias_recursos_minerais_GO.geojson"
META = json.load(open(arquivo("dados/SGB_GeoSGB/recmin/ocorrencias_recursos_minerais_GO.metadados.json"), encoding="utf-8"))
GPKG = f"{BASE}/outputs/mapas/minera_goias_mapas_v1.gpkg"

_b1 = open(f"{BASE}/base_consolidada_work/scripts/build_base1_mineral_ano.py", encoding="utf-8").read()
_ns = {}
exec(_b1.split("# 2) Carregar as fontes")[0], _ns)
norm, RAW2KEY = _ns["norm"], _ns["RAW2KEY"]
md = json.load(open(f"{TMP}/_min_def.json", encoding="utf-8"))
_ordem = sorted(md.items(), key=lambda kv: (kv[1][1], kv[1][0]))
KEY2ID = {k: f"MIN_{i + 1:03d}" for i, (k, _) in enumerate(_ordem)}
NOME = {KEY2ID[k]: v[0] for k, v in md.items()}

FONTES = {  # url_recurso e arquivos iguais aos da 07 (a governança confere linha a linha)
    "SRC_SGB_RECMIN": (META["url_requisicao"], [ARQ]),
    "SRC_IBGE_MALHA_2025": ("https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/UFs/GO/GO_Municipios_2025.zip",
                            ["dados/IBGE/GO_Municipios_2025.zip"]),
    "SRC_ANM_SIGMINE": ("https://dadosabertos.anm.gov.br/SIGMINE/PROCESSOS_MINERARIOS/GO.zip", ["dados/ANM/sigmine/GO.zip"]),
}
DATA = {sid: data_acesso(pads)
        for sid, (_, pads) in FONTES.items()}
IDS_FONTE = list(FONTES)
RESPONSAVEL = "Squad 1 / Estudante 1 — checagens automáticas do pipeline (ver 14b)"

# nomes do RECMIN que não estão no crosswalk da Base 1 -- decididos um a um (aba 06b)
SINONIMOS = {norm(k): v for k, v in {
    "Brita": ("cascalho", "brita = rocha britada (categoria ANM 'Rochas (Britadas) e Cascalho')"),
    "Cromo": ("cromo", "mesma substância"),
    "Água termal": ("agua_mineral_grupo", "água termal é regida pela ANM como água mineral (uso balneário)"),
    "Chumbo": ("chumbo", "mesma substância"),
    "Flúor": ("fluorita_criolita", "o flúor é lavrado como fluorita"),
    "Pirita": ("enxofre", "pirita (sulfeto de ferro) como minério de enxofre"),
    "Berílio": ("berilio", "mesma substância"),
    "Quartzo hialino (Cristal de rocha)": ("quartzo_piezo", "cristal de rocha = quartzo em cristal"),
    "Folhelho carbonoso": ("rocha_ou_material_nc", "rocha sem categoria ANM própria (não é carvão mineral)"),
    "Urânio": ("uranio_radioativos", "mesma substância (monopólio da União, sem lavra privada)"),
    "Fósforo": ("fosfato", "o fósforo é lavrado como fosfato"),
    "Epsomita": ("magnesio", "epsomita = sulfato de magnésio"),
    "Vanádio": ("vanadio", "mesma substância"),
    "Pegmatito": ("rocha_ou_material_nc", "rocha hospedeira, não substância"),
    "Andaluzita": ("cianita_refratarios", "andaluzita é mineral refratário do grupo da cianita"),
    "Rocha ornamental": ("rochas_ornamentais", "mesma categoria (o RECMIN não informa o tipo de uso)"),
    "Crisoprásio": ("geodos_agatas_calcedonia", "crisoprásio é variedade de calcedônia"),
    "Zircônio": ("zirconio", "mesma substância"),
    "Platina": ("platina", "categoria ANM 'Platina (Grupo da)'"),
    "Alumínio": ("aluminio_bauxita", "o alumínio é lavrado como bauxita"),
    "Molibdênio": ("molibdenio", "mesma substância"),
    "Trona": ("minerais_industriais_outros", "carbonato de sódio evaporítico, sem categoria ANM própria"),
    "Silício": ("quartzo_piezo", "o silício vem do quartzo (mesma categoria de QUARTZO no crosswalk da Base 1)"),
    "Tungstênio": ("tungstenio", "mesma substância"),
    "Quartzo fumê": ("gemas", "variedade gemológica de quartzo"),
    "Quartzo citrino": ("gemas", "variedade gemológica de quartzo"),
    "Cálcio": ("calcario", "cálcio lavrado como calcário (calcita)"),
    "Folhelho": ("rocha_ou_material_nc", "rocha sem categoria ANM própria"),
}.items()}
SEM_CATEGORIA = {norm(k): v for k, v in {
    "Índio": "sem categoria ANM: subproduto de zinco/estanho, sem lavra própria",
    "Arsênio": "sem categoria ANM: em geral associado a ouro e sulfetos",
}.items()}
ROCHAS = {"rochas_ornamentais", "rochas_ornamentais_outras", "cascalho", "rocha_ou_material_nc"}
DESCARTADOS = ["localizacao_mina", "situacao_garimpo", "sureg", "origem", "geologo", "datum"]


def partes(s):
    """Substâncias do RECMIN: separadas por vírgula, sem quebrar dentro de parênteses ('Quartzo hialino (Cristal de rocha)')."""
    return list(dict.fromkeys(p.strip() for p in re.split(r";|,(?![^()]*\))", str(s or "")) if p.strip()))


def txt(x):
    """NaN, None ou texto vazio -> None (nulos do GeoJSON podem chegar como NaN, que quebra comparação e a célula do Excel)."""
    if x is None or (isinstance(x, float) and pd.isna(x)) or (isinstance(x, str) and not x.strip()):
        return None
    return x


def mapear(nome):
    k = norm(nome)
    if k in RAW2KEY and RAW2KEY[k]:
        chave = RAW2KEY[k]
        just = "crosswalk da Base 1 (01b)"
        if chave in ROCHAS:
            just += "; rocha sem tipo de uso no RECMIN: categoria padrão da rocha (a 01c usa o uso quando a fonte informa)"
        return chave, "crosswalk_base1", just
    if k in SINONIMOS:
        return SINONIMOS[k][0], "sinonimo_recmin", SINONIMOS[k][1]
    if k in SEM_CATEGORIA:
        return None, "sem_categoria_anm", SEM_CATEGORIA[k]
    return "___", None, None


# ---------------------------------------------------------------------------
# 1) recorte pela malha do IBGE e evidência dos campos descartados
# ---------------------------------------------------------------------------
g = gpd.read_file(arquivo(ARQ))
mun = gpd.read_file(GPKG, layer="municipios_go", engine="pyogrio")
j = gpd.sjoin(g.to_crs(mun.crs), mun[["municipality_id", "municipio_nome", "geometry"]], predicate="within", how="left")
fora = j[j["municipality_id"].isna()]
d = j[j["municipality_id"].notna()].drop(columns="index_right").reset_index(drop=True)
if d["id_ocorrencia"].duplicated().any():
    raise SystemExit("id_ocorrencia repetido dentro de Goiás: occurrence_id deixaria de ser único")
evid = dict(
    localizacao_mina=Counter(d["localizacao_mina"].fillna("(vazio)")).most_common(3),
    situacao_garimpo_igual_situacao_mina=float((d["situacao_mina"].fillna("~") == d["situacao_garimpo"].fillna("~")).mean()),
    motivo_garimpo_igual_motivo_mina=float((d["motivo_inatividade_mina"].fillna("~") == d["motivo_inatividade_garimpo"].fillna("~")).mean()),
    sureg=Counter(d["sureg"].fillna("(vazio)")).most_common(3), origem=Counter(d["origem"].fillna("(vazio)")).most_common(3),
    datum=Counter(d["datum"].fillna("(vazio)")).most_common(3), geologo_distintos=int(d["geologo"].nunique()))
top_loc = evid["localizacao_mina"][0][1] / len(d)
if top_loc < 0.8 or evid["situacao_garimpo_igual_situacao_mina"] < 1.0 or len(evid["sureg"]) > 1 or len(evid["origem"]) > 1:
    raise SystemExit(f"a evidência para descartar campos mudou -- revisar antes de descartar: {evid}")
print(f"RECMIN: {len(g)} pontos baixados; {len(d)} dentro de GO; fora por UF: {dict(Counter(fora['uf']))}")

# ---------------------------------------------------------------------------
# 2) crosswalk das substâncias (100% decidido, senão para)
# ---------------------------------------------------------------------------
subs_linha = [partes(s) for s in d["substancias"]]
cont = Counter(n for ps in subs_linha for n in ps)
MAPA = {n: mapear(n) for n in cont}
sem_decisao = [n for n, v in MAPA.items() if v[0] == "___"]
if sem_decisao:
    raise SystemExit(f"substâncias do RECMIN sem decisão no crosswalk: {sem_decisao}")

# ---------------------------------------------------------------------------
# 3) processos da ANM e projetos da 04 que contêm cada ponto
# ---------------------------------------------------------------------------
proc = gpd.read_file(GPKG, layer="processos_minerarios_go", columns=["operation_id", "processo_anm", "categoria_mapa"], engine="pyogrio")
pj = gpd.sjoin(d[["id_ocorrencia", "geometry"]], proc, predicate="within", how="left")
SOB = {}
for occ, grp in pj.groupby("id_ocorrencia"):
    ok = grp.dropna(subset=["processo_anm"])
    SOB[occ] = (sorted(set(ok["processo_anm"])), sorted(set(ok["operation_id"])), sorted(set(ok["categoria_mapa"])))
p04 = json.load(open(f"{TMP}/_projetos_04.json", encoding="utf-8"))
C4 = {c: i for i, c in enumerate(p04["colunas"])}
PROC2PRJ = {p.strip(): row[C4["project_id"]] for row in p04["linhas"] for p in str(row[C4["processos_anm"]]).split(";")}
coords = defaultdict(list)
for occ, lon, lat in zip(d["id_ocorrencia"], d["longitude"], d["latitude"]):
    coords[(round(lon, 6), round(lat, 6))].append(f"OCC_{int(occ)}")

# ---------------------------------------------------------------------------
# 4) linhas da 06
# ---------------------------------------------------------------------------
linhas = []
for i, r in d.iterrows():
    occ = int(r["id_ocorrencia"])
    ps = subs_linha[i]
    ids = list(dict.fromkeys(KEY2ID[MAPA[n][0]] for n in ps if MAPA[n][0]))
    semcat = [n for n in ps if MAPA[n][0] is None]
    processos, ops, cats = SOB.get(r["id_ocorrencia"], ([], [], []))
    prjs = sorted({PROC2PRJ[p] for p in processos if p in PROC2PRJ})
    obs, alerta = [], False
    if norm(txt(r["municipio"]) or "") != norm(r["municipio_nome"]):
        obs.append(f"município informado no RECMIN: {r['municipio']}; o ponto cai em {r['municipio_nome']} (malha 2025)")
        alerta = True
    if r["uf"] != "GO":
        obs.append(f"UF informada no RECMIN: {r['uf']}; o ponto cai dentro de Goiás")
        alerta = True
    irmaos = [x for x in coords[(round(r["longitude"], 6), round(r["latitude"], 6))] if x != f"OCC_{occ}"]
    if irmaos:
        obs.append("mesma coordenada de " + ", ".join(irmaos))
    if txt(r["motivo_inatividade_garimpo"]) != txt(r["motivo_inatividade_mina"]):
        obs.append(f"motivo de inatividade do garimpo: {r['motivo_inatividade_garimpo']}")
    if semcat:
        obs.append("substância sem categoria ANM: " + ", ".join(semcat))
    dc = r["data_cadastro"]
    data_cad = dc.strftime("%Y-%m-%d") if pd.notna(dc) else None
    linhas.append({k: txt(v) for k, v in dict(
        occurrence_id=f"OCC_{occ}", nome_local=r["toponimia"], mineral_ids="; ".join(ids) or None, mineral_names="; ".join(NOME[x] for x in ids) or None,
        substancias_original=r["substancias"], substancias_sem_categoria_anm="; ".join(semcat) or None, classe_utilitaria=r["classes_utilitarias"],
        importancia=r["importancia"], status_economico=r["status_economico"], situacao_explotacao=r["situacao_mina"] or None,
        motivo_inatividade=r["motivo_inatividade_mina"] or None, municipality_id=r["municipality_id"], municipality_name=r["municipio_nome"],
        municipio_informado=r["municipio"], uf_informada=r["uf"], latitude=round(float(r["latitude"]), 6), longitude=round(float(r["longitude"]), 6),
        metodo_geoposicionamento=r["metodo_geoposicionamento"], provincia_mineral=r["provincia"], rochas_hospedeiras=r["rochas_hospedeiras"],
        rochas_encaixantes=r["rochas_encaixantes"], rochas_afloramento=r["rochas"], morfologia=r["morfologia"], texturas=r["texturas"],
        tipos_alteracao=r["tipos_alteracao"], tipo_afloramento=r["tipo_afloramento"], descricao=r["descricao"], projeto_sgb=r["projeto"],
        folha_sgb=r["folha"], numero_campo=r["numero_campo"], afloramento_id_sgb=int(r["id_afloramento"]), data_cadastro=data_cad,
        categoria_anm_sobreposta=cats[0] if cats else "fora_de_processo", processos_anm_sobrepostos="; ".join(processos) or None,
        operation_ids_sobrepostos="; ".join(ops) or None, project_ids_sobrepostos="; ".join(prjs) or None,
        valor_observado_estimado="observado", metodo_estimacao=None, status_validacao="alerta_localizacao" if alerta else "valido",
        responsavel_validacao=RESPONSAVEL, source_id="; ".join(IDS_FONTE), source_url="; ".join(FONTES[x][0] for x in IDS_FONTE),
        data_acesso="; ".join(DATA[x] for x in IDS_FONTE), periodo_referencia=f"cadastro no GeoSGB em {data_cad}" if data_cad else "sem data de cadastro",
        tipo_fonte="oficial", observacao="; ".join(obs) or None).items()})
ORDEM_IMP = {"Depósito": 0, "Ocorrência": 1, "Indício": 2, "Indeterminado": 3}
linhas.sort(key=lambda x: (ORDEM_IMP.get(x["importancia"], 9), x["mineral_names"] or "~", int(x["occurrence_id"][4:])))

cw = [dict(substancia_original=n, substancia_normalizada=norm(n), ocorrencias=c, mineral_id=KEY2ID[MAPA[n][0]] if MAPA[n][0] else None,
           mineral_name=NOME[KEY2ID[MAPA[n][0]]] if MAPA[n][0] else None, tipo_correspondencia=MAPA[n][1], justificativa=MAPA[n][2])
      for n, c in cont.items()]
ORDEM_TIPO = {"sem_categoria_anm": 0, "sinonimo_recmin": 1, "crosswalk_base1": 2}
cw.sort(key=lambda x: (ORDEM_TIPO[x["tipo_correspondencia"]], -x["ocorrencias"], x["substancia_original"]))

minas = [x for x in linhas if x["status_economico"] == "Mina"]
resumo = dict(
    baixados=len(g), dentro_go=len(d), fora_por_uf=Counter(fora["uf"]), uf_divergente=int((d["uf"] != "GO").sum()),
    municipio_divergente=sum(1 for x in linhas if "município informado" in (x["observacao"] or "")),
    coordenadas_repetidas=sum(1 for v in coords.values() if len(v) > 1), status_economico=Counter(x["status_economico"] for x in linhas),
    importancia=Counter(x["importancia"] for x in linhas), categoria_anm=Counter(x["categoria_anm_sobreposta"] for x in linhas),
    em_projeto_04=sum(1 for x in linhas if x["project_ids_sobrepostos"]),
    minas_recmin=len(minas), minas_em_operacao_ativa=sum(1 for x in minas if x["categoria_anm_sobreposta"] == "1_operacao_ativa"),
    metodo_carta_250k=sum(1 for x in linhas if "1:250.000" in str(x["metodo_geoposicionamento"])),
    anos_cadastro=Counter((x["data_cadastro"] or "????")[:4] for x in linhas), nomes_substancia=len(cw),
    crosswalk_por_tipo=Counter(x["tipo_correspondencia"] for x in cw), mencoes=sum(cont.values()),
    mencoes_sem_categoria=sum(x["ocorrencias"] for x in cw if x["tipo_correspondencia"] == "sem_categoria_anm"),
    campos_descartados=DESCARTADOS, evidencia_descarte=evid, sha256=META["sha256"], data_download=META["data_download_utc"])
for nome, obj in (("_ocorrencias_06.json", dict(colunas=list(linhas[0].keys()), linhas=[list(x.values()) for x in linhas])),
                  ("_ocorrencias_06b.json", dict(colunas=list(cw[0].keys()), linhas=[list(x.values()) for x in cw])),
                  ("_ocorrencias_06_resumo.json", resumo)):
    with open(f"{TMP}/{nome}", "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1 if nome.endswith("resumo.json") else None, default=str)
print(json.dumps(resumo, ensure_ascii=False, default=str))
