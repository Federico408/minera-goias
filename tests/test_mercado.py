"""The Mercado tab reads a curated public-source file, so its shape has to hold."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
DATA = PUBLIC / 'data' / 'mercado' / 'mercado_v1.json'

PROSE = {
    'operacoes': ('mineral', 'local', 'situacao', 'nota'),
    'transacoes': ('ativo', 'rotulo'),
    'referencias': ('mineral', 'onde', 'receita', 'resultado', 'nota'),
    'regulacao': ('nome', 'descricao'),
    'noticias': ('titulo', 'resumo'),
    'indicadores': ('valor', 'rotulo', 'detalhe'),
}


class MercadoDataTests(unittest.TestCase):
    def setUp(self):
        self.packet = json.loads(DATA.read_text(encoding='utf-8'))

    def test_every_section_has_content(self):
        for section in (*PROSE, 'oportunidades', 'riscos', 'fontes'):
            self.assertTrue(self.packet[section], section)

    def test_prose_fields_carry_both_languages(self):
        for section, fields in PROSE.items():
            for row in self.packet[section]:
                for field in fields:
                    value = row[field]
                    self.assertEqual(set(value), {'pt', 'en'}, f'{section}.{field}')
                    self.assertTrue(value['pt'].strip() and value['en'].strip(), f'{section}.{field}')
        for section in ('oportunidades', 'riscos'):
            for row in self.packet[section]:
                self.assertEqual(set(row), {'pt', 'en'}, section)
        self.assertEqual(set(self.packet['nota']), {'pt', 'en'})

    def test_links_are_https(self):
        links = [row['link'] for row in self.packet['noticias']] + [row['link'] for row in self.packet['fontes']]
        for link in links:
            self.assertTrue(link.startswith('https://'), link)

    def test_news_dates_are_year_month(self):
        for row in self.packet['noticias']:
            self.assertRegex(row['data'], r'^\d{4}-\d{2}$')

    def test_deal_bars_have_a_comparable_number(self):
        # The bar widths come from this field, so it has to be a number in one currency.
        for row in self.packet['transacoes']:
            self.assertIsInstance(row['valor_usd_milhoes'], (int, float))
            self.assertGreater(row['valor_usd_milhoes'], 0)

    def test_metric_tones_match_the_stylesheet(self):
        for row in self.packet['indicadores']:
            self.assertIn(row['tom'], {'a', 'b', 'c', 'd'})


class MercadoPanelTests(unittest.TestCase):
    def setUp(self):
        self.markup = (PUBLIC / 'painel.html').read_text(encoding='utf-8')
        self.code = (PUBLIC / 'mercado.js').read_text(encoding='utf-8')

    def test_the_panel_is_wired_to_the_sidebar_and_the_renderer(self):
        self.assertIn('<button data-view="mercado">', self.markup)
        self.assertIn('id="mercado-view"', self.markup)
        self.assertIn('/mercado.js', self.markup)
        painel = (PUBLIC / 'painel.js').read_text(encoding='utf-8')
        self.assertIn("'radar','mercado'", painel)
        self.assertIn("window.showMercado", painel)
        # Atlas stays the first tab; Mercado must not take its place.
        self.assertEqual(re.findall(r'data-view="(\w+)"', self.markup)[0], 'atlas')

    def test_every_container_the_renderer_fills_exists_in_the_page(self):
        for target in re.findall(r"el\('([\w-]+)'\)", self.code):
            self.assertIn(f'id="{target}"', self.markup, target)

    def test_external_links_open_safely(self):
        for anchor in re.findall(r'<a href="\$\{escape\(r\.link\)\}"[^>]*>', self.code):
            self.assertIn('rel="noopener noreferrer"', anchor)
        self.assertEqual(self.code.count('target="_blank"'), self.code.count('rel="noopener noreferrer"'))


if __name__ == '__main__':
    unittest.main()
