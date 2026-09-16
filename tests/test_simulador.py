"""Parâmetros do simulador (public/data/simulador/parametros_v0.json) e rastreabilidade da aba Simulador."""
import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / 'public' / 'data' / 'simulador' / 'parametros_v0.json'
PUBLIC = ROOT / 'public'
MINERAIS_SQUAD2 = ROOT / 'Squad 2' / 'data' / 'demo' / 'minerals_demo.csv'

GOVERNANCA = (
    'source_id', 'source_name', 'source_url', 'data_acesso', 'periodo_referencia',
    'tipo_fonte', 'valor_observado_estimado', 'metodo_estimacao',
    'status_validacao', 'responsavel_validacao',
)
NATUREZAS = {'observado', 'estimado', 'ilustrativo'}


class ParametrosTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(PARAMS.read_text(encoding='utf-8'))

    def test_versao_e_horizonte_declarados(self):
        self.assertRegex(self.d['versao'], r'^\d+\.\d+\.\d+$')
        self.assertRegex(self.d['data_versao'], r'^\d{4}-\d{2}-\d{2}$')
        self.assertEqual(self.d['horizonte'], {'inicio': 2027, 'fim': 2040})
        self.assertEqual(self.d['ano_base'], 2025)
        self.assertLess(self.d['ano_base'], self.d['horizonte']['inicio'])

    def test_as_sete_operacoes_do_material_base(self):
        ops = self.d['operacoes']
        self.assertEqual(len(ops), 7)
        for op in ops:
            for campo in ('operation_id', 'mineral_id', 'company_name', 'municipality_name',
                          'production_t', 'energy_intensity_mwh_t', 'production_basis',
                          'valor_observado_estimado', 'source_id'):
                self.assertIn(campo, op, op.get('operation_id'))
            self.assertGreater(op['production_t'], 0)
            self.assertGreater(op['energy_intensity_mwh_t'], 0)
            self.assertIn(op['valor_observado_estimado'], NATUREZAS)
        self.assertEqual(len({o['operation_id'] for o in ops}), 7)
        self.assertAlmostEqual(sum(o['production_t'] for o in ops), 3_000_000, places=6)

    def test_divergencia_do_baseline_fica_registrada(self):
        # Produção x intensidade não reproduz a energia publicada porque a produção vem
        # arredondada em Mt na origem. O simulador registra a diferença em vez de ajustar.
        conf = self.d['conferencia_baseline']
        calculada = sum(o['production_t'] * o['energy_intensity_mwh_t'] for o in self.d['operacoes']) / 1e6
        publicada = sum(o['energy_twh_publicado'] for o in self.d['operacoes'])
        self.assertAlmostEqual(conf['energia_calculada_twh'], calculada, places=4)
        self.assertAlmostEqual(conf['energia_publicada_twh'], publicada, places=4)
        self.assertAlmostEqual(conf['divergencia_percentual'],
                               (calculada - publicada) / publicada * 100, places=2)
        self.assertTrue(conf['nota'])

    def test_tres_cenarios_com_cores_do_guia_visual(self):
        cen = {c['scenario']: c for c in self.d['cenarios']}
        self.assertEqual(set(cen), {'conservador', 'referencia', 'expansao'})
        self.assertEqual(cen['conservador']['cor'], '#5B8DB8')
        self.assertEqual(cen['referencia']['cor'], '#123B66')
        self.assertEqual(cen['expansao']['cor'], '#C6A15B')
        self.assertLess(cen['conservador']['fator_producao'], cen['referencia']['fator_producao'])
        self.assertLess(cen['referencia']['fator_producao'], cen['expansao']['fator_producao'])
        for c in cen.values():
            self.assertTrue(0 <= c['ganho_eficiencia_anual_padrao'] < 1)
            self.assertEqual(c['valor_observado_estimado'], 'ilustrativo')

    def test_toda_medida_aponta_para_uma_fonte_completa(self):
        fontes = {f['source_id']: f for f in self.d['fontes']}
        for f in self.d['fontes']:
            for campo in GOVERNANCA:
                self.assertIn(campo, f, f['source_id'])
            self.assertIn(f['valor_observado_estimado'], NATUREZAS)
            self.assertRegex(f['data_acesso'], r'^\d{4}-\d{2}-\d{2}$')
        referencias = [o['source_id'] for o in self.d['operacoes']]
        for c in self.d['cenarios']:
            referencias += [c['fator_producao_source_id'], c['ganho_eficiencia_source_id']]
        for sid in referencias:
            self.assertIn(sid, fontes, sid)
        self.assertEqual(set(fontes), set(referencias))

    def test_valores_arbitrados_declaram_o_metodo(self):
        for f in self.d['fontes']:
            if f['valor_observado_estimado'] == 'ilustrativo':
                self.assertTrue(f['metodo_estimacao'], f['source_id'])
                self.assertNotEqual(f['status_validacao'], 'validado')

    def test_mineral_id_segue_o_catalogo_do_squad_2(self):
        # Contrato de integração: o simulador reusa os identificadores do motor do Squad 2,
        # para que a troca dos parâmetros ilustrativos pelos reais não exija remapeamento.
        with MINERAIS_SQUAD2.open(encoding='utf-8-sig') as fh:
            catalogo = {linha['mineral_id']: linha['mineral_name'] for linha in csv.DictReader(fh)}
        for op in self.d['operacoes']:
            self.assertIn(op['mineral_id'], catalogo, op['operation_id'])
            self.assertEqual(op['mineral_name'], catalogo[op['mineral_id']], op['operation_id'])

    def test_producao_declarada_confere_com_o_valor_publicado_em_mt(self):
        for op in self.d['operacoes']:
            self.assertAlmostEqual(op['production_t'], op['production_mt_publicado'] * 1e6, places=6)


