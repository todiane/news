# test_log.py in /home/djangify/newsapi.djangify.com/
import os
import logging

log_dir = os.path.join(os.path.dirname(__file__), 'tmp')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename=os.path.join(log_dir, 'test.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.info("Test log entry")
