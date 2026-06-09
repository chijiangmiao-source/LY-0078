# -*- coding: utf-8 -*-
from tg import FullStackApplicationConfigurator
import breakfast_management
from breakfast_management.lib import app_globals, helpers
from breakfast_management.controllers.root import RootController


base_config = FullStackApplicationConfigurator()
base_config.update_blueprint({
    'package': breakfast_management,
    'root_controller': RootController(),
    'renderers': ['genshi', 'json'],
    'default_renderer': 'genshi',
    'use_dotted_templatenames': False,
    'auto_reload_templates': True,
    'tg.strict_tmpl_context': False,
})
