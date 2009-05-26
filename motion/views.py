from urlparse import urljoin

from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.simple import redirect_to
from django.http import Http404, HttpResponseRedirect, HttpResponseServerError, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import SiteProfileNotAvailable

from motion import forms
import typepad
import typepadapp.forms
from typepadapp import models, signals
from typepadapp.views.base import TypePadView


def home(request, page=1):
    """
    Determine the homepage view based on settings. Options are the list
    of recent member activity, a featured user's profile page, or the list
    of activity of people you are following in the group.
    """
    if settings.FEATURED_MEMBER:
        # Home page is a featured user.
        return FeaturedMemberView(request, settings.FEATURED_MEMBER, view='home')
    if settings.HOME_MEMBER_EVENTS:
        from django.contrib.auth import get_user
        typepad.client.batch_request()
        user = get_user(request)
        typepad.client.complete_batch()
        if user.is_authenticated():
            # Home page is the user's inbox.
            return FollowingEventsView(request, page=page, view='home')
    # Home page is group events.
    return GroupEventsView(request, page=page, view='home')


class AssetEventView(TypePadView):
    
    def filter_object_list(self):
        """
        Only include Events with Assets - that is, where event.object is an Asset.
        """
        self.object_list.entries = [event for event in self.object_list.entries if isinstance(event.object, models.Asset)]


class GroupEventsView(AssetEventView):
    paginate_by = settings.EVENTS_PER_PAGE
    form = forms.PostForm
    template_name = "events.html"

    def select_from_typepad(self, request, page=1, view='events', *args, **kwargs):
        self.object_list = request.group.events.filter(start_index=self.offset, max_results=self.limit)
        memberships = request.group.memberships.filter(member=True)[:settings.MEMBERS_PER_WIDGET]
        if request.user.is_authenticated():
            following = request.user.following(group=request.group, max_results=settings.FOLLOWERS_PER_WIDGET)
            followers = request.user.followers(group=request.group, max_results=settings.FOLLOWERS_PER_WIDGET)
            actions = request.user.group_events(request.group, max_results=0)
            upload_xhr_endpoint = reverse('upload_url')
            upload_complete_endpoint = urljoin(settings.FRONTEND_URL, reverse('upload_complete'))
        self.context.update(locals())

    def post(self, request, *args, **kwargs):
        if self.form_instance.is_valid():
            post = self.form_instance.save()
            new_post = post.save(group=request.group)
            if request.is_ajax():
                return self.render_to_response('assets/asset.html', { 'entry': new_post })
            else:
                return HttpResponseRedirect(reverse('home'))


class FollowingEventsView(AssetEventView):
    """
    User Inbox

    View entries posted to this group from members that the logged-in user is
    following. This is a custom list for the logged-in user.
    """
    template_name = "following.html"
    paginate_by = settings.EVENTS_PER_PAGE
    login_required = True

    def select_from_typepad(self, request, view='following', *args, **kwargs):
        self.paginate_template = reverse('following_events') + '/page/%d'
        if request.user.is_authenticated():
            self.object_list = request.user.notifications.filter(start_index=self.offset, max_results=self.limit)


class AssetView(TypePadView):
    """
    Post Permalink Page

    Display the entry with comments. More comments can be loaded via ajax. The
    logged-in user has the option to delete an entry, post a comment, or mark
    the entry as a favorite.
    """
    form = forms.CommentForm
    template_name = "permalink.html"

    def select_from_typepad(self, request, postid, *args, **kwargs):
        entry = models.Asset.get_by_url_id(postid)
        comments = entry.comments.filter(start_index=1, max_results=settings.COMMENTS_PER_PAGE)
        self.context.update(locals())

    def post(self, request, postid, *args, **kwargs):
        # Delete entry
        if 'delete' in request.POST:
            # Fetch the asset to delete
            asset_id = request.POST.get('asset-id')
            if asset_id is None:
                raise Http404

            typepad.client.batch_request()
            self.select_typepad_user(request)
            asset = models.Asset.get_by_url_id(asset_id)
            typepad.client.complete_batch()

            # Check permissions for deleting an asset
            if request.user.is_superuser or (settings.ALLOW_USERS_TO_DELETE_POSTS and request.user.id == asset.author.id):
                asset.delete()
                if isinstance(asset, models.Comment):
                    # Return to permalink page
                    return HttpResponseRedirect(request.path)
                # Redirect to home
                return HttpResponseRedirect(reverse('home'))
            # Not allowed to delete
            return HttpResponseForbidden('User not authorized to delete this asset.')

        elif 'comment' in request.POST:
            if self.form_instance.is_valid():
                typepad.client.batch_request()
                asset = models.Asset.get_by_url_id(postid)
                typepad.client.complete_batch()
                comment = self.form_instance.save()
                asset.comments.post(comment)
                # Return to permalink page
                return HttpResponseRedirect(request.path)


