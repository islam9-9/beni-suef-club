"""Run through the club's Odoo shell after taking an offline backup."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
assert env.cr.dbname == 'beni_suef_club_dev', 'This script is club-specific'
language = env['res.lang'].with_context(active_test=False).search([('code', '=', 'ar_001')], limit=1)
assert language, 'Standard Arabic is unavailable'
env['base.language.install'].create({
    'lang_ids': [(6, 0, language.ids)],
    'overwrite': False,
}).lang_install()
users = env['res.users'].with_context(active_test=False).search([('share', '=', False)])
users.write({'lang': language.code})
env.ref('base.public_user').write({'lang': language.code})
template = env.ref('base.default_user', raise_if_not_found=False)
if template:
    template.write({'lang': language.code})
env['ir.default'].set('res.partner', 'lang', language.code)
env.ref('account.menu_finance').with_context(lang=language.code).write({'name': '\u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a'})
env.ref('purchase.menu_purchase_root').with_context(lang=language.code).write({'name': '\u0627\u0644\u0645\u0634\u062a\u0631\u064a\u0627\u062a'})
env.cr.commit()
print('Arabic enabled for internal users:', len(users))
for menu in env['ir.ui.menu'].with_context(lang=language.code).search([('parent_id', '=', False)]):
    print(menu.id, menu.name)
