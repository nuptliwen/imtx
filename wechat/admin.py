from django.contrib import admin

from wechat.models import WechatUser, Article, MessageResponse

admin.site.register(WechatUser)
admin.site.register(Article)
admin.site.register(MessageResponse)
