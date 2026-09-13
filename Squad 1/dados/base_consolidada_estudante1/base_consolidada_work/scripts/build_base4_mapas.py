# -*- coding: utf-8 -*-
"""Base 4 -- Camadas de mapa (Goias): municipios, processos minerarios, operacoes ativas e
amostras geoquimicas do SGB, com as MESMAS chaves das Bases 1-3 (mineral_id, company_id,
municipality_id, operation_id) e a auditoria do cruzamento espacial.

Pente fino desta base (achados que definem as decisoes abaixo):
  * SIGMINE e malha IBGE estao no mesmo datum (SIRGAS 2000, EPSG:4674): sem reprojecao dos dados.
    Areas e intersecoes sao calculadas numa Albers equivalente (a Polyconic EPSG:5880 superestima
    a area de GO em ~0,3%).
  * 27 poligonos do SIGMINE tem autointersecao de anel -> make_valid (area inalterada).
  * 176 processos estao fragmentados em 948 feicoes SEM sobreposicao (uniao/soma = 1,0) ->
    dissolvidos em uma geometria por processo.
  * O campo UF do SIGMINE NAO e recorte territorial (UF=MG tem 355 poligonos parcialmente dentro
    de GO) -> o recorte usa a geometria; cada processo leva a fracao de area em GO.
  * O SIGMINE nao tem municipio: juncao espacial (maior area de intersecao), validada contra o
    municipio textual do Cadastro Mineiro.
  * Empresa pelo NUMERO DO PROCESSO (92,2%) e nome so como reserva (65,9%); zero conflitos.
  * O ponto 'centro da caixa' cai fora do proprio municipio em 20 casos -> representative_point.
  * O GeoSGB baixado NAO tem camada de ocorrencias (RECMIN): so pontos de amostragem geoquimica,
    com teores em planilhas separadas (chave NUM_LAB), unidades mistas (Au em ppm num projeto e ppb
    em outro) e separador decimal misto ('< 0,1' ao lado de '11.1').
"""
import contextlib, io, json, os, re, sys, warnings, zipfile
from collections import Counter, defaultdict

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.validation import make_valid

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
from caminhos import BASE, TMP  # caminhos relativos ao projeto — ver caminhos.py
OUTDIR = f"{BASE}/outputs/mapas"
GPKG = f"{OUTDIR}/minera_goias_mapas_v1.gpkg"
os.makedirs(OUTDIR, exist_ok=True)

CRS_GEO = "EPSG:4674"  # SIRGAS 2000 -- o das duas fontes
CRS_AREA = "+proj=aea +lat_0=-32 +lon_0=-60 +lat_1=-5 +lat_2=-42 +x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs"

auditoria = []


def audit(camada, verificacao, n, resultado, decisao):
    auditoria.append(dict(camada=camada, verificacao=verificacao, n=n, resultado=resultado, decisao=decisao))


# ---------------------------------------------------------------------------
# 0) reaproveita chaves e pontes da Base 3 (que por sua vez reaproveita a Base 1)
# ---------------------------------------------------------------------------
class _Mudo(io.StringIO):
    def reconfigure(self, **k):
        pass


B3 = {"__name__": "base3"}
with contextlib.redirect_stdout(_Mudo()):
    exec(open(f"{BASE}/base_consolidada_work/scripts/build_base3_empresa_mineral_ano.py", encoding="utf-8").read(), B3)
sys.stdout.reconfigure(encoding="utf-8")
norm, norm_razao, canon_processo = B3["norm"], B3["norm_razao"], B3["canon_processo"]
RAW2KEY, MIN_DEF = B3["RAW2KEY"], B3["MIN_DEF"]
proc2company, EMP, nome_para_raiz = B3["proc2company"], B3["EMP"], B3["nome_para_raiz"]
registros, cfem = B3["registros"], B3["cfem"]
_ordem = sorted(MIN_DEF.items(), key=lambda kv: (kv[1][1], kv[1][0]))
KEY2ID = {k: f"MIN_{i + 1:03d}" for i, (k, _) in enumerate(_ordem)}
print("Chaves das Bases 1-3 carregadas.")


def _num(s):
    s = str(s).strip()
    if not s:
        return 0.0
    s = s.replace(".", "").replace(",", ".") if "," in s else s
    try:
        return float(s)
    except ValueError:
        return 0.0


