"""Run using Odoo shell against the newly initialized club database only."""
import json
from pathlib import Path
assert env.cr.dbname == 'beni_suef_club_dev'
root = Path(r'C:\Users\accis\ClubRuntime')
access = json.loads((root/'access.json').read_text())
company = env.ref('base.main_company')
company.write({'name': 'نادي بني سويف الرياضي — بيئة تجريبية', 'country_id': env.ref('base.eg').id, 'currency_id': env.ref('base.EGP').id})
admin = env.ref('base.user_admin')
admin.write({'login': access['login'], 'password': access['password'], 'name': 'Club Administrator', 'lang': 'ar_001', 'tz': 'Africa/Cairo'})
params = env['ir.config_parameter'].sudo()
params.set_param('web.base.url', access['url'])
params.set_param('web.base.url.freeze', 'True')
env.cr.commit()
installed = env['ir.module.module'].search([('state', '=', 'installed')])
assert not installed.filtered(lambda m: m.license == 'OEEL-1'), 'Enterprise module detected'
print('Bootstrap complete. Installed modules:', ', '.join(installed.mapped('name')))
