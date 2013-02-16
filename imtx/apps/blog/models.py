import os
import re
import Image

from django.db import models
from django.conf import settings
from django.db.models import signals
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes import generic
from django.template.defaultfilters import linebreaksbr
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext
from django.db.models.fields.files import ImageFieldFile
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags, clean_html

from tagging.models import Tag
from tagging.fields import TagField

from imtx.apps.comments.models import Comment
from imtx.apps.comments.signals import  comment_save
from managers import PostManager, MenuManager

@models.permalink
def tag_get_absolute_url(self):
    return ('tag-view', [self.name])
setattr(Tag, 'get_absolute_url', tag_get_absolute_url)

class Category(models.Model):
    title = models.CharField(max_length=250, help_text=_('Maximum 250 '
            'characters.'))
    slug = models.SlugField(unique=True, help_text=_('Suggested value '
            'automatically generated from title. Must be unique.'))
    description = models.TextField()

    class Meta:
        ordering = ['title']
        verbose_name_plural = _('Categories')

    def __unicode__(self):
        return self.title

    def get_post_count(self):
        '''Return the post number under the category'''
        return Post.objects.get_post_by_category(self).count()

    @models.permalink
    def get_absolute_url(self):
        return ('post-category', [str(self.slug)])

class Post(models.Model):
    TYPE_CHOICES = (
        ('page', _('Page')),
        ('post', _('Post')),
    )
    STATUS_CHOICES = (
        ('publish', _('Published')),
        ('draft', _('Unpublished')),
    )
    COMMENT_CHOICES = (
        ('open', _('Open')),
        ('closed', _('Closed')),
    )
    title = models.CharField(max_length=64)
    content = models.TextField()
    date = models.DateTimeField()
    author = models.ForeignKey(User, default=0)
    category = models.ManyToManyField(Category)
    type = models.CharField(max_length=20, default='post', choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, default='draft', choices=STATUS_CHOICES)
    comments =  generic.GenericRelation(Comment, 
                    object_id_field='object_pk',
                    content_type_field='content_type')
    comment_status = models.CharField(max_length=20, default='open', choices=COMMENT_CHOICES)
    objects = PostManager()
    tag = TagField()

    def save(self, *args, **kwargs):
        self.content = clean_html(self.content)

        super(Post, self).save(*args, **kwargs)

        # Initial the views and comments count to 0 if the PostMeta isn't available
        pm, created = PostMeta.objects.get_or_create(post=self, meta_key='views')
        if created:
            pm.meta_value = '0'
            pm.save()

        pm, created = PostMeta.objects.get_or_create(post=self, meta_key='comments_count')
        if created:
            pm.meta_value = '0'
            pm.save()

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('single_post', [str(self.id)])

    def get_admin_url(self):
        return '/admin/blog/post/%d/' % self.id

    def get_author(self):
        try:
            profile = self.author.get_profile()
        except Exception:
            name = self.author.username
        else:
            name = profile.nickname

        return name

    def get_views_count(self):
        return PostMeta.objects.get(post=self, meta_key='views').meta_value

    def hit_views(self):
        pm = PostMeta.objects.get(post=self, meta_key='views')
        pm.meta_value = str(int(pm.meta_value) + 1)
        pm.save()

    def get_publish_info(self):
        return _("Post by %(author)s at %(year)s") % {'author': self.get_author(),
                                                      'year': self.date.year}

    def get_comments_info(self):
        count = PostMeta.objects.get(post=self.id, meta_key='comments_count').meta_value
        if int(count):
            return ungettext('%(count)d Comment', '%(count)d Comments', count) % {'count': count}
        else:
            return _('No Comment')

    def hit_comments(self):
        pm = PostMeta.objects.get(post=self, meta_key='comments_count')
        pm.meta_value = str(self.get_comments().count())
        pm.save()

    def get_comments(self):
        return Comment.objects.for_model(self)

    def get_tags(self):
        return Tag.objects.get_for_object(self)

    def __get_excerpt(self):
        return self.content.split('<!--more-->')[0]

    excerpt = property(__get_excerpt)

    def __get_remain(self):
        return self.content.split('<!--more-->')[1]

    remain = property(__get_remain)

    def __get_pagebreak(self):
        try:
            self.content.index('<!--more-->')
        except ValueError:
            return False
        else:
            return True
    pagebreak = property(__get_pagebreak)

    def get_categories(self):
        return self.category.all()

    def is_public(self):
        if self.status == 'publish':
            return True
        else:
            return False

    @property
    def allow_comment(self):
        if self.comment_status == 'closed':
            return False
        else:
            return True

    def get_description(self, length=120):
        return ''.join(strip_tags(self.content).split('\n'))[:length - 3] + u'...'

    def get_media_url(self):
        r_imtx_media = re.compile('''<img.*src="(http:\/\/imtx.me\/media\/\w+\/\d+\/\d+\/[-\w\d]+.(jpg|png))"''')
        r_local_media = re.compile('''<img.*src="(\/media\/\w+\/\d+\/\d+\/[-\w\d]+.(jpg|png))"''')

        try:
            return r_imtx_media.findall(self.content)[0][0]
        except:
            pass

        try:
            local_url = r_local_media.findall(self.content)[0][0]
            return 'http://imtx.me' + local_url
        except:
            pass

        return ''

class PostMeta(models.Model):
    post = models.ForeignKey(Post)
    meta_key = models.CharField(max_length=128)
    meta_value = models.TextField()

    def __unicode__(self):
        return '<%s: %s>' % (self.meta_key, self.meta_value)

