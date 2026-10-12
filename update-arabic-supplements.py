"""Run inside club Odoo shell after install-arabic-supplements.py."""
assert env.cr.dbname == 'beni_suef_club_dev'
names = ['base_accounting_kit', 'base_account_budget', 'membership', 'membership_delegated_partner']
modules = env['ir.module.module'].search([('name', 'in', names), ('state', '=', 'installed')])
assert len(modules) == len(names)
modules._update_translations(['ar_001'], overwrite=True)
env.cr.commit()
print('Arabic supplements imported:', len(modules))
