"""
References
*
"""
from django.test import TestCase
from .models import UserProfile, Book
# Create your tests here.

class BookExists(TestCase):
    def test_book_creation(self):
        book = Book.objects.create(title="test book")
        self.assertEqual(Book.objects.count(), 1)

class BookTitleMatches(TestCase):
    def test_book_title(self):
        book = Book.objects.create(title="test book")
        self.assertEqual(book.title, "test book")
