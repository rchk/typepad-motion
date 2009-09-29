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

import os.path

from django.conf.urls.defaults import *


app_path = os.path.dirname(__file__)
app_dir = os.path.basename(app_path)
media_dir = os.path.join(app_path, 'static')
theme_dir = os.path.join(app_path, 'static', 'theme')

urlpatterns = patterns('motion.views',
    # main index
    url(r'^$', 'home', name='home'),
    url(r'^page/(?P<page>\d+)/?$', 'home'),

    # file upload callback
    url(r'^upload_complete/?$', 'upload_complete', name='upload_complete'),

    # post permalink
    url(r'^entry/(?P<postid>\w+)/?', 'AssetView', name='asset'),

    # group events
    url(r'^events/?$', 'GroupEventsView', name='group_events'),
    url(r'^events/page/(?P<page>\d+)/?$', 'GroupEventsView'),

    # following inbox
    url(r'^following/?$', 'FollowingEventsView', name='following_events'),
    url(r'^following/page/(?P<page>\d+)/?$', 'FollowingEventsView'),

    # member pages (userids are [a-zA-Z0-9_]+)
    url(r'^members/?$', 'MembersView', name='members'),
    url(r'^members/page/(?P<page>\d+)/?$', 'MembersView'),
    url(r'^members/(?P<userid>\w+)/?$', 'MemberView', name='member'),
    url(r'^members/(?P<userid>\w+)/page/(?P<page>\d+)/?$', 'MemberView'),
    url(r'^members/(?P<userid>\w+)/following/?$', 'RelationshipsView', {'rel': 'following'}, name='following'),
    url(r'^members/(?P<userid>\w+)/followers/?$', 'RelationshipsView', {'rel': 'followers'}, name='followers'),
    url(r'^members/(?P<userid>\w+)/(?P<rel>following|followers)/page/(?P<page>\d+)/?$', 'RelationshipsView'),
)

urlpatterns += patterns('motion.ajax',
    url(r'^ajax/more_comments/?$', 'more_comments', name='comments_url'),
    url(r'^ajax/favorite/?$', 'favorite', name='favorite_url'),
    url(r'^ajax/edit_profile/?$', 'edit_profile', name='edit_profile_url'),
    url(r'^ajax/upload_url/?$', 'upload_url', name='upload_url'),
)

# terms of service / privacy pages
urlpatterns += patterns('typepadapp.views.generic.simple',
    url(r'^terms/?$', 'direct_to_template', {'template': 'motion/pages/terms.html'}, name='terms'),
    url(r'^privacy/?$', 'direct_to_template', {'template': 'motion/pages/privacy.html'}, name='privacy'),
)

# Feeds
from motion.feeds import PublicEventsFeed, MemberFeed, CommentsFeed
urlpatterns += patterns('',
    url(r'^feeds/(?P<url>.*)/?$', 'django.contrib.syndication.views.feed',
        {'feed_dict':
            {
                'events'  : PublicEventsFeed, # home/index page feed
                'members' : MemberFeed,       # member page feed
                'entry'   : CommentsFeed,     # permalink comments feed
            }
        }, name='feeds'),
)

urlpatterns += patterns('',
    url(r'^static/motion/(?P<path>.*)/?$', 'django.views.static.serve',
        kwargs={ 'document_root': media_dir }),
    # Appends a static url for your theme
    url(r'^static/themes/%s/(?P<path>.*)/?$' % app_dir, 'django.views.static.serve',
        kwargs={ 'document_root': theme_dir }),
)
