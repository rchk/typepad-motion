from django import http
from django.conf import settings
from django.template.loader import render_to_string
from django.template import RequestContext
from django.utils import simplejson

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
    from django.contrib.auth import get_user
    request.user = get_user(request)
    asset = models.Asset.get_by_url_id(asset_id)
    comments = asset.comments.filter(start_index=offset, max_results=settings.COMMENTS_PER_PAGE)
    typepad.client.complete_batch()

    # Render HTML for comments
    comment_string = ''
    for comment in comments.entries:
        comment_string += render_to_string('assets/comment.html', {
            'comment': comment,
        }, context_instance=RequestContext(request))

    # Return HTML
    return http.HttpResponse(comment_string)


@ajax_required
def favorite(request):
    """
    Add this item to the user's favorites. Return OK.
    """

    action = request.POST.get('action', 'favorite')

    asset_id = request.POST.get('asset_id')
    if not asset_id:
        raise http.Http404

    # TODO: do we need to do these requests? we should only need the IDs, really
    typepad.client.batch_request()
    from django.contrib.auth import get_user
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
    from django.contrib.auth import get_user
    user = get_user(request)
    typepad.client.complete_batch()

    profile = user.get_profile()
    profileform = typepadapp.forms.UserProfileForm(request.POST, instance=profile)

    if profileform.is_valid():
        profileform.save()
        return http.HttpResponse(simplejson.dumps({'status': 'success', 'data': 'OK'}))
    else:
        errorfields = [k for k, v in profileform.errors.items()]
        return http.HttpResponse(simplejson.dumps({'status': 'error', 'data': ','.join(errorfields)}))


@ajax_required
def upload_url(request):
    """
    Return an upload URL that the client can use to POST a media asset.
    """
    ## TODO backend url from api
    remote_url = request.application.browser_upload_endpoint
    url = request.oauth_client.get_file_upload_url(remote_url)
    url = 'for(;;);%s' % url # no third party sites allowed.
    return http.HttpResponse(url)
