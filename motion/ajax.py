from django import http
from django.conf import settings
from django.contrib.auth import get_user
from django.template.loader import render_to_string
from django.template import RequestContext

try:
    import json
except ImportError:
    import simplejson as json

import typepad
from typepadapp import models
import typepadapp.forms
from typepadapp.decorators import ajax_required


@ajax_required
def more_comments(request):
    """
    Fetch more comments for the asset and return the HTML
    for the additional comments.
    """

    asset_id = request.GET.get('asset_id')
    offset = request.GET.get('offset')
    if not asset_id or not offset:
        raise http.Http404

    # Fetch more comments!
    typepad.client.batch_request()
    request.user = get_user(request)
    asset = models.Asset.get_by_url_id(asset_id)
    comments = asset.comments.filter(start_index=offset,
        max_results=settings.COMMENTS_PER_PAGE)
    typepad.client.complete_batch()

    # Render HTML for comments
    comment_string = ''
    for comment in comments.entries:
        comment_string += render_to_string('motion/assets/comment.html', {
            'comment': comment,
        }, context_instance=RequestContext(request))

    # Return HTML
    return http.HttpResponse(comment_string)


@ajax_required
def more_events(request):
    """
    Fetch more events for the user and return the HTML for the additional
    events.

    This method is a stop-gap measure to filter out non-local events from
    a user's "following" event stream. Once the API does this itself,
    we can eliminate this in favor of proper pagination of the following
    page.
    """

    events = []
    offset = int(request.GET.get('offset', 1))

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

    while True:
        typepad.client.batch_request()
        if not hasattr(request, 'user'):
            request.user = get_user(request)
        more = request.user.notifications.filter(start_index=offset,
            max_results=50)
        typepad.client.complete_batch()
        offset += filtrate(more, events)

        if offset > more.total_results \
            or len(events) > settings.EVENTS_PER_PAGE:
            break

    data = {}
    # provide the next offset to be used for the next block of events
    # the client can't determine this on their own since
    if len(events) > settings.EVENTS_PER_PAGE:
        data['next_offset'] = offset - 1
        events = events[:settings.EVENTS_PER_PAGE]

    # Render HTML for assets
    event_string = ''
    for event in events:
        event_string += render_to_string('motion/assets/asset.html', {
            'entry': event.object,
            'event': event,
        }, context_instance=RequestContext(request))
    data['events'] = event_string

    return http.HttpResponse(json.dumps(data))


@ajax_required
def favorite(request):
    """
    Add this item to the user's favorites. Return OK.
    """

    action = request.POST.get('action', 'favorite')

    asset_id = request.POST.get('asset_id')
    if not asset_id:
        raise http.Http404

    typepad.client.batch_request()
    request.user = get_user(request)
    asset = models.Asset.get_by_url_id(asset_id)
    typepad.client.complete_batch()

    if action == 'favorite':
        favorite = models.Favorite()
        favorite.in_reply_to = asset.asset_ref
        request.user.favorites.post(favorite)
    else:
        favorite = models.Favorite.get_by_user_asset(request.user.url_id, asset_id)
        favorite.delete()

    return http.HttpResponse('OK')


@ajax_required
def edit_profile(request):

    typepad.client.batch_request()
    user = get_user(request)
    typepad.client.complete_batch()

    profile = user.get_profile()
    profileform = typepadapp.forms.UserProfileForm(request.POST, instance=profile)

    if profileform.is_valid():
        profileform.save()
        return http.HttpResponse(json.dumps({'status': 'success', 'data': 'OK'}))
    else:
        errorfields = [k for k, v in profileform.errors.items()]
        return http.HttpResponse(json.dumps({'status': 'error', 'data': ','.join(errorfields)}))


@ajax_required
def upload_url(request):
    """
    Return an upload URL that the client can use to POST a media asset.
    """
    remote_url = request.application.browser_upload_endpoint
    url = request.oauth_client.get_file_upload_url(remote_url)
    url = 'for(;;);%s' % url # no third party sites allowed.
    return http.HttpResponse(url)
