# -*- coding: utf-8 -*-
"""Atualiza o protótipo (v1 -> v2): substitui 05_dim_municipios e 10_cons_municipio_ano por
dados REAIS cruzados de IBGE (malha + população + PIB), CFEM e Cadastro Mineiro, e adiciona a
aba de auditoria do cruzamento de município (pente fino)."""
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from caminhos import BASE, TMP  # caminhos relativos ao projeto — ver caminhos.py
SRC = f"{BASE}/documentacao/prototipo_bases_consolidadas_v1_base1.xlsx"
OUT = f"{BASE}/documentacao/prototipo_bases_consolidadas_v3.xlsx"

NAVY, TEAL, LBLUE, WHITE = "17365D", "1F6D7A", "DCE6F1", "FFFFFF"

mun_dim = json.load(open(f"{TMP}/_mun_dim.json", encoding="utf-8"))
crosswalk = json.load(open(f"{TMP}/_crosswalk_mun.json", encoding="utf-8"))
base2 = json.load(open(f"{TMP}/_base2_rows.json", encoding="utf-8"))

wb = openpyxl.load_workbook(SRC)


def style_header(ws, title, note, ncol):
    last_col = get_column_letter(ncol)
    ws.merge_cells(f"A1:{last_col}1")
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, color=WHITE, size=14)
    ws["A1"].fill = PatternFill("solid", fgColor=NAVY)
    ws.row_dimensions[1].height = 26
    ws.merge_cells(f"A2:{last_col}2")
    ws["A2"] = note
    ws["A2"].font = Font(italic=True, color="404040", size=10)
    ws["A2"].fill = PatternFill("solid", fgColor=LBLUE)
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[2].height = 60


def write_table(ws, columns, rows, table_name, header_row=4):
    ncol = len(columns)
    for i, c in enumerate(columns, start=1):
        cell = ws.cell(row=header_row, column=i, value=c["label"])
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=TEAL)
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    ws.row_dimensions[header_row].height = 28
    for r_i, row in enumerate(rows, start=header_row + 1):
        for c_i, c in enumerate(columns, start=1):
            val = row.get(c["key"], "")
            if val == "" or val is None:
                val = None
            cell = ws.cell(row=r_i, column=c_i, value=val)
            if c.get("fmt") and val is not None:
                cell.number_format = c["fmt"]
    last_row = header_row + max(1, len(rows))
    if rows:
        last_col = get_column_letter(ncol)
        tbl = Table(displayName=table_name, ref=f"A{header_row}:{last_col}{last_row}")
        tbl.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        ws.add_table(tbl)
    for i, c in enumerate(columns, start=1):
        ws.column_dimensions[get_column_letter(i)].width = c.get("width", 16)
    ws.freeze_panes = ws.cell(row=header_row + 1, column=min(4, ncol + 1)).coordinate


# ---------------------------------------------------------------------------
# 05_dim_municipios (REAL, 246 municípios)
# ---------------------------------------------------------------------------
del wb["05_dim_municipios"]
ws = wb.create_sheet("05_dim_municipios")
ws.sheet_view.showGridLines = False
cols = [
    dict(key="municipality_id", label="municipality_id", width=14),
    dict(key="municipio_nome", label="municipio_nome", width=26),
    dict(key="uf", label="uf", width=6),
    dict(key="area_km2", label="area_km2", width=12, fmt="#,##0.000"),
    dict(key="latitude", label="latitude", width=13, fmt="0.000000"),
    dict(key="longitude", label="longitude", width=13, fmt="0.000000"),
    dict(key="regiao_imediata", label="regiao_geografica_imediata", width=28),
    dict(key="regiao_intermediaria", label="regiao_geografica_intermediaria", width=26),
    dict(key="source_ids", label="source_ids", width=20),
]
rows = []
for mid, d in sorted(mun_dim.items(), key=lambda kv: kv[1]["municipio_nome"]):
    r = dict(d); r["source_ids"] = "SRC_IBGE_MALHA_2025"
    rows.append(r)
style_header(ws, "Dimensão — Municípios (v2, real)",
             "246 municípios de Goiás — malha oficial IBGE 2025. latitude/longitude = representative_point do polígono (garantido dentro do município; "
             "não é a sede municipal). Antes da v5 era o centro da caixa envolvente, que caía fora do próprio município em 20 casos. "
             "regiao_geografica_imediata/intermediaria = divisão regional oficial IBGE (útil para agrupar municípios em análises regionais).",
             len(cols))
write_table(ws, cols, rows, "DimMunicipiosV2")
print("05_dim_municipios (real) escrita:", len(rows), "municípios")

