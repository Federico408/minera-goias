# -*- coding: utf-8 -*-
"""Abas 04 e 04b (v5 -> v5a_projetos): camada ANM do Radar de Projetos gerada por build_projetos_04.py.
Depois entram a 12 (write_interface_12), a 08 (write_fato_08) e a governança valida tudo."""
import json
import sys

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

sys.stdout.reconfigure(encoding="utf-8")
from caminhos import BASE, TMP  # caminhos relativos ao projeto — ver caminhos.py
SRC = f"{BASE}/documentacao/prototipo_bases_consolidadas_v5a_ocorrencias.xlsx"  # v5 + abas 06/06b reais (write_ocorrencias_06)
OUT = f"{BASE}/documentacao/prototipo_bases_consolidadas_v5b_projetos.xlsx"
HDR = 4
NAVY, TEAL, LBLUE, WHITE = "17365D", "1F6D7A", "DCE6F1", "FFFFFF"

p04 = json.load(open(f"{TMP}/_projetos_04.json", encoding="utf-8"))
p04b = json.load(open(f"{TMP}/_projetos_04b.json", encoding="utf-8"))
res = json.load(open(f"{TMP}/_projetos_04_resumo.json", encoding="utf-8"))
LARG = dict(project_id=19, nome_projeto=46, company_id=21, razao_social=30, mineral_id=10, mineral_name=22, municipality_id=11, municipality_name=20,
            latitude=11, longitude=11, tipo_projeto=26, estagio=30, classificacao_maturidade=12, criterio_classificacao=46, capacidade_t_ano=12,
            capex_brl=12, ano_previsto_entrada=10, processo_ancora=13, qtd_processos=9, processos_anm=30, operation_ids=30, area_ha=12,
            relatorio_final_aprovado=10, evento_licenciamento_ambiental=11, operacao_adjacente=24, data_evidencia=12, ultimo_evento=50,
            valor_observado_estimado=11, status_validacao=24, responsavel_validacao=30, source_id=40, source_url=50, data_acesso=24,
            periodo_referencia=30, tipo_fonte=9, observacao=60,
            tipo_evento=56, classe_evento=22, palavra_chave=18, processos=10, fases=56, exemplo_processo=14, vira_projeto=10)
FMT = dict(latitude="0.000000", longitude="0.000000", area_ha="#,##0.00", qtd_processos="0", processos="#,##0",
           capacidade_t_ano="#,##0", capex_brl="#,##0", ano_previsto_entrada="0")


def br(x, casas=0):
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def escrever(wb, aba, titulo, nota, dados, tabela, altura, pos=None):
    if aba in wb.sheetnames:
        pos = wb.sheetnames.index(aba) if pos is None else pos
        del wb[aba]
    ws = wb.create_sheet(aba, pos) if pos is not None else wb.create_sheet(aba)
    ws.sheet_view.showGridLines = False
    cols, linhas = dados["colunas"], dados["linhas"]
    last = get_column_letter(len(cols))
    ws.merge_cells(f"A1:{last}1")
    ws["A1"] = titulo
    ws["A1"].font = Font(bold=True, color=WHITE, size=14)
    ws["A1"].fill = PatternFill("solid", fgColor=NAVY)
    ws.row_dimensions[1].height = 26
    ws.merge_cells(f"A2:{last}2")
    ws["A2"] = nota
    ws["A2"].font = Font(italic=True, color="404040", size=10)
    ws["A2"].fill = PatternFill("solid", fgColor=LBLUE)
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[2].height = altura
    for i, c in enumerate(cols, start=1):
        cell = ws.cell(row=HDR, column=i, value=c)
        cell.font = Font(bold=True, color=WHITE)
        cell.fill = PatternFill("solid", fgColor=TEAL)
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    ws.row_dimensions[HDR].height = 30
    fmt_col = {cols.index(k): f for k, f in FMT.items() if k in cols}
    for r_i, linha in enumerate(linhas, start=HDR + 1):
        for c_i, v in enumerate(linha):
            if v is None or v == "":
                continue
            cell = ws.cell(row=r_i, column=c_i + 1, value=v)
            if c_i in fmt_col:
                cell.number_format = fmt_col[c_i]
    t = Table(displayName=tabela, ref=f"A{HDR}:{last}{HDR + max(1, len(linhas))}")
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(t)
    for i, c in enumerate(cols, start=1):
        ws.column_dimensions[get_column_letter(i)].width = LARG.get(c, 16)
    ws.freeze_panes = ws.cell(row=HDR + 1, column=3).coordinate
    print(f"{aba} escrita: {len(linhas)} linhas × {len(cols)} colunas")