def _limpo(v):
    if v is None:
        return None
    if isinstance(v, np.bool_):
        return bool(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return None if np.isnan(v) else float(v)
    return v


def registros_json(df):
    return [{k: _limpo(v) for k, v in r.items()} for r in df.drop(columns="geometry", errors="ignore").astype(object).to_dict("records")]


# ---------------------------------------------------------------------------
# 1) Municipios (IBGE 2025)
# ---------------------------------------------------------------------------
mun = gpd.read_file(f"zip://{BASE}/dados/IBGE/GO_Municipios_2025.zip!GO_Municipios_2025.shp")
assert mun.crs.to_epsg() == 4674, mun.crs
mun = mun.rename(columns={"CD_MUN": "municipality_id", "NM_MUN": "municipio_nome",
                          "NM_RGI": "regiao_imediata", "NM_RGINT": "regiao_intermediaria"})
mun["area_km2_ibge"] = mun["AREA_KM2"].astype(float)
mun["area_km2_calculada"] = (mun.to_crs(CRS_AREA).area / 1e6).round(3)
rp = mun.geometry.representative_point()
mun["latitude"], mun["longitude"] = rp.y.round(6), rp.x.round(6)

bb = mun.bounds
bbc = gpd.GeoSeries(gpd.points_from_xy((bb.minx + bb.maxx) / 2, (bb.miny + bb.maxy) / 2), crs=mun.crs, index=mun.index)
fora = mun.loc[~mun.geometry.contains(bbc), "municipio_nome"].tolist()
audit("municipios_go", "Ponto 'centro da caixa envolvente' (usado nas versões anteriores da Base 2) cai fora do próprio município",
      len(fora), ", ".join(fora), "Substituído por representative_point (garantido dentro do polígono) na camada e na Base 2.")
audit("municipios_go", "Área total: soma AREA_KM2 do IBGE vs. calculada em Albers equivalente",
      246, f"IBGE {mun['area_km2_ibge'].sum():,.0f} km² | calculada {mun['area_km2_calculada'].sum():,.0f} km²",
      "Diferença residual de generalização da malha; mantidas as duas colunas.")

b2 = pd.DataFrame(json.load(open(f"{TMP}/_base2_rows.json", encoding="utf-8")))
g2 = b2.groupby("municipality_id")
met = pd.DataFrame({
    "cfem_2025_brl": b2[b2["ano"] == 2025].groupby("municipality_id")["cfem_recolhido_brl"].sum(min_count=1),
    "cfem_2022_2026_brl": g2["cfem_recolhido_brl"].sum(min_count=1),
    "populacao_2025": g2["populacao"].max(),
    "pib_2023_brl": g2["pib_total_brl"].max(),
    "qtd_processos_cadastro": g2["qtd_processos_cadastro_mineiro"].max(),
    "principais_minerais": g2["principais_minerais_cadastro"].first(),
})
mun = mun.merge(met, left_on="municipality_id", right_index=True, how="left")
print(f"Municípios: {len(mun)}; pontos de rótulo corrigidos: {len(fora)}")

# ---------------------------------------------------------------------------
# 2) Processos minerarios (SIGMINE)
# ---------------------------------------------------------------------------
sig = gpd.read_file(f"zip://{BASE}/dados/ANM/sigmine/GO.zip!GO.shp")
assert sig.crs.to_epsg() == 4674, sig.crs
invalidas = ~sig.is_valid
area_antes = sig.loc[invalidas].to_crs(CRS_AREA).area.sum()
sig["geometria_reparada"] = invalidas
sig["geometry"] = sig.geometry.apply(lambda x: x if x.is_valid else make_valid(x))
audit("processos_minerarios_go", "Polígonos inválidos (autointerseção de anel)", int(invalidas.sum()),
      f"área antes {area_antes / 1e4:,.1f} ha | depois {sig.loc[invalidas].to_crs(CRS_AREA).area.sum() / 1e4:,.1f} ha",
      "Reparados com make_valid; flag geometria_reparada = verdadeiro.")

sig["processo_anm"] = sig["PROCESSO"].map(canon_processo)
n_feic = sig.groupby("processo_anm").size()
audit("processos_minerarios_go", "Processos fragmentados em várias feições", int((n_feic > 1).sum()),
      f"{int(n_feic[n_feic > 1].sum())} feições; fragmentos sem sobreposição (união/soma = 1,0); variam só AREA_HA e ID",
      "Dissolvidos em 1 geometria por processo; AREA_HA somada; qtd_feicoes_originais preservada.")

proc = sig.dissolve(by="processo_anm", aggfunc={
    "NOME": "first", "SUBS": "first", "FASE": "first", "ULT_EVENTO": "first", "USO": "first",
    "UF": "first", "DSProcesso": "first", "AREA_HA": "sum", "geometria_reparada": "max"}).reset_index()
proc["qtd_feicoes_originais"] = proc["processo_anm"].map(n_feic)
proc["operation_id"] = "OPE_" + proc["processo_anm"].str.replace("/", "_", regex=False)
procA = proc.to_crs(CRS_AREA)
proc["area_ha_calculada"] = (procA.area / 1e4).round(2).values
proc["area_ha_declarada"] = proc["AREA_HA"].astype(float).round(2)
razao = proc["area_ha_calculada"] / proc["area_ha_declarada"].replace(0, np.nan)
audit("processos_minerarios_go", "Área calculada vs. AREA_HA declarada no SIGMINE", len(proc),
      f"razão mediana {razao.median():.4f}; divergência > 5% em {int((abs(razao - 1) > 0.05).sum())} processos",
      "Mantidas as duas colunas; divergências > 5% ficam para revisão.")

# juncao espacial com municipios (maior area de intersecao)
munA = mun[["municipality_id", "municipio_nome", "geometry"]].to_crs(CRS_AREA)
inter = gpd.overlay(procA[["processo_anm", "geometry"]], munA, how="intersection", keep_geom_type=True)
inter["a"] = inter.area
area_tot = procA.set_index("processo_anm").area
frac = (inter.groupby("processo_anm")["a"].sum() / area_tot).clip(upper=1)
princ = inter.sort_values("a", ascending=False).drop_duplicates("processo_anm").set_index("processo_anm")
lista = inter.sort_values("a", ascending=False).groupby("processo_anm")["municipio_nome"].agg("; ".join)
proc["fracao_area_em_go"] = proc["processo_anm"].map(frac).fillna(0).round(4)
proc["municipality_id"] = proc["processo_anm"].map(princ["municipality_id"])
proc["municipio_nome"] = proc["processo_anm"].map(princ["municipio_nome"])
proc["municipios_intersectados"] = proc["processo_anm"].map(lista)
proc["qtd_municipios"] = proc["processo_anm"].map(inter.groupby("processo_anm")["municipality_id"].nunique()).fillna(0).astype(int)
audit("processos_minerarios_go", "Processos que atravessam mais de um município", int((proc["qtd_municipios"] > 1).sum()),
      f"máximo {proc['qtd_municipios'].max()} municípios", "municipality_id = município de MAIOR área; lista completa em municipios_intersectados.")

por_uf = proc.assign(dentro=proc["fracao_area_em_go"] > 0.999).groupby("UF")["dentro"].agg(["size", "sum"])
audit("processos_minerarios_go", "Campo UF do SIGMINE como recorte territorial", len(proc),
      "; ".join(f"UF={u}: {int(r['size'])} processos, {int(r['sum'])} 100% dentro de GO" for u, r in por_uf.iterrows()),
      "UF NÃO usado como filtro; recorte pela geometria, com fracao_area_em_go por processo.")
audit("processos_minerarios_go", "Processos com menos de 50% da área em Goiás", int((proc["fracao_area_em_go"] < 0.5).sum()),
      "polígonos de divisa com MG/TO/MT/BA/MS/DF", "Mantidos (a parte goiana existe); filtrar por fracao_area_em_go se a análise exigir.")

# teste de simplificacao para a web (registrado para justificar a decisao de NAO simplificar)
_s10 = procA.geometry.simplify(10, preserve_topology=True)
_rel = (procA.area - _s10.area).abs() / procA.area
audit("processos_minerarios_go", "Simplificação da geometria para a web (teste com tolerância de 10 m)", len(proc),
      f"perda de área total só {100 * (procA.area - _s10.area).abs().sum() / procA.area.sum():.3f}%, mas {int((_rel > 0.01).sum())} polígonos "
      f"variam > 1% e {int((_rel > 0.10).sum())} variam > 10% — os piores são poligonais < 2 ha de licenciamento/garimpeira, que colapsam",
      "REJEITADA: são poligonais legais de título minerário. A web usa arquivos sem simplificação divididos por grupo de categoria "
      "e vector tiles (PMTiles); a generalização por zoom dos tiles é só visual.")
del _s10, _rel

# validacao: municipio espacial x municipio textual do Cadastro Mineiro
cad_mun = defaultdict(set)
for reg in registros:
    cad_mun[reg["processo"]].update(reg["municipios"])
todos_esp = inter.groupby("processo_anm")["municipality_id"].agg(set)
comuns = [p for p in proc["processo_anm"] if p in cad_mun and p in todos_esp.index]
concorda = [p for p in comuns if todos_esp[p] & cad_mun[p]]
nome_mun = dict(zip(mun["municipality_id"], mun["municipio_nome"]))
audit("processos_minerarios_go", "Município espacial vs. município textual do Cadastro Mineiro", len(comuns),
      f"concordância {100 * len(concorda) / len(comuns):.2f}% ({len(comuns) - len(concorda)} discordâncias)",
      "Vale a junção espacial (limites municipais atuais); o texto do Cadastro guarda o município da época do registro.")
for p in sorted(set(comuns) - set(concorda)):
    audit("processos_minerarios_go", f"Discordância espacial x Cadastro — processo {p}", 1,
          f"espacial: {', '.join(sorted(nome_mun[c] for c in todos_esp[p]))} | Cadastro: {', '.join(sorted(nome_mun[c] for c in cad_mun[p]))}",
          "Padrão compatível com desmembramento municipal posterior ao registro (ex.: Jussara → Santa Fé de Goiás); confirmar no histórico territorial do IBGE.")
sem_cad = [p for p in proc["processo_anm"] if p not in cad_mun]
audit("processos_minerarios_go", "Processos sem município no Cadastro Mineiro (junção espacial é a única fonte)", len(sem_cad),
      "fecha o gap QC06 da base v1 (operações sem município)", "municipality_id atribuído pela geometria.")

# empresa: processo primeiro, nome do SIGMINE como reserva
cid_l, ident_l, razao_l = [], [], []
conflitos = 0
for p, nome in zip(proc["processo_anm"], proc["NOME"]):
    nr = norm_razao(nome)
    via_nome = f"COM_CNPJ_{nome_para_raiz[nr]}" if nr in nome_para_raiz else None
    if p in proc2company:
        cid, ident = proc2company[p], "ponte_processo_cadastro"
        if via_nome and via_nome != cid:
            conflitos += 1
    elif via_nome:
        cid, ident = via_nome, "nome_sigmine_casado_com_raiz_cnpj"
    else:
        cid, ident = None, "sem_correspondencia"
    cid_l.append(cid)
    ident_l.append(ident)
    razao_l.append(EMP[cid]["nomes"].most_common(1)[0][0] if cid in EMP else str(nome).strip())
proc["company_id"], proc["identificacao_empresa"], proc["razao_social"] = cid_l, ident_l, razao_l
# LGPD: CPF dentro do nome do titular (empresário individual) só é mascarado DEPOIS de atribuir o company_id,
# que precisa do nome original para casar com o Cadastro Mineiro. Vale para a 03, a 04 e todas as camadas de mapa.
mascarar_cpf = B3["mascarar_cpf"]
proc["razao_social"] = proc["razao_social"].map(mascarar_cpf)
proc["NOME"] = proc["NOME"].map(mascarar_cpf)
ci = Counter(ident_l)
audit("processos_minerarios_go", "Atribuição de company_id", len(proc),
      f"via processo {ci['ponte_processo_cadastro']} | via nome {ci['nome_sigmine_casado_com_raiz_cnpj']} | sem par {ci['sem_correspondencia']} | conflitos processo×nome {conflitos}",
      "Processo tem prioridade; nome só quando o processo não existe no Cadastro Mineiro.")

# minerais
min_ids, min_princ, nao_map = [], [], Counter()
mineral_key_com_uso, USO_ROCHAS = B3["mineral_key_com_uso"], B3["USO_ROCHAS"]
for subs, uso in zip(proc["SUBS"], proc["USO"]):
    ks = []
    for t in re.split(r"[,;]", str(subs)):
        t = t.strip()
        if not t:
            continue
        if RAW2KEY.get(norm(t), "___") == "___":
            nao_map[t] += 1
            continue
        k, _regra = mineral_key_com_uso(t, uso, USO_ROCHAS["padrao"])  # rochas: categoria pelo tipo de uso (v7)
        if k and k not in ks:
            ks.append(k)
    min_ids.append("; ".join(KEY2ID[k] for k in ks))
    min_princ.append(MIN_DEF[ks[0]][0] if ks else "")
proc["mineral_ids"], proc["mineral_principal"] = min_ids, min_princ
audit("processos_minerarios_go", "Substâncias do SIGMINE sem mineral_id", sum(nao_map.values()),
      "; ".join(f"{t} ({c})" for t, c in nao_map.most_common(5)) or "nenhuma", "Mesmo crosswalk da Base 1 (01b).")

# CFEM e categoria de mapa
cfem["_v"] = cfem["ValorRecolhido"].map(_num)
cfem_rec = cfem[cfem["_ano"].isin([2024, 2025, 2026])].groupby("_proc")["_v"].sum()
cfem_tot = cfem.groupby("_proc")["_v"].sum()
proc["cfem_2024_2026_brl"] = proc["processo_anm"].map(cfem_rec).round(2)
proc["cfem_2022_2026_brl"] = proc["processo_anm"].map(cfem_tot).round(2)
sem_geo = set(cfem_tot.index) - set(proc["processo_anm"])
audit("processos_minerarios_go", "Processos com CFEM mas sem polígono no SIGMINE", len(sem_geo),
      f"R$ {cfem_tot.reindex(list(sem_geo)).sum():,.2f} em 2022-2026 (inclui a série 96xxxx já vista na Base 3)",
      "Não aparecem no mapa; o valor continua na Base 3 (COM_NAO_IDENTIFICADO).")

LAVRA = {"CONCESSÃO DE LAVRA", "LAVRA GARIMPEIRA", "LICENCIAMENTO", "REGISTRO DE EXTRAÇÃO"}
PRE_LAVRA = {"REQUERIMENTO DE LAVRA", "DIREITO DE REQUERER A LAVRA"}
PESQUISA = {"AUTORIZAÇÃO DE PESQUISA", "REQUERIMENTO DE PESQUISA"}
REQUER = {"REQUERIMENTO DE LICENCIAMENTO", "REQUERIMENTO DE LAVRA GARIMPEIRA", "REQUERIMENTO DE REGISTRO DE EXTRAÇÃO"}
DISP = {"DISPONIBILIDADE", "APTO PARA DISPONIBILIDADE"}
CATEGORIAS = {
    "1_operacao_ativa": "Operação ativa (título de lavra + CFEM 2024-2026)",
    "2_lavra_sem_cfem_recente": "Lavra autorizada, sem CFEM recente",
    "3_cfem_sem_titulo_de_lavra": "Recolhe CFEM sem título de lavra",
    "4_pre_lavra": "Pré-lavra (requerimento/direito de lavra)",
    "5_pesquisa": "Pesquisa",
    "6_requerimento_licenc_garimpeira": "Requerimento de licenciamento ou lavra garimpeira",
    "7_disponibilidade": "Disponibilidade (área devolvida à ANM)",
    "8_outros": "Outros / não cadastrado",
}


def categoria(fase, rec):
    rec = 0 if pd.isna(rec) else rec
    if fase in LAVRA and rec > 0:
        return "1_operacao_ativa"
    if fase in LAVRA:
        return "2_lavra_sem_cfem_recente"
    if rec > 0:
        return "3_cfem_sem_titulo_de_lavra"
    if fase in PRE_LAVRA:
        return "4_pre_lavra"
    if fase in PESQUISA:
        return "5_pesquisa"
    if fase in REQUER:
        return "6_requerimento_licenc_garimpeira"
    if fase in DISP:
        return "7_disponibilidade"
    return "8_outros"


proc["categoria_mapa"] = [categoria(f, r) for f, r in zip(proc["FASE"], proc["cfem_2024_2026_brl"])]
proc["status_operacional"] = proc["categoria_mapa"].map(CATEGORIAS)
rp_proc = proc.geometry.representative_point()
proc["latitude"], proc["longitude"] = rp_proc.y.round(6), rp_proc.x.round(6)
proc = proc.rename(columns={"FASE": "fase_atual", "ULT_EVENTO": "ultimo_evento", "USO": "uso_declarado",
                            "UF": "uf_declarada_sigmine", "NOME": "titular_sigmine", "SUBS": "substancias_sigmine"})
proc["source_ids"] = "SRC_ANM_SIGMINE; SRC_IBGE_MALHA_2025" + np.where(proc["identificacao_empresa"] == "ponte_processo_cadastro", "; SRC_ANM_CADASTRO", "") \
    + np.where(proc["cfem_2022_2026_brl"].notna(), "; SRC_ANM_CFEM", "")
cat_counts = proc["categoria_mapa"].value_counts().sort_index()
print("Processos por categoria:", dict(cat_counts))

mun["qtd_processos_sigmine"] = mun["municipality_id"].map(inter.groupby("municipality_id")["processo_anm"].nunique()).fillna(0).astype(int)
mun["qtd_operacoes_ativas"] = mun["municipality_id"].map(proc[proc["categoria_mapa"] == "1_operacao_ativa"].groupby("municipality_id").size()).fillna(0).astype(int)

COLS_PROC = ["operation_id", "processo_anm", "company_id", "razao_social", "identificacao_empresa", "titular_sigmine",
             "mineral_ids", "mineral_principal", "substancias_sigmine", "municipality_id", "municipio_nome",
             "municipios_intersectados", "qtd_municipios", "fase_atual", "categoria_mapa", "status_operacional",
             "ultimo_evento", "uso_declarado", "cfem_2024_2026_brl", "cfem_2022_2026_brl", "area_ha_calculada",
             "area_ha_declarada", "fracao_area_em_go", "latitude", "longitude", "uf_declarada_sigmine",
             "qtd_feicoes_originais", "geometria_reparada", "source_ids", "geometry"]
proc = proc[COLS_PROC]
ops = proc[proc["categoria_mapa"] == "1_operacao_ativa"].copy()
ops["geometry"] = ops.geometry.representative_point()
ops = gpd.GeoDataFrame(ops.drop(columns=["geometry"]), geometry=ops["geometry"], crs=CRS_GEO)

# ---------------------------------------------------------------------------
# 3) Amostras geoquimicas do SGB (evidencia geologica -- NAO sao ocorrencias minerais)
# ---------------------------------------------------------------------------
FONTES_GQ = [
    ("Geologia e Metalogenia do Oeste de Goiás (2017)", "dados/SGB_GeoSGB/sig_vetorial/geoquimica_metalogenia_oeste_de_goias_2017.zip", "Geologia_e_Metalogenia_do_Oeste_de_Goias.shp"),
    ("Noroeste de Goiás - Folha Bonópolis (2007)", "dados/SGB_GeoSGB/sig_vetorial/geoquimica_noroeste_de_goias.zip", "Noroeste_de_Goias.shp"),
    ("Folha Goiás - PLGB (1991)", "dados/SGB_GeoSGB/sig_vetorial/geoquimica_Fl_goias_PLGB_1999_vr1.zip", "Geoquímica - Projeto Folha Goiás (PLGB)/Folha_Goias_PLGB.shp"),
]
# Cu e Ni padronizados em ppm; Au em ppb
FATOR = {("CU", "PPM"): 1, ("CU", "PPB"): 1e-3, ("CU", "PCT"): 1e4,
         ("NI", "PPM"): 1, ("NI", "PPB"): 1e-3, ("NI", "PCT"): 1e4,
         ("AU", "PPM"): 1e3, ("AU", "PPB"): 1, ("AU", "PCT"): 1e7}


def parse_teor(raw):
    s = str(raw).strip()
    if s in ("", "nan", "None"):
        return None, None, "vazio"
    if s.upper() in ("N.A.", "NA", "ND", "N.D.", "IS"):
        return None, None, "nao_analisado"
    censurado = s.startswith("<")
    try:
        v = float(s.lstrip("<").strip().replace(",", "."))  # separador decimal misto na mesma planilha
    except ValueError:
        return None, None, "invalido"
    return (None, v, "abaixo_ld") if censurado else (v, None, "quantificado")


gq_rows = []
for projeto, zp, inner in FONTES_GQ:
    pts = gpd.read_file(f"zip://{BASE}/{zp}!{inner}")
    assert pts.crs.to_epsg() == 4674, pts.crs
    pts.columns = [c if c == "geometry" else c.upper() for c in pts.columns]
    analises = defaultdict(lambda: defaultdict(list))
    n_dup = n_virg = 0
    with zipfile.ZipFile(f"{BASE}/{zp}") as z:
        for x in [n for n in z.namelist() if n.lower().endswith(".xlsx")]:
            xl = pd.ExcelFile(io.BytesIO(z.read(x)))
            for sh in xl.sheet_names:
                df = xl.parse(sh, dtype=str)
                cols = {str(c).strip().upper(): c for c in df.columns}
                elem = [(m.group(1), m.group(2), cols[cu]) for cu in cols for m in [re.match(r"^(AU|CU|NI)_(PPM|PPB|PCT)$", cu)] if m]
                if "NUM_LAB" not in cols or not elem:
                    continue
                labs = df[cols["NUM_LAB"]].astype(str).str.strip().str.upper()
                n_dup += int((labs.value_counts() > 1).sum())
                for lab, (_, r) in zip(labs, df.iterrows()):
                    for el, un, c in elem:
                        raw = r[c]
                        if isinstance(raw, str) and raw.strip().startswith("<") and "," in raw:
                            n_virg += 1
                        val, ld, st = parse_teor(raw)
                        f = FATOR[(el, un)]
                        analises[lab][el].append((st, None if val is None else val * f, None if ld is None else ld * f, un))
    au_st = Counter()
    au_ld = set()
    for _, p in pts.iterrows():
        lab = str(p.get("NUM_LAB", "")).strip().upper()
        rec = dict(amostra_id=f"AMO_{lab}", num_lab=lab, num_campo=p.get("NUM_CAMPO"), projeto_sgb=projeto,
                   classe_amostra=p.get("CLASSE"), data_visita=str(p.get("DTVISITA"))[:10], geometry=p.geometry)
        for el, col, unid in [("CU", "cu_ppm", "ppm"), ("NI", "ni_ppm", "ppm"), ("AU", "au_ppb", "ppb")]:
            lst = analises.get(lab, {}).get(el, [])
            quant = [v for st, v, _, _ in lst if st == "quantificado"]
            lds = [ld for st, _, ld, _ in lst if st == "abaixo_ld"]
            if quant:
                rec[col], rec[f"{col}_status"] = round(max(quant), 4), "quantificado"
            elif lds:
                rec[col], rec[f"{col}_status"] = None, f"< {min(lds):g} {unid} (abaixo do limite de detecção)"
            elif lst:
                rec[col], rec[f"{col}_status"] = None, "não analisado"
            else:
                rec[col], rec[f"{col}_status"] = None, "sem análise química"
            if el == "AU" and lst:
                au_st["quantificado" if quant else "abaixo_ld" if lds else "outro"] += 1
                au_ld.update(f"{ld:g} ppb (original em {u})" for st, _, ld, u in lst if st == "abaixo_ld")
        rec["n_analises"] = max((len(v) for v in analises.get(lab, {}).values()), default=0)
        rec["minerais_quantificados"] = "; ".join(KEY2ID[k] for k, c in (("cobre", "cu_ppm"), ("niquel", "ni_ppm")) if rec[c] is not None)
        gq_rows.append(rec)
    com_analise = sum(1 for _, p in pts.iterrows() if str(p.get("NUM_LAB", "")).strip().upper() in analises)
    audit("amostras_geoquimicas_sgb_go", f"{projeto}: pontos com análise química (junção por NUM_LAB)", len(pts),
          f"{com_analise} com análise; {len(pts) - com_analise} só mineralometria/sem química; NUM_LAB com mais de uma análise: {n_dup}",
          "Várias análises da mesma amostra: mantido o MAIOR teor quantificado; n_analises registra quantas havia.")
    if au_st:
        audit("amostras_geoquimicas_sgb_go", f"{projeto}: ouro (Au)", sum(au_st.values()),
              f"quantificado {au_st['quantificado']} | abaixo do LD {au_st['abaixo_ld']} | limites: {', '.join(sorted(au_ld))}",
              "Au padronizado em ppb. Sem nenhum valor quantificado, a coluna não indica anomalia — e os LDs das campanhas diferem em 1.000×, então 'abaixo do LD' não é comparável entre elas.")
    if n_virg:
        audit("amostras_geoquimicas_sgb_go", f"{projeto}: separador decimal misto", n_virg,
              "valores censurados escritos com vírgula ('< 0,1') em planilha que usa ponto ('11.1')", "Normalizado para ponto antes da conversão numérica.")

gq = gpd.GeoDataFrame(gq_rows, geometry="geometry", crs=CRS_GEO)
dup_ids = gq["amostra_id"].duplicated(keep=False)
if dup_ids.any():
    gq.loc[dup_ids, "amostra_id"] = gq.loc[dup_ids, "amostra_id"] + "_" + gq.loc[dup_ids].groupby("amostra_id").cumcount().astype(str)
gq = gpd.sjoin(gq, mun[["municipality_id", "municipio_nome", "geometry"]], how="left", predicate="within").drop(columns="index_right")
audit("amostras_geoquimicas_sgb_go", "Amostras fora do território de Goiás (junção espacial)", int(gq["municipality_id"].isna().sum()),
      f"de {len(gq)} pontos", "Mantidas sem municipality_id.")
audit("ocorrencias_minerais_recmin", "Camada de ocorrências/depósitos (RECMIN) nos pacotes GeoSGB baixados", 0,
      "não existe: os pacotes têm geologia, afloramentos (minerais formadores de rocha) e amostragem geoquímica",
      "Os pacotes locais não têm RECMIN: as ocorrências vieram do WFS oficial do SGB e estão na aba 06 (build_ocorrencias_06.py). "
      "Pontos geoquímicos NÃO devem ser simbolizados como ocorrência.")
print(f"Amostras geoquímicas: {len(gq)}")

# ---------------------------------------------------------------------------
# 4) Gravacao: GeoJSON (web, RFC 7946) + GeoPackage (QGIS, resolucao total) + preview
# ---------------------------------------------------------------------------
if os.path.exists(GPKG):
    os.remove(GPKG)

COLS_MUN = ["municipality_id", "municipio_nome", "regiao_imediata", "regiao_intermediaria", "area_km2_ibge",
            "area_km2_calculada", "latitude", "longitude", "populacao_2025", "pib_2023_brl", "cfem_2025_brl",
            "cfem_2022_2026_brl", "qtd_processos_cadastro", "qtd_processos_sigmine", "qtd_operacoes_ativas",
            "principais_minerais", "geometry"]
camadas = [
    ("CAM_01", "municipios_go", mun[COLS_MUN], 0.0005, "Limites municipais oficiais + indicadores da Base 2"),
    ("CAM_02", "processos_minerarios_go", proc, None, "Polígonos dos processos minerários (SIGMINE) com empresa, mineral, município e categoria"),
    ("CAM_03", "operacoes_ativas_go", ops, None, "Um ponto por operação ativa (título de lavra + CFEM 2024-2026)"),
    ("CAM_04", "amostras_geoquimicas_sgb_go", gq, None, "Pontos de amostragem geoquímica do SGB com Cu/Ni/Au — evidência geológica, NÃO ocorrência mineral"),
]
catalogo = []
for cid_cam, nome, gdf, tol, desc in camadas:
    gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=CRS_GEO)
    gdf.to_file(GPKG, layer=nome, driver="GPKG", engine="pyogrio")
    web = gdf.copy()
    if tol:
        web["geometry"] = web.geometry.simplify(tol, preserve_topology=True)
    path = f"{OUTDIR}/{nome}.geojson"
    if os.path.exists(path):
        os.remove(path)
    web.to_file(path, driver="GeoJSON", engine="pyogrio", RFC7946="YES", COORDINATE_PRECISION=6)
    catalogo.append(dict(
        camada_id=cid_cam, nome_camada=nome, descricao=desc, tipo_geometria=", ".join(sorted(set(gdf.geom_type))),
        n_feicoes=len(gdf), arquivo_geojson=f"outputs/mapas/{nome}.geojson", tamanho_geojson_mb=round(os.path.getsize(path) / 1e6, 1),
        camada_gpkg=f"outputs/mapas/minera_goias_mapas_v1.gpkg › {nome}",
        crs="GeoJSON: WGS 84 (RFC 7946) | GPKG: SIRGAS 2000 (EPSG:4674)",
        simplificacao_web=f"simplify {tol}° (~{tol * 111000:.0f} m), só no GeoJSON" if tol else "nenhuma",
        chave_primaria={"CAM_01": "municipality_id", "CAM_02": "operation_id", "CAM_03": "operation_id", "CAM_04": "amostra_id"}[cid_cam],
        chaves_de_juncao={"CAM_01": "municipality_id → 05_dim_municipios, 10_cons_municipio_ano",
                          "CAM_02": "operation_id → 03_dim_operacoes; company_id → 02_dim_empresas; mineral_ids → 01_dim_minerais; municipality_id → 05_dim_municipios",
                          "CAM_03": "igual à CAM_02 (subconjunto)",
                          "CAM_04": "municipality_id → 05_dim_municipios; minerais_quantificados → 01_dim_minerais"}[cid_cam],
        source_ids={"CAM_01": "SRC_IBGE_MALHA_2025; SRC_IBGE_POP; SRC_IBGE_PIB; SRC_ANM_CFEM; SRC_ANM_CADASTRO",
                    "CAM_02": "SRC_ANM_SIGMINE; SRC_ANM_CADASTRO; SRC_ANM_CFEM; SRC_IBGE_MALHA_2025",
                    "CAM_03": "SRC_ANM_SIGMINE; SRC_ANM_CFEM",
                    "CAM_04": "SRC_SGB_GEOSGB; SRC_IBGE_MALHA_2025"}[cid_cam],
        simbologia={"CAM_01": "polígono neutro; coroplético opcional (CFEM, população)",
                    "CAM_02": "cor por categoria_mapa (8 classes)",
                    "CAM_03": "marcador sólido destacado",
                    "CAM_04": "marcador pequeno distinto (triângulo) — nunca o mesmo símbolo de ocorrência/projeto"}[cid_cam],
    ))