# ---------------------------------------------------------------------------
# 05b_crosswalk_municipios (nova)
# ---------------------------------------------------------------------------
if "05b_crosswalk_municipios" in wb.sheetnames:
    del wb["05b_crosswalk_municipios"]
ws2 = wb.create_sheet("05b_crosswalk_municipios")
ws2.sheet_view.showGridLines = False
cols2 = [
    dict(key="fonte", label="fonte", width=32),
    dict(key="valor_original", label="valor_original (bruto na fonte)", width=40),
    dict(key="valor_normalizado", label="valor_normalizado", width=28),
    dict(key="contagem", label="contagem", width=10, fmt="#,##0"),
    dict(key="municipio_atribuido", label="municipio_id / nome atribuído", width=32),
    dict(key="tipo_correspondencia", label="tipo_correspondência", width=32),
]
crosswalk.sort(key=lambda r: (r["fonte"], -(r["contagem"] if isinstance(r["contagem"], int) else 0)))
style_header(ws2, "Auditoria — Normalização e cruzamento da chave 'município' (pente fino)",
             "599 linhas cobrindo CFEM (por código IBGE, já vinha certo — usado como QA do nome) e Cadastro Mineiro (por nome, campo multivalorado 'Municipio(s)'). "
             "ACHADO IMPORTANTE: o filtro original de 'GO' (usado também na Base 1) testava se a STRING INTEIRA terminava em '- GO', o que (a) deixava de fora processos "
             "onde Goiás aparece no meio de uma lista multivalorada (ex.: 'Cachoeira Dourada - GO, Cachoeira Dourada - MG') e (b) por outro caminho (via Superintendência) "
             "também deixava ENTRAR por engano processos de outros estados cuja Superintendência regional da ANM é 'Goiás'. Corrigido aqui para checar CADA município do "
             "campo multivalorado individualmente contra a malha IBGE de GO. Tipo 'outro_estado_em_processo_de_fronteira' = município real de outro estado (MG/TO/MT/BA/MS/DF) "
             "citado numa mesma linha que também cita um município de Goiás (processo de fronteira) — mantido fora da dimensão de município de GO, mas a linha do processo "
             "continua contando para o(s) município(s) que É(são) de Goiás.",
             len(cols2))
write_table(ws2, cols2, crosswalk, "CrosswalkMunicipios")
print("05b_crosswalk_municipios escrita:", len(crosswalk), "linhas")

# ---------------------------------------------------------------------------
# 10_cons_municipio_ano (REAL)
# ---------------------------------------------------------------------------
del wb["10_cons_municipio_ano"]
ws3 = wb.create_sheet("10_cons_municipio_ano")
ws3.sheet_view.showGridLines = False
cols3 = [
    dict(key="municipality_id", label="municipality_id", width=14),
    dict(key="municipio_nome", label="municipio_nome", width=22),
    dict(key="uf", label="uf", width=6),
    dict(key="ano", label="ano", width=8, fmt="0"),
    dict(key="area_km2", label="area_km2", width=11, fmt="#,##0.0"),
    dict(key="latitude", label="latitude", width=13, fmt="0.000000"),
    dict(key="longitude", label="longitude", width=13, fmt="0.000000"),
    dict(key="cfem_recolhido_brl", label="cfem_recolhido_brl", width=16, fmt="#,##0"),
    dict(key="cfem_qtd_titulares_distintos", label="cfem_qtd_titulares_distintos", width=15, fmt="0"),
    dict(key="cfem_qtd_minerais_distintos", label="cfem_qtd_minerais_distintos", width=14, fmt="0"),
    dict(key="qtd_processos_cadastro_mineiro", label="qtd_processos_cadastro_mineiro", width=15, fmt="0"),
    dict(key="qtd_titulares_cadastro_mineiro", label="qtd_titulares_cadastro_mineiro", width=15, fmt="0"),
    dict(key="principais_minerais_cadastro", label="principais_minerais_cadastro (snapshot)", width=42),
    dict(key="populacao", label="populacao", width=11, fmt="#,##0"),
    dict(key="populacao_ano", label="populacao_ano", width=11, fmt="0"),
    dict(key="pib_total_brl", label="pib_total_brl", width=14, fmt="#,##0"),
    dict(key="pib_ano", label="pib_ano", width=9, fmt="0"),
    dict(key="regiao_imediata", label="regiao_geografica_imediata", width=26),
    dict(key="source_ids", label="source_ids", width=26),
    dict(key="observacao", label="observacao", width=40),
]
rows3 = sorted(base2, key=lambda r: (r["municipio_nome"], (r["ano"] is None, r["ano"])))
style_header(ws3, "Consolidada — Município × Ano (Goiás) — v2, dados reais",
             f"{len(rows3)} linhas, 246 municípios. CFEM por ano real (2022–2026); população (2025) e PIB (2023; o SIDRA publica em mil reais, convertido aqui para R$) são o 'último ano disponível' do IBGE, aparecem só na linha do respectivo ano — NÃO foram estimados para os outros anos. "
             "qtd_processos/titulares/principais_minerais do Cadastro Mineiro são uma FOTOGRAFIA atual (repetida em todas as linhas do município, não variam por ano). "
             "cfem_qtd_minerais_distintos usa o mesmo mineral_id canônico da Base 1 (01_dim_minerais) — ver 01b para o cruzamento completo da chave mineral. "
             "Limitação conhecida (mesma da Base 1 / QC06): SIGMINE não tem campo de município no atributo — a contagem de processos por município vem só do Cadastro Mineiro, não do SIGMINE.",
             len(cols3))
