# -*- coding: utf-8 -*-
"""Base 2 -- Municipio x Ano (Goias). Normaliza a chave 'municipio' entre a malha IBGE 2025,
CFEM e Cadastro Mineiro (mesmo "pente fino" da Base 1), cruza com populacao/PIB (IBGE) e produz
a base consolidada + a auditoria do cruzamento."""
import glob, json, re, struct, sys, unicodedata, zipfile
from collections import Counter, defaultdict
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
from caminhos import BASE, TMP, arquivo  # caminhos relativos ao projeto — ver caminhos.py


def norm(s):
    s = re.sub(r"\s+", " ", str(s)).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def strip_uf_suffix(s):
    return re.sub(r"\s*-\s*[A-Z]{2}\s*$", "", str(s).strip(), flags=re.I).strip()


def go_municipio_id(token):
    """Codigo IBGE se o token e um municipio de Goias; None caso contrario.

    NAO basta remover o sufixo '- UF' e casar pelo nome: 24 municipios de outros estados sao
    homonimos de municipios goianos (MUNDO NOVO - MS, SANTA ISABEL - SP, NOVA VENEZA - SC,
    CACHOEIRA DOURADA - MG, BARRO ALTO - BA, LAGOA SANTA - MG, MORRINHOS - CE, SAO SIMAO - SP...),
    somando 1.186 ocorrencias no Cadastro Mineiro. Se houver sufixo de UF e ele nao for 'GO',
    o token e rejeitado sem tentar casar pelo nome.
    """
    t = str(token).strip()
    m = re.search(r"-\s*([A-Za-z]{2})\s*$", t)
    if m:
        if m.group(1).upper() != "GO":
            return None
        t = t[:m.start()].strip()
    return NAME2ID.get(norm(t))


def read_csv(path, sep=",", encoding="cp1252"):
    return pd.read_csv(path, sep=sep, encoding=encoding, encoding_errors="replace",
                        dtype=str, keep_default_na=False, engine="python", on_bad_lines="skip")


def split_multi(v):
    v = re.sub(r"\s+", " ", str(v)).strip()
    return [x.strip() for x in re.split(r"[,;]", v) if x.strip()]


def read_dbf_bytes(data, encoding="utf-8"):
    n_records = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    fields, pos = [], 32
    while data[pos] != 0x0D:
        desc = data[pos:pos + 32]
        name = desc[:11].split(b"\x00", 1)[0].decode("ascii", "replace")
        fields.append((name, desc[16]))
        pos += 32
    rows, pos = [], header_len
    for _ in range(n_records):
        raw = data[pos:pos + record_len]
        pos += record_len
        if not raw or raw[0:1] == b"*":
            continue
        rpos, row = 1, {}
        for name, length in fields:
            row[name] = raw[rpos:rpos + length].decode(encoding, "replace").strip()
            rpos += length
        rows.append(row)
    return rows


def shape_bbox_centers(data):
    centers, pos = [], 100
    while pos + 8 <= len(data):
        _, words = struct.unpack(">2i", data[pos:pos + 8])
        content = data[pos + 8:pos + 8 + words * 2]
        pos += 8 + words * 2
        if len(content) < 4:
            centers.append((None, None)); continue
        shape_type = struct.unpack("<i", content[:4])[0]
        if shape_type == 0:
            centers.append((None, None))
        elif shape_type == 1 and len(content) >= 20:
            x, y = struct.unpack("<2d", content[4:20]); centers.append((x, y))
        elif len(content) >= 36:
            xmin, ymin, xmax, ymax = struct.unpack("<4d", content[4:36])
            centers.append(((xmin + xmax) / 2, (ymin + ymax) / 2))
        else:
            centers.append((None, None))
    return centers


def to_num(s):
    s = str(s).strip()
    if not s or s in {"-", ",00", "..", "...", "X"}:
        return None
    s = s.replace(".", "").replace(",", ".") if "," in s else s
    try:
        return float(s)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# 1) IBGE malha -- dimensao canonica de municipios (246)
