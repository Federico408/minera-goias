"""Retrato do atlas gerado por scripts/build_atlas_base.py a partir da base consolidada do Squad 1 (v13)."""
import base64,json,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ANOS=[2022,2023,2024,2025,2026]
def atlas():return json.loads((ROOT/'data/atlas/atlas.json').read_text(encoding='utf-8'))
class AtlasTests(unittest.TestCase):
 def test_municipalities_geometry_and_cfem(self):
  d=atlas();mun=d['municipalities']
  self.assertEqual(len(mun),246)
  self.assertEqual(len({m['code'] for m in mun}),246)
  self.assertTrue(all(len(m['code'])==7 and m['code'].startswith('52') for m in mun))
  for m in mun:
   self.assertTrue(m['rings'])
   for ring in m['rings']:
    self.assertEqual(ring[0],ring[-1]);self.assertGreaterEqual(len(ring),4)
    for lat,lon in ring:
     self.assertTrue(-19.51<lat<-12.38);self.assertTrue(-53.26<lon<-45.89)
  self.assertEqual(len(d['dams']),23)
  total=sum(m['cfem_total'] for m in mun)
  self.assertAlmostEqual(total,sum(r['valor'] for r in d['cfem_years']),places=2)
  # conciliado com o arquivo bruto da CFEM na base consolidada (aba 14b da planilha)
  self.assertAlmostEqual(total,867578398.91,places=2)
 def test_yearly_cfem_covers_every_municipality(self):
  d=atlas();por_nome={m['name']:m for m in d['municipalities']}
  self.assertEqual(d['cfem']['anos'],ANOS)
  self.assertEqual({x['Município'] for x in d['cfem']['linhas']},set(por_nome))
  for x in d['cfem']['linhas']:
   self.assertAlmostEqual(sum(x[str(a)] for a in ANOS),por_nome[x['Município']]['cfem_total'],places=2)
 def test_encoded_process_integrity_without_holder_data(self):
  p=json.loads((ROOT/'data/atlas/processes.json').read_text(encoding='utf-8'))
  def arr(key,fmt):
   b=base64.b64decode(p[key]);return struct.unpack('<'+fmt*(len(b)//struct.calcsize(fmt)),b)
  n=p['n'];self.assertEqual(n,16656)  # processos do SIGMINE em Goiás na base consolidada (aba 03)
  for key in ('nome','dNome','titular','razao_social','company_id'):self.assertNotIn(key,p)
  self.assertEqual(len(p['processo'].split('\x01')),n)
  for key,fmt in [('g','B'),('fase','B'),('subs','H'),('area','f')]:self.assertEqual(len(arr(key,fmt)),n)
  xy,starts,owners=arr('xy','H'),arr('ringStart','I'),arr('ringPoly','H')
  self.assertEqual(starts[-1]*2,len(xy));self.assertEqual(len(starts),len(owners)+1)
  self.assertEqual(set(owners),set(range(n)))  # todo processo tem ao menos um anel
  self.assertTrue(all(b-a>=3 for a,b in zip(starts,starts[1:])))
  self.assertLessEqual(len(p['grupos']),5)  # public/atlas.js tem cinco cores de fase
  self.assertTrue(all(g<len(p['grupos']) for g in arr('g','B')))
  self.assertEqual(sum(r['n'] for r in p['resumo']),n)
 def test_series_units_and_coverage(self):
  d=atlas()
  self.assertEqual([r['Ano'] for r in d['cfem_years']],ANOS)
  self.assertEqual([r['Ano'] for r in d['cfem_comparable']],ANOS)
  self.assertTrue(all(c['v']<=y['valor']+0.01 for c,y in zip(d['cfem_comparable'],d['cfem_years'])))
  self.assertEqual(d['energy_months'][0]['rotulo'],'2024-04')
  self.assertEqual(d['energy_months'][-1]['rotulo'],'2026-06')
  self.assertNotIn('empresas_ee',d['energy'][0])
  self.assertEqual(d['beneficiated'][0]['ano'],2010)
  subs=d['production']['subs']
  self.assertTrue(subs)
  self.assertEqual({s['sub'] for s in subs},set(d['production']['dados']))
  self.assertEqual(sorted(d['meta']['retained_from_artifact']['layers']),['dams','energy','energy_months'])
