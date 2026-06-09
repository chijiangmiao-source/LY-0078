# -*- coding: utf-8 -*-
from sqlobject import connectionForURI, sqlhub

from breakfast_management.config.app_cfg import base_config


__all__ = ['load_environment']


def setup_sqlobject(conf):
    dburi = conf.get('sqlobject.dburi') or conf.get('sqlalchemy.url')
    if dburi:
        conn = connectionForURI(dburi)
        sqlhub.processConnection = conn

        from breakfast_management import model
        model.init_model(sqlhub)


def load_environment(global_conf, app_conf):
    conf = base_config.configure(global_conf, app_conf)
    base_config.setup(conf)
    setup_sqlobject(conf)
    return conf
