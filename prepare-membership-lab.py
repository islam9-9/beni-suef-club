"""Create an isolated OCA membership evaluation from the verified generic backup."""
import configparser
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import zipfile

here = Path(__file__).resolve().parent
root = Path(json.loads((here / 'runtime.json').read_text())['runtime'])
backup = Path(json.loads(Path(r'D:\odoo com\basic\LATEST.json').read_text())['folder'])
db = 'club_membership_lab'
cfg = root / 'membership-lab.conf'
if cfg.exists():
    raise SystemExit('Lab already prepared; refusing to overwrite.')
hashes = json.loads((backup / 'SHA256.json').read_text())
for name in ['database.dump', 'filestore.zip']:
    assert hashlib.sha256((backup / name).read_bytes()).hexdigest() == hashes[name]
c = configparser.ConfigParser(interpolation=None)
c.read(root / 'odoo.conf')
o = c['options']
o['db_name'] = db
o['dbfilter'] = '^' + db + '$'
o['http_port'] = '8096'
o['http_interface'] = '127.0.0.1'
o['max_cron_threads'] = '0'
o['logfile'] = str(root / 'membership-lab.log')
o['addons_path'] += ',' + str(root / 'downloads/OCA-association-19')
pg_env = os.environ.copy()
pg_env['PGPASSWORD'] = (root / 'pg-admin-password.txt').read_text().strip()
args = ['-h', o['db_host'], '-p', o['db_port'], '-U', 'club_pg_admin']
for tool, extra in [('createdb', ['-O', o['db_user'], db]), ('pg_restore', ['--exit-on-error', '--no-owner', '--no-acl', '--role', o['db_user'], '-d', db, str(backup / 'database.dump')])]:
    subprocess.run([str(root / 'pgsql/bin' / (tool + '.exe')), *args, *extra], env=pg_env, check=True)
with zipfile.ZipFile(backup / 'filestore.zip') as z:
    z.extractall(root / 'data/filestore' / db)
with cfg.open('w') as f:
    c.write(f)
source = root / ('odoo-' + json.loads((here / 'source.lock.json').read_text())['odoo']['commit'])
command = [str(root / 'venv/Scripts/python.exe'), str(source / 'odoo-bin')]
subprocess.run([*command, '-c', str(cfg), '-i', 'membership,membership_delegated_partner', '--without-demo=all', '--test-enable', '--test-tags', '/membership,/membership_delegated_partner', '--stop-after-init', '--no-http'], check=True)
access = {'url': 'http://127.0.0.1:8096', 'database': db, 'login': 'membership.admin', 'password': secrets.token_urlsafe(24)}
code = "env.ref('base.user_admin').write(" + repr({'login': access['login'], 'password': access['password']}) + "); env.company.name = 'Membership Evaluation - TEST ONLY'; env['ir.config_parameter'].sudo().set_param('web.base.url', 'http://127.0.0.1:8096'); env.cr.commit()"
subprocess.run([*command, 'shell', '-c', str(cfg), '--no-http'], input=code, encoding='utf-8', check=True)
(root / 'membership-lab-access.json').write_text(json.dumps(access), encoding='utf-8')
print('Lab ready on port 8096; access details stored privately in runtime.')