# ---------------------------------------------------------------------------
import geopandas as gpd

_malha = gpd.read_file("zip://" + arquivo("dados/IBGE/GO_Municipios_2025.zip") + "!GO_Municipios_2025.shp")
# CORRECAO (v5): latitude/longitude eram o centro da caixa envolvente do poligono, que cai FORA do
# proprio municipio em 20 dos 246 casos (Jussara, Itaja, Pires do Rio, Goianira...). O
# representative_point e garantido dentro do poligono.
_rp = _malha.geometry.representative_point()
MUN_DIM = {}
for r, pt in zip(_malha.drop(columns="geometry").to_dict("records"), _rp):
    MUN_DIM[r["CD_MUN"]] = dict(
        municipality_id=r["CD_MUN"], municipio_nome=r["NM_MUN"], uf="GO",
        area_km2=to_num(r["AREA_KM2"]), latitude=round(pt.y, 6), longitude=round(pt.x, 6),
        regiao_imediata=r["NM_RGI"], regiao_intermediaria=r["NM_RGINT"],
    )
NAME2ID = {norm(r["municipio_nome"]): r["municipality_id"] for r in MUN_DIM.values()}
print(f"Malha IBGE 2025: {len(MUN_DIM)} municípios de Goiás carregados.")

# ---------------------------------------------------------------------------
# 2) CFEM -- ja tem CodigoMunicipio (usar como chave primaria; nome so para QA)
# ---------------------------------------------------------------------------
cfem = read_csv(arquivo("dados/ANM/cfem/CFEM_Arrecadacao_2022_2026_GO.csv"), sep=";")
cfem["_cod"] = cfem["CodigoMunicipio"].str.split(".").str[0]
cfem["_ano"] = pd.to_numeric(cfem["Ano"], errors="coerce")

crosswalk = []
qa_bad = []
for cod, nome in cfem[["_cod", "Município"]].drop_duplicates().itertuples(index=False):
    if cod in MUN_DIM:
        nome_ibge = MUN_DIM[cod]["municipio_nome"]
        tipo = "identico_por_codigo" if norm(nome) == norm(nome_ibge) else "codigo_bate_nome_diverge_grafia"
        crosswalk.append(dict(fonte="CFEM(GO)", valor_original=f"{cod} / {nome}", valor_normalizado=norm(nome),
                               contagem=int((cfem["_cod"] == cod).sum()), municipio_atribuido=f"{cod} — {nome_ibge}",
                               tipo_correspondencia=tipo))
    else:
        qa_bad.append((cod, nome))
        crosswalk.append(dict(fonte="CFEM(GO)", valor_original=f"{cod} / {nome}", valor_normalizado=norm(nome),
                               contagem=int((cfem["_cod"] == cod).sum()), municipio_atribuido="SEM_CORRESPONDENCIA",
                               tipo_correspondencia="sem_correspondencia"))
print(f"CFEM: {cfem['_cod'].nunique()} códigos de município distintos; sem correspondência na malha: {len(qa_bad)}")
for b in qa_bad:
    print("  ", b)

