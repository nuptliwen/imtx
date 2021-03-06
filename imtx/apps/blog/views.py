from django.http import Http404, HttpResponseRedirect, QueryDict
from django.conf.urls import *
from django.db.models import Q
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.forms.util import ErrorList
from django.utils import html
from django.core import urlresolvers
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.cache import cache_page

from tagging.models import Tag, TaggedItem

from forms import MediaForm
from models import Post, Category
from models import Menu
from imtx.apps.comments.views import get_comment_cookie_meta
from imtx.apps.pagination.utils import get_page

def get_query(request):
    query = html.escape(request.GET.get('s', ''))
    return query

@vary_on_headers('Host')
def index(request):
    page = get_page(request)

    posts = Post.objects.get_post()
    return render_to_response('post/post_list.html', {
                'posts': posts,
                'page': page,
                }, context_instance=RequestContext(request)
            )

def single_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not request.user.is_staff and not post.is_public():
        raise Http404

    post.hit_views()

    return render_to_response('post/post_detail.html', {
                'post': post,
                'comment_meta': get_comment_cookie_meta(request),
                },
                context_instance=RequestContext(request),
            )

def single_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not request.user.is_staff and not post.is_public():
        raise Http404

    post.hit_views()

    return render_to_response('post/post_detail.html', {
                'post': post,
                'comment_meta': get_comment_cookie_meta(request),
                },
                context_instance=RequestContext(request),
            )

@cache_page(60 * 60 * 24)
def stats(request):
    latest_post = Post.objects.latest()
    earliest_post = Post.objects.earliest()

    latest_year = latest_post.date.year;
    earliest_year = earliest_post.date.year;

    yearly_count_dict = {}

    for year in range(earliest_year, latest_year + 1):
        yearly_count_dict[year] = Post.objects.filter(date__year=year).count()

    return render_to_response('post/stats.html',
            {'yearly_count_dict': yearly_count_dict,
                'current': 'stats'},
            context_instance=RequestContext(request),
            )

def static_pages(request, page):
    menu = get_object_or_404(Menu, slug=page)
    #TODO deal with the multi-level
    post = menu.page
    post.hit_views()

    return render_to_response('post/page.html', 
            {'post': post, 'current': page},
                context_instance=RequestContext(request),
            )

def category_view(request, slug):
    cat = get_object_or_404(Category, slug=slug)
    posts = Post.objects.get_post_by_category(cat)
    page = get_page(request)
    title = 'Category Archives: %s' % cat.title

    return render_to_response('post/archive.html', {
                'category': cat, 
                'posts': posts,
                'path': request.path,
                'page': page,
                'title': title,
                }, context_instance=RequestContext(request)
            )

def archive_view(request, year, month):
    posts = Post.objects.get_post_by_date(year, month)
    page = get_page(request)
    title = 'Monthly Archives: %s-%s' % (year, month)
    
    return render_to_response('post/archive.html', {
                'year': year,
                'month': month,
                'posts': posts,
                'path': request.path,
                'page': page,
                'title': title,
                }, context_instance=RequestContext(request)
            )

def tag_view(request, name):
    tag = get_object_or_404(Tag, name=name)
    posts = TaggedItem.objects.get_by_model(Post, tag).order_by('-date')
    page = get_page(request)
    title = 'Tag archives for: %s' % tag

    return render_to_response('tag/tag.html', {
                                            'tag': tag,
                                            'posts': posts,
                                            'page': page,
                                            'pagi_path': request.path,
                                            'title': title,
                                            }, context_instance = RequestContext(request))

def search(request):
    query = get_query(request)
    page = get_page(request)

    qd = request.GET.copy()
    if 'page' in qd:
        qd.pop('page')

    posts = None

    if query:
        if 'search' in request.COOKIES:
            message = 'You are searching too often. Slow down.'
            return render_to_response('post/error.html',
                    {'message': message}
                    )
        qset = (
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )

        posts = Post.objects.filter(qset, status='publish').distinct().order_by('-date')

    title = 'Search results for: %s' % query

    response = render_to_response('search.html', {
                              'query': query,
                              'posts': posts,
                              'page': page,
                              'pagi_path': qd.urlencode(),
                              'title': title,
                              }, RequestContext(request))
    response.set_cookie('search',request.META['REMOTE_ADDR'], max_age=1)

    return response

def redirect_feed(request):
    return HttpResponseRedirect(urlresolvers.reverse('feed'))

@login_required(redirect_field_name='next')
def upload(request):
    if request.method == 'POST':
        form = MediaForm(request.POST, request.FILES)
        if form.is_valid():
            new_object = form.save(commit=False)
            new_object.save()
            form.clean()
    else:
        form = MediaForm()
    return render_to_response('utils/upload.html', {'form': form},
            context_instance=RequestContext(request))

from datetime import time, date, datetime
from time import strptime

from pingback import create_ping_func
from django_xmlrpc import xmlrpcdispatcher

# create simple function which returns Post object and accepts
# exactly same arguments as 'details' view.
def pingback_post_handler(post_id, **kwargs):
    return Post.objects.get(id=post_id)

def pingback_page_handler(page, **kwargs):
    return Menu.objects.get(slug=page).page

# define association between view name and our handler
ping_details = {
    'single_post': pingback_post_handler,
    'static_pages': pingback_page_handler,
}

# create xml rpc method, which will process all
# ping requests
ping_func = create_ping_func(**ping_details)

# register this method in the dispatcher
xmlrpcdispatcher.register_function(ping_func, 'pingback.ping')
