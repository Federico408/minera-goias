# -*- coding: utf-8 -*-
"""Camadas de mapa das abas 04 (projetos) e 06 (ocorrências): CAM_06 projetos_futuros e CAM_05 ocorrencias_minerais_recmin.

A Base 4 grava as camadas de municípios, processos, operações e geoquímica, mas roda ANTES de build_projetos_04 e
build_ocorrencias_06 (os dois leem a camada de processos que ela grava). Este passo roda depois deles e:
  - grava cada camada no GeoPackage da Base 4 (SIRGAS 2000, todas as colunas da aba) e em GeoJSON para a web
    (WGS 84, RFC 7946, colunas principais): um ponto por linha da aba, com as mesmas chaves;
  - troca as entradas reservadas CAM_05/CAM_06 do catálogo da aba 13 e registra na 13b a checagem dos pontos;
  - atualiza a tabela de outputs/mapas/LEIA-ME.md e gera uma prévia em PNG.
Coordenadas não são recalculadas aqui: 04 = ponto representativo da união dos processos do projeto; 06 = coordenada do
RECMIN (83% posicionada em carta 1:250.000).
"""
import json
import os
import sys

import geopandas as gpd
import pandas as pd
import pyogrio

sys.stdout.reconfigure(encoding="utf-8")
from caminhos import BASE, TMP  # caminhos relativos ao projeto — ver caminhos.py

OUTDIR = f"{BASE}/outputs/mapas"
GPKG = f"{OUTDIR}/minera_goias_mapas_v1.gpkg"
CRS_GEO = "EPSG:4674"
MARCA = "Camada exportada"  # prefixo das linhas de auditoria deste passo: rodar de novo não duplica

CAMADAS = [
    dict(camada_id="CAM_06", nome="projetos_futuros", json="_projetos_04.json", aba="04_dim_projetos", chave="project_id",
         descricao="Projetos que ainda não produzem — camada ANM do Radar de Projetos (um ponto por projeto da aba 04)",
         web=["project_id", "nome_projeto", "company_id", "razao_social", "mineral_id", "mineral_name", "municipality_id",
              "municipality_name", "tipo_projeto", "estagio", "classificacao_maturidade", "processo_ancora", "qtd_processos",
              "operation_ids", "area_ha", "data_evidencia", "status_validacao"],
         juncao="project_id → 04_dim_projetos; operation_ids → 03_dim_operacoes e CAM_02 (polígonos dos processos do projeto); "
                "company_id → 02_dim_empresas; mineral_id → 01_dim_minerais; municipality_id → 05_dim_municipios",
         simbologia="cor por classificacao_maturidade (provável, possível, sinal); brownfield (tipo_projeto) com contorno escuro — "
                    "símbolo diferente de processo, operação e ocorrência",
         ponto="ponto representativo da união dos processos do projeto (fica dentro dos polígonos)"),
    dict(camada_id="CAM_05", nome="ocorrencias_minerais_recmin", json="_ocorrencias_06.json", aba="06_dim_ocorrencias_geologicas", chave="occurrence_id",
         descricao="Ocorrências e depósitos minerais do RECMIN (SGB) dentro de Goiás — evidência geológica, não projeto (um ponto por linha da aba 06)",
         web=["occurrence_id", "nome_local", "mineral_ids", "mineral_names", "classe_utilitaria", "importancia", "status_economico",
              "situacao_explotacao", "municipality_id", "municipality_name", "metodo_geoposicionamento", "data_cadastro",
              "categoria_anm_sobreposta", "operation_ids_sobrepostos", "project_ids_sobrepostos", "status_validacao"],
         juncao="occurrence_id → 06_dim_ocorrencias_geologicas; mineral_ids → 01_dim_minerais (multivalorado); municipality_id → "
                "05_dim_municipios; operation_ids_sobrepostos → 03_dim_operacoes; project_ids_sobrepostos → 04_dim_projetos",
         simbologia="losango por importancia (Depósito, Ocorrência, Indício, Indeterminado) — nunca o mesmo símbolo de processo, operação ou projeto",
         ponto="coordenada do RECMIN; 83% posicionada em carta 1:250.000 (erro de centenas de metros)"),
]

catalogo = json.load(open(f"{TMP}/_mapas_catalogo.json", encoding="utf-8"))
auditoria = [a for a in json.load(open(f"{TMP}/_mapas_auditoria.json", encoding="utf-8"))
             if not str(a.get("verificacao", "")).startswith(MARCA)]