# --- versoes web da CAM_02, SEM simplificacao --------------------------------
# O GeoJSON completo (29 colunas) passa de 50 MB: pesado demais para o navegador. Em vez de simplificar
# (rejeitado, ver auditoria), reduz colunas, usa 5 casas decimais (~1 m) e divide por grupo de categoria,
# para o frontend carregar lavra/operacao na abertura e o resto sob demanda. Mais os vector tiles.
COLS_WEB = ["operation_id", "company_id", "razao_social", "mineral_principal", "municipality_id",
            "categoria_mapa", "cfem_2024_2026_brl", "geometry"]
GRUPOS_WEB = {
    "lavra_e_operacao": (["1_operacao_ativa", "2_lavra_sem_cfem_recente", "3_cfem_sem_titulo_de_lavra"], "carregar na abertura do mapa"),
    "pre_lavra_e_requerimentos": (["4_pre_lavra", "6_requerimento_licenc_garimpeira"], "carregar sob demanda"),
    "pesquisa": (["5_pesquisa"], "carregar sob demanda (maior grupo)"),
    "disponibilidade_e_outros": (["7_disponibilidade", "8_outros"], "carregar sob demanda"),
}
WEBDIR = f"{OUTDIR}/web"
os.makedirs(WEBDIR, exist_ok=True)
for i, (grupo, (cats, uso)) in enumerate(GRUPOS_WEB.items(), start=1):
    sub = gpd.GeoDataFrame(proc.loc[proc["categoria_mapa"].isin(cats), COLS_WEB], geometry="geometry", crs=CRS_GEO)
    path = f"{WEBDIR}/processos_{grupo}.geojson"
    if os.path.exists(path):
        os.remove(path)
    sub.to_file(path, driver="GeoJSON", engine="pyogrio", RFC7946="YES", COORDINATE_PRECISION=5)
    catalogo.append(dict(
        camada_id=f"CAM_02_WEB_{i}", nome_camada=f"processos_{grupo}",
        descricao=f"Versão web da CAM_02 — {', '.join(cats)}; {uso}",
        tipo_geometria=", ".join(sorted(set(sub.geom_type))), n_feicoes=len(sub),
        arquivo_geojson=f"outputs/mapas/web/processos_{grupo}.geojson", tamanho_geojson_mb=round(os.path.getsize(path) / 1e6, 1),
        camada_gpkg="(atributos completos na CAM_02)", crs="WGS 84 (RFC 7946)",
        simplificacao_web="nenhuma — 8 colunas, 5 casas decimais (~1 m)", chave_primaria="operation_id",
        chaves_de_juncao="operation_id → CAM_02 / 03_dim_operacoes (demais atributos)", source_ids="SRC_ANM_SIGMINE; SRC_ANM_CADASTRO; SRC_ANM_CFEM; SRC_IBGE_MALHA_2025", observacao="Derivada da CAM_02 (mesmos processos e chaves).",
        simbologia="cor por categoria_mapa"))

