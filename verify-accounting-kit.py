"""Read-only installation and view checks; not an accounting correctness audit."""
import json
from pathlib import Path
import requests

root = Path(json.loads((Path(__file__).parent/'runtime.json').read_text())['runtime'])
access = json.loads((root/'access.json').read_text())
session = requests.Session()
def rpc(path, params):
    response = session.post(access['url']+path, json={'jsonrpc':'2.0','method':'call','params':params,'id':1}, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if payload.get('error'):
        raise RuntimeError(payload['error'].get('data', {}).get('message', 'RPC error'))
    return payload['result']
assert rpc('/web/session/authenticate', {'db':access['database'],'login':access['login'],'password':access['password']})['uid']
def call(model, method, args=None, kwargs=None):
    return rpc('/web/dataset/call_kw/'+model+'/'+method, {'model':model,'method':method,'args':args or [],'kwargs':kwargs or {}})
modules = call('ir.module.module', 'search_read', [[('name','in',['base_accounting_kit','base_account_budget','cybrosys_support_client'])]], {'fields':['name','state','installed_version']})
assert len(modules) == 3 and all(m['state']=='installed' for m in modules)
print('Installed:', json.dumps(modules, ensure_ascii=True))
for model in ['account.move','account.account','account.journal','account.asset.asset','account.balance.report','account.aged.trial.balance','import.bank.statement','account.cash.book.report']:
    result = call(model, 'get_views', kwargs={'views':[[False,'form']], 'options':{'toolbar':False}})
    assert result.get('views',{}).get('form')
    print('Form accessible:', model)
menus = call('ir.ui.menu','load_menus',[False])
assert menus
print('Menus loaded; chart accounts:', call('account.account','search_count',[[]]))
print('PASS: installation, authenticated access and server-side form generation. No posted transactions created.')
