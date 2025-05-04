"""
References
*
"""
from django.urls import path
from .views import (
    home, manage_requests, process_borrow_request, process_collection_request, profile_settings, librarian_view, patron_view,
    add_book, add_collection, book_detail, 
    edit_book, delete_book, edit_collection, delete_collection,
    learn_more, collection_detail, add_authorized_users, borrowed_books, request_collection_access, upgrade_to_librarian, list_patrons, trending_books, all_collections
)

urlpatterns = [
    path('', home, name='home'),
    path('profile-settings/', profile_settings, name='profile_settings'),

    path('borrowed-books/', borrowed_books, name='borrowed_books'),

    path('librarian/', librarian_view, name='librarian_view'),
    path('patron/', patron_view, name='patron_view'),
    path('add-book/', add_book, name='add_book'),
    path('add-collection/', add_collection, name='add_collection'),
    path('book/<int:book_id>/', book_detail, name='book_detail'),
    path('edit-book/<int:book_id>/', edit_book, name='edit_book'),
    path('delete-book/<int:book_id>/', delete_book, name='delete_book'),
    path('edit-collection/<int:collection_id>/', edit_collection, name='edit_collection'),
    path('delete-collection/<int:collection_id>/', delete_collection, name='delete_collection'),
    path('learn-more/', learn_more, name='learn_more'),
    path('collection/<int:collection_id>/', collection_detail, name='collection_detail'),  # New route
    path('collections/<int:collection_id>/add-authorized-users/', add_authorized_users, name='add_authorized_users'),
    path('collection/<int:collection_id>/request-access/', request_collection_access, name='request_collection_access'),
    path('manage-requests/', manage_requests, name='manage_requests'),    path('borrow-requests/<int:request_id>/<str:action>/', process_borrow_request, name='process_borrow_request'),
    path('manage-requests/borrow/<int:request_id>/<str:action>/', process_borrow_request, name='process_borrow_request'),
    path('manage-requests/collection/<int:request_id>/<str:action>/', process_collection_request, name='process_collection_request'),
    path('patrons/', list_patrons, name='list_patrons'),
    path('upgrade-user/<int:user_id>', upgrade_to_librarian, name='upgrade_to_librarian'),
    path('collections/<int:collection_id>/add-authorized-users/', add_authorized_users, name='add_authorized_users'),
    path('collections/', all_collections, name='all_collections'),
    path('trending/', trending_books, name='trending')
]