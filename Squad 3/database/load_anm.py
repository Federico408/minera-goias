#!/usr/bin/env python3
"""Load the ANM sources into the business tables.

Reads only what the sources actually state: the substance dictionary, the IBGE
municipality codes already extracted for the atlas, and the cadastral shapefile.
Nothing is inferred - no unit conversion, no company matched by resemblance, no
document invented where the source does not give one.

    python3 "Squad 3/database/load_anm.py" --sqlite /tmp/negocio.sqlite --root .
    python3 "Squad 3/database/load_anm.py" --mysql --root /srv/minera-goias/current
"""
import argparse
import json
import os
import re
import sqlite3
import struct
import sys
import unicodedata
import zipfile
from pathlib import Path

SOURCE_ID = 'ANM_CADASTRO'
SUBSTANCES = 'Squad 1/dados/Substancia.txt'
SHAPEFILE = 'Squad 1/Dados brutos/ANM - SIGMINE/GO.zip'
ATLAS = 'data/atlas/atlas.json'


def normalize(value):
    """Upper case without accents or double spaces - the company key."""
    folded = unicodedata.normalize('NFKD', str(value or ''))
    plain = ''.join(c for c in folded if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', plain).strip().upper()


def read_dbf(archive, member):
    """Minimal dBase III reader: the shapefile attribute table, no dependencies."""
    with archive.open(member) as handle:
        header = handle.read(32)
        count = struct.unpack('<I', header[4:8])[0]
        header_length = struct.unpack('<H', header[8:10])[0]
        record_length = struct.unpack('<H', header[10:12])[0]
        fields, rest = [], handle.read(header_length - 32)
        for offset in range(0, len(rest) - 1, 32):
            block = rest[offset:offset + 32]
            if len(block) < 32 or block[0] == 0x0D:
                break
            fields.append((block[:11].split(b'\x00')[0].decode('latin1'), block[16]))
        for _ in range(count):
            record = handle.read(record_length)
            if len(record) < record_length or record[:1] == b'*':  # deleted row
                continue
            position, row = 1, {}
            for name, size in fields:
                raw = record[position:position + size]
                # The DBF is latin1 on disk but the strings inside were written as UTF-8.
                text = raw.decode('latin1').strip()
                try:
                    text = text.encode('latin1').decode('utf-8')
                except (UnicodeDecodeError, UnicodeEncodeError):
                    pass
                row[name] = text
                position += size
            yield row


def substances(root):
    raw = (root / SUBSTANCES).read_bytes()
    for encoding in ('utf-8-sig', 'cp1252', 'latin1'):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    rows = []
    for line in text.splitlines()[1:]:
        if not line.strip():
            continue
        identifier, _, name = line.partition(';')
        if identifier.strip().isdigit() and name.strip():
            rows.append((int(identifier), name.strip()))
    return rows


def municipalities(root):
    packet = json.loads((root / ATLAS).read_text(encoding='utf-8'))
    return [(m['code'], m['name']) for m in packet['municipalities']]


def claims(root):
    with zipfile.ZipFile(root / SHAPEFILE) as archive:
        member = next(n for n in archive.namelist() if n.lower().endswith('.dbf'))
        for row in read_dbf(archive, member):
            processo = (row.get('PROCESSO') or '').strip()
            if not processo:
                continue
            try:
                area = float(row.get('AREA_HA') or 0)
            except ValueError:
                area = None
            yield {
                'processo_anm': processo,
                'titular_nome': (row.get('NOME') or '').strip() or None,
                'substancia_anm': (row.get('SUBS') or '').strip() or None,
                'fase': (row.get('FASE') or '').strip() or None,
                'uso': (row.get('USO') or '').strip() or None,
                'ultimo_evento': (row.get('ULT_EVENTO') or '').strip()[:120] or None,
                'id_poligono': (row.get('ID') or '').strip()[:40] or None,
                'uf': (row.get('UF') or '').strip()[:2] or None,
                'area_ha': area,
            }


class Target:
    """One writer for both back ends; MySQL only differs in the placeholder."""

    def __init__(self, connection, mysql):
        self.connection, self.mysql = connection, mysql

    def execute(self, sql, args=()):
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql.replace('?', '%s') if self.mysql else sql, args)
            return cursor.lastrowid
        finally:
            cursor.close()

    def rows(self, sql, args=()):
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql.replace('?', '%s') if self.mysql else sql, args)
            return cursor.fetchall()
        finally:
            cursor.close()


def create_sqlite_schema(connection):
    """Same shape as schema.sql, in the dialect SQLite accepts, for dry runs."""
    connection.executescript('''
    CREATE TABLE IF NOT EXISTS tb_fontes(source_id TEXT PRIMARY KEY, titulo TEXT NOT NULL,
      instituicao TEXT, url_arquivo TEXT, cobertura TEXT, notas_metodologicas TEXT);
    CREATE TABLE IF NOT EXISTS tb_municipios(codigo_ibge TEXT PRIMARY KEY, nome_municipio TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS tb_minerais(mineral_id INTEGER PRIMARY KEY AUTOINCREMENT,
      id_substancia_anm INTEGER UNIQUE, mineral_name TEXT NOT NULL, sinonimos TEXT, observacao TEXT);
    CREATE TABLE IF NOT EXISTS tb_empresas(empresa_id INTEGER PRIMARY KEY AUTOINCREMENT,
      nome_empresa TEXT NOT NULL, nome_empresa_normalizado TEXT NOT NULL UNIQUE,
      documento_cnpj_cpf TEXT UNIQUE, tipo_pessoa TEXT);
    CREATE TABLE IF NOT EXISTS tb_projetos(processo_anm TEXT PRIMARY KEY, empresa_id INTEGER,
      titular_nome TEXT, ultimo_evento TEXT, uf TEXT, poligonos INTEGER NOT NULL DEFAULT 0,
      substancia_anm TEXT, mineral_id INTEGER, fase TEXT, uso TEXT, area_ha REAL, categoria TEXT,
      source_id TEXT, data_acesso TEXT, periodo_referencia TEXT,
      valor_observado_estimado TEXT DEFAULT 'Real', status_validacao TEXT, responsavel_validacao TEXT);
    CREATE TABLE IF NOT EXISTS tb_projeto_poligono(poligono_id INTEGER PRIMARY KEY AUTOINCREMENT,
      processo_anm TEXT NOT NULL, id_poligono_origem TEXT, area_ha REAL);
    ''')
    connection.commit()


