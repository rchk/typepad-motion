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