pm = f"{WEBDIR}/processos_minerarios_go.pmtiles"
try:
    if os.path.exists(pm):
        os.remove(pm)
    gpd.GeoDataFrame(proc[COLS_WEB], geometry="geometry", crs=CRS_GEO).to_file(
        pm, driver="PMTiles", engine="pyogrio", layer="processos", MINZOOM=5, MAXZOOM=14)
    catalogo.append(dict(
        camada_id="CAM_02_TILES", nome_camada="processos (vector tiles)",
        descricao="Vector tiles da CAM_02 (camada 'processos'), zoom 5–14 — a forma recomendada de exibir os 16 mil polígonos no navegador (MapLibre + protomaps)",
        tipo_geometria="Polygon (MVT)", n_feicoes=len(proc),
        arquivo_geojson="outputs/mapas/web/processos_minerarios_go.pmtiles", tamanho_geojson_mb=round(os.path.getsize(pm) / 1e6, 1),
        camada_gpkg="(atributos completos na CAM_02)", crs="Web Mercator (EPSG:3857, gerado pelo GDAL)",
        simplificacao_web="generalização por nível de zoom (visual); precisão legal no GeoPackage", chave_primaria="operation_id",
        chaves_de_juncao="operation_id → CAM_02 / 03_dim_operacoes", source_ids="SRC_ANM_SIGMINE; SRC_ANM_CADASTRO; SRC_ANM_CFEM; SRC_IBGE_MALHA_2025", observacao="Derivada da CAM_02 (mesmos processos e chaves).", simbologia="cor por categoria_mapa"))