class MembersView(TypePadView):
    """
    Member List Page

    Paginated list of all members in the group with the option for a logged-in
    user to follow/unfollow.
    """
    paginate_by = settings.MEMBERS_PER_PAGE
    template_name = "members.html"

    def select_from_typepad(self, request, *args, **kwargs):
        self.paginate_template = reverse('members') + '/page/%d'
        self.object_list = request.group.memberships.filter(start_index=self.offset, max_results=self.limit, member=True)
        self.context.update(locals())


class MemberView(AssetEventView):
    """ Member Profile Page
        Displays basic info about the user
        as well as their recent activity in the group.
    """
    paginate_by = settings.MEMBERS_PER_PAGE
    template_name = "member.html"
    methods = ('GET', 'POST')

    def select_from_typepad(self, request, userid, *args, **kwargs):
        ## TODO should this be a group user? or is this handled somewhere else?
        #user = models.User.get_group_user(request.group, userid)
        self.paginate_template = reverse('member', args=[userid]) + '/page/%d'
        # FIXME: this should be conditioned if possible, so we don't load
        # the same user twice if a user is viewing their own profile.
        member = models.User.get_by_url_id(userid)
        elsewhere = member.elsewhere_accounts
        # following/followers are shown on TypePad-supplied widget now; no need to select these
        # following = member.following(group=request.group)
        # followers = member.followers(group=request.group)
        self.object_list = member.group_events(request.group, start_index=self.offset, max_results=self.limit)
        self.context.update(locals())

    def get(self, request, userid, *args, **kwargs):
        self.context['is_self'] = request.user.id == self.context['member'].id
        elsewhere = self.context['elsewhere']
        if elsewhere:
            for acct in elsewhere:
                if acct.provider_name == 'twitter':
                    self.context.update({
                        'twitter_username': acct.username
                    })
                    break

        try:
            profile = self.context['member'].get_profile()
        except SiteProfileNotAvailable:
            pass
        else:
            profileform = typepadapp.forms.UserProfileForm(instance=profile)
            if self.context['is_self']:
                self.context['profileform'] = profileform
            else:
                self.context['profiledata'] = profileform

        return super(MemberView, self).get(request, userid, *args, **kwargs)


class FeaturedMemberView(MemberView):
    """ Featured Member Profile Page """
    template_name = "featured_member.html"


class RelationshipsView(TypePadView):
    """
    Following/followers Page

    Displays members of the group who are following or followers of the
    logged-in user.
    """
    paginate_by = settings.MEMBERS_PER_PAGE
    template_name = "members.html"

    def select_from_typepad(self, request, userid, rel, *args, **kwargs):
        if rel not in ('following', 'followers'):
            # The URL regex *should* prevent this
            raise Http404

        # Fetch logged-in group member
        member = models.User.get_by_url_id(userid)
        paginate_template = reverse(rel, args=[userid]) + '/page/%d'

        self.object_list = getattr(member, rel)(start_index=self.offset, max_results=self.limit, group=request.group)
        self.context.update(locals())


def upload_complete(request):
    """
    Callback after uploading directly to TypePad which verifies the response
    as 'okay' or displays an error message page to the user.
    """
    status = request.GET['status']
    if status == '201' or status == '200':
        # Signal that a new object has been created
        instance = models.Asset.get(request.GET['asset_url'], batch=False)
        signals.post_save.send(sender=upload_complete, instance=instance)
        # Redirect to clear the GET data
        return HttpResponseRedirect(reverse('home'))
    return render_to_response('error.html', {
        'message': request.GET['error'],
    }, context_instance=RequestContext(request))


def handle_exception(request, *args, **kwargs):
    """
    Custom exception handler for Django.

    Note that settings.DEBUG must be False or this handler is never run.
    """

    import sys
    import logging

    # Get the latest exception from Python system service
    exception = sys.exc_info()[0]

    # Use  Python logging module to log the exception
    # For more information see:
    # http://docs.python.org/lib/module-logging.html
    logging.error("Uncaught exception got through, rendering 500 page")
    logging.exception(exception)

    # Output user visible HTTP response
    from django.template.loader import render_to_string
    return HttpResponseServerError(render_to_string("500.html", {
            'title': "Sorry, we're experiencing technical difficulties.",
        },
        context_instance=RequestContext(request)))
