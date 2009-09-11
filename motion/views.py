from urlparse import urljoin, urlparse
import re

from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.simple import redirect_to
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import SiteProfileNotAvailable
from django.contrib.auth import get_user
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe

from motion import forms
import typepad
import typepadapp.forms
from typepadapp import models, signals
from typepadapp.views.base import TypePadView


### Moderation
if 'moderation' in settings.INSTALLED_APPS:
    from moderation import models as moderation
else:
    moderation = None


def home(request, page=1, **kwargs):
    """
    Determine the homepage view based on settings. Options are the list
    of recent member activity, a featured user's profile page, or the list
    of activity of people you are following in the group.
    """
    if settings.FEATURED_MEMBER:
        # Home page is a featured user.
        return FeaturedMemberView(request, settings.FEATURED_MEMBER,
            page=page, view='home', **kwargs)
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
        Only include Events with Assets - that is, where event.object is an
        Asset.
        """
        self.object_list.entries = [event for event in self.object_list.entries
            if isinstance(event.object, models.Asset) and event.object.is_local]

        ### Moderation
        if moderation:
            id_list = [event.object.url_id for event in self.object_list.entries]
            if id_list:
                suppressed = moderation.Asset.objects.filter(asset_id__in=id_list,
                    status=moderation.Asset.SUPPRESSED)
                if suppressed:
                    suppressed_ids = [a.asset_id for a in suppressed]
                    self.object_list.entries = [event for event in self.object_list.entries
                        if event.object.url_id not in suppressed_ids]


def configure_crosspost_field(view):

    if 'elsewhere' in view.context:
        elsewhere = view.context['elsewhere']
        choices = []
        for acct in elsewhere:
            if acct.crosspostable:
                choices.append((acct.id,
                    mark_safe("""<img src="%(icon)s" height="16" width="16" alt="" /> """
                    """%(provider)s """
                    """(%(username)s) """ % {
                        'icon': acct.provider_icon_url,
                        'provider': acct.provider_name,
                        'username': acct.username
                    })
                ))

        if len(choices):
            view.form_instance.fields['crosspost'].choices = choices


class AssetPostView(TypePadView):
    """
    Views that subclass AssetPostView may post new content
    to a group.
    """
    form = forms.PostForm

    def setup(self, request, *args, **kwargs):
        super(AssetPostView, self).setup(request, *args, **kwargs)
        configure_crosspost_field(self)

    def select_from_typepad(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            upload_xhr_endpoint = reverse('upload_url')
            elsewhere = request.user.elsewhere_accounts

            ### Moderation
            if moderation:
                upload_xhr_endpoint = reverse('moderated_upload_url')

            upload_complete_endpoint = urljoin(settings.FRONTEND_URL, reverse('upload_complete'))
        self.context.update(locals())

    def post(self, request, *args, **kwargs):
        if self.form_instance.is_valid():
            post = self.form_instance.save()
        else:
            request.flash.add('errors', _('Please correct the errors below.'))
            return

        ### Moderation
        if moderation:
            # lets hand off to the moderation app
            from moderation import views as mod_view
            if mod_view.moderate_post(request, post):
                return HttpResponseRedirect(request.path)

        try:
            new_post = post.save(group=request.group)
        except models.assets.Video.ConduitError, ex:
            request.flash.add('errors', ex.message)
            # TODO: if request.FILES['file'], do we need to remove the uploaded file?
        else:
            request.flash.add('notices', _('Post created successfully!'))
            if request.is_ajax():
                return self.render_to_response('motion/assets/asset.html', { 'entry': new_post })
            else: # Return to current page.
                return HttpResponseRedirect(request.path)


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


class FollowingEventsView(TypePadView):
    """
    User Inbox

    View entries posted to this group from members that the logged-in user is
    following. This is a custom list for the logged-in user.
    """
    template_name = "motion/following.html"
    # until the API can filter external events for us, we need to select
    # 50 at a time; once the API works, restore to settings.EVENTS_PER_PAGE
    paginate_by = 50
    login_required = True

    def select_from_typepad(self, request, view='following', *args, **kwargs):
        self.paginate_template = reverse('following_events') + '/page/%d'
        self.object_list = request.user.notifications.filter(start_index=self.offset,
            max_results=self.paginate_by)

    def get(self, request, *args, **kwargs):
        """
        This method is a stop-gap measure to filter out non-local events from
        a user's "following" event stream. Once the API does this itself,
        we can eliminate this in favor of proper pagination of the following
        page. The class paginate_by value should also be restored to
        settings.EVENT_PER_PAGE.
        """

        events = []
        offset = 1

        def filtrate(more, events):
            num = 0
            for e in more:
                if e.is_local_asset:
                    events.append(e)
                # step forward our offset
                num += 1
                if len(events) == settings.EVENTS_PER_PAGE + 1:
                    return num
            return num

        # filter out any non-local events
        offset += filtrate(self.object_list.entries, events)

        requests = 1
        while offset <= self.object_list.total_results \
            and len(events) <= settings.EVENTS_PER_PAGE:
            # more, please.
            typepad.client.batch_request()
            more = request.user.notifications.filter(start_index=offset,
                max_results=self.paginate_by)
            typepad.client.complete_batch()
            offset += filtrate(more, events)
            # lets not overdo it
            requests += 1
            if requests == 3:
                break

        if len(events) > settings.EVENTS_PER_PAGE:
            self.context['next_offset'] = offset - 1
            events = events[:settings.EVENTS_PER_PAGE]

        self.object_list.entries = events

        return super(FollowingEventsView, self).get(request, *args, **kwargs)


class AssetView(TypePadView):
    """
    Post Permalink Page

    Display the entry with comments. More comments can be loaded via ajax. The
    logged-in user has the option to delete an entry, post a comment, or mark
    the entry as a favorite.
    """
    form = forms.CommentForm
    template_name = "motion/permalink.html"

    def setup(self, request, *args, **kwargs):
        super(AssetView, self).setup(request, *args, **kwargs)
        configure_crosspost_field(self)

    def select_from_typepad(self, request, postid, *args, **kwargs):
        entry = models.Asset.get_by_url_id(postid)

        if request.user.is_authenticated():
            elsewhere = request.user.elsewhere_accounts

        if request.method == 'GET':
            # no need to do these for POST...
            comments = entry.comments.filter(start_index=1, max_results=settings.COMMENTS_PER_PAGE)
            favorites = entry.favorites

        self.context.update(locals())

    def get(self, request, *args, **kwargs):
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

        ### Moderation
        if moderation:
            entry.moderation_approved = moderation.Asset.objects.filter(asset_id=entry.url_id,
                status=moderation.Asset.APPROVED)
            if not entry.moderation_approved and request.user.is_authenticated():
                entry.moderation_flagged = moderation.Flag.objects.filter(tp_asset_id=entry.url_id,
                    user_id=request.user.url_id)

            comments = self.context['comments']

            id_list = [comment.url_id for comment in comments]
            if id_list:
                approved = moderation.Asset.objects.filter(asset_id__in=id_list,
                    status=moderation.Asset.APPROVED)
                approved_ids = [a.asset_id for a in approved]

                suppressed = moderation.Asset.objects.filter(asset_id__in=id_list,
                    status=moderation.Asset.SUPPRESSED)
                suppressed_ids = [a.asset_id for a in suppressed]

                if request.user.is_authenticated():
                    flags = moderation.Flag.objects.filter(tp_asset_id__in=id_list,
                        user_id=request.user.url_id)
                    flag_ids = [f.tp_asset_id for f in flags]
                else:
                    flag_ids = []

                for comment in comments:
                    if comment.url_id in suppressed_ids:
                        comment.suppress = True
                    if comment.url_id in approved_ids:
                        comment.moderation_approved = True
                    if comment.url_id in flag_ids:
                        comment.moderation_flagged = True

        return super(AssetView, self).get(request, *args, **kwargs)

    def post(self, request, postid, *args, **kwargs):
        # Delete entry
        if 'delete' in request.POST:
            # Fetch the asset to delete
            asset_id = request.POST.get('asset-id')
            if asset_id is None:
                raise Http404

            entry = self.context['entry']
            if entry.url_id == asset_id:
                asset = entry
            else:
                # this request must be to delete a comment shown on this page
                typepad.client.batch_request()
                asset = models.Asset.get_by_url_id(asset_id)
                typepad.client.complete_batch()

            # Only let plain users delete stuff if so configured.
            if request.user.is_superuser or settings.ALLOW_USERS_TO_DELETE_POSTS:
                try:
                    asset.delete()
                except asset.Forbidden:
                    pass
                else:
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
                self.select_typepad_user(request)
                asset = models.Asset.get_by_url_id(postid)
                typepad.client.complete_batch()
                comment = self.form_instance.save()
                comment.in_reply_to = asset.asset_ref

                ### Moderation
                if moderation:
                    from moderation import views as mod_view
                    if mod_view.moderate_post(request, comment):
                        return HttpResponseRedirect(request.path)

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
        self.object_list = request.group.memberships.filter(start_index=self.offset,
            max_results=self.limit, member=True)
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

        if request.method == 'GET':
            # no need to do these for POST requests
            elsewhere = member.elsewhere_accounts
            self.object_list = member.group_events(request.group,
                start_index=self.offset, max_results=self.limit)

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


        ### Moderation
        if moderation:
            if hasattr(settings, 'MODERATE_SOME') and settings.MODERATE_SOME:
                blacklist = moderation.Blacklist.objects.filter(user_id=member.url_id)
                if blacklist:
                    self.context['moderation_moderated'] = not blacklist[0].block
                    self.context['moderation_blocked'] = blacklist[0].block
                else:
                    self.context['moderation_unmoderated'] = True


        return super(MemberView, self).get(request, userid, *args, **kwargs)

    def post(self, request, userid, *args, **kwargs):
        # post from the ban user form?
        if request.POST.get('form-action') == 'ban-user':
            user_memberships = self.context['user_memberships']

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

            if not request.user.is_superuser or is_admin:
                # must be an admin to ban and cannot ban/unban another admin
                raise Http404

            if is_member:
                # ban user
                user_membership.block()
            elif is_blocked:
                # unban user
                user_membership.unblock()

        ### Moderation
        elif moderation and request.POST.get('form-action') == 'moderate-user':
            member = self.context['member']

            try:
                blacklist = moderation.Blacklist.objects.get(user_id=member.url_id)
            except:
                blacklist = moderation.Blacklist()
                blacklist.user_id = member.url_id

            if request.POST['moderation_status'] == 'block':
                blacklist.block = True
                blacklist.save()
                request.flash.add('notices', _('This user can no longer post.'))
            elif request.POST['moderation_status'] == 'moderate':
                blacklist.block = False
                blacklist.save()
                request.flash.add('notices', _('This user\'s posts will be moderated.'))
            elif blacklist and blacklist.pk:
                blacklist.delete()
                request.flash.add('notices', _('This user is no longer moderated.'))

        else:
            return super(MemberView, self).post(request, userid, *args, **kwargs)

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

        self.object_list = getattr(member, rel)(start_index=self.offset,
            max_results=self.limit, group=request.group)
        self.context.update(locals())


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
