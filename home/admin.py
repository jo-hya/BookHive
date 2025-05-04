"""
References
* https://stackoverflow.com/questions/4870619/django-after-login-redirect-user-to-his-custom-page-mysite-com-username
"""
from django.contrib import admin
from .models import UserProfile, Book, Collection, Notification

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'first_name', 'last_name', 'user_type')
    search_fields = ('user__username', 'first_name', 'last_name')
    list_filter = ('user_type',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'isbn', 'owner')
    search_fields = ('title', 'author', 'isbn')
    list_filter = ('owner',)

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'creator', 'is_public')
    search_fields = ('title', 'creator__username')
    list_filter = ('is_public',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'read')
    list_filter  = ('read',)
    search_fields = ('user__username', 'message')