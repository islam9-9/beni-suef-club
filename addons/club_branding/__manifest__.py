{
    'name': 'Beni Suef Club Identity',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['community_workspace', 'muk_web_refresh', 'cybrosys_support_client', 'base_accounting_kit'],
    'data': ['views/login.xml', 'views/home.xml', 'views/accounting_arabic.xml'],
    'assets': {
        'web.assets_frontend': ['club_branding/static/src/club_login.scss'],
        'web.assets_backend': ['club_branding/static/src/club_backend.scss', 'club_branding/static/src/sidebar.xml', 'club_branding/static/src/arabic.xml', 'club_branding/static/src/home.js', 'club_branding/static/src/home.xml'],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
}
