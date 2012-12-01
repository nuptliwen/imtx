from django.contrib import admin

from manity.models import Purchaser

class PurchaseAdmin(admin.ModelAdmin):
    pass

admin.site.register(Purchaser, PurchaseAdmin)
