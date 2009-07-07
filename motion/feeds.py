from datetime import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _

from typepadapp import models
from typepadapp.views.base import TypePadEventFeed
import typepad


class PublicEventsFeed(TypePadEventFeed):
    description_template = 'motion/assets/feed.html'

    def title(self):
        return _("Recent Entries in %(group)s") \
            % { 'group': self.request.group.display_name }

    def link(self):
        return reverse("group_events")

    def subtitle(self):
        return self.request.group.tagline

    def select_from_typepad(self, *args, **kwargs):
        self.items = self.request.group.events.filter(max_results=settings.ITEMS_PER_FEED)


class MemberFeed(TypePadEventFeed):
    description_template = 'motion/assets/feed.html'

    def select_from_typepad(self, bits, *args, **kwargs):
        # check that bits has only one member (just the userid)
        if len(bits) != 1:
            raise ObjectDoesNotExist
        userid = bits[0]
        user = models.User.get_by_url_id(userid)
        self.items = user.group_events(self.request.group,
            max_results=settings.ITEMS_PER_FEED)
        self.object = user

    def title(self, obj):
        return _("Recent Entries from %(user)s") \
            % { 'user': obj.display_name }

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def subtitle(self, obj):
        return _("Recent Entries from %(user)s in %(group)s.") \
            % { 'user': obj.display_name,
                'group': self.request.group.display_name }


class CommentsFeed(TypePadEventFeed):
    description_template = 'motion/assets/feed.html'

    def select_from_typepad(self, bits, *args, **kwargs):
        # check that bits has only one member (just the asset id)
        if len(bits) != 1:
            raise ObjectDoesNotExist
        assetid = bits[0]
        asset = models.Asset.get_by_url_id(assetid)
        comments = asset.comments.filter(start_index=1,
            max_results=settings.ITEMS_PER_FEED)
        self.comments = comments
        self.object = asset

    def title(self, obj):
        return _("Recent Comments on %(title)s") % { 'title': obj }

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def subtitle(self, obj):
        return _("Recent Comments on %(title)s in %(group)s.") \
            % { 'title': obj, 'group': self.request.group.display_name }

    def items(self):
        comments = self.comments
        events = []
        for comment in comments:
            event = typepad.Event()
            event.object = comment
            event.actor = comment.author
            event.published = comment.published
            events.append(event)
        return events
