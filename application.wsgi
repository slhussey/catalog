# Bridge code between the wsgi in Apache and the original Flask application

import sys

#Expand Python classes path with my application's path
sys.path.insert(0, "/var/www/html/catalog")

from application import app

#Initialize WSGI app object
application = app
