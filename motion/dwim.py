from django.utils.html import escape
from django.http import Http404, HttpResponse, HttpResponseRedirect
from urlparse import urlparse
from urllib import quote
import httplib2
import re
import simplejson as json

def oembed(url):
    """
    Parameters:
        url: Link to resource to resolve and return metadata.

    Returns:
        dictionary of metadata for given link. Elements in dictionary:
        provider_name: identifier for provider of resource. Currently
            "Flickr", "YouTube" or "raw".
        url: Original URL given.
        html: A block of HTML markup that should be used to render the
            URL given.
        width: A string representing the width (in pixels) of the HTML block.
        height: A string representing the height (in pixels) of the HTML
            block.
        type: Identifier representing the type of resource. Should be one
            of: "video", "image", "photo", "audio" ("photo" is appropriate
            for a Flickr photo for instance, but "image" is the type for
            a raw JPEG url; presentation may differ between these two
            types).
    """
    parts = urlparse(url)
    req_url = None
    provider = None

    # Provider-specific oembed link handling; this should be done through
    # a registry of oembed providers
    if re.search("^(www\.)?flickr\.com$", parts[1]):
        req_url = "http://www.flickr.com/services/oembed/?format=json&url=%s" % quote(url)
        provider = "Flickr"

    # Dumb handling for YouTube links; they don't support oembed yet.
    elif re.search("^(www\.)?youtube\.com$", parts[1]):
        view_url = re.sub('(www\.)?youtube\.com/watch\?v=', 'www.youtube.com/v/', url)
        return {
            "provider_name": "YouTube",
            "url": url,
            "html": """<object width="425" height="344"><param name="movie" value="%(url)s&hl=en&fs=1"></param><param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="%(url)s&hl=en&fs=1" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="425" height="344"></embed></object>""" % { "url": escape(view_url) },
            "width": "425",
            "height": "344",
            "type": "video"
        }

    # No handler for this URL; attempt to detect if it is an image or not.
    else:
        req_url = url
        provider = "raw"

    # No request URL? We can't do anything then.
    if req_url is None:
        return None

    http = httplib2.Http()

    # For 'raw' providers, just do a HEAD request and determine if it
    # is an image MIME type or not for now.
    if provider == "raw":
        # do a HEAD request
        (response, content) = http.request(req_url, "HEAD")
        if re.match('image/', response['content-type']):
            # hey, it's an image!
            return {
                "provider_name": "raw",
                "url": req_url,
                "type": "image"
            }
        return None

    # Regular oembed request
    (response, content) = http.request(req_url)
    # content = re.sub("\\'", "'", content)
    try:
        embed = json.loads( content )
    except:
        return None

    embed['provider_name'] = provider
    return embed

def url_render(request):
    """
    Interface:

    Method: POST
    Parameter: 'url' (one or more)
    Value: URL to render

    Returns:
        JSON formatted data structure in the following format:
        {
            response: {
                blocks: {
                    'url': {
                        'html': 'html of rendered url',
                        'type': 'type of rendered url'
                    }
                }
            }
        }

    "type" in the structure above can be one of:
        'video', 'image', 'link', 'audio'

    """
    urls = request.POST.getlist('url')
    blocks = {}
    for url in urls:
        # default handling (autolink url)
        blocks[url] = { "html": """<p class="embed embed-link"><a href="%(url)s">%(url)s</a></p>""" % { "url": escape(url) }, "type": "link" }

        try:
            embed = oembed(url)
            if embed:
                if 'type' in embed:
                    data_type = embed['type']

                # Provider-specific rendering
                if embed['provider_name'] == 'Flickr':
                    html = ("""<div class="embed embed-image"><span class="embed-inner">"""
                        + """<a href="%(orig_url)s"><img src="%(url)s" width="%(width)s" height="%(height)s" alt="%(title)s" /></a>"""
                        + """<span class="caption">%(title)s</span>"""
                        + """</span></div>""") % {
                        "orig_url": escape(url),
                            "url": escape(embed['url']), "width": escape(embed['width']),
                            "height": escape(embed['height']), "title": escape(embed['title']) }
                    data_type = "photo"

                elif embed['provider_name'] == 'YouTube':
                    html = """<div class="embed embed-video"><span class="embed-inner">""" \
                        + embed['html'] \
                        + """<span class="caption"></span>""" \
                        + """</span></div>"""

                elif embed['provider_name'] == 'raw':
                    html = ("""<div class="embed embed-image"><span class="embed-inner">"""
                        + """<a href="%(url)s"><img src="%(url)s" alt="" /></a>"""
                        + """<span class="caption"></span>"""
                        + """</span></div>""") % { "url": escape(embed['url']) }

                if html:
                    blocks[url] = { "html": html, "type": data_type }
        except:
            # TBD: for now; this causes the link to be hyperlinked if
            # an exception was raised above
            pass

    response = json.dumps( { "response": { "blocks": blocks } } )
    return HttpResponse(response, "application/json")