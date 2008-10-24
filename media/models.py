import os
from django.db import models
from settings import MEDIA_ROOT
from django.utils.translation import ugettext as _
from django.db.models.fields.files import ImageFieldFile
from utils import make_thumb

UPLOAD_ROOT = 'upload'
THUMB_ROOT = 'upload/thumb'

class Media(models.Model):
    title = models.CharField(max_length = 120)
    image = models.ImageField(upload_to = UPLOAD_ROOT)
    thumb = models.ImageField(upload_to = THUMB_ROOT, blank = True)
    date = models.DateTimeField(auto_now_add = True)

    class Meta:
        verbose_name_plural = _('Media')

    def save(self):
        base, ext = os.path.splitext(os.path.basename(self.image.path))
        thumb_pixbuf = make_thumb(os.path.join(MEDIA_ROOT, self.image.name))
        relate_thumb_path = os.path.join(THUMB_ROOT, base + '.thumb' + ext)
        thumb_path = os.path.join(MEDIA_ROOT, relate_thumb_path)
        thumb_pixbuf.save(thumb_path)
        self.thumb = ImageFieldFile(self, self.thumb, relate_thumb_path)

        super(Media, self).save()

    def __unicode__(self):
        return _('%s, uploaded at %s') % (self.title, self.date.strftime('%T %h %d, %Y'))