wb = openpyxl.load_workbook(SRC)
pc, pe = res["por_classe"], res["por_estagio"]
nota04 = (
    f"CAMADA ANM do Radar de Projetos (o radar completo é entrega do Squad 1 / Estudante 2). {br(res['projetos'])} projetos que ainda NÃO produzem, "
    f"formados por {br(res['processos_vivos'])} processos de Goiás em estágio de desenvolvimento: título de lavra sem CFEM em 2024–2026, pré-lavra ou "
    f"requerimento de licenciamento/lavra garimpeira. Ficaram de fora {br(res['terminais'])} processos cujo último evento é terminal (indeferimento, "
    f"desistência, baixa, caducidade, renúncia — regras na 04b) e {br(res['pesquisa_fora'])} processos de pesquisa (processo de pesquisa não é projeto; guia, "
    "seção 9). Processos contíguos (≤ 100 m) do mesmo titular e mineral são um projeto; project_id = PRJ_ + processo-âncora (o de estágio mais avançado). "
    f"Classificação só com evidência da ANM, com teto em 'provável': provável {br(pc.get('provável', 0))}, possível {br(pc.get('possível', 0))}, "
    f"sinal {br(pc.get('sinal', 0))} (critério em criterio_classificacao). 'Definido', 'construção' e 'expansão' exigem RI, CVM ou SEMAD; capacidade, CAPEX e "
    f"ano previsto ficam VAZIOS de propósito. {br(res['brownfield'])} projetos estão a até 500 m de operação ativa do mesmo titular e mineral (candidatos a "
    "expansão). Só o último evento de cada processo está nos dados abertos: o histórico completo (licença ambiental obtida, PAE analisado) está nos microdados "
    "do SCM (ProcessoEvento.txt), ainda não baixados.")
escrever(wb, "04_dim_projetos", "Dimensão — Projetos: camada ANM do Radar de Projetos (v10, real)", nota04, p04, "DimProjetosV10", 110)
tc = res["tipos_por_classe"]
nota04b = (
    f"{res['tipos_evento']} tipos de último evento do SIGMINE nos {br(res['universo'])} processos candidatos, cada um com a classe atribuída: encerramento "
    f"({tc.get('encerramento', 0)} tipos — o processo NÃO vira projeto), disputa ({tc.get('disputa', 0)} — vira projeto, classe no máximo 'sinal'), "
    f"licenciamento_ambiental ({tc.get('licenciamento_ambiental', 0)}) e andamento ({tc.get('andamento', 0)}). A primeira regra que casa vence, na ordem "
    "exceções → encerramento → disputa → licenciamento ambiental; palavra_chave mostra o trecho que decidiu. Exceções revistas uma a uma: 'torna sem efeito', "
    "'recurso provido', 'opção de regime', 'guia de utilização', 'desistência parcial' e 'arquivamento de auto de embargo' não encerram o processo; "
    "'reconsideração negada' encerra; 'instaura processo administrativo' e 'processo sancionador instaurado' são disputa; 'memorial para eventual contestação' não é disputa; "
    "multas, autos de infração e prorrogação de prazo negada ficam em andamento (não encerram o processo). A coluna 'Situação' "
    "do Cadastro Mineiro não serve para isso: é 'Sim' (ativo) em 100% das linhas dos dados abertos.")
escrever(wb, "04b_eventos_anm_classificados", "Auditoria — Último evento dos processos na ANM: classe atribuída (v10)", nota04b, p04b, "EventosAnmV10", 70)
wb._sheets.sort(key=lambda s: s.title)
wb.save(OUT)
print("SALVO:", OUT)
