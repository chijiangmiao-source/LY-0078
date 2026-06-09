# -*- coding: utf-8 -*-
from breakfast_management.config.environment import load_environment
from breakfast_management.config.app_cfg import base_config

application = None


def make_app(global_conf, full_stack=True, **app_conf):
    global application
    conf = load_environment(global_conf, app_conf)
    app = base_config.make_wsgi_app(global_conf, app_conf)
    application = app
    return app
