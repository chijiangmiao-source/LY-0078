# -*- coding: utf-8 -*-
from breakfast_management.config.environment import load_environment
from tg import AppConfig

application = None


def make_app(global_conf, full_stack=True, **app_conf):
    global application
    config = load_environment(global_conf, app_conf)
    app = config.make_wsgi_app()
    application = app
    return app
