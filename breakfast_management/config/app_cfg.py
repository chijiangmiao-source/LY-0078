# -*- coding: utf-8 -*-
from tg.configuration import AppConfig
import breakfast_management
from breakfast_management import model
from breakfast_management.lib import app_globals, helpers
from sqlobject.mysql import builder


class CustomAppConfig(AppConfig):
    def __init__(self):
        AppConfig.__init__(self)
        self.default_renderer = 'genshi'
        self.renderers = ['genshi', 'json']
        self.use_sqlalchemy = False
        self.use_sqlobject = True
        self.use_toscawidgets = False
        self.use_toscawidgets2 = True
        self.package_name = 'breakfast_management'
        self.package = breakfast_management
        self.auth_backend = None
        self.use_dotted_templatenames = False
        self.base_template = 'breakfast_management.templates.master'
        self.templating.genshi.loader_options = {
            'auto_reload': True,
        }
        self.paths['templates'] = [breakfast_management.__path__[0] + '/templates']

    def setup_sqlalchemy(self):
        pass

    def setup_helpers_and_globals(self):
        self['tg.app_globals'] = app_globals.Globals()
        self['tg.strict_tmpl_context'] = False
        self['pylons.app_globals'] = app_globals.Globals()
        self['pylons.h'] = helpers

    def setup_routes(self):
        from tg.configuration.routing import make_map
        from routes import Mapper

        def rss_remap(url):
            return url

        mapper = make_map(self)
        with mapper.submapper(controller='root') as m:
            m.connect('home', '/', action='index')
            m.connect('/login', action='login')
            m.connect('/logout', action='logout')
            m.connect('/dashboard', action='dashboard')

        with mapper.submapper(path_prefix='/rooms', controller='rooms') as m:
            m.connect('/', action='index')
            m.connect('/new', action='new')
            m.connect('/create', action='create')
            m.connect('/{id}/edit', action='edit')
            m.connect('/{id}/update', action='update')
            m.connect('/{id}/delete', action='delete')

        with mapper.submapper(path_prefix='/guests', controller='guests') as m:
            m.connect('/', action='index')
            m.connect('/new', action='new')
            m.connect('/create', action='create')
            m.connect('/{id}/edit', action='edit')
            m.connect('/{id}/update', action='update')
            m.connect('/{id}/delete', action='delete')

        with mapper.submapper(path_prefix='/packages', controller='packages') as m:
            m.connect('/', action='index')
            m.connect('/new', action='new')
            m.connect('/create', action='create')
            m.connect('/{id}/edit', action='edit')
            m.connect('/{id}/update', action='update')
            m.connect('/{id}/delete', action='delete')

        with mapper.submapper(path_prefix='/baskets', controller='baskets') as m:
            m.connect('/', action='index')
            m.connect('/new', action='new')
            m.connect('/create', action='create')
            m.connect('/{id}/edit', action='edit')
            m.connect('/{id}/update', action='update')
            m.connect('/{id}/delete', action='delete')

        with mapper.submapper(path_prefix='/schedules', controller='schedules') as m:
            m.connect('/', action='index')
            m.connect('/new', action='new')
            m.connect('/create', action='create')
            m.connect('/{id}/edit', action='edit')
            m.connect('/{id}/update', action='update')
            m.connect('/{id}/delete', action='delete')
            m.connect('/{id}/complete', action='complete')

        with mapper.submapper(path_prefix='/assembly', controller='assembly') as m:
            m.connect('/', action='index')
            m.connect('/create', action='create')

        with mapper.submapper(path_prefix='/deliveries', controller='deliveries') as m:
            m.connect('/', action='index')
            m.connect('/new', action='new')
            m.connect('/create', action='create')
            m.connect('/{id}/deliver', action='deliver')
            m.connect('/{id}/return', action='return_basket')
            m.connect('/{id}/delete', action='delete')

        with mapper.submapper(path_prefix='/api', controller='api') as m:
            m.connect('/stats', action='stats')
            m.connect('/search', action='search')

        self['routes.map'] = mapper
        self['routes.directory'] = rss_remap


base_config = CustomAppConfig()
