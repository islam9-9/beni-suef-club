{
    'name': 'Community Workspace',
    'summary': 'Reusable Arabic-friendly workspace styling for Community projects',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'Community Workspace Team',
    'depends': ['muk_web_theme'],
    'data': ['views/login.xml'],
    'assets': {
        'web.assets_backend': ['community_workspace/static/src/scss/workspace.scss'],
        'web.assets_frontend': ['community_workspace/static/src/scss/login.scss'],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