# ---------------------------------------------------------------------------
# 3) Cadastro Mineiro -- "Municipio(s)" multivalorado, sem codigo -- casar por NOME
#    (pente fino: usar o filtro por TOKEN, nao pela string toda, e revisar residuais)
# ---------------------------------------------------------------------------
cad_rows = []  # (municipio_id, processo, titular, cpf_cnpj, substancia_raw)
non_go_tokens = Counter()
seen_names_go = Counter()
for path in sorted(glob.glob(arquivo("dados/ANM/cadastro_mineiro/*.csv"))):
    df = read_csv(path)
    muncol = next((c for c in df.columns if "unicipio" in c.lower()), None)
    if muncol is None:
        continue
    proccol = next((c for c in df.columns if c.strip() == "Processo"), None)
    titcol = next((c for c in df.columns if c.strip() == "Titular"), None)
    doccol = next((c for c in df.columns if "CPF/CNPJ" in c), None)
    subcol = next((c for c in df.columns if "ubst" in c), None)
    usocol = next((c for c in df.columns if "Uso" in c), None)
    for _, r in df.iterrows():
        mun_raw = str(r.get(muncol, ""))
        tokens = split_multi(mun_raw)
        go_ids, non_go_in_row = [], []
        for t in tokens:
            mid = go_municipio_id(t)
            if mid:
                go_ids.append(mid)
                seen_names_go[t] += 1
            else:
                non_go_in_row.append(t)
        if not go_ids:
            continue  # linha sem nenhum municipio de GO -- fora do escopo, nao e "residual", e so nao-GO mesmo
        for t in non_go_in_row:
            non_go_tokens[t] += 1  # municipio real de outro estado, coexistindo numa linha que TEM um municipio GO valido
        for mid in set(go_ids):
            cad_rows.append((mid, r.get(proccol, ""), r.get(titcol, ""), r.get(doccol, ""), r.get(subcol, ""),
                             r.get(usocol, "") if usocol else ""))

print(f"Cadastro Mineiro: {len(cad_rows)} linhas (município-processo) válidas em GO; "
      f"{len(non_go_tokens)} municípios de outro estado identificados coexistindo em processos de fronteira "
      f"({sum(non_go_tokens.values())} ocorrências) -- excluídos da dimensão GO, mas a linha do processo foi mantida "
      f"pelo(s) município(s) que É(são) de Goiás.")
for raw, cnt in non_go_tokens.most_common():
    crosswalk.append(dict(fonte="Cadastro_Mineiro(GO, token multivalorado)", valor_original=raw, valor_normalizado=norm(strip_uf_suffix(raw)),
                          contagem=cnt, municipio_atribuido="(excluído — município de outro estado, ver observação)",
                          tipo_correspondencia="outro_estado_em_processo_de_fronteira"))
for raw, cnt in seen_names_go.most_common():
    mid = go_municipio_id(raw)
    crosswalk.append(dict(fonte="Cadastro_Mineiro(GO)", valor_original=raw, valor_normalizado=norm(strip_uf_suffix(raw)),
                          contagem=cnt, municipio_atribuido=f"{mid} — {MUN_DIM[mid]['municipio_nome']}",
                          tipo_correspondencia="identico_apos_remover_sufixo_GO"))

print(f"\nTotal de município(s) distintos citados no Cadastro Mineiro que batem com a malha GO: "
      f"{len({r[0] for r in cad_rows})} de {len(MUN_DIM)}.")

with open(f"{TMP}/_crosswalk_mun.json", "w", encoding="utf-8") as f:
    json.dump(crosswalk, f, ensure_ascii=False)
print("crosswalk município salvo:", len(crosswalk), "linhas")

# reaproveita a dimensao canonica de minerais da Base 1 (mesmas definicoes, sem duplicar).
# Corta no marcador em vez de por numero de linha, para nao quebrar quando a Base 1 for editada.
_b1_src = open(f"{BASE}/base_consolidada_work/scripts/build_base1_mineral_ano.py", encoding="utf-8").read()
_b1_defs = _b1_src.split("# 2) Carregar as fontes")[0]
_b1_ns = {}
exec(_b1_defs, _b1_ns)  # so as definicoes: norm, MIN_DEF, RAW2KEY, ANM_CATEGORY_TO_KEY
RAW2KEY_MIN = _b1_ns["RAW2KEY"]
MIN_DEF = _b1_ns["MIN_DEF"]
mineral_key_com_uso, canon_proc, eh_rocha = _b1_ns["mineral_key_com_uso"], _b1_ns["canon_proc"], _b1_ns["eh_rocha"]
# uso das rochas por processo e uso majoritário em GO, calculados pela Base 1 (que roda antes)
USO_ROCHAS = json.load(open(f"{TMP}/_uso_rochas.json", encoding="utf-8"))