write_table(ws3, cols3, rows3, "ConsMunicipioAnoV2")
print("10_cons_municipio_ano (real) escrita:", len(rows3), "linhas")

# ---------------------------------------------------------------------------
# Nota de atualizacao no LEIA-ME
# ---------------------------------------------------------------------------
leia = wb["00_LEIA-ME"]
r = leia.max_row + 2
banner = leia.cell(row=r, column=2, value="ATUALIZAÇÃO v2 (Base 2 real — municípios)")
banner.font = Font(bold=True, size=12, color=WHITE)
banner.fill = PatternFill("solid", fgColor=TEAL)
leia.cell(row=r, column=1).fill = PatternFill("solid", fgColor=TEAL)
r += 1
texto = ("05_dim_municipios e 10_cons_municipio_ano agora são o cruzamento REAL de IBGE (malha 2025 + "
         "população 2025 + PIB 2023), CFEM e Cadastro Mineiro — ver a aba 05b_crosswalk_municipios. "
         "As demais abas (02–04, 06–08, 11–14) ainda são a maquete ilustrativa da v0.")
cell = leia.cell(row=r, column=2, value=texto)
cell.font = Font(size=10.5)
cell.alignment = Alignment(wrap_text=True, vertical="top")
leia.row_dimensions[r].height = 44

r += 2
banner3 = leia.cell(row=r, column=2, value="ATUALIZAÇÃO v3 — correção do filtro de município (afeta Bases 1 e 2)")
banner3.font = Font(bold=True, size=12, color=WHITE)
banner3.fill = PatternFill("solid", fgColor="C65911")
leia.cell(row=r, column=1).fill = PatternFill("solid", fgColor="C65911")
r += 1
texto3 = ("O Cadastro Mineiro é um arquivo NACIONAL e o campo 'Municipio(s)' é multivalorado. O filtro de Goiás "
          "usado nas versões v1/v2 tinha três defeitos, todos corrigidos nesta versão: (1) testava se a STRING "
          "INTEIRA terminava em '- GO', perdendo processos de divisa em que Goiás não é o último item da lista; "
          "(2) aceitava a linha quando a Superintendência regional da ANM era a de Goiás, deixando entrar processos "
          "inteiramente de outros estados (a jurisdição administrativa não segue a fronteira estadual); e (3) ao "
          "remover o sufixo '- UF' e casar pelo nome, atribuía a Goiás 24 municípios HOMÔNIMOS de outros estados "
          "(Mundo Novo-MS/BA, Santa Isabel-SP, Nova Veneza-SC, Cachoeira Dourada-MG, Barro Alto-BA, Lagoa Santa-MG, "
          "Morrinhos-CE, São Simão-SP, Hidrolândia-CE, Itajá-RN, Trindade-PE, Jussara-BA/PR, São Domingos-SE/BA/SC/PB, "
          "Formoso-MG, Iporá-PR, Piranhas-AL, Nova Aurora-PR, Davinópolis-MA, Estrela do Norte-SP), somando 1.186 "
          "ocorrências. Efeito: na Base 1, 35 dos 59 minerais tiveram contagem de processos/titulares alterada "
          "(saldo -73 processos, com movimento nos dois sentidos); na Base 2, 19 municípios foram corrigidos "
          "(-850 processos no total) — os mais afetados foram Mundo Novo (204→65), Nova Veneza (119→24), "
          "Lagoa Santa (66→7) e Santa Isabel (140→71). Produção (ANM Bruta/Beneficiada), CFEM e SIGMINE NÃO foram "
          "afetados: têm recorte de UF próprio e não dependem desse filtro.")
cell3 = leia.cell(row=r, column=2, value=texto3)
cell3.font = Font(size=10.5)
cell3.alignment = Alignment(wrap_text=True, vertical="top")
leia.row_dimensions[r].height = 160

wb._sheets.sort(key=lambda ws: ws.title)
wb.active = 0
wb.save(OUT)
print("SALVO:", OUT)
