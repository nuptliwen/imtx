from django.db import models

class Purchaser(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    class Meta:
        unique_together = (("name", "email"),)

    def __unicode__(self):
        return u'%s <%s>' % (self.name, self.email)