class Profile(models.Model):
	user = models.ForeignKey(User, unique=True)

	nickname = models.CharField(max_length=30)
	website = models.URLField(blank=True)

	def save(self):
		if not self.nickname:
			self.nickname = self.user.username
		super(Profile, self).save()

	def __unicode__(self):
		return self.nickname

class Link(models.Model):
    url = models.URLField()
    name = models.CharField(max_length=255)
    description = models.TextField()
    is_public   = models.BooleanField(_('is public'), default=True)

    def __unicode__(self):
        return '%s: %s' % (self.name, self.url)

WATER_BIG = os.path.join(settings.STATIC_ROOT, 'img/logo.png')
WATER_SMALL = os.path.join(settings.STATIC_ROOT, 'img/logo_small.png')

class Menu(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120, blank=True)
    page = models.ForeignKey(Post, blank=True, null=True)
    weight = models.PositiveSmallIntegerField(default=0)
    url = models.URLField(blank=True)
    parent = models.ForeignKey('self', blank=True, null=True)
    visible = models.BooleanField(default=True)
    objects = MenuManager()

    def __unicode__(self):
        return self.title

    @property
    def title(self):
        if self.page:
            return self.page.title
        return self.name

    def get_absolute_url(self):
        if self.page:
            return self.get_absolute_url()
        return self.url

class Media(models.Model):
    UPLOAD_ROOT = 'uploads/%Y/%m'
    WATER_ROOT = 'pictures/%Y/%m'
    THUMB_SIZE = '640'
    LOGO_SIZE = '48'

    title = models.CharField(max_length=120)
    image = models.ImageField(upload_to=UPLOAD_ROOT)
    watermarked = models.ImageField(blank=True, upload_to=WATER_ROOT)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = _('Media')

    def save(self, *args, **kwargs):
        super(Media, self).save(*args, **kwargs)
        base = Image.open(self.image.path)
        width, height = base.size

        if width > 480:
            logo = Image.open(WATER_BIG)
        else:
            logo = Image.open(WATER_SMALL)

        base.paste(logo, (base.size[0] - logo.size[0], base.size[1] - logo.size[1]), logo)

        water_folder = os.path.join(settings.MEDIA_ROOT, self.date.strftime(self.WATER_ROOT))
        if not os.path.exists(water_folder):
            os.makedirs(water_folder)

        relate_path = os.path.join(self.date.strftime(self.WATER_ROOT),
                                   os.path.basename(self.image.name))

        base.save(os.path.join(settings.MEDIA_ROOT, relate_path))
        self.watermarked = ImageFieldFile(self, self.watermarked, relate_path)
        super(Media, self).save(*args, **kwargs)

    def __unicode__(self):
        return _('%(title)s, uploaded at %(date)s') % {'title': self.title,
                                                       'date': self.date.strftime('%I:%M%p, %Y/%m/%d')}

    def get_thumb_url(self):
        try:
            return self.watermarked.url
        except:
            return self.image.url

    def get_logo_url(self):
        return self.image.url + '?width=' + self.LOGO_SIZE + '&height=' + self.LOGO_SIZE

from pingback.client import ping_external_links, ping_directories

signals.post_save.connect(
        ping_external_links(content_attr='content', url_attr='get_absolute_url'),
        sender=Post, weak=False)

#signals.post_save.connect(
#        ping_directories(content_attr='content', url_attr='get_absolute_url'),
#        sender=Post, weak=False)

def on_comment_save(sender, comment, *args, **kwargs):
    post = comment.object
    post.hit_comments()

    subject = _('Your comment at "%s" now has a reply') % comment.object.title
    from_email = "IMTX <no-replay@imtx.me>"

    if comment.parent_id != u'0' and comment.parent.mail_notify:
        to_email = "%s <%s>" % (comment.parent.user_name, comment.parent.email)

        comment_dict = {
            'your_content': comment.parent.content.replace('\n', '| '),
            'your_content_html': linebreaksbr(comment.parent.content),
            'reply_author': comment.user_name,
            'reply_content': comment.content.replace('\n', '| '),
            'reply_content_html': linebreaksbr(comment.content),
            'url': comment.get_url()
        }

        text_content = _('''You said:
| %(your_content)s

%(reply_author)s replied:
| %(reply_content)s

Visit this link to view detail: %(url)s''' % comment_dict)

        html_content = _('''You said:
<blockquote>%(your_content_html)s</blockquote>
<br />
%(reply_author)s replied:
<blockquote>%(reply_content_html)s</blockquote>
<br />
Visit this link to view detail: <a href="%(url)s">%(url)s</a>''' % comment_dict)
    else:
        to_email = "%s <%s>" % (settings.ADMINS[0][0], settings.ADMINS[0][1])
        comment_dict = {
            'reply_author': comment.user_name,
            'reply_content': comment.content.replace('\n', '| '),
            'reply_content_html': linebreaksbr(comment.content),
            'url': comment.get_url()
        }

        text_content = _('''%(reply_author)s replied:
| %(reply_content)s

Visit this link to view detail: %(url)s''' % comment_dict)

        html_content = _('''%(reply_author)s replied:
<blockquote>%(reply_content_html)s</blockquote>
<br />
Visit this link to view detail: <a href="%(url)s">%(url)s</a>''' % comment_dict)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

comment_save.connect(on_comment_save)
