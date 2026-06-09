# -*- coding: utf-8 -*-
import os
from sqlobject import connectionForURI, sqlhub
from sqlobject.mysql import MySQLConnection
import tg
from tg.configuration import milestones
from tg.support import converters
from tg.configuration.utils import coerce_config

from breakfast_management.config.app_cfg import base_config


__all__ = ['load_environment']

base_config = base_config


def setup_sqlobject():
    from tg.configuration import config
    dburi = config.get('sqlobject.dburi') or config.get('sqlalchemy.url')
    if dburi:
        if dburi.startswith('mysql://'):
            conn = MySQLConnection(
                db=dburi.split('/')[-1].split('?')[0],
                user=dburi.split('//')[1].split(':')[0],
                password=dburi.split(':')[2].split('@')[0],
                host=dburi.split('@')[1].split('/')[0].split(':')[0] if ':' in dburi.split('@')[1].split('/')[0] else dburi.split('@')[1].split('/')[0],
                port=int(dburi.split(':')[-1].split('/')[0]) if ':' in dburi.split('@')[1] else 3306,
                charset='utf8mb4'
            )
        else:
            conn = connectionForURI(dburi)
        sqlhub.processConnection = conn

        from breakfast_management import model
        model.init_model(sqlhub)


def load_environment(global_conf, app_conf):
    tg.config.update(global_conf)
    tg.config.update(app_conf)

    base_config.init_config(tg.config)
    base_config.setup_helpers_and_globals()
    base_config.setup_routes()

    milestones.config_ready.register(setup_sqlobject)
    milestones.config_ready.call()

    base_config.call_on_startup()
    return base_config
