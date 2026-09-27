def post_init_hook(env):
    """Set initial defaults once; subsequent theme preferences remain editable."""
    settings = env['res.config.settings']
    env['muk_web_colors.color_assets_editor'].replace_color_variables_values(
        settings.COLOR_ASSET_LIGHT_URL,
        settings.COLOR_BUNDLE_LIGHT_NAME,
        [{'name': 'color_brand', 'value': '#172D40'},
         {'name': 'color_primary', 'value': '#087F8C'},
         {'name': 'color_success', 'value': '#21845A'},
         {'name': 'color_info', 'value': '#2879B5'},
         {'name': 'color_warning', 'value': '#B77913'},
         {'name': 'color_danger', 'value': '#C23B45'}],
    )
