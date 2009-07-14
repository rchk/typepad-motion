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

from urlparse import urljoin, urlparse
import re

from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.simple import redirect_to
from django.http import Http404, HttpResponseRedirect, HttpResponseServerError, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import SiteProfileNotAvailable
from django.contrib.auth import get_user
from django.utils.translation import ugettext as _

from motion import forms
import typepad
import typepadapp.forms
from typepadapp import models, signals
from typepadapp.views.base import TypePadView


def home(request, page=1, **kwargs):
    """
    Determine the homepage view based on settings. Options are the list
    of recent member activity, a featured user's profile page, or the list
    of activity of people you are following in the group.
    """
    if settings.FEATURED_MEMBER:
        # Home page is a featured user.
        return FeaturedMemberView(request, settings.FEATURED_MEMBER, page=page, view='home', **kwargs)
    if settings.HOME_MEMBER_EVENTS:
        typepad.client.batch_request()
        user = get_user(request)
        typepad.client.complete_batch()
        if user.is_authenticated():
            # Home page is the user's inbox.
            return FollowingEventsView(request, page=page, view='home', **kwargs)
    # Home page is group events.
    return GroupEventsView(request, page=page, view='home', **kwargs)


class AssetEventView(TypePadView):

    def filter_object_list(self):
        """
        Only include Events with Assets - that is, where event.object is an Asset.
        """
        self.object_list.entries = [event for event in self.object_list.entries if isinstance(event.object, models.Asset)]


