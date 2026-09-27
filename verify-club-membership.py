"""Read-only verification of OCA membership on the club database."""
import json
from pathlib import Path
import requests

root = Path(json.loads((Path(__file__).parent / 'runtime.json').read_text())['runtime'])
a = json.loads((root / 'access.json').read_text())
assert a['database'] == 'beni_suef_club_dev'
s = requests.Session()
r = s.post(a['url'] + '/web/session/authenticate', json={'jsonrpc': '2.0', 'method': 'call', 'params': {'db': a['database'], 'login': a['login'], 'password': a['password']}, 'id': 1}, timeout=60).json()
assert r.get('result', {}).get('uid'), 'Authentication failed'
def call(model, method, args, kwargs=None):
    r = s.post(a['url'] + '/web/dataset/call_kw', json={'jsonrpc': '2.0', 'method': 'call', 'params': {'model': model, 'method': method, 'args': args, 'kwargs': kwargs or {}}, 'id': 2}, timeout=60).json()
    assert 'error' not in r, r.get('error', {}).get('data', {}).get('message')
    return r['result']
modules = call('ir.module.module', 'search_read', [[['name', 'in', ['membership', 'membership_delegated_partner']]]], {'fields': ['name', 'state', 'installed_version']})
assert len(modules) == 2 and all(m['state'] == 'installed' for m in modules)
for model in ['res.partner', 'membership.membership_line', 'membership.membership_category', 'membership.invoice']:
    call(model, 'get_views', [[[False, 'form']]], {'options': {}})
    print('Form OK:', model)
samples = call('res.partner', 'search_count', [[['name', 'in', ['TEST - Primary social member', 'TEST - Associated member']]]])
assert samples == 0, 'Lab samples unexpectedly present'
menus = s.get(a['url'] + '/web/webclient/load_menus', timeout=60)
menus.raise_for_status()
assert 'membership.menu_membership' in menus.text, 'Membership menu missing'
print('PASS: club membership installed; forms and menu accessible; no lab members copied.')
print(json.dumps(modules))
