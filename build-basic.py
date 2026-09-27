"""Build a fresh, credential-free baseline and verify a full database restore.

Uses this machine's private runtime.json. Never copies the club database.
Each run creates new isolated build/test databases and a versioned archive.
"""
import configparser
import datetime
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = Path(json.loads((HERE / 'runtime.json').read_text())['runtime'])
DEST = Path(r'D:\odoo com\basic')
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
db = 'community_basic_' + stamp
test_db = db + '_restore'
folder = DEST / stamp
folder.mkdir(parents=True, exist_ok=False)
c = configparser.ConfigParser(interpolation=None)
c.read(ROOT / 'odoo.conf')
o = c['options']
source = ROOT / ('odoo-' + json.loads((HERE / 'source.lock.json').read_text())['odoo']['commit'])
python = ROOT / 'venv/Scripts/python.exe'
pg = ROOT / 'pgsql/bin'
pg_env = os.environ.copy()
pg_env['PGPASSWORD'] = (ROOT / 'pg-admin-password.txt').read_text().strip()
connection = ['-h', o['db_host'], '-p', o['db_port'], '-U', 'club_pg_admin']

def pg_run(program, args):
    subprocess.run([str(pg / (program + '.exe')), *connection, *args], env=pg_env, check=True, stdout=subprocess.DEVNULL)

def shell(database, code):
    result = subprocess.run([str(python), str(source / 'odoo-bin'), 'shell', '-c', str(ROOT / 'odoo.conf'), '-d', database, '--no-http', '--logfile', str(ROOT / 'basic-shell.log')], input=code, text=True, encoding='utf-8', capture_output=True)
    if result.returncode:
        raise RuntimeError('Odoo shell failed: ' + result.stderr[-2500:])
    return result.stdout

pg_run('createdb', ['-O', o['db_user'], db])
print('Created isolated baseline:', db, flush=True)
subprocess.run([str(python), str(source / 'odoo-bin'), '-c', str(ROOT / 'odoo.conf'), '-d', db, '-i', 'contacts,account,purchase,stock,base_accounting_kit,community_workspace', '--without-demo=all', '--load-language=ar_001', '--stop-after-init', '--no-http', '--logfile', str(ROOT / 'basic-build.log')], check=True)
shell(db, """
import secrets
company = env.ref('base.main_company')
company.write({'name': 'Community Business', 'country_id': env.ref('base.eg').id, 'currency_id': env.ref('base.EGP').id, 'email': False, 'phone': False, 'website': False})
env.ref('base.user_admin').write({'login': 'admin', 'name': 'Administrator', 'password': secrets.token_urlsafe(48), 'lang': 'ar_001', 'tz': 'Africa/Cairo'})
env['ir.mail_server'].search([]).unlink()
env['ir.cron'].search([]).write({'active': False})
env['ir.config_parameter'].sudo().set_param('auth_signup.invitation_scope', 'b2b')
for model in ['account.move', 'sale.order', 'purchase.order', 'stock.picking']:
    assert env[model].search_count([]) == 0, model
assert not env['ir.module.module'].search([('state','=','installed'),('license','=','OEEL-1')])
env.cr.commit()
print('Clean generic baseline configured')
""")
pg_run('pg_dump', ['-Fc', '--no-owner', '--no-acl', '-f', str(folder / 'database.dump'), db])
store = ROOT / 'data/filestore' / db
with zipfile.ZipFile(folder / 'filestore.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    if store.exists():
        for path in store.rglob('*'):
            if path.is_file():
                z.write(path, path.relative_to(store))
print('Testing full restore:', test_db, flush=True)
pg_run('createdb', ['-O', o['db_user'], test_db])
pg_run('pg_restore', ['--exit-on-error', '--no-owner', '--no-acl', '--role', o['db_user'], '-d', test_db, str(folder / 'database.dump')])
test_store = ROOT / 'data/filestore' / test_db
with zipfile.ZipFile(folder / 'filestore.zip') as z:
    assert z.testzip() is None
    z.extractall(test_store)
verification = shell(test_db, """
import json
from pathlib import Path
assert env.company.name == 'Community Business'
for name in ['base_accounting_kit', 'base_account_budget', 'community_workspace', 'muk_web_theme']:
    assert env['ir.module.module'].search([('name','=',name)]).state == 'installed', name
for model in ['account.move', 'sale.order', 'purchase.order', 'stock.picking']:
    assert not env[model].search_count([]), model
for model in ['account.move', 'account.asset.asset', 'account.balance.report']:
    env[model].get_views([(False, 'form')], {})
for attachment in env['ir.attachment'].search([('store_fname','!=',False)]):
    assert Path(attachment._full_path(attachment.store_fname)).is_file(), attachment.id
print(json.dumps({'restore': 'PASS', 'company': env.company.name, 'transactions': 0, 'modules': {m.name: m.installed_version for m in env['ir.module.module'].search([('state','=','installed')])}}))
""")
report = json.loads(next(line for line in verification.splitlines() if line.startswith('{"restore"')))
(folder / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
shutil.copytree(HERE / 'addons', folder / 'addons', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
lock = json.loads((HERE / 'third-party.lock.json').read_text())
for vendor, checkout in [('cybrosys', 'CybroAddons-19'), ('muk', 'MuK-19')]:
    for module in lock[vendor]['modules']:
        shutil.copytree(ROOT / 'downloads' / checkout / module, folder / 'addons' / module, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
for name in ['source.lock.json', 'third-party.lock.json', 'requirements.txt', 'restore-basic.py']:
    shutil.copy2(HERE / name, folder / name)
shutil.copy2(ROOT / 'source.zip', folder / 'odoo-community-source.zip')
shutil.copy2(ROOT / 'downloads/MuK-19/LICENSE', folder / 'MUK-LICENSE.txt')
shutil.copy2(HERE / 'docs/BASIC_RESTORE.md', folder / 'README.md')
hashes = {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
(folder / 'SHA256.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
(DEST / 'LATEST.json').write_text(json.dumps({'folder': str(folder), 'verified': True, 'database': db, 'restore_test_database': test_db}, indent=2), encoding='utf-8')
print('VERIFIED baseline saved:', folder, flush=True)
