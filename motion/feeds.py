from django.contrib.syndication.feeds import Feed
from django.utils.feedgenerator import Atom1Feed
import typepad
from typepadapp import models
import settings

class PublicEventsFeed(Feed):
    feed_type = Atom1Feed

    title = "Recent Entries in %s" % models.GROUP.display_name
    link = "/"
    subtitle = models.GROUP.tagline
    description_template = 'assets/feed.html'

    def items(self):
        typepad.client.batch_request()
        events = models.GROUP.events.filter(max_results=settings.ITEMS_PER_FEED)
        typepad.client.complete_batch()
        return [event.object for event in events]

    def item_link(self, item):
        return item.get_absolute_url()

    def item_author_name(self, item):
        return item.author.display_name

    def item_author_link(self, item):
        return item.author.get_absolute_url()

    def item_pubdate(self, item):
        return item.published

class MemberFeed(Feed):
    feed_type = Atom1Feed
    description_template = 'assets/feed.html'

    def get_object(self, bits):
        # check that bits has only one member (just the userid)
        if len(bits) != 1:
            raise ObjectDoesNotExist
        userid = bits[0]
        typepad.client.batch_request()
        models.User.get_by_id(userid)
        typepad.client.complete_batch()
        return user

    def title(self, obj):
        return "Recent Entries from %s" % obj.display_name

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def subtitle(self, obj):
        return "Recent Entries from %s in %s." % (obj.display_name, models.GROUP.display_name)

    def items(self, obj):
        typepad.client.batch_request()
        events = obj.group_events(max_results=settings.ITEMS_PER_FEED)
        typepad.client.complete_batch()
        return [event.object for event in events]

class CommentsFeed(Feed):
    feed_type = Atom1Feed
    description_template = 'assets/feed.html'

    def get_object(self, bits):
        # check that bits has only one member (just the asset id)
        if len(bits) != 1:
            raise ObjectDoesNotExist
        assetid = bits[0]
        typepad.client.batch_request()
        asset = models.Asset.get_by_id(assetid)
        typepad.client.complete_batch()
        return asset

    def title(self, obj):
        return "Recent Comments on %s" % obj

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def subtitle(self, obj):
        return "Recent Comments on %s in %s." % (obj, models.GROUP.display_name)

    def items(self, obj):
        typepad.client.batch_request()
        comments = obj.comments.filter(start_index=1, max_results=settings.COMMENTS_PER_PAGE)
        typepad.client.complete_batch()
        return comments

    def item_link(self, item):
        return item.get_absolute_url()