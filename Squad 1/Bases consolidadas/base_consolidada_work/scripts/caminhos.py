# -*- coding: utf-8 -*-
"""Caminhos do pipeline, calculados a partir da posição DESTE arquivo — nenhum caminho fixo de uma máquina.

BASE    = pasta do projeto: a que contém documentacao/, outputs/ e base_consolidada_work/ (dois níveis acima de scripts/).
          Para rodar os scripts contra outra pasta, defina a variável de ambiente MINERA_BASE.
TMP     = JSONs intermediários entre as etapas. Padrão: <pasta temporária do sistema>/minera_goias_pipeline (fora do OneDrive
          e do git); para usar outra pasta, defina MINERA_TMP.
arquivo = traduz o caminho LÓGICO de um arquivo bruto — "dados/ANM/cfem/…", como as abas 07 e 08 citam — para o arquivo físico.
          Há dois arranjos:
            • cópia de trabalho: <BASE>/dados/<caminho lógico>;
            • GitHub: Squad 1/Dados brutos/<pasta da fonte>/<arquivo>, ao lado de Squad 1/Bases consolidadas/ (que é a BASE).
          Sem <BASE>/dados/, vale o arranjo do GitHub; a variável MINERA_BRUTOS aponta outra pasta no formato "Dados brutos".
          O caminho lógico não muda com o arranjo, então a planilha gerada é a mesma nos dois.

data_acesso = data (AAAA-MM-DD) do arquivo mais recente de um conjunto de caminhos lógicos. Na cópia de trabalho é a data de
          modificação do arquivo; no GitHub, clonar muda essa data, então vale a registrada em Dados brutos/datas_de_acesso.json.

Os scripts importam daqui (`from caminhos import BASE, TMP, arquivo`), inclusive o código que um script executa de outro com
exec(): basta base_consolidada_work/scripts/ estar no sys.path, o que o Python já garante ao rodar qualquer script desta pasta.
"""
import os
import tempfile
from pathlib import Path

BASE = os.environ.get("MINERA_BASE") or str(Path(__file__).resolve().parents[2])
TMP = os.environ.get("MINERA_TMP") or os.path.join(tempfile.gettempdir(), "minera_goias_pipeline")
os.makedirs(TMP, exist_ok=True)

DADOS_TRABALHO = os.path.join(BASE, "dados")
BRUTOS = os.environ.get("MINERA_BRUTOS") or os.path.join(os.path.dirname(BASE), "Dados brutos")
ARRANJO = "github" if os.environ.get("MINERA_BRUTOS") or not os.path.isdir(DADOS_TRABALHO) else "trabalho"

# prefixo do caminho lógico -> pasta da fonte em "Dados brutos" (o prefixo mais longo vence)
PASTAS_BRUTOS = {
    "dados/ANM/producao_amb_ral/": "ANM - Anuário Mineral Brasileiro (AMB)",
    "dados/ANM/cfem/": "ANM - CFEM",
    "dados/ANM/cadastro_mineiro/": "ANM - Cadastro Mineiro",
    "dados/ANM/sigmine/": "ANM - SIGMINE",
    "dados/ANM/investimento_pesquisa/": "ANM - Investimento em pesquisa mineral",
    "dados/ANM/agua_mineral/": "ANM - Água mineral",
    "dados/ANM_derivados_analises/": "ANM - Planilhas derivadas",
    "dados/IBGE/GO_Municipios_2025.zip": "IBGE - Malha municipal 2025",
    "dados/IBGE/ibge_malha_municipal_goias_2024.zip": "IBGE - Malha municipal 2024",
    "dados/IBGE/": "IBGE - População e PIB (SIDRA)",
    "dados/IMB/": "IMB - Goiás em Dados",
    "dados/SGB_GeoSGB/recmin/": "SGB - RECMIN",
    "dados/SGB_GeoSGB/sig_vetorial/geoquimica_": "SGB - GeoSGB geoquímica",
    "dados/SGB_GeoSGB/sig_vetorial/": "SGB - SIG geológico",
    "dados/SGB_GeoSGB/geoquimica_tabular/": "SGB - Geoquímica Folha Nazário",
    "dados/SGB_GeoSGB/mapas_referencia_GO/": "SGB - Mapas de referência",
}


def arquivo(logico):
    """Caminho físico (aceita curingas do glob) a partir do caminho lógico relativo à BASE, como "dados/ANM/cfem/*.csv"."""
    logico = logico.replace("\\", "/")
    if not logico.startswith("dados/") or ARRANJO == "trabalho":
        return os.path.join(BASE, logico)
    for prefixo in sorted(PASTAS_BRUTOS, key=len, reverse=True):
        if logico.startswith(prefixo):
            return os.path.join(BRUTOS, PASTAS_BRUTOS[prefixo], logico.rsplit("/", 1)[1])
    return os.path.join(BRUTOS, logico[len("dados/"):])


def logico(fisico):
    """Inverso de arquivo(): o caminho lógico "dados/…" de um arquivo físico."""
    fisico = os.path.abspath(fisico)
    if ARRANJO == "trabalho":
        return os.path.relpath(fisico, BASE).replace("\\", "/")
    pasta, nome = os.path.basename(os.path.dirname(fisico)), os.path.basename(fisico)
    for prefixo, destino in PASTAS_BRUTOS.items():
        if destino == pasta:
            return (prefixo if prefixo.endswith("/") else prefixo.rsplit("/", 1)[0] + "/") + nome
    return "dados/" + os.path.relpath(fisico, BRUTOS).replace("\\", "/")


ARQUIVO_DATAS = "datas_de_acesso.json"  # em "Dados brutos": caminho lógico -> data em que o arquivo foi baixado


def data_acesso(padroes):
    """Data (AAAA-MM-DD, UTC) do arquivo mais recente dos padrões lógicos; "" se nenhum existe."""
    import glob
    from datetime import datetime, timezone
    arqs = sorted({a for p in padroes for a in glob.glob(arquivo(p))})
    if not arqs:
        return ""
    datas = {}
    if ARRANJO == "github" and os.path.exists(os.path.join(BRUTOS, ARQUIVO_DATAS)):
        import json
        with open(os.path.join(BRUTOS, ARQUIVO_DATAS), encoding="utf-8") as f:
            datas = json.load(f)
    return max(datas.get(logico(a)) or datetime.fromtimestamp(os.path.getmtime(a), tz=timezone.utc).strftime("%Y-%m-%d") for a in arqs)


def arquivos_brutos():
    """Todos os arquivos físicos de dados brutos do arranjo em uso, como caminhos lógicos."""
    raiz = DADOS_TRABALHO if ARRANJO == "trabalho" else BRUTOS
    return sorted(logico(os.path.join(d, n)) for d, _, ns in os.walk(raiz) for n in ns)
