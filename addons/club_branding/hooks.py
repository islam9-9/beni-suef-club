import base64
from odoo.tools import file_open

def post_init_hook(env):
    with file_open('club_branding/static/img/club_logo.png', 'rb') as source:
        logo = base64.b64encode(source.read())
    company = env.ref('base.main_company')
    company.write({'name': 'نادي بني سويف الرياضي', 'logo': logo, 'favicon': logo})
    settings = env['res.config.settings']
    env['muk_web_colors.color_assets_editor'].replace_color_variables_values(
        settings.COLOR_ASSET_LIGHT_URL, settings.COLOR_BUNDLE_LIGHT_NAME,
        [{'name': 'color_brand', 'value': '#142E42'},
         {'name': 'color_primary', 'value': '#245B94'}],
    )