except Exception as e:  # nao derruba a Base 4 se o driver faltar em outra maquina
    audit("processos_minerarios_go", "Geração de vector tiles (PMTiles)", 0, f"falhou: {e}", "Usar os GeoJSON por grupo em outputs/mapas/web/.")

for cid_cam, nome, desc in [("CAM_05", "ocorrencias_minerais_recmin", "Ocorrências e depósitos minerais (RECMIN/SGB)"),
                            ("CAM_06", "projetos_futuros", "Projetos que ainda não produzem — camada ANM do Radar de Projetos")]:
    catalogo.append(dict(camada_id=cid_cam, nome_camada=nome, descricao=desc, tipo_geometria="ponto", n_feicoes=0,
                         arquivo_geojson="NÃO GERADA", tamanho_geojson_mb=None, camada_gpkg="",
                         crs="", simplificacao_web="", chave_primaria={"CAM_05": "occurrence_id", "CAM_06": "project_id"}[cid_cam],
                         chaves_de_juncao="", source_ids="",  # sem fonte ainda: o motivo fica em observacao (source_ids so aceita IDs do catalogo 07)
                         simbologia="reservar símbolo próprio (guia: ocorrência ≠ processo ≠ operação ≠ projeto)",
                         ))
# os dados das duas camadas já existem (abas 06 e 04), mas a Base 4 roda ANTES de build_projetos_04/build_ocorrencias_06,
# então o arquivo de camada ainda não é exportado aqui — o catálogo aponta para as abas
catalogo[-2]["observacao"] = ("Dados prontos na aba 06_dim_ocorrencias_geologicas (um ponto por ocorrência, com latitude/longitude; RECMIN do WFS do SGB). "
                              "Arquivo de camada ainda não exportado: a Base 4 roda antes da aba 06.")
