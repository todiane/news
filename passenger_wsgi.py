# /home/djangify/newsapi.djangify.com/passenger_wsgi.py
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# Set up logging
def setup_logging():
    logger = logging.getLogger('passenger_wsgi')
    logger.setLevel(logging.DEBUG)
    
    log_dir = os.path.join(os.path.dirname(__file__), 'tmp')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=1024 * 1024,
        backupCount=5
    )
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()
logger.info('Starting passenger_wsgi.py')

try:
    # Add virtualenv site-packages
    VENV_PATH = "/home/djangify/virtualenv/newsapi.djangify.com/3.10"
    SITE_PACKAGES_PATH = os.path.join(VENV_PATH, 'lib', 'python3.10', 'site-packages')
    sys.path.insert(0, SITE_PACKAGES_PATH)
    
    # Add application paths - note the order is important
    BASE_PATH = "/home/djangify/newsapi.djangify.com"
    BACKEND_PATH = os.path.join(BASE_PATH, "backend")
    APP_PATH = os.path.join(BACKEND_PATH, "app")
    
    # Add paths in reverse order (most specific first)
    sys.path.insert(0, APP_PATH)
    sys.path.insert(0, BACKEND_PATH)
    sys.path.insert(0, BASE_PATH)
    
    logger.info(f'Python paths:')
    logger.info(f'BASE_PATH: {BASE_PATH}')
    logger.info(f'BACKEND_PATH: {BACKEND_PATH}')
    logger.info(f'APP_PATH: {APP_PATH}')
    
    logger.info('Importing FastAPI app...')
    from backend.main import app
    
    logger.info('FastAPI app imported successfully')
    application = app

except Exception as e:
    logger.error(f'Error in passenger_wsgi.py: {str(e)}', exc_info=True)
    raise

logger.info('passenger_wsgi.py initialization complete')
