from django.http import Http404, HttpResponse, HttpResponseRedirect, QueryDict
from django.core.paginator import Paginator, InvalidPage
from django.conf.urls.defaults import *
from django.db.models import Q
from django.template import TemplateDoesNotExist, RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.models import User
from django.forms.util import ErrorList
from django.utils import encoding, html
from pulog.models import Post, Category, Comment
from pulog.forms import CommentForm

def index(request):
    query = html.escape(request.GET.get('s', ''))

    if query:
        if 'search' in request.COOKIES:
            message = 'You are searching too often. Slow down.'
            return render_to_response('post/error.html',
                    {'message': message}
                    )
        posts = search(request)
        SEARCH = True
    else:
        posts = Post.objects.get_post()
        SEARCH = False

    if len(posts) > 5:
        page = Paginator(posts, 5).page(1)
        current_page = 1
        posts = page.object_list
    else:
        page = None
        current_page = None

    if SEARCH:
        response = render_to_response('post/search.html', {
            'page': page,
            'posts': posts,
            'query': query,
            'current_page': current_page},
            context_instance = RequestContext(request),
        )
        response.set_cookie('search',request.META['REMOTE_ADDR'], max_age = 10)

        return response
    else:
        return render_to_response('post/post_list.html', 
                    {'page': page,
                    'posts': posts,
                    'current_page': current_page},
                    context_instance = RequestContext(request)
                    )

def search(request):
    query = html.escape(request.GET.get('s', ''))
    page_num = html.escape(request.GET.get('p', ''))

    if not page_num:
        page_num = 1

    link = request.path

    qset = (
        Q(title__icontains = query) |
        Q(content__icontains = query)
    )

    return Post.objects.filter(qset).distinct().order_by('-date')

def page(request, num):
    query = html.escape(request.GET.get('s', ''))

    if query:
        posts = search(request)
        SEARCH = True
    else:
        posts = Post.objects.get_post()
        SEARCH = False

    if num:
        num = int(num)
    else:
        num = 1

    page = Paginator(posts, 5).page(num)
    posts = page.object_list
    current_page = num

    if SEARCH:
        return render_to_response('post/search.html', {
            'page': page,
            'posts': posts,
            'query': query,
            'current_page': current_page},
            context_instance = RequestContext(request),
        )
    else:
        return render_to_response('post/post_list.html', 
                    {'page': page,
                    'posts': posts,
                    'current_page': current_page},
                    context_instance = RequestContext(request)
                    )

def comments_post(request):
    post = Post.objects.filter(id = int(request.POST['post_id']))[0]
    form = CommentForm(request.POST)

    message = ''

    if request.user.is_authenticated():
        if form.data['content']:
            comment = Comment(post = post,
                    author = request.user.get_profile().nickname,
                    email = request.user.email,
                    url = request.user.get_profile().website,
                    IP = request.META['REMOTE_ADDR'],
                    content = form.data['content'],
                    )
            comment.save()
            form = CommentForm()
            return HttpResponseRedirect('%s#comment-%d' % (post.get_absolute_url(), comment.id))
        else:
            form = CommentForm(request.POST)
    else:
        if form.is_valid():
            author = form.cleaned_data['author']
            for user in User.objects.all():
                if author == user.username or author == user.get_profile().nickname:
                    form = CommentForm(request.POST)
                    el = ErrorList()
                    el.append('You can not use the name.')
                    form.errors['author'] = el
                else:
                    if 'ip' in request.COOKIES:
                        message = 'You are posting comments too quickly. Slow down.'
                        return render_to_response('post/error.html',
                                {'message': message}
                                )
                    content = form.cleaned_data['content']
                    email = form.cleaned_data['email']
                    url = form.cleaned_data['url']
                    ip = request.META['REMOTE_ADDR']

                    comment = Comment(post = post,
                            author = author,
                            email = email,
                            url = url,
                            IP = ip,
                            content = content,
                            )
                    comment.save()

                    response = HttpResponseRedirect('/archives/%s.html#comment-%d' % (request.POST['post_id'], comment.id))
                    response.set_cookie('ip',request.META['REMOTE_ADDR'], max_age = 30)
                    response.set_cookie('author', author)
                    response.set_cookie('email', email)
                    response.set_cookie('url', url)

                    return response
        else:
            form = CommentForm(request.POST)

    for field in ['author', 'email', 'content', 'url']:
        if field in form.errors:
            if form.errors[field][0]:
                message = '[%s] %s' % (field.title(), form.errors[field][0].capitalize())
                break

    return render_to_response('post/error.html',
            {'message': message}
            )

def single_post(request, post_id):
    post = get_object_or_404(Post, id = post_id)

    if post:
        if not post_id in request.session:
            request.session[post_id] = 'visited'
            post.view = post.view + 1
            post.save()

#        author = ''
#        email = ''
#        url = ''
#        if 'author' in request.COOKIES:
#            author = request.COOKIES['author']
#        if 'email' in request.COOKIES:
#            email = request.COOKIES['email']
#        if 'url' in request.COOKIES:
#            url = request.COOKIES['url']

#        qd = QueryDict('author=%s&email=%s&url=%s' % (author, email, url))
#        form = CommentForm(qd)

        return render_to_response('post/post_detail.html', 
                    {
                        'post': post,
#                        'form': form,
                    },
                    context_instance = RequestContext(request),
                    )
    else:
        return Http404

def static_pages(request, page):
    for post in Post.objects.get_page():
        try:
            if post.slug == page:
                return render_to_response('post/page.html', 
                        {'post': post, 'current': post.slug},
                        )
        except TypeError:
            raise Http404

    raise Http404

def category_view(request, slugname, page_num = None):
    slugname = encoding.iri_to_uri(slugname)
    cat = Category.objects.filter(slug = slugname)[0]
    posts = Post.objects.get_post_by_category(cat)

    if page_num:
        current_page = int(page_num)
    else:
        current_page = 1
    
    link = '/archives/category/%s' % slugname

    page = None
    if len(posts) > 5:
        page = Paginator(posts, 5).page(current_page)
        posts = page.object_list

    return render_to_response('post/archive.html', 
                {'category': cat, 
                'posts': posts,
                'page': page,
                'current_page': current_page,
                'link': link},
                context_instance = RequestContext(request)
                )

def archive_view(request, year, month, page_num = None):
    posts = Post.objects.get_post_by_date(year, month)

    if page_num:
        current_page = int(page_num)
    else:
        current_page = 1
    
    link = '/archives/%s/%s' % (year, month)

    page = None
    if len(posts) > 5:
        page = Paginator(posts, 5).page(current_page)
        posts = page.object_list
    
    return render_to_response('post/archive.html', 
                { 'year': year,
                'month': month,
                'posts': posts,
                'page': page,
                'current_page': current_page,
                'link': link},
                context_instance = RequestContext(request)
                )