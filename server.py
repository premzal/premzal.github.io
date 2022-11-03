from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.renderers import render_to_response
from pyramid.response import FileResponse

import mysql.connector as mysql
import os

def get_home(req):
    return FileResponse('Website/home.html')

''' Route Configurations '''
if __name__ == '__main__':
  config = Configurator()
  
  config.include('pyramid_jinja2')
  config.add_jinja2_renderer('.html')
  
  config.add_route('get_home', '/')
  config.add_view(get_home, route_name='get_home')
  
  config.add_static_view(name='/', path='./public', cache_max_age=3600)

  app = config.make_wsgi_app()
  server = make_server('0.0.0.0', 6000, app)
  server.serve_forever()

