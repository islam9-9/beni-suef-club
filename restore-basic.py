"""Restore into a NEW database using a privately prepared Odoo configuration.
Usage: python restore-basic.py --config C:\\private\\odoo.conf --pg-bin C:\\pgsql\\bin --odoo C:\\odoo\\odoo-bin --database new_project
PGPASSWORD must contain the password of PGUSER (a database creation role).
Config addons_path must include this package's addons; data_dir must be writable.
"""
import argparse
import configparser
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

p = argparse.ArgumentParser(description=__doc__)
for name in ['config', 'pg-bin', 'odoo', 'database']:
    p.add_argument('--' + name, required=True)
a = p.parse_args()
assert re.fullmatch('[a-z][a-z0-9_]{2,62}', a.database), 'Use a new lowercase database name'
assert os.environ.get('PGPASSWORD') and os.environ.get('PGUSER'), 'Set PGUSER and PGPASSWORD privately'
root = Path(__file__).resolve().parent
for name, digest in json.loads((root / 'SHA256.json').read_text()).items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
c = configparser.ConfigParser(interpolation=None)
c.read(a.config)
o = c['options']
assert o['db_name'] == a.database, 'Config db_name must match the NEW target database'
password = getpass.getpass('New project administrator password (minimum 12 characters): ')
assert len(password) >= 12
assert password == getpass.getpass('Confirm password: ')
args = ['-h', o['db_host'], '-p', o['db_port'], '-U', os.environ['PGUSER']]
def run(program, extra):
    subprocess.run([str(Path(a.pg_bin) / (program + '.exe')), *args, *extra], check=True)
# createdb deliberately fails if the target already exists. Never overwrite.
run('createdb', ['-O', o['db_user'], a.database])
run('pg_restore', ['--exit-on-error', '--no-owner', '--no-acl', '--role', o['db_user'], '-d', a.database, str(root / 'database.dump')])
target = Path(o['data_dir']) / 'filestore' / a.database
with zipfile.ZipFile(root / 'filestore.zip') as z:
    for member in z.namelist():
        assert (target / member).resolve().is_relative_to(target.resolve())
    z.extractall(target)
code = "env.ref('base.user_admin').write({'password': " + repr(password) + "}); env.cr.commit()"
subprocess.run([sys.executable, a.odoo, 'shell', '-c', a.config, '-d', a.database, '--no-http'], input=code, encoding='utf-8', check=True)
print('Restored. Login: admin. Configure company, accounting chart, and required scheduled actions before operational use.')
