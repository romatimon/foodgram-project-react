from django.contrib import admin

from .models import Subscription, User


@admin.register(Subscription)
class SubscribeAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_filter = ('username', 'email')
