# passenger_wsgi.py
import os
import sys

# Add application directory to Python path
VENV_PATH = "/home/djangify/virtualenv/newsapi.djangify.com/3.10"
APP_PATH = "/home/djangify/newsapi.djangify.com/backend"

# Activate virtual environment
activate_this = f"{VENV_PATH}/bin/activate_this.py"
exec(open(activate_this).read(), {'__file__': activate_this})

# Add application path to system path
sys.path.insert(0, APP_PATH)

# Import FastAPI application
from backend.main import app

# Create ASGI application
application = app
