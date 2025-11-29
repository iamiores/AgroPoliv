from django.contrib import admin
from .models import User, Item, Kit, KitItem, Article, Service, ServiceOrder, Order, PromoCode, UsersQuestion, Comment

admin.site.register(Item)
admin.site.register(Kit)
admin.site.register(KitItem)
admin.site.register(Article)
admin.site.register(User)
admin.site.register(Service)
admin.site.register(ServiceOrder)
admin.site.register(Order)
admin.site.register(PromoCode)
admin.site.register(UsersQuestion)
admin.site.register(Comment)