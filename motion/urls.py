import os.path

from django.conf.urls.defaults import *


app_path = os.path.dirname(__file__)
app_dir = os.path.basename(app_path)
media_dir = os.path.join(app_path, 'static')
theme_dir = os.path.join(app_path, 'static', 'theme')

urlpatterns = patterns('motion.views',
    # main index
    url(r'^$', 'home', name='home'),
    url(r'^$', 'home', name='motion_post_url'), # an alias for home
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
    url(r'^ajax/more_events/?$', 'more_events', name='events_url'),
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