def mineral_key_of(raw, uso=None):
    return mineral_key_com_uso(raw, uso, USO_ROCHAS["padrao"])[0]


def mineral_key_cfem(raw, processo, ano_processo=""):
    """Rochas na CFEM: o uso vem do processo (a CFEM não tem campo de uso)."""
    uso = None
    if eh_rocha(raw):
        pc = canon_proc(processo, ano_processo)
        uso = USO_ROCHAS["proc_subst"].get(f"{pc}|{norm(raw)}") or USO_ROCHAS["proc"].get(pc)
    return mineral_key_of(raw, uso)


# ---------------------------------------------------------------------------
# 4) IBGE -- populacao e PIB municipais (SIDRA), filtrado a GO (D1C comeca com 52)
# ---------------------------------------------------------------------------
pop = json.load(open(arquivo("dados/IBGE/populacao_municipal_goias_ultimo_ano.json"), encoding="utf-8"))[1:]
pib = json.load(open(arquivo("dados/IBGE/pib_municipal_goias_ultimo_ano.json"), encoding="utf-8"))[1:]
pop_by_mun = {}
for r in pop:
    if r["D1C"].startswith("52") and len(r["D1C"]) == 7:
        pop_by_mun[r["D1C"]] = (to_num(r["V"]), int(r["D3C"]))
pib_by_mun = {}
_unidades_pib = Counter()
for r in pib:
    if r["D1C"].startswith("52") and len(r["D1C"]) == 7:
        # CORRECAO (v5): o SIDRA publica o PIB municipal em MIL reais (MN = 'Mil Reais'); a coluna da
        # base e em R$, entao converte. Sem isso Alto Horizonte aparecia com R$ 623 mil em vez de R$ 623 mi.
        _unidades_pib[r["MN"]] += 1
        fator = 1000 if r["MN"].strip().lower() == "mil reais" else 1
        v = to_num(r["V"])
        pib_by_mun[r["D1C"]] = (None if v is None else v * fator, int(r["D3C"]))
print("Unidade do PIB no SIDRA:", dict(_unidades_pib), "-> convertido para R$")
sem_pop = set(MUN_DIM) - set(pop_by_mun)
sem_pib = set(MUN_DIM) - set(pib_by_mun)
print(f"\nPopulação IBGE: {len(pop_by_mun)}/{len(MUN_DIM)} municípios (faltando: {sorted(MUN_DIM[m]['municipio_nome'] for m in sem_pop)})")
print(f"PIB IBGE: {len(pib_by_mun)}/{len(MUN_DIM)} municípios (faltando: {sorted(MUN_DIM[m]['municipio_nome'] for m in sem_pib)})")

# ---------------------------------------------------------------------------
# 5) Agregacao CFEM por (municipio, ano)
# ---------------------------------------------------------------------------
cfem_by_mun_ano = defaultdict(lambda: defaultdict(float))
cfem_titulares = defaultdict(lambda: defaultdict(set))
cfem_minerais = defaultdict(lambda: defaultdict(set))
for _, r in cfem.iterrows():
    cod, ano = r["_cod"], r["_ano"]
    if cod not in MUN_DIM or pd.isna(ano):
        continue
    ano = int(ano)
    v = to_num(r["ValorRecolhido"])
    if v is not None:
        cfem_by_mun_ano[cod][ano] += v
    doc = re.sub(r"\D", "", str(r["CPF_CNPJ"]))
    if doc:
        cfem_titulares[cod][ano].add(doc)
    mk = mineral_key_cfem(r["Substância"], r["Processo"], r["AnoDoProcesso"])
    if mk:
        cfem_minerais[cod][ano].add(mk)

