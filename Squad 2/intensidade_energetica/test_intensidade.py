"""Checagens da Base de Intensidade Energética v1. Uso: python "Squad 2/intensidade_energetica/test_intensidade.py"."""
import csv
import unittest
from pathlib import Path

import build_intensidade as b

PASTA = Path(__file__).resolve().parent
NATUREZAS = {"observado", "calculado", "benchmark", "estimado"}
OBRIGATORIOS = ["intensity_id", "mineral_id", "mineral_name", "operation_id", "tecnologia", "production_basis",
                "energy_intensity_mwh_t", "intensidade_unidade", "natureza_dado", "source_id", "usar_no_motor"]


def ler(nome):
    with open(PASTA / nome, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


class IntensidadeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = ler("base_intensidade_energetica_v1.csv")
        cls.motor = ler("energy_intensity_para_motor_v1.csv")
        cls.gerada = b.build()
        b.marcar_uso_no_motor(cls.gerada)

    def test_csv_igual_ao_que_o_script_gera(self):
        self.assertEqual(len(self.base), len(self.gerada))
        for arq, ger in zip(self.base, self.gerada):
            self.assertEqual(arq["intensity_id"], ger["intensity_id"])
            self.assertAlmostEqual(float(arq["energy_intensity_mwh_t"]), ger["energy_intensity_mwh_t"], places=5)

    def test_campos_minimos_e_dominios(self):
        ids = [r["intensity_id"] for r in self.base]
        self.assertEqual(len(ids), len(set(ids)))
        for r in self.base:
            for c in OBRIGATORIOS:
                if c == "operation_id" and r["processos_anm"]:
                    continue  # sem poligonal no SIGMINE: o processo da ANM identifica a operação
                self.assertTrue(r[c], (r["intensity_id"], c))
            self.assertIn(r["natureza_dado"], NATUREZAS)
            self.assertGreater(float(r["energy_intensity_mwh_t"]), 0)

    def test_colunas_exigidas_pelo_pdf_da_entrega(self):
        # S2-E2 "Campos mínimos" e §3 "Padrão mínimo de rastreabilidade" da Entrega Avaliativa 1
        exigidas = ["mineral_id", "mineral_name", "project_id", "operation_id", "tecnologia", "production_t", "energy_mwh",
                    "energy_intensity_mwh_t", "unidade", "year", "source_id", "natureza_dado", "source_url", "data_acesso",
                    "periodo_referencia", "tipo_fonte", "valor_observado_estimado", "metodo_estimacao", "status_validacao",
                    "responsavel_validacao"]
        for c in exigidas:
            self.assertIn(c, self.base[0])

    def test_rota_tecnologica_so_com_fonte(self):
        for r in self.base:
            if r["rota_tecnologica"]:
                self.assertEqual(r["tecnologia_status"], b.ROTA_PAINEL)

    def test_intensidade_e_energia_sobre_producao_em_t(self):
        for r in self.base:
            if r["natureza_dado"] == "benchmark":
                continue
            e, p = float(r["energy_mwh"]), float(r["production_t"])
            self.assertAlmostEqual(float(r["energy_intensity_mwh_t"]), e / p, delta=1e-4 * e / p)
            if r["intensidade_unidade"] == "MWh/kg":  # ouro: 1 t = 1.000 kg
                self.assertAlmostEqual(float(r["intensidade_valor"]) * 1000, float(r["energy_intensity_mwh_t"]), delta=1)

    def test_benchmark_nunca_parece_observacao(self):
        for r in self.base:
            if r["source_id"] == "SRC_FGV_EPGE_001":
                self.assertEqual(r["natureza_dado"], "benchmark")
                self.assertTrue(r["usar_no_motor"].startswith("não"))

    def test_estimativas_trazem_metodo(self):
        for r in self.base:
            if r["natureza_dado"] == "estimado":
                self.assertTrue(r["metodo_estimacao"], r["intensity_id"])

    def test_arquivo_do_motor_segue_o_contrato(self):
        self.assertEqual(len(self.motor), sum(r["usar_no_motor"] == "sim" for r in self.base))
        base_por_id = {r["intensity_id"]: r for r in self.base}
        for m in self.motor:
            self.assertIn(m["production_basis"], {"rom", "beneficiada", "conteudo_mineral"})
            self.assertEqual(m["year"], "2025")
            self.assertEqual(base_por_id[m["intensity_id"]]["compatibilidade_temporal"], "mesmo_ano")
        # sem dupla contagem: cada (mineral, operação, base) aparece uma vez
        chaves = [(m["mineral_id"], m["operation_id"], m["production_basis"]) for m in self.motor]
        self.assertEqual(len(chaves), len(set(chaves)))

    def test_plantas_da_anglo_somam_o_total(self):
        total = next(r for r in self.base if r["operation_id"] == "AGG_COM_CNPJ_42184226_NI" and r["nivel"] == "operacao_empresa")
        plantas = [r for r in self.base if r["mineral_id"] == "MIN_022" and r["nivel"] == "unidade_consumidora"]
        self.assertEqual(len(plantas), 2)
        self.assertAlmostEqual(sum(float(r["energy_mwh"]) for r in plantas), float(total["energy_mwh"]), places=2)
        self.assertAlmostEqual(sum(float(r["production_t"]) for r in plantas), float(total["production_t"]), places=2)


if __name__ == "__main__":
    unittest.main()
