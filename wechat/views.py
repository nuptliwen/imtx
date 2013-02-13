import hashlib

from django.http import HttpResponse
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from wechat.utils import process_request
from imtx.apps.blog.models import Post

WECHAT_TOKEN = getattr(settings, 'WECHAT_TOKEN', '')

@csrf_exempt
def index(request):
    if request.method == 'GET':
        token = WECHAT_TOKEN
        timestamp = request.GET.get('timestamp', '')
        nonce = request.GET.get('nonce', '')
        echostr = request.GET.get('echostr', '')
        signature = request.GET.get('signature', '')

        params = [token, timestamp, nonce]
        params.sort()
        hashed = hashlib.sha1(''.join(params)).hexdigest()
        if hashed == signature:
            return HttpResponse(echostr)
    elif request.method == 'POST':
        return process_request(request)

    return HttpResponse('Hello World!')


def show_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not request.user.is_staff and not post.is_public():
        raise Http404

    post.hit_views()

    return render_to_response('wechat/index.html',
                              {'post': post},
                              context_instance=RequestContext(request))