catalogo[-1]["observacao"] = ("Dados prontos na aba 04_dim_projetos (ponto representativo de cada projeto, com latitude/longitude). "
                              "Arquivo de camada ainda não exportado: a Base 4 roda antes da aba 04.")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

CORES = {"1_operacao_ativa": "#C0392B", "2_lavra_sem_cfem_recente": "#E67E22", "3_cfem_sem_titulo_de_lavra": "#8E44AD",
         "4_pre_lavra": "#F4D03F", "5_pesquisa": "#5DADE2", "6_requerimento_licenc_garimpeira": "#48C9B0",
         "7_disponibilidade": "#CCD1D1", "8_outros": "#95A5A6"}
fig, ax = plt.subplots(figsize=(11, 12))
mun.plot(ax=ax, facecolor="#FBFBF8", edgecolor="#8A9099", linewidth=0.35)
for cat in sorted(CORES, reverse=True):
    s = proc[proc["categoria_mapa"] == cat]
    if len(s):
        s.plot(ax=ax, facecolor=CORES[cat], edgecolor="none", alpha=0.8)
gq.plot(ax=ax, marker="^", color="#1E8449", markersize=4, alpha=0.7)
ops.plot(ax=ax, color="#C0392B", edgecolor="black", linewidth=0.4, markersize=14)
leg = [Patch(facecolor=CORES[c], label=f"{CATEGORIAS[c]} ({cat_counts.get(c, 0):,})".replace(",", ".")) for c in CORES]
leg += [Line2D([], [], marker="o", ls="", color="#C0392B", markeredgecolor="black", label=f"Ponto de operação ativa ({len(ops)})"),
        Line2D([], [], marker="^", ls="", color="#1E8449", label=f"Amostra geoquímica SGB ({len(gq):,})".replace(",", "."))]
