# -*- coding: utf-8 -*-
"""Aba 08 (v5 -> v5b_fato): grava o fato longo gerado por build_fato_08.py no lugar da maquete.
A governança (write_governanca_into_workbook.py) roda depois e valida a aba (cobertura das fontes,
conciliação com 09-11, campos de governança por linha e integridade referencial)."""
import json
import sys

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

sys.stdout.reconfigure(encoding="utf-8")
from caminhos import BASE, TMP  # caminhos relativos ao projeto — ver caminhos.py
SRC = f"{BASE}/documentacao/prototipo_bases_consolidadas_v5c_interface.xlsx"  # v5 + 06/06b + 04/04b + 12 (write_ocorrencias_06 → write_projetos_04 → write_interface_12)
OUT = f"{BASE}/documentacao/prototipo_bases_consolidadas_v5d_fato.xlsx"
ABA = "08_fato_producao_energia"
HDR = 4
NAVY, TEAL, LBLUE, WHITE = "17365D", "1F6D7A", "DCE6F1", "FFFFFF"

fato = json.load(open(f"{TMP}/_fato_08.json", encoding="utf-8"))
resumo = json.load(open(f"{TMP}/_fato_08_resumo.json", encoding="utf-8"))
COLS, LINHAS = fato["colunas"], fato["linhas"]
LARG = dict(fato_id=13, metrica=26, year=7, periodo_referencia=10, uf=5, mineral_id=10, mineral_name=24, company_id=21,
            operation_id=17, processo_anm=13, project_id=10, municipality_id=11, valor_original=18, unidade_original=9, tratamento=36,
            valor_tratado=16, unidade_padrao=9, production_basis=14, valor_observado_estimado=12, metodo_estimacao=14,
            erro_estimativa_intervalo=12, status_validacao=24, responsavel_validacao=34, source_id=20, tipo_fonte=9,
            source_url=44, data_acesso=11, source_file=40, source_linha=9, coluna_original=36, mineral_nome_original=26, notas=60)
FMT = {"year": "0", "source_linha": "0", "valor_tratado": "#,##0.00########"}


def br(n):
    return f"{n:,}".replace(",", ".")


wb = openpyxl.load_workbook(SRC)
pos = wb.sheetnames.index(ABA)
del wb[ABA]
ws = wb.create_sheet(ABA, pos)
ws.sheet_view.showGridLines = False
last = get_column_letter(len(COLS))
ws.merge_cells(f"A1:{last}1")
ws["A1"] = "Fato — Produção e CFEM em formato longo, rastreável até a célula da fonte (v8, real)"
ws["A1"].font = Font(bold=True, color=WHITE, size=14)
ws["A1"].fill = PatternFill("solid", fgColor=NAVY)
ws.row_dimensions[1].height = 26
ws.merge_cells(f"A2:{last}2")
n = resumo["linhas_por_fonte"]
ws["A2"] = (
    f"{br(len(LINHAS))} linhas = uma por célula numérica de 3 fontes: AMB produção bruta ({br(n['SRC_ANM_PROD_BRUTA'])}) e beneficiada "
    f"({br(n['SRC_ANM_PROD_BENEF'])}), todas as UFs, {resumo['periodo_amb']}; CFEM Goiás ({br(n['SRC_ANM_CFEM'])}), mensal, {resumo['periodo_cfem']}. "
    "valor_original é o texto da célula (nunca sobrescrito); valor_tratado é o valor final na unidade padrão (massa em t, R$ em BRL) e é o que as abas "
    "09, 10 e 11 somam — conciliação na 14b. source_file + source_linha + coluna_original apontam a célula exata. Fora da tabela ficam só "
    f"{br(resumo['celulas_fora']['contido_nao_se_aplica'])} células de contido com unidade '-' (não se aplica) e {br(resumo['celulas_fora']['vazias'])} células vazias. "
    "Não há linhas de energia: nenhuma fonte do Squad 1 mede consumo — elas entram com o Squad 2, identificadas em valor_observado_estimado e metodo_estimacao.")
ws["A2"].font = Font(italic=True, color="404040", size=10)
ws["A2"].fill = PatternFill("solid", fgColor=LBLUE)
ws["A2"].alignment = Alignment(wrap_text=True, vertical="center")
ws.row_dimensions[2].height = 66

for i, c in enumerate(COLS, start=1):
    cell = ws.cell(row=HDR, column=i, value=c)
    cell.font = Font(bold=True, color=WHITE)
    cell.fill = PatternFill("solid", fgColor=TEAL)
    cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
ws.row_dimensions[HDR].height = 30

# ~150 mil linhas: só cria célula para valor preenchido e reaproveita o mesmo objeto de texto (memória)
fmt_col = {COLS.index(k): f for k, f in FMT.items()}
cache = {}
for i in range(len(LINHAS)):
    linha, LINHAS[i] = LINHAS[i], None
    r_i = HDR + 1 + i
    for c_i, v in enumerate(linha):
        if v is None or v == "":
            continue
        if isinstance(v, str):
            v = cache.setdefault(v, v)
        cell = ws.cell(row=r_i, column=c_i + 1, value=v)
        f = fmt_col.get(c_i)
        if f:
            cell.number_format = f

t = Table(displayName="FatoProducaoV8", ref=f"A{HDR}:{last}{HDR + len(LINHAS)}")
t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ws.add_table(t)
for i, c in enumerate(COLS, start=1):
    ws.column_dimensions[get_column_letter(i)].width = LARG.get(c, 16)
ws.freeze_panes = ws.cell(row=HDR + 1, column=3).coordinate

wb.save(OUT)
print(f"{ABA} escrita: {len(LINHAS)} linhas × {len(COLS)} colunas -> {OUT}")
