"""Offline backup: stop the club Odoo process before using this utility."""
import configparser
import datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import zipfile

root = Path(json.loads((Path(__file__).parent/'runtime.json').read_text())['runtime'])
with socket.socket() as s:
    if s.connect_ex(('127.0.0.1', 8095)) == 0:
        raise SystemExit('Stop the club server before backup to keep DB and attachments consistent.')
c = configparser.ConfigParser(interpolation=None)
c.read(root/'odoo.conf')
o = c['options']
assert o['db_name'] == 'beni_suef_club_dev'
folder = root/'backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
folder.mkdir(parents=True)
pg = root/'pgsql/bin'
envvars = os.environ.copy()
envvars['PGPASSWORD'] = o['db_password']
subprocess.run([str(pg/'pg_dump.exe'), '-h', o['db_host'], '-p', o['db_port'], '-U', o['db_user'], '-Fc', '--no-owner', '--no-acl', '-f', str(folder/'database.dump'), o['db_name']], env=envvars, check=True)
subprocess.run([str(pg/'pg_restore.exe'), '--list', str(folder/'database.dump')], check=True, stdout=subprocess.DEVNULL)
store = root/'data/filestore'/o['db_name']
with zipfile.ZipFile(folder/'filestore.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    if store.exists():
        for f in store.rglob('*'):
            if f.is_file():
                z.write(f, f.relative_to(store))
with zipfile.ZipFile(folder/'filestore.zip', 'r') as z:
    assert z.testzip() is None
(folder/'source.json').write_text((root/'source.json').read_text())
print('Backup created; archive readability verified (not a full restore test):', folder)