ax.legend(handles=leg, loc="lower left", fontsize=8, frameon=True, title="MINERA Goiás — Base 4 (prévia)", title_fontsize=9)
ax.set_axis_off()
ax.set_title("Processos minerários, operações ativas e amostragem geoquímica — Goiás", fontsize=12)
fig.savefig(f"{OUTDIR}/preview_mapa_go.png", dpi=130, bbox_inches="tight")
plt.close(fig)

with open(f"{TMP}/_mapas_catalogo.json", "w", encoding="utf-8") as f:
    json.dump(catalogo, f, ensure_ascii=False)
with open(f"{TMP}/_mapas_auditoria.json", "w", encoding="utf-8") as f:
    json.dump([{k: _limpo(v) for k, v in a.items()} for a in auditoria], f, ensure_ascii=False)
with open(f"{TMP}/_dim_operacoes.json", "w", encoding="utf-8") as f:
    json.dump(registros_json(proc), f, ensure_ascii=False)
with open(f"{TMP}/_mapas_resumo.json", "w", encoding="utf-8") as f:
    json.dump({"categorias": {k: int(v) for k, v in cat_counts.items()}, "rotulos": CATEGORIAS}, f, ensure_ascii=False)

linhas = ["# Mapas — MINERA Goiás (Base 4)", "",
          "Gerado por `base_consolidada_work/scripts/build_base4_mapas.py`. Catálogo completo e auditoria na aba "
          "`13_mapas_camadas` / `13b_auditoria_mapas` de `documentacao/prototipo_bases_consolidadas_v5.xlsx`.", "",
          "| camada | geometria | feições | arquivo web | chave |", "|---|---|---:|---|---|"]
