"""
References
* https://medium.com/@nasim.fatima015/implementing-request-and-response-logging-middleware-in-django-d08a4dbf4dfb
"""
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class BlockAdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.user.is_authenticated and request.user.is_superuser
                and not request.path.startswith(reverse('admin:index'))):
            logout(request)
            return redirect('/')

        return self.get_response(request)

class NotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and hasattr(user, 'userprofile') \
           and user.userprofile.user_type == 'patron':
            
            for note in user.notifications.unread():
                messages.info(request, note.message)
                note.read = True
                note.save()

        response = self.get_response(request)
        return response