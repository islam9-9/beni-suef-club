"""Local development provisioning. Never modifies existing Odoo databases."""
import configparser
import json
import secrets
from pathlib import Path
import psycopg2
from psycopg2 import sql

ROOT = Path.home() / 'AppData/Local/BeniSuefClub'
PROJECT = Path(__file__).parent
NAME = 'beni_suef_club_dev'
ROLE = 'beni_suef_club'
old = configparser.ConfigParser(interpolation=None)
old.read(r'C:\Program Files\Odoo 19.0e.20251117\server\odoo.conf')
o = old['options']
conn = psycopg2.connect(host=o['db_host'], port=o['db_port'], user=o['db_user'], password=o['db_password'], dbname='postgres')
conn.autocommit = True
cur = conn.cursor()
cur.execute('SELECT rolcreatedb,rolcreaterole,rolsuper FROM pg_roles WHERE rolname=current_user')
print('Provisioning privileges:', cur.fetchone())
cur.execute('SELECT 1 FROM pg_database WHERE datname=%s', (NAME,))
if cur.fetchone():
    raise SystemExit('Target database already exists; refusing to overwrite.')
cur.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (ROLE,))
if cur.fetchone():
    raise SystemExit('Target role already exists; refusing to overwrite.')
password = secrets.token_urlsafe(32)
cur.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD %s NOSUPERUSER NOCREATEDB NOCREATEROLE').format(sql.Identifier(ROLE)), (password,))
cur.execute(sql.SQL('CREATE DATABASE {} OWNER {} TEMPLATE template0 ENCODING %s').format(sql.Identifier(NAME), sql.Identifier(ROLE)), ('UTF8',))
cur.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(NAME)))
source = json.loads((ROOT / 'source.json').read_text())
server = ROOT / ('odoo-' + source['commit'])
(PROJECT / 'addons').mkdir(exist_ok=True)
for part in ('data', 'logs', 'backups'):
    (ROOT / part).mkdir(exist_ok=True)
config = configparser.ConfigParser(interpolation=None)
config['options'] = {
    'admin_passwd': secrets.token_urlsafe(40),
    'db_host': o['db_host'], 'db_port': o['db_port'],
    'db_user': ROLE, 'db_password': password,
    'db_name': NAME, 'dbfilter': '^' + NAME + '$', 'list_db': 'False',
    'http_interface': '127.0.0.1', 'http_port': '8095',
    'addons_path': ','.join(str(p) for p in (server/'odoo/addons', server/'addons', PROJECT/'addons')),
    'data_dir': str(ROOT/'data'), 'logfile': str(ROOT/'logs/odoo.log'),
    'without_demo': 'all', 'workers': '0', 'max_cron_threads': '1',
}
with (ROOT/'odoo.conf').open('w') as f:
    config.write(f)
(ROOT/'access.json').write_text(json.dumps({'url':'http://127.0.0.1:8095','database':NAME,'login':'club.admin','password':secrets.token_urlsafe(20)}, indent=2))
print('Created isolated development database and configuration:', NAME)
