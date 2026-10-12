"""Install versioned PO supplements before updating the four modules' translations.

Run with the club virtualenv while Odoo is stopped. Original PO files are kept
under the private runtime; rerunning merges by msgid without losing other terms.
"""
import datetime
import json
import shutil
import socket
import runpy
from pathlib import Path

import polib

project = Path(__file__).resolve().parent
runpy.run_path(str(project / 'verify-arabic-supplements.py'))
runtime = Path(json.loads((project / 'runtime.json').read_text())['runtime'])
with socket.socket() as connection:
    if connection.connect_ex(('127.0.0.1', 8095)) == 0:
        raise SystemExit('Stop club Odoo before installing translation supplements.')

sources = {
    'base_accounting_kit': runtime / 'downloads/CybroAddons-19',
    'base_account_budget': runtime / 'downloads/CybroAddons-19',
    'membership': runtime / 'downloads/OCA-association-19',
    'membership_delegated_partner': runtime / 'downloads/OCA-association-19',
}
backup = runtime / 'translation-backups' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
for module, root in sources.items():
    folder = root / module / 'i18n'
    assert folder.is_dir(), f'Missing module: {module}'
    target = folder / 'ar_001.po'
    base = target if target.exists() else folder / 'ar.po'
    if base.exists():
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(base, backup / f'{module}-{base.name}')
        merged = polib.pofile(str(base))
    else:
        merged = polib.POFile()
    supplement = polib.pofile(str(project / 'translations' / f'{module}.po'))
    merged.metadata.update(supplement.metadata)
    for entry in supplement:
        old = merged.find(entry.msgid, msgctxt=entry.msgctxt)
        if old:
            merged.remove(old)
        merged.append(entry)
    temporary = target.with_suffix('.po.tmp')
    merged.save(str(temporary))
    temporary.replace(target)
    print(module, 'supplemental terms:', len(supplement))
print('Original translations backup:', backup)