class PaginaTests(unittest.TestCase):
    def test_pagina_carrega_motor_e_parametros(self):
        html = (PUBLIC / 'simulador.html').read_text(encoding='utf-8')
        self.assertIn('/simulador-engine.js', html)
        self.assertIn('/simulador.js', html)
        self.assertIn('/simulador.css', html)
        js = (PUBLIC / 'simulador.js').read_text(encoding='utf-8')
        self.assertIn('/data/simulador/parametros_v0.json', js)

    def test_calculo_fica_fora_da_interface(self):
        engine = (PUBLIC / 'simulador-engine.js').read_text(encoding='utf-8')
        self.assertNotIn('document.', engine)
        self.assertNotIn('getElementById', engine)

    def test_simulador_nao_consulta_fonte_externa(self):
        # O simulador reproduz o motor a partir do arquivo de parâmetros; nesta etapa
        # não deve buscar nada fora do próprio repositório.
        for nome in ('simulador.js', 'simulador-engine.js', 'simulador.html'):
            texto = (PUBLIC / nome).read_text(encoding='utf-8')
            self.assertNotIn('http://', texto, nome)
            self.assertNotIn('https://', texto, nome)


# Padrões genéricos, para que nenhum segredo precise ser escrito neste arquivo.
PROIBIDOS = (
    ('endereço de e-mail', re.compile(r'[\w.+-]+@[\w-]+\.[\w]{2,}')),
    ('credencial declarada', re.compile(r'(senha|password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S', re.I)),
    ('chave privada', re.compile(r'BEGIN [A-Z ]*PRIVATE KEY')),
    ('token de provedor', re.compile(r'\b(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,})\b')),
)


class SegredosTests(unittest.TestCase):
    def test_nenhum_segredo_ou_dado_pessoal_nos_arquivos(self):
        alvos = [PARAMS, ROOT / 'tests' / 'simulador.test.js', ROOT / 'tests' / 'test_simulador.py']
        alvos += [PUBLIC / n for n in
                  ('simulador.html', 'simulador.css', 'simulador.js', 'simulador-engine.js')]
        alvos.append(ROOT / 'Squad 3' / 'documentacao' / 'simulador' / 'README.md')
        for caminho in alvos:
            texto = caminho.read_text(encoding='utf-8')
            for rotulo, padrao in PROIBIDOS:
                achado = padrao.search(texto)
                self.assertIsNone(achado, f'{caminho.name}: {rotulo} — {achado.group(0) if achado else ""}')


if __name__ == '__main__':
    unittest.main()