class AssetPostView(TypePadView):
    """
    Views that subclass AssetPostView may post new content
    to a group.
    """
    form = forms.PostForm

    def select_from_typepad(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            upload_xhr_endpoint = reverse('upload_url')
            upload_complete_endpoint = urljoin(settings.FRONTEND_URL, reverse('upload_complete'))
        self.context.update(locals())

    def post(self, request, *args, **kwargs):
        if self.form_instance.is_valid():
            post = self.form_instance.save()
            try:
                new_post = post.save(group=request.group)
            except models.assets.Video.ConduitError, ex:
                request.flash.add('errors', ex.message)
            else:
                request.flash.add('notices', _('Post created successfully!'))
                if request.is_ajax():
                    return self.render_to_response('motion/assets/asset.html', { 'entry': new_post })
                else: # Return to current page.
                    return HttpResponseRedirect(request.path)
        else:
            request.flash.add('errors', _('Please correct the errors below.'))


class GroupEventsView(AssetEventView, AssetPostView):
    paginate_by = settings.EVENTS_PER_PAGE
    template_name = "motion/events.html"

    def select_from_typepad(self, request, page=1, view='events', *args, **kwargs):
        self.paginate_template = reverse('group_events') + '/page/%d'
        self.object_list = request.group.events.filter(start_index=self.offset, max_results=self.limit)
        memberships = request.group.memberships.filter(member=True)[:settings.MEMBERS_PER_WIDGET]
        if request.user.is_authenticated():
            following = request.user.following(group=request.group, max_results=settings.FOLLOWERS_PER_WIDGET)
            followers = request.user.followers(group=request.group, max_results=settings.FOLLOWERS_PER_WIDGET)
        self.context.update(locals())
        super(GroupEventsView, self).select_from_typepad(request, *args, **kwargs)

    # FIXME: This is a temporary patch for the R38-R39 ATP transition.
    # R39 changes the membership source/target mapping, but we
    # need to handle the case where it is the 'wrong' way in case
    # we don't update all sites at the same moment we're releasing
    # R39. See also cases 87042 and 88799.
    def get(self, request, *args, **kwargs):
        if 'followers' in self.context:
            rels = self.context['followers'].entries
            if len(rels) and request.user.url_id != rels[0].target.url_id:
                # target isn't what it should be; swap all target/source due to
                # an api bug
                for r in rels:
                    r.source, r.target = r.target, r.source
        return super(GroupEventsView, self).get(request, *args, **kwargs)


class FollowingEventsView(TypePadView):
    """
    User Inbox

    View entries posted to this group from members that the logged-in user is
    following. This is a custom list for the logged-in user.
    """
    template_name = "motion/following.html"
    paginate_by = settings.EVENTS_PER_PAGE
    login_required = True

    def select_from_typepad(self, request, view='following', *args, **kwargs):
        self.paginate_template = reverse('following_events') + '/page/%d'

        self.object_list = request.user.notifications.filter(by_group=request.group,
            start_index=self.offset, max_results=self.paginate_by)


class AssetView(TypePadView):
    """
    Post Permalink Page

    Display the entry with comments. More comments can be loaded via ajax. The
    logged-in user has the option to delete an entry, post a comment, or mark
    the entry as a favorite.
    """
    form = forms.CommentForm
    template_name = "motion/permalink.html"

    def select_from_typepad(self, request, postid, *args, **kwargs):
        entry = models.Asset.get_by_url_id(postid)
        comments = entry.comments.filter(start_index=1, max_results=settings.COMMENTS_PER_PAGE)
        favorites = entry.favorites
        self.context.update(locals())

    def get(self, *args, **kwargs):
        # Verify this user is a member of the group.
        entry = self.context['entry']

        if not entry.is_local:
            # if this entry isn't local, 404
            raise Http404

        # Make a faux event object since our templates expect an event
        # object and attributes to be present
        event = typepad.Event()
        event.object = entry
        event.actor = entry.author
        event.published = entry.published
        self.context['event'] = event

        return super(AssetView, self).get(*args, **kwargs)

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
                    request.flash.add('notices', _('Comment deleted.'))
                    return HttpResponseRedirect(request.path)
                # Redirect to home
                request.flash.add('notices', _('Post deleted.'))
                return HttpResponseRedirect(reverse('home'))
            # Not allowed to delete
            return HttpResponseForbidden(_('User not authorized to delete this asset.'))

        elif 'comment' in request.POST:
            if self.form_instance.is_valid():
                typepad.client.batch_request()
                asset = models.Asset.get_by_url_id(postid)
                typepad.client.complete_batch()
                comment = self.form_instance.save()
                asset.comments.post(comment)
                request.flash.add('notices', _('Comment created successfully!'))
                # Return to permalink page
                return HttpResponseRedirect(request.path)


class MembersView(TypePadView):
    """
    Member List Page

    Paginated list of all members in the group with the option for a logged-in
    user to follow/unfollow.
    """
    paginate_by = settings.MEMBERS_PER_PAGE
    template_name = "motion/members.html"

    def select_from_typepad(self, request, *args, **kwargs):
        self.paginate_template = reverse('members') + '/page/%d'
        self.object_list = request.group.memberships.filter(start_index=self.offset, max_results=self.limit, member=True)
        self.context.update(locals())


class MemberView(AssetEventView):
    """ Member Profile Page
        Displays basic info about the user
        as well as their recent activity in the group.
    """
    paginate_by = settings.EVENTS_PER_PAGE
    template_name = "motion/member.html"
    methods = ('GET', 'POST')

    def select_from_typepad(self, request, userid, *args, **kwargs):
        self.paginate_template = reverse('member', args=[userid]) + '/page/%d'

        member = models.User.get_by_url_id(userid)
        user_memberships = member.memberships.filter(by_group=request.group)
        elsewhere = member.elsewhere_accounts
        self.object_list = member.group_events(request.group, start_index=self.offset, max_results=self.limit)

        self.context.update(locals())
        super(MemberView, self).select_from_typepad(request, userid, *args, **kwargs)

    def get(self, request, userid, *args, **kwargs):
        # Verify this user is a member of the group.
        user_memberships = self.context['user_memberships']
        member = self.context['member']

        try:
            user_membership = user_memberships[0]
        except IndexError:
            is_member = False
            is_blocked = False
        else:
            is_member = user_membership.is_member()
            is_blocked = user_membership.is_blocked()

        if not request.user.is_superuser: # admins can see all members
            if not len(self.object_list) and not is_member:
                # if the user has no events and they aren't a member of the group,
                # then this is a 404, effectively
                raise Http404

        self.context['is_self'] = request.user.id == member.id
        self.context['is_member'] = is_member
        self.context['is_blocked'] = is_blocked

        elsewhere = self.context['elsewhere']
        if elsewhere:
            for acct in elsewhere:
                if acct.provider_name == 'twitter':
                    self.context.update({
                        'twitter_username': acct.username
                    })
                    break

        try:
            profile = member.get_profile()
        except SiteProfileNotAvailable:
            pass
        else:
            profileform = typepadapp.forms.UserProfileForm(instance=profile)
            if self.context['is_self']:
                self.context['profileform'] = profileform
            else:
                self.context['profiledata'] = profileform

        return super(MemberView, self).get(request, userid, *args, **kwargs)

    def post(self, request, userid, *args, **kwargs):

        # post from the ban user form?
        if not request.POST.get('form-action') == 'ban-user':
            return super(MemberView, self).post(request, userid, *args, **kwargs)

        typepad.client.batch_request()
        request_user = get_user(request)
        user_memberships = models.User.get_by_url_id(userid).memberships.filter(by_group=request.group)
        typepad.client.complete_batch()

        try:
            user_membership = user_memberships[0]
        except IndexError:
            is_admin = False
            is_member = False
            is_blocked = False
        else:
            is_admin = user_membership.is_admin()
            is_member = user_membership.is_member()
            is_blocked = user_membership.is_blocked()

        if not request_user.is_superuser or is_admin:
            # must be an admin to ban and cannot ban/unban another admin
            raise Http404

        if is_member:
            # ban user
            user_membership.block()
        elif is_blocked:
            # unban user
            user_membership.unblock()

        # Return to current page.
        return HttpResponseRedirect(request.path)


class FeaturedMemberView(MemberView, AssetPostView):
    """ Featured Member Profile Page """
    template_name = "motion/featured_member.html"

    def select_from_typepad(self, request, userid, *args, **kwargs):
        super(FeaturedMemberView, self).select_from_typepad(request, userid, *args, **kwargs)
        memberships = request.group.memberships.filter(member=True)[:settings.MEMBERS_PER_WIDGET]
        # this view can be accessed in different ways; lets preserve the
        # request path used, and strip off any pagination portion to construct
        # the pagination template
        path = request.path
        path = re.sub('(/page/\d+)?/?$', '', path)
        self.paginate_template = path + '/page/%d'
        self.context.update(locals())
        super(FeaturedMemberView, self).select_from_typepad(request, userid, *args, **kwargs)


class RelationshipsView(TypePadView):
    """
    Following/followers Page

    Displays members of the group who are following or followers of the
    logged-in user.
    """
    paginate_by = settings.MEMBERS_PER_PAGE
    template_name = "motion/members.html"

    def select_from_typepad(self, request, userid, rel, *args, **kwargs):
        if rel not in ('following', 'followers'):
            # The URL regex *should* prevent this
            raise Http404

        # Fetch logged-in group member
        member = models.User.get_by_url_id(userid)
        self.paginate_template = reverse(rel, args=[userid]) + '/page/%d'

        self.object_list = getattr(member, rel)(start_index=self.offset, max_results=self.limit, group=request.group)
        self.context.update(locals())

    # FIXME: This is a temporary patch for the R38-R39 ATP transition.
    # R39 changes the membership source/target mapping, but we
    # need to handle the case where it is the 'wrong' way in case
    # we don't update all sites at the same moment we're releasing
    # R39. See also cases 87042 and 88799.
    def get(self, request, userid, rel, *args, **kwargs):
        if rel == 'followers':
            rels = self.object_list.entries
            if len(rels) and \
                userid not in (rels[0].target.url_id, rels[0].target.preferred_username):
                # target isn't what it should be; swap all target/source due to
                # an api bug
                for r in rels:
                    r.source, r.target = r.target, r.source
        return super(RelationshipsView, self).get(request, userid, rel, *args, **kwargs)


def upload_complete(request):
    """
    Callback after uploading directly to TypePad which verifies the response
    as 'okay' or displays an error message page to the user.
    """
    status = request.GET['status']
    if status == '201' or status == '200':
        # Signal that a new object has been created
        parts = urlparse(request.GET['asset_url'])
        instance = models.Asset.get(parts[2], batch=False)
        request.flash.add('notices', _('Thanks for the %(type)s!') \
            % { 'type': instance.type_label.lower() })
        signals.post_save.send(sender=upload_complete, instance=instance)
        # Redirect to clear the GET data
        if settings.FEATURED_MEMBER:
            typepad.client.batch_request()
            user = get_user(request)
            typepad.client.complete_batch()
            if not user.is_authenticated() or not user.is_featured_member:
                return HttpResponseRedirect(reverse('group_events'))
        return HttpResponseRedirect(reverse('home'))
    return render_to_response('motion/error.html', {
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
    return HttpResponseServerError(render_to_string("motion/500.html", {
            'title': _("Sorry, we're experiencing technical difficulties."),
        },
        context_instance=RequestContext(request)))


def handle_not_found(request, *args, **kwargs):
    """
    Custom 404 handler for Django.
    """

    import sys
    import logging

    # Get the latest exception from Python system service
    exception = sys.exc_info()[0]

    # Use  Python logging module to log the exception
    # For more information see:
    # http://docs.python.org/lib/module-logging.html
    logging.error("Uncaught exception got through, rendering 404 page")
    logging.exception(exception)

    # Output user visible HTTP response
    from django.template.loader import render_to_string
    return HttpResponseServerError(render_to_string("motion/404.html", {},
        context_instance=RequestContext(request)))
