from django.urls import path
from .views import browse_home, book_detail
urlpatterns = [
    path('', browse_home, name='browse'),
    path('book/<int:book_id>/', book_detail, name='book_detail'),
]