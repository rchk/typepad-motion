# Copyright (c) 2009 Six Apart Ltd.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of Six Apart Ltd. nor the names of its contributors may
#   be used to endorse or promote products derived from this software without
#   specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

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

# Enable this if you need to customize application phrases or
# need real localization
USE_I18N = False

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
    'djangoflash.middleware.FlashMiddleware',
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
    'djangoflash.context_processors.flash',
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

BACKEND_URL = 'https://api.typepad.com'
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

BATCH_REQUESTS = not os.getenv('TYPEPAD_BATCHLESS')

SESSION_COOKIE_NAME = 'motion'
TYPEPAD_COOKIES = {}

AUTH_PROFILE_MODULE = ''
CACHE_BACKEND = 'locmem:///'

POST_TYPES =  [
    { "id": "post", "label": _("Text") },
    { "id": "link", "label": _("Link") },
    { "id": "photo", "label": _("Photo") },
    { "id": "video", "label": _("Video") },
    { "id": "audio", "label": _("Audio") },
]

DEFAULT_USERPIC_PATH = 'images/default-avatars/spaceface-50x50.jpg'

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
# Maximum number of characters for a link when
# used as a title.
LINK_TITLE_LENGTH = 60
# Set to True to provide the full post content in feeds
FULL_FEED_CONTENT = False
# Target photo thumbnail resolution for display; this does not restrict
# size of photos that are posted to the group
PHOTO_MAX_WIDTH = 460
# Target video size for display
VIDEO_MAX_WIDTH = 400

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
