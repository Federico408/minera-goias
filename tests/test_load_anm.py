"""The load must not lose rows, invent documents, or total areas that may overlap."""
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Squad 3' / 'database'))
import load_anm  # noqa: E402


class LoadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = str(Path(cls.tmp.name) / 'negocio.sqlite')
        connection = sqlite3.connect(cls.db)
        load_anm.create_sqlite_schema(connection)
        cls.report = load_anm.load(load_anm.Target(connection, False), ROOT, '2026-09-13')
        connection.close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def query(self, sql, args=()):
        conn = sqlite3.connect(self.db)
        try:
            return conn.execute(sql, args).fetchall()
        finally:
            conn.close()

    def test_every_polygon_survives_the_process_key(self):
        # 17.428 polygons across 16.656 processes: keying only by process loses 772.
        self.assertEqual(self.report['poligonos'], 17428)
        self.assertEqual(self.report['projetos'], 16656)
        self.assertEqual(self.query('SELECT COUNT(*) FROM tb_projeto_poligono')[0][0], 17428)
        self.assertEqual(self.query('SELECT COUNT(*) FROM tb_projetos')[0][0], 16656)
        orphans = self.query('''SELECT COUNT(*) FROM tb_projeto_poligono g
            LEFT JOIN tb_projetos p ON p.processo_anm=g.processo_anm WHERE p.processo_anm IS NULL''')
        self.assertEqual(orphans[0][0], 0)

    def test_repeated_source_identifiers_are_kept_not_collapsed(self):
        # The shapefile reuses the same GUID across processes and twice within one,
        # so it is stored as an attribute and every source row survives.
        repeated = self.query('''SELECT COUNT(*) FROM tb_projeto_poligono
            WHERE id_poligono_origem='{97401F18-F795-4221-AA07-A7AFD0AC4938}' ''')
        self.assertEqual(repeated[0][0], 3)

    def test_area_is_not_totalled_when_polygons_may_overlap(self):
        multi = self.query('SELECT COUNT(*) FROM tb_projetos WHERE poligonos > 1 AND area_ha IS NOT NULL')
        self.assertEqual(multi[0][0], 0)
        single = self.query('SELECT COUNT(*) FROM tb_projetos WHERE poligonos = 1 AND area_ha IS NOT NULL')
        self.assertGreater(single[0][0], 10000)

    def test_no_document_is_invented_for_holders(self):
        self.assertEqual(self.query('SELECT COUNT(*) FROM tb_empresas WHERE documento_cnpj_cpf IS NOT NULL')[0][0], 0)
        self.assertEqual(self.query('SELECT COUNT(*) FROM tb_empresas')[0][0], self.report['empresas'])
        blank = self.query("SELECT COUNT(*) FROM tb_empresas WHERE nome_empresa_normalizado = ''")
        self.assertEqual(blank[0][0], 0)

    def test_substances_come_from_the_anm_dictionary(self):
        self.assertEqual(self.report['minerais'], 862)
        self.assertEqual(self.query('SELECT COUNT(*) FROM tb_minerais WHERE id_substancia_anm IS NULL')[0][0], 0)
        # Everything the source actually names resolves; only its own placeholder does not.
        unresolved = self.query('''SELECT DISTINCT substancia_anm FROM tb_projetos
            WHERE mineral_id IS NULL AND substancia_anm IS NOT NULL''')
        self.assertEqual([row[0] for row in unresolved], ['DADO NÃO CADASTRADO'])

    def test_municipalities_carry_the_ibge_code(self):
        self.assertEqual(self.report['municipios'], 246)
        codes = self.query('SELECT codigo_ibge FROM tb_municipios LIMIT 5')
        self.assertTrue(all(code[0].isdigit() and len(code[0]) == 7 for code in codes))

    def test_reload_is_idempotent(self):
        connection = sqlite3.connect(self.db)
        try:
            load_anm.load(load_anm.Target(connection, False), ROOT, '2026-09-13')
        finally:
            connection.close()
        self.assertEqual(self.query('SELECT COUNT(*) FROM tb_projetos')[0][0], 16656)
        self.assertEqual(self.query('SELECT COUNT(*) FROM tb_empresas')[0][0], self.report['empresas'])

    def test_holder_name_is_kept_but_stays_out_of_the_public_endpoint(self):
        named = self.query('SELECT COUNT(*) FROM tb_projetos WHERE titular_nome IS NOT NULL')[0][0]
        self.assertGreater(named, 10000)
        api = (ROOT / 'Squad 3' / 'backend' / 'main.py').read_text(encoding='utf-8')
        public = api.split("if version == 'v2':", 1)[1].split('elif version', 1)[0]
        self.assertNotIn('titular_nome', public)
        self.assertNotIn('nome_empresa', public)


if __name__ == '__main__':
    unittest.main()
