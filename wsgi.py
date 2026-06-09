# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paste.deploy import loadapp

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'development.ini')
application = loadapp('config:' + config_file)

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    server = make_server('0.0.0.0', 8080, application)
    print('Starting server on http://0.0.0.0:8080')
    server.serve_forever()
