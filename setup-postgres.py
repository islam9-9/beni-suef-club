"""One-time migration of the new club development DB to a private PG16 instance."""
import configparser
import json
import os
from pathlib import Path
import secrets
import subprocess
import zipfile
import psycopg2
from psycopg2 import sql

root = Path(json.loads((Path(__file__).parent/'runtime.json').read_text())['runtime'])
with zipfile.ZipFile(root/'postgres.zip') as z:
    for name in z.namelist():
        if name.startswith(('pgsql/bin/', 'pgsql/lib/', 'pgsql/share/')):
            z.extract(name, root)
pg = root/'pgsql/bin'
data = root/'pgdata'
if data.exists():
    raise SystemExit('PG data already exists; refusing initialization')
adminpass = secrets.token_urlsafe(40)
passwordfile = root/'pg-admin-password.txt'
passwordfile.write_text(adminpass)
flags = subprocess.CREATE_NO_WINDOW
subprocess.run([str(pg/'initdb.exe'), '-D', str(data), '-U', 'club_pg_admin', '--pwfile='+str(passwordfile), '-A', 'scram-sha-256', '-E', 'UTF8', '--locale=C'], check=True, creationflags=flags)
with (data/'postgresql.conf').open('a') as f:
    f.write("\nlisten_addresses = '127.0.0.1'\nport = 5495\n")
subprocess.run([str(pg/'pg_ctl.exe'), '-D', str(data), '-l', str(root/'logs/postgres.log'), '-w', 'start'], check=True, creationflags=flags)
c = configparser.ConfigParser(interpolation=None)
c.read(root/'odoo.conf')
o = c['options']
assert o['db_name'] == 'beni_suef_club_dev'
dump = root/'backups/pre-pg16.dump'
environ = os.environ.copy()
environ['PGPASSWORD'] = o['db_password']
subprocess.run([str(pg/'pg_dump.exe'), '-h', o['db_host'], '-p', o['db_port'], '-U', o['db_user'], '-Fc', '--no-owner', '--no-acl', '-f', str(dump), o['db_name']], env=environ, check=True, creationflags=flags)
con = psycopg2.connect(host='127.0.0.1', port=5495, user='club_pg_admin', password=adminpass, dbname='postgres')
con.autocommit = True
with con.cursor() as cr:
    cr.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD %s NOSUPERUSER NOCREATEDB NOCREATEROLE').format(sql.Identifier(o['db_user'])), (o['db_password'],))
    cr.execute(sql.SQL('CREATE DATABASE {} OWNER {} TEMPLATE template0 ENCODING %s').format(sql.Identifier(o['db_name']), sql.Identifier(o['db_user'])), ('UTF8',))
    cr.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(o['db_name'])))
con.close()
subprocess.run([str(pg/'pg_restore.exe'), '-h', '127.0.0.1', '-p', '5495', '-U', o['db_user'], '-d', o['db_name'], '--no-owner', '--no-acl', '--exit-on-error', str(dump)], env=environ, check=True, creationflags=flags)
o['db_host'] = '127.0.0.1'
o['db_port'] = '5495'
with (root/'odoo.conf').open('w') as f:
    c.write(f)
print('Migrated club database to private PostgreSQL on localhost:5495')