# ---------------------------------------------------------------------------
# 6) Cadastro Mineiro -- snapshot por municipio (processos, titulares, top minerais)
# ---------------------------------------------------------------------------
cad_processos = defaultdict(set)
cad_titulares = defaultdict(set)
cad_minerais = defaultdict(Counter)
for mid, proc, tit, doc, subs, usos_raw in cad_rows:
    if proc:
        cad_processos[mid].add(proc)
    ident = re.sub(r"\D", "", str(doc)) or norm(tit)
    if ident:
        cad_titulares[mid].add(ident)
    _subs, _usos = split_multi(subs), split_multi(usos_raw)
    if len(_usos) != len(_subs):
        _usos = [""] * len(_subs)
    for s, u in zip(_subs, _usos):
        mk = mineral_key_of(s, u)
        if mk:
            cad_minerais[mid][mk] += 1

# ---------------------------------------------------------------------------
# 7) Montagem final -- Base 2 (municipio x ano)
# ---------------------------------------------------------------------------
base2_rows = []
for mid, dim in MUN_DIM.items():
    anos = sorted(set(cfem_by_mun_ano.get(mid, {}).keys()) | ({pop_by_mun[mid][1]} if mid in pop_by_mun else set()) | ({pib_by_mun[mid][1]} if mid in pib_by_mun else set()))
    if not anos:
        anos = [None]
    top_minerais = [MIN_DEF[k][0] for k, _ in cad_minerais.get(mid, Counter()).most_common(5)]
    for ano in anos:
        pop_v = pop_by_mun[mid][0] if (mid in pop_by_mun and pop_by_mun[mid][1] == ano) else None
        pib_v = pib_by_mun[mid][0] if (mid in pib_by_mun and pib_by_mun[mid][1] == ano) else None
        cfem_v = cfem_by_mun_ano.get(mid, {}).get(ano) if ano is not None else None
        n_tit_cfem = len(cfem_titulares.get(mid, {}).get(ano, set())) if ano is not None else None
        n_min_cfem = len(cfem_minerais.get(mid, {}).get(ano, set())) if ano is not None else None
        base2_rows.append(dict(
            municipality_id=mid, municipio_nome=dim["municipio_nome"], uf="GO", ano=ano,
            area_km2=dim["area_km2"], latitude=dim["latitude"], longitude=dim["longitude"],
            regiao_imediata=dim["regiao_imediata"], regiao_intermediaria=dim["regiao_intermediaria"],
            cfem_recolhido_brl=cfem_v, cfem_qtd_titulares_distintos=n_tit_cfem, cfem_qtd_minerais_distintos=n_min_cfem,
            populacao=pop_v, populacao_ano=pop_by_mun[mid][1] if mid in pop_by_mun else None,
            pib_total_brl=pib_v, pib_ano=pib_by_mun[mid][1] if mid in pib_by_mun else None,
            qtd_processos_cadastro_mineiro=len(cad_processos.get(mid, [])),
            qtd_titulares_cadastro_mineiro=len(cad_titulares.get(mid, [])),
            principais_minerais_cadastro="; ".join(top_minerais),
            # CORRECAO (v6): populacao e PIB vinham do IBGE sem serem citados; agora cada fonte entra se alguma
            # coluna da linha veio dela.
            source_ids="; ".join(s for s, usa in [
                ("SRC_IBGE_MALHA_2025", True), ("SRC_ANM_CFEM", cfem_v is not None or bool(n_tit_cfem)),
                ("SRC_ANM_CADASTRO", True), ("SRC_IBGE_POP", pop_v is not None), ("SRC_IBGE_PIB", pib_v is not None)] if usa),
            observacao="",
        ))

print(f"\nBase 2 (município x ano): {len(base2_rows)} linhas geradas para {len(MUN_DIM)} municípios.")
with open(f"{TMP}/_base2_rows.json", "w", encoding="utf-8") as f:
    json.dump(base2_rows, f, ensure_ascii=False)
with open(f"{TMP}/_mun_dim.json", "w", encoding="utf-8") as f:
    json.dump(MUN_DIM, f, ensure_ascii=False)
print("Arquivos intermediários da Base 2 salvos.")