def load(target, root, access_date):
    report = {'minerais': 0, 'municipios': 0, 'empresas': 0, 'projetos': 0, 'poligonos': 0,
              'projetos_sem_titular': 0, 'substancias_nao_resolvidas': 0}

    target.execute('''INSERT INTO tb_fontes(source_id,titulo,instituicao,url_arquivo,cobertura,notas_metodologicas)
        VALUES(?,?,?,?,?,?) ON CONFLICT(source_id) DO NOTHING'''
        if not target.mysql else
        '''INSERT IGNORE INTO tb_fontes(source_id,titulo,instituicao,url_arquivo,cobertura,notas_metodologicas)
        VALUES(?,?,?,?,?,?)''',
        (SOURCE_ID, 'Cadastro mineiro e dicionário de substâncias', 'ANM',
         SHAPEFILE, 'Goiás', 'Carga direta das fontes; sem conversão de unidade nem inferência de titular.'))

    keep = 'ON CONFLICT DO NOTHING' if not target.mysql else ''
    prefix = 'INSERT IGNORE INTO' if target.mysql else 'INSERT INTO'

    for code, name in municipalities(root):
        target.execute(f'{prefix} tb_municipios(codigo_ibge,nome_municipio) VALUES(?,?) {keep}', (code, name))
        report['municipios'] += 1

    by_substance = {}
    for identifier, name in substances(root):
        target.execute(f'{prefix} tb_minerais(id_substancia_anm,mineral_name) VALUES(?,?) {keep}',
                       (identifier, name))
        report['minerais'] += 1
    for mineral_id, name in target.rows('SELECT mineral_id,mineral_name FROM tb_minerais'):
        by_substance[normalize(name)] = mineral_id

    companies = {}
    for row in target.rows('SELECT empresa_id,nome_empresa_normalizado FROM tb_empresas'):
        companies[row[1]] = row[0]

    # One process can carry many polygons; group first so no row is lost to the key.
    grouped = {}
    for claim in claims(root):
        entry = grouped.setdefault(claim['processo_anm'], {'claim': claim, 'polygons': []})
        entry['polygons'].append((claim['id_poligono'], claim['area_ha']))
    report['poligonos'] = sum(len(e['polygons']) for e in grouped.values())

    for entry in grouped.values():
        claim = entry['claim']
        empresa_id = None
        if claim['titular_nome']:
            key = normalize(claim['titular_nome'])
            if key not in companies:
                target.execute(f'{prefix} tb_empresas(nome_empresa,nome_empresa_normalizado) VALUES(?,?) {keep}',
                               (claim['titular_nome'][:200], key[:200]))
                found = target.rows('SELECT empresa_id FROM tb_empresas WHERE nome_empresa_normalizado=?', (key[:200],))
                companies[key] = found[0][0] if found else None
                report['empresas'] += 1
            empresa_id = companies[key]
        else:
            report['projetos_sem_titular'] += 1

        mineral_id = by_substance.get(normalize(claim['substancia_anm'])) if claim['substancia_anm'] else None
        if claim['substancia_anm'] and mineral_id is None:
            report['substancias_nao_resolvidas'] += 1

        polygons = entry['polygons']
        # Areas of different polygons may overlap, so a total is only stated when
        # the process has a single polygon. Otherwise the detail stays per polygon.
        area = polygons[0][1] if len(polygons) == 1 else None
        target.execute(f'''{prefix} tb_projetos(processo_anm,empresa_id,titular_nome,ultimo_evento,
            uf,poligonos,substancia_anm,mineral_id,fase,uso,area_ha,source_id,data_acesso,
            valor_observado_estimado,status_validacao) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) {keep}''',
            (claim['processo_anm'], empresa_id, claim['titular_nome'], claim['ultimo_evento'],
             claim['uf'], len(polygons), claim['substancia_anm'], mineral_id, claim['fase'],
             claim['uso'], area, SOURCE_ID, access_date, 'Real', 'nao_validado'))
        report['projetos'] += 1
        # The source repeats polygon identifiers, so rewriting this process's
        # polygons wholesale is what keeps a reload both lossless and idempotent.
        target.execute('DELETE FROM tb_projeto_poligono WHERE processo_anm=?', (claim['processo_anm'],))
        for polygon_id, polygon_area in polygons:
            target.execute('INSERT INTO tb_projeto_poligono(processo_anm,id_poligono_origem,area_ha) '
                           'VALUES(?,?,?)', (claim['processo_anm'], polygon_id, polygon_area))

    target.connection.commit()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description='Carrega as fontes da ANM nas tabelas de negócio.')
    parser.add_argument('--root', default='.', help='raiz do repositório com as fontes')
    parser.add_argument('--sqlite', help='caminho de um SQLite para ensaio; fora da pasta inspecionada')
    parser.add_argument('--mysql', action='store_true', help='usa o MySQL configurado no ambiente')
    parser.add_argument('--data-acesso', default='2026-09-13')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve(strict=True)

    if args.mysql:
        import pymysql
        connection = pymysql.connect(host=os.getenv('DB_HOST', 'localhost'), user=os.getenv('DB_USER'),
                                     password=os.getenv('DB_PASSWORD'), database=os.getenv('DB_NAME', 'db_minera_goias'))
        target = Target(connection, True)
    elif args.sqlite:
        connection = sqlite3.connect(args.sqlite)
        create_sqlite_schema(connection)
        target = Target(connection, False)
    else:
        parser.error('informe --sqlite para ensaio ou --mysql para a carga real')

    try:
        report = load(target, root, args.data_acesso)
    finally:
        target.connection.close()
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
