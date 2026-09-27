"""Run in Odoo shell against club_membership_lab ONLY; creates labelled samples."""
import json
from datetime import timedelta
from pathlib import Path
from odoo import fields
from odoo.exceptions import ValidationError

assert env.cr.dbname == 'club_membership_lab'
today = fields.Date.today()
Partner = env['res.partner']
category = env['membership.membership_category'].create({'name': 'TEST - Social membership'})
product = env['product.product'].create({
    'name': 'TEST ONLY - membership period (no approved price)',
    'type': 'service', 'membership': True, 'list_price': 0,
    'membership_date_from': today, 'membership_date_to': today + timedelta(days=364),
    'membership_category_id': category.id,
})
primary = Partner.create({'name': 'TEST - Primary social member'})
dependent = Partner.create({'name': 'TEST - Associated member', 'associate_member_id': primary.id})
line = env['membership.membership_line'].create({
    'partner_id': primary.id, 'membership_id': product.id,
    'date': today, 'date_from': today, 'date_to': today + timedelta(days=364),
    'state': 'free', 'member_price': 0,
})
assert primary.membership_state == 'free'
assert dependent.membership_state == primary.membership_state
assert dependent.membership_stop == primary.membership_stop
assert dependent.membership_category_ids == primary.membership_category_ids
try:
    with env.cr.savepoint():
        primary.associate_member_id = dependent
except ValidationError:
    pass
else:
    raise AssertionError('Circular membership association accepted')
# A second membership period retains history; no pricing policy implied.
renewal = env['membership.membership_line'].create({
    'partner_id': primary.id, 'membership_id': product.id,
    'date': today, 'date_from': today + timedelta(days=365),
    'date_to': today + timedelta(days=729), 'state': 'waiting', 'member_price': 0,
})
assert len(primary.member_line_ids) == 2
assert primary.membership_state == 'free'
for model in ['res.partner', 'membership.membership_line', 'membership.membership_category', 'membership.invoice']:
    env[model].get_views([(False, 'form')], {})
assert not env['account.move'].search_count([]), 'Unexpected financial entries'
acl = env.ref('membership.access_product_membership_manager')
report = {
    'database': env.cr.dbname, 'sample_primary_id': primary.id,
    'association_state_dates_categories': 'PASS', 'circular_association_rejected': 'PASS',
    'second_period_preserves_history': 'PASS', 'forms': 'PASS', 'financial_entries': 0,
    'finding_product_acl': {'group': acl.group_id.name, 'create': acl.perm_create, 'write': acl.perm_write, 'delete': acl.perm_unlink},
    'limitations': ['No family kinship or dependent eligibility workflow', 'No administrative approval workflow', 'Membership line status is editable', 'Renewal prices and club policies not configured'],
}
env.cr.commit()
Path(r'C:\Users\accis\ClubRuntime\membership-evaluation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
