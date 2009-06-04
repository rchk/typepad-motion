import logging

from settings import INSTALLED_APPS

INSTALLED_APPS = INSTALLED_APPS + ('typepadapp', 'motion')

DATABASE_ENGINE = 'sqlite3'

COMMENTS_PER_PAGE = 10
EVENTS_PER_PAGE = 10
MEMBERS_PER_WIDGET = 10

LOG_LEVEL = logging.CRITICAL
LOG_FORMAT = '%(name)-20s %(levelname)-8s %(message)s'
LOG_LEVELS = {}

BACKEND_URL = 'http://localhost'
TYPEPAD_COOKIES = {}
BATCH_REQUESTS = True

