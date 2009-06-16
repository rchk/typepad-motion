# Motion application settings.
# You can override these in your custom app settings.py.
import os
import logging
from django.utils.translation import ugettext_lazy as _

DEBUG = False
TEMPLATE_DEBUG = DEBUG

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'dev.db'
DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''

APPEND_SLASH = False

TIME_ZONE = 'ETC/UTC'
USE_I18N = True
LANGUAGE_CODE = 'en-us'
LANGUAGES = (
    ('en', _('English')),
)

MEDIA_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/media/'

AUTHENTICATION_BACKENDS = (
    'typepadapp.backends.TypePadBackend',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'typepadapp.csrf_middleware.CsrfMiddleware', # django.contrib.csrf.middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'typepadapp.middleware.ConfigurationMiddleware',
    'typepadapp.debug_middleware.DebugToolbarMiddleware',
    'typepadapp.middleware.ApplicationMiddleware',
    'typepadapp.middleware.UserAgentMiddleware',
    'typepadapp.middleware.AuthorizationExceptionMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.media',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'typepadapp.context_processors.settings',
)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'motion',
    'typepadapp',
)

##############################
# POTION INSTALL SETTINGS    #
##############################
SITE_ID = 1
SECRET_KEY = ''

BACKEND_URL = 'http://127.0.0.1:8800'
FRONTEND_URL = 'http://127.0.0.1:8000'

## Potion site layout settings.
# Override these in your settings.py for a
# different homepage.
# 1. Group activity.
FEATURED_MEMBER = None
HOME_MEMBER_EVENTS = False
# 2. Featured member.
# FEATURED_MEMBER = '' # Featured member XID
# HOME_MEMBER_EVENTS = False
# 3. Following activity.
# FEATURED_MEMBER = None
# HOME_MEMBER_EVENTS = True

LOGIN_URL = '/login'

OAUTH_CONSUMER_KEY = 'key'
OAUTH_CONSUMER_SECRET = 'secret'
OAUTH_GENERAL_PURPOSE_KEY = 'gp_key'
OAUTH_GENERAL_PURPOSE_SECRET = 'gp_secret'
TYPEPAD_API_KEY = OAUTH_CONSUMER_KEY

OAUTH_CALLBACK_URL = '%s/authorize/' % FRONTEND_URL

BATCH_REQUESTS = not os.getenv('TYPEPAD_BATCHLESS')

SESSION_COOKIE_NAME = 'motion'
TYPEPAD_COOKIES = {}

AUTH_PROFILE_MODULE = ''
CACHE_BACKEND = 'locmem:///'

POST_TYPES =  [
    { "id": "post", "label": "Text" },
    { "id": "link", "label": "Link" },
    { "id": "photo", "label": "Photo" },
    { "id": "video", "label": "Video" },
    { "id": "audio", "label": "Audio" },
]

DEFAULT_USERPIC_PATH = 'images/default-avatars/spaceface-50x50.jpg'

USE_GRAVATAR = False
USE_DWIM = False
USE_TITLES = False

# Switches to enable/disable posting/commenting/rating/following
ALLOW_POSTING = True
ALLOW_COMMENTING = True
ALLOW_RATING = True

# Allow users to delete their own posts and comments
ALLOW_USERS_TO_DELETE_POSTS = True
# Allow users to post new content to the group
ALLOW_COMMUNITY_POSTS = True

# Number of events on the home page.
EVENTS_PER_PAGE = 25
# Number of items in the atom feed.
ITEMS_PER_FEED = 18
COMMENTS_PER_PAGE = 50
# Group members, following, followers
MEMBERS_PER_PAGE = 18
MEMBERS_PER_WIDGET = 30
FOLLOWERS_PER_WIDGET = 5
# Max number or words for a short paragraph,
# used for truncating on the front page.
PARAGRAPH_WORDCOUNT = 100

# Default CSS theme to use for site
THEME = 'motion'

# Logging
LOG_FORMAT = '%(name)-20s %(levelname)-8s %(message)s'
LOG_LEVEL = logging.INFO
LOG_LEVELS = {
    'remoteobjects.http': logging.WARNING,
    'batchhttp.client': logging.WARNING,
    'typepad.oauthclient': logging.WARNING,
}