mun = pyogrio.read_dataframe(GPKG, layer="municipios_go", columns=["municipality_id", "municipio_nome"])
camadas = {}
for c in CAMADAS:
    d = json.load(open(f"{TMP}/{c['json']}", encoding="utf-8"))
    df = pd.DataFrame(d["linhas"], columns=d["colunas"])
    assert df[c["chave"]].notna().all() and df[c["chave"]].is_unique, f"{c['nome']}: {c['chave']} vazio ou repetido"
    sem_coord = df["latitude"].isna() | df["longitude"].isna()
    assert not sem_coord.any(), f"{c['nome']}: {int(sem_coord.sum())} linhas sem coordenada"
    faltam = [k for k in c["web"] if k not in df.columns]
    assert not faltam, f"{c['nome']}: colunas da versão web ausentes na aba: {faltam}"
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["longitude"], df["latitude"]), crs=CRS_GEO)
    gdf.to_file(GPKG, layer=c["nome"], driver="GPKG", engine="pyogrio", OVERWRITE="YES")
    path = f"{OUTDIR}/{c['nome']}.geojson"
    if os.path.exists(path):
        os.remove(path)
    gdf[c["web"] + ["geometry"]].to_file(path, driver="GeoJSON", engine="pyogrio", RFC7946="YES", COORDINATE_PRECISION=6)
    camadas[c["nome"]] = gdf

    # checagem dos pontos: dentro da malha de Goiás e no mesmo município da aba
    j = gpd.sjoin(gdf[[c["chave"], "municipality_id", "geometry"]],
                  mun.rename(columns={"municipality_id": "mun_malha"})[["mun_malha", "geometry"]], predicate="within", how="left")
    j = j[~j.index.duplicated(keep="first")]
    fora = j["mun_malha"].isna()
    difere = ~fora & (j["mun_malha"].astype(str) != j["municipality_id"].astype(str))
    exemplos = ", ".join(j.loc[fora | difere, c["chave"]].astype(str).head(8))
    causa = ""
    if c["camada_id"] == "CAM_06" and (fora.any() or difere.any()):
        # projeto = união de processos: confere nos polígonos por que o ponto sai do estado ou do município da aba
        proc = pyogrio.read_dataframe(GPKG, layer="processos_minerarios_go", columns=["operation_id"]).set_index("operation_id").geometry
        go, mung = mun.union_all(), mun.set_index("municipality_id").geometry

        def uniao(ids):
            return gpd.GeoSeries([proc[i] for i in str(ids).split("; ") if i in proc.index], crs=CRS_GEO).union_all()

        cruza = sum(0 < uniao(r["operation_ids"]).intersection(go).area < uniao(r["operation_ids"]).area
                    for _, r in gdf.loc[j.index[fora]].iterrows())
        multi = sum(uniao(r["operation_ids"]).intersects(mung[m]) and sum(uniao(r["operation_ids"]).intersects(g) for g in mung.values) > 1
                    for (_, r), m in zip(gdf.loc[j.index[difere]].iterrows(), j.loc[difere, "mun_malha"]))
        causa = (f" Conferido nos polígonos: {cruza} de {int(fora.sum())} pontos fora de GO são projetos cujos processos cruzam a divisa (parte em Goiás); "
                 f"{multi} de {int(difere.sum())} em outro município são projetos em mais de um município, com o ponto num município que os "
                 "processos tocam (a aba 04 usa o município de maior área do processo-âncora).")
    auditoria.append(dict(
        camada=c["nome"], verificacao=f"{MARCA}: ponto dentro da malha de Goiás e no mesmo município da aba {c['aba'][:2]}",
        n=int(fora.sum() + difere.sum()),
        resultado=(f"{len(gdf):,} pontos; fora da malha de GO: {int(fora.sum())}; em outro município: {int(difere.sum())}".replace(",", ".")
                   + (f" (ex.: {exemplos})" if exemplos else "")),
        decisao=f"Coordenada e município mantidos como na aba {c['aba'][:2]} (não recalculados aqui). Ponto: {c['ponto']}.{causa}"))
    auditoria.append(dict(
        camada=c["nome"], verificacao=f"{MARCA}: {c['chave']} único e uma feição por linha da aba {c['aba'][:2]}",
        n=0, resultado=f"{len(gdf):,} feições = {len(df):,} linhas; {c['chave']} sem vazio nem repetição".replace(",", "."),
        decisao="A camada carrega as chaves da aba; atributos completos no GeoPackage, principais no GeoJSON."))

    fontes = "; ".join(dict.fromkeys(s.strip() for v in df["source_id"].dropna() for s in str(v).split(";") if s.strip()))
    entrada = dict(
        camada_id=c["camada_id"], nome_camada=c["nome"], descricao=c["descricao"], tipo_geometria="Point", n_feicoes=len(gdf),
        arquivo_geojson=f"outputs/mapas/{c['nome']}.geojson", tamanho_geojson_mb=round(os.path.getsize(path) / 1e6, 1),
        camada_gpkg=f"outputs/mapas/minera_goias_mapas_v1.gpkg › {c['nome']}",
        crs="GeoJSON: WGS 84 (RFC 7946) | GPKG: SIRGAS 2000 (EPSG:4674)",
        simplificacao_web=f"nenhuma — {len(c['web'])} colunas no GeoJSON; as {len(df.columns)} da aba no GPKG",
        chave_primaria=c["chave"], chaves_de_juncao=c["juncao"], source_ids=fontes, simbologia=c["simbologia"],
        observacao=f"Gerada por build_mapas_04_06.py a partir da aba {c['aba']}. Ponto: {c['ponto']}.")
    i = next(k for k, x in enumerate(catalogo) if x["camada_id"] == c["camada_id"])
    catalogo[i] = entrada

