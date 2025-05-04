"""
References
* https://stackoverflow.com/questions/76647063/how-to-select-multiple-choices-for-a-field-in-django
* https://stackoverflow.com/questions/72675222/how-to-give-specific-users-specific-persmissions-to-view-and-edit-specific-areas
* https://stackoverflow.com/questions/67765946/check-if-a-user-type-exists-in-manytomanyfield-in-django
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db.models import Avg
from django.utils import timezone


class Book(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, blank=True, null=True)
    subject = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True, default='N/A')
    publication_year = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    book_picture = models.ImageField(upload_to='book_pictures/', null=True, blank=True)
    borrow_length = models.PositiveIntegerField(default=14)
    class BookStatus(models.TextChoices):
        AVAILABLE = "available"
        BORROWED = "borrowed"
    book_status = models.CharField(max_length=9, choices=BookStatus.choices, default=BookStatus.AVAILABLE)


    def __str__(self):
        # return self.user.username
        return self.title

    def average_rating(self):
        avg = self.ratings.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0

class BookImage(models.Model):
    book = models.ForeignKey(Book, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='other_images/')


@receiver(post_delete, sender=Book)
def delete_book_file(sender, instance, **kwargs):
    if instance.book_picture:
        instance.book_picture.delete(save=False)

class Collection(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    items = models.ManyToManyField(Book, blank=True, related_name='collections')
    is_public = models.BooleanField(default=True)  # Public by default; librarians can set private
    authorized_users = models.ManyToManyField(User, blank=True, related_name='authorized_collections')

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, blank=False, null=True)
    last_name = models.CharField(max_length=255, blank=False, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    university = models.CharField(max_length=255, blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    borrowed_books = models.ManyToManyField(Book, blank=True, related_name='borrowed_by')

    class UserType(models.TextChoices):
        LIBRARIAN = "librarian"
        PATRON = "patron"
    user_type = models.CharField(max_length=10, choices=UserType.choices, default=UserType.PATRON)

    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)


class Rating(models.Model):
    user = models.ForeignKey('UserProfile', on_delete=models.CASCADE, related_name='ratings')
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')  # Ensures a user can rate a book only once

    def __str__(self):
        return f"{self.user} rated {self.book} - {self.rating} stars"
    




class Comment(models.Model):
    user = models.ForeignKey('UserProfile', on_delete=models.CASCADE, related_name='comments')
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')  # Ensures a user can comment on a book only once

    def __str__(self):
        return f"Comment by {self.user} on {self.book}"

class CollectionAccessRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='access_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collection_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.requester.username} -> {self.collection.title} ({self.status})"

class BorrowRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrow_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrow_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.requester.username} requests {self.book.title} ({self.status})"

class NotificationQuerySet(models.QuerySet):
    def unread(self):
        return self.filter(read=False)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    read = models.BooleanField(default=False)

    objects = NotificationQuerySet.as_manager()

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"