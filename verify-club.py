"""Read-only smoke checks. Never prints credentials or session cookies."""
import configparser
import json
from pathlib import Path
import requests
from lxml import html
import psycopg2

root = Path(json.loads((Path(__file__).parent/'runtime.json').read_text())['runtime'])
a = json.loads((root/'access.json').read_text())
s = requests.Session()
r = s.get(a['url']+'/web/login', timeout=60)
assert r.status_code == 200, f'Login page: {r.status_code}'
print('Login page: OK')
r = s.post(a['url']+'/web/session/authenticate', json={'jsonrpc':'2.0','method':'call','params':{'db':a['database'],'login':a['login'],'password':a['password']},'id':1}, timeout=60)
result = r.json()
assert result.get('result', {}).get('uid'), 'Authentication failed'
print('Administrator authentication: OK')
r = s.get(a['url']+'/odoo', timeout=120)
assert r.status_code == 200, f'Backend: {r.status_code}'
tree = html.fromstring(r.text)
assets = tree.xpath('//script[@src]/@src | //link[@rel="stylesheet"]/@href')
checked = 0
for url in assets:
    if url.startswith('/web/assets/'):
        response = s.get(a['url']+url, timeout=120)
        assert response.status_code == 200, f'Asset failure: {url}'
        assert 'Could not execute command' not in response.text, 'Asset compiler unavailable'
        checked += 1
print('Backend HTTP and asset downloads: OK; bundles:', checked)
c = configparser.ConfigParser(interpolation=None)
c.read(root/'odoo.conf')
o = c['options']
assert o['db_port'] == '5495'
with psycopg2.connect(host=o['db_host'],port=o['db_port'],user=o['db_user'],password=o['db_password'],dbname=o['db_name']) as con:
    with con.cursor() as cr:
        cr.execute('SHOW server_version')
        print('PostgreSQL:', cr.fetchone()[0])
        cr.execute("SELECT name FROM ir_module_module WHERE state='installed' AND license='OEEL-1'")
        assert not cr.fetchall(), 'Enterprise modules found'
        cr.execute("SELECT name FROM ir_module_module WHERE state='installed' AND name IN ('contacts','account','purchase','stock') ORDER BY name")
        assert len(cr.fetchall()) == 4
        cr.execute('SELECT rolcreatedb,rolcreaterole,rolsuper FROM pg_roles WHERE rolname=current_user')
        assert cr.fetchone() == (False, False, False)
print('Community modules and restricted DB role: OK')
(root/'verification.json').write_text(json.dumps({'login':True,'authentication':True,'backend_http':True,'asset_bundles':checked,'community_only':True,'postgres_port':5495},indent=2))