with open(f"{TMP}/_mapas_catalogo.json", "w", encoding="utf-8") as f:
    json.dump(catalogo, f, ensure_ascii=False)
with open(f"{TMP}/_mapas_auditoria.json", "w", encoding="utf-8") as f:
    json.dump(auditoria, f, ensure_ascii=False)

# LEIA-ME das camadas (escrito pela Base 4): troca as linhas "NÃO GERADA" e explica a origem das duas camadas
leia = f"{OUTDIR}/LEIA-ME.md"
if os.path.exists(leia):
    linhas = open(leia, encoding="utf-8").read().rstrip("\n").split("\n")
    for c in catalogo:
        if c["camada_id"] in ("CAM_05", "CAM_06"):
            nova = f"| {c['nome_camada']} | {c['tipo_geometria']} | {c['n_feicoes']:,} | {c['arquivo_geojson']} | {c['chave_primaria']} |".replace(",", ".")
            linhas = [nova if l.startswith(f"| {c['nome_camada']} |") else l for l in linhas]
    nota = ("- `projetos_futuros` (aba 04) e `ocorrencias_minerais_recmin` (aba 06) são gravadas por `build_mapas_04_06.py`, depois das abas. "
            "Projeto, ocorrência, processo e operação têm símbolos diferentes; prévia em `preview_mapa_projetos_ocorrencias.png`.")
    if nota not in linhas:
        linhas.append(nota)
    open(leia, "w", encoding="utf-8").write("\n".join(linhas) + "\n")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

CLASSE = {"provável": "#0F6FB0", "possível": "#0D9488", "sinal": "#9AA9B4"}
IMPORTANCIA = {"Depósito": "#C2681B", "Ocorrência": "#8250C4", "Indício": "#B03A55", "Indeterminado": "#D9C09A"}
fig, (a1, a2) = plt.subplots(1, 2, figsize=(17, 9.5))
for ax in (a1, a2):
    mun.plot(ax=ax, facecolor="#FBFBF8", edgecolor="#8A9099", linewidth=0.3)
    ax.set_axis_off()
p = camadas["projetos_futuros"]
for k in ["sinal", "possível", "provável"]:
    p[p["classificacao_maturidade"] == k].plot(ax=a1, color=CLASSE[k], markersize=7, alpha=0.85)
bf = p[p["tipo_projeto"].astype(str).str.startswith("brownfield")]
bf.plot(ax=a1, facecolor="none", edgecolor="black", markersize=30, linewidth=0.7)
a1.legend(handles=[Line2D([], [], marker="o", ls="", color=CLASSE[k], label=f"{k} ({int((p['classificacao_maturidade'] == k).sum()):,})".replace(",", "."))
                   for k in CLASSE] + [Line2D([], [], marker="o", ls="", markerfacecolor="none", markeredgecolor="black", label=f"brownfield ({len(bf)})")],
          loc="lower left", fontsize=9, title="Classificação", title_fontsize=9)
a1.set_title(f"Projetos que ainda não produzem (aba 04) — {len(p):,} pontos".replace(",", "."), fontsize=12)
o = camadas["ocorrencias_minerais_recmin"]
for k in ["Indeterminado", "Indício", "Ocorrência", "Depósito"]:
    o[o["importancia"] == k].plot(ax=a2, color=IMPORTANCIA[k], marker="D", markersize=9, alpha=0.85)
a2.legend(handles=[Line2D([], [], marker="D", ls="", color=IMPORTANCIA[k], label=f"{k} ({int((o['importancia'] == k).sum()):,})".replace(",", "."))
                   for k in IMPORTANCIA], loc="lower left", fontsize=9, title="Importância (RECMIN)", title_fontsize=9)
a2.set_title(f"Ocorrências e depósitos minerais (aba 06) — {len(o):,} pontos".replace(",", "."), fontsize=12)
fig.savefig(f"{OUTDIR}/preview_mapa_projetos_ocorrencias.png", dpi=120, bbox_inches="tight")
plt.close(fig)

for c in catalogo:
    if c["camada_id"] in ("CAM_05", "CAM_06"):
        print(f"{c['camada_id']} {c['nome_camada']}: {c['n_feicoes']} pontos, {c['tamanho_geojson_mb']} MB | fontes: {c['source_ids']}")
for a in auditoria:
    if str(a["verificacao"]).startswith(MARCA):
        print(f"  13b {a['camada']}: n={a['n']} | {a['resultado']}")
print("camadas no GeoPackage:", [n for n, _ in pyogrio.list_layers(GPKG)])
