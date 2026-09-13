# -*- coding: utf-8 -*-
"""Caminhos do pipeline, calculados a partir da posição DESTE arquivo — nenhum caminho fixo de uma máquina.

BASE = pasta do projeto, a que contém dados/, documentacao/, outputs/ e base_consolidada_work/ (dois níveis acima de scripts/).
       Para rodar estes scripts contra dados guardados em outra pasta (ex.: a cópia do GitHub lendo o dados/ local, que não
       é versionado), defina a variável de ambiente MINERA_BASE.
TMP  = JSONs intermediários entre as etapas. Padrão: <pasta temporária do sistema>/minera_goias_pipeline (fora do OneDrive
       e do git); para usar outra pasta, defina a variável de ambiente MINERA_TMP.

Os scripts importam daqui (`from caminhos import BASE, TMP`), inclusive o código que um script executa de outro com exec():
basta base_consolidada_work/scripts/ estar no sys.path, o que o Python já garante ao rodar qualquer script desta pasta.
"""
import os
import tempfile
from pathlib import Path

BASE = os.environ.get("MINERA_BASE") or str(Path(__file__).resolve().parents[2])
TMP = os.environ.get("MINERA_TMP") or os.path.join(tempfile.gettempdir(), "minera_goias_pipeline")
os.makedirs(TMP, exist_ok=True)