for c in catalogo:
    linhas.append(f"| {c['nome_camada']} | {c['tipo_geometria']} | {c['n_feicoes']:,} | {c['arquivo_geojson']} | {c['chave_primaria']} |".replace(",", "."))
linhas += ["", "- **Para o frontend, use a pasta `web/`.** `processos_minerarios_go.geojson` (completo, 29 colunas) é para análise e é pesado "
           "demais para o navegador. Na web: carregue `web/processos_lavra_e_operacao.geojson` na abertura e os outros grupos sob demanda, "
           "ou use os vector tiles `web/processos_minerarios_go.pmtiles` (MapLibre + protomaps). A geometria NÃO foi simplificada: "
           "simplificar deformava poligonais legais pequenas (ver aba 13b).",
           "- GeoJSON em WGS 84 (RFC 7946); o GeoPackage mantém SIRGAS 2000 e resolução total (use-o no QGIS).",
           "- `amostras_geoquimicas_sgb_go` é evidência geológica: **não** simbolizar como ocorrência mineral nem como projeto.",
           "- Categorias de `processos_minerarios_go.categoria_mapa`:"]
linhas += [f"  - `{k}` — {v} ({int(cat_counts.get(k, 0)):,})".replace(",", ".") for k, v in CATEGORIAS.items()]
open(f"{OUTDIR}/LEIA-ME.md", "w", encoding="utf-8").write("\n".join(linhas) + "\n")

print("Camadas gravadas:")
for c in catalogo:
    print(f"   {c['camada_id']} {c['nome_camada']:32s} {c['n_feicoes']:>7} feições  {c['tamanho_geojson_mb'] or '-'} MB")
print("Auditoria:", len(auditoria), "linhas | GPKG:", round(os.path.getsize(GPKG) / 1e6, 1), "MB")
