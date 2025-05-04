"""
References
* https://stackoverflow.com/questions/72675222/how-to-give-specific-users-specific-persmissions-to-view-and-edit-specific-areas
"""
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import models
from django.db.models import Q
from django.http import Http404
from home.models import Book
from django.db.models.signals import post_delete
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from django.views.decorators.http import require_POST


from .forms import PatronProfileSettingsForm, ProfileSettingsForm, BookForm, CollectionForm, AuthorizedUsersForm, RatingForm, CommentForm
from .models import BorrowRequest, CollectionAccessRequest, UserProfile, Book, Collection, Book, Rating, Comment, BookImage, Notification

def home(request):
    if request.user.is_authenticated:
        if not hasattr(request.user, 'userprofile'):
            return redirect('profile_settings')
        # if request.user.userprofile.user_type == "librarian":
        #     return redirect('librarian_view')
        # elif request.user.userprofile.user_type == "patron":
        #     return redirect('patron_view')
        return redirect('browse')
    return render(request, "home/home.html")

def learn_more(request):
    return render(request, 'learn_more.html')

@login_required
def patron_view(request):
    if request.user.userprofile.user_type != "patron":
        return redirect('home')
    books = Book.objects.filter(owner=request.user)
    my_collections = Collection.objects.filter(creator=request.user)
    authorized_collections = Collection.objects.filter(
        Q(authorized_users=request.user) |
        Q(is_public=True)
    ).distinct()
    other_private_collections = Collection.objects.filter(is_public=False).exclude(creator=request.user).exclude(authorized_users=request.user)
    # notifications = request.user.notifications.unread().order_by('-id')
    
    unread_notes = request.user.notifications.unread().order_by('-id')

    for note in unread_notes:
        messages.info(request, note.message)
        note.read = True
        note.save()

    return render(request, 'home/patron_view.html', {
        'books': books,
        'collections': my_collections,
        'authorized_collections': authorized_collections,
        'other_private_collections': other_private_collections,
        # 'notifications': notifications,
    }
)

@login_required
def librarian_view(request):
    if request.user.userprofile.user_type != "librarian":
        return redirect('home')
    books = Book.objects.filter(owner=request.user)
    all_books = Book.objects.all()
    collections = Collection.objects.filter(creator=request.user)
    authorized_collections = Collection.objects.all()
    return render(request, 'home/librarian_view.html', {
        'books': books,
        'all_books': all_books,
        'collections': collections,
        'authorized_collections': authorized_collections
    })

@login_required
def profile_settings(request):
    if hasattr(request.user, 'userprofile'):
        user_profile = request.user.userprofile
        created = False
    else:
        user_profile = UserProfile(user=request.user)
        created = True

    if created:
        form = ProfileSettingsForm(request.POST or None, request.FILES or None, instance=user_profile)
    else:
        if user_profile.user_type == 'patron':
            form = PatronProfileSettingsForm(request.POST or None, request.FILES or None, instance=user_profile)
        else:
            form = ProfileSettingsForm(request.POST or None, request.FILES or None, instance=user_profile)

    if request.method == "POST":
        if form.is_valid():
            profile = form.save()
            return redirect("home")

    social_account = SocialAccount.objects.get(user=request.user, provider='google')
    email = social_account.extra_data['email']
    return render(request, "home/profile_settings.html", {"form": form, "email": email})

@login_required
def add_book(request):
    if request.user.userprofile.user_type != "librarian":
        return redirect('home')
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            if "book_picture" in request.FILES:
                uploaded_file = request.FILES["book_picture"]
                uploaded_file.seek(0)
                book.book_picture = uploaded_file
            book.owner = request.user 
            form.save()

            selected_collections = form.cleaned_data.get('collections') or []
            for collection in selected_collections:
                collection.items.add(book)

            return redirect('patron_view' if request.user.userprofile.user_type == "patron" else 'librarian_view')  
    else:
        form = BookForm()
    return render(request, 'home/book_form.html', {'form': form})

@login_required
def edit_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.user.userprofile.user_type != "librarian":
        return redirect('/')
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save(commit=False)
            if "book_picture" in request.FILES:
                uploaded_file = request.FILES["book_picture"]
                uploaded_file.seek(0)
                book.book_picture = uploaded_file
            book.save()

            return redirect('patron_view' if request.user.userprofile.user_type == "patron" else 'librarian_view')
    else:
        form = BookForm(instance=book)
    return render(request, 'home/book_form.html', {'form': form})

@login_required
def delete_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.user.userprofile.user_type != "librarian":
        return redirect('/')
    if request.method == 'POST':
        book.delete()
        return redirect('patron_view' if request.user.userprofile.user_type == "patron" else 'librarian_view')
    return redirect('patron_view' if request.user.userprofile.user_type == "patron" else 'librarian_view')

@receiver(post_delete, sender=Book)
def delete_book_pictures(sender, instance, **kwargs):
    if instance.book_picture:
        instance.book_picture.delete(save=False)

    for image in instance.images.all():
        if image.image:
            image.image.delete(save=False)
        image.delete()

@login_required
def add_collection(request):
    if request.user.userprofile.user_type not in ["librarian", "patron"]:
        return redirect('home')

    restricted_books = Book.objects.filter(collections__is_public=False).distinct()
    available_books = Book.objects.exclude(id__in=restricted_books)

    if request.method == 'POST':
        form = CollectionForm(request.POST, user=request.user)
        form.fields['items'].queryset = available_books

        if form.is_valid():
            collection = form.save(commit=False)
            collection.creator = request.user
            if request.user.userprofile.user_type == "patron":
                collection.is_public = True
            collection.save()
            form.save_m2m()

            if not collection.is_public:
                added_books = form.cleaned_data['items']
                public_books = Collection.objects.filter(is_public=True, items__in=added_books).distinct()
                for pub in public_books:
                    pub.items.remove(*added_books)
                return redirect('add_authorized_users', collection_id=collection.id)

            if collection.is_public:
                collection.authorized_users.set(
                    User.objects.filter().values_list('id', flat=True)
                )

            return redirect(
                'patron_view' if request.user.userprofile.user_type == "patron"
                else 'librarian_view'
            )
        else:
            form.fields['items'].queryset = available_books
            return render(request, 'home/collection_form.html', {'form': form})
    else:
        form = CollectionForm(user=request.user)
        form.fields['items'].queryset = available_books

        if request.user.userprofile.user_type == "patron":
            del form.fields['is_public']

    return render(request, 'home/collection_form.html', {'form': form})

@login_required
def edit_collection(request, collection_id):
    collection = get_object_or_404(Collection, pk=collection_id)

    if collection.creator != request.user and request.user.userprofile.user_type != 'librarian':
        raise Http404

    restricted_books = Book.objects.filter(collections__is_public=False).exclude(collections__id=collection.id).distinct()
    available_books = Book.objects.exclude(id__in=restricted_books)
    
    if request.method == 'POST':
        form = CollectionForm(request.POST, instance=collection, user=request.user)
        form.fields['items'].queryset = available_books

        if form.is_valid():
            updated_collection = form.save(commit=False)
            if request.user.userprofile.user_type == "patron":
                updated_collection.is_public = True
            updated_collection.save()
            form.save_m2m()

            if not updated_collection.is_public:
                added_books = form.cleaned_data['items']
                public_books = Collection.objects.filter(is_public=True, items__in=added_books).distinct()
                for pub in public_books:
                    pub.items.remove(*added_books)
                return redirect('add_authorized_users', collection_id=updated_collection.id)

            updated_collection.authorized_users.set(
                User.objects.filter().values_list('id', flat=True)
            )

            return redirect(
                'patron_view' if request.user.userprofile.user_type == "patron"
                else 'librarian_view'
            )
        else:
            form.fields['items'].queryset = available_books
            return render(request, 'home/collection_form.html', {'form': form})
    else:
        form = CollectionForm(instance=collection, user=request.user)
        form.fields['items'].queryset = available_books

        if request.user.userprofile.user_type == "patron":
            del form.fields['is_public']

    return render(request, 'home/collection_form.html', {'form': form})

@login_required
def borrowed_books(request):
    user_profile = request.user.userprofile
    books_list = user_profile.borrowed_books.all()

    # Apply pagination (like browse)
    paginator = Paginator(books_list, 9)  # 9 books per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Handle return action
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        book = get_object_or_404(Book, pk=book_id)
        if book in user_profile.borrowed_books.all():
            user_profile.borrowed_books.remove(book)
            book.book_status = 'available'
            book.save()
            messages.success(request, f"You have returned '{book.title}'!")
        else:
            messages.warning(request, f"'{book.title}' was not in your borrowed list!")
        return redirect('borrowed_books')

    # Subjects for filter (optional, can remove if not needed)
    subjects = Book.objects.exclude(subject__isnull=True).exclude(subject__exact='').values_list('subject', flat=True).distinct().order_by('subject')

    context = {
        'books': page_obj,
        'pagination': page_obj,
        'subjects': subjects,
    }
    return render(request, 'borrowed_books.html', context)


@login_required
def delete_collection(request, collection_id):
    collection = get_object_or_404(Collection, pk=collection_id)
    if collection.creator != request.user and request.user.userprofile.user_type != 'librarian':
        raise Http404
    if request.method == 'POST':
        collection.delete()
        return redirect('patron_view' if request.user.userprofile.user_type == "patron" else 'librarian_view')
    return redirect('patron_view' if request.user.userprofile.user_type == "patron" else 'librarian_view')

@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    
    # Fetch existing rating/comment for the current user (if any)
    existing_rating = Rating.objects.filter(user=request.user.userprofile, book=book).first()
    existing_comment = Comment.objects.filter(user=request.user.userprofile, book=book).first()
    
    # Initialize forms with existing data if available
    rating_form = RatingForm(instance=existing_rating) if existing_rating else RatingForm()
    comment_form = CommentForm(instance=existing_comment) if existing_comment else CommentForm()

    if request.method == 'POST':
        if request.FILES.get('image'):
            image_file = request.FILES['image']
            BookImage.objects.create(book=book, image=image_file)
            return redirect('book_detail', book_id=book_id)
        if 'rating_submit' in request.POST:  # Handle rating submission
            rating_form = RatingForm(request.POST, instance=existing_rating)
            if rating_form.is_valid():
                rating = rating_form.save(commit=False)
                rating.user = request.user.userprofile
                rating.book = book
                rating.save()
                messages.success(request, "Your rating has been submitted!")
            else:
                messages.error(request, "Invalid rating. Please enter a value between 1 and 5.")
        elif 'comment_submit' in request.POST:  # Handle comment submission
            comment_form = CommentForm(request.POST, instance=existing_comment)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.user = request.user.userprofile
                comment.book = book
                comment.save()
                messages.success(request, "Your comment has been submitted!")
            else:
                messages.error(request, "Invalid comment. Please ensure it’s under 1000 characters.")

    # Calculate average rating (still visible to all)
    avg_rating = book.ratings.aggregate(models.Avg('rating'))['rating__avg'] or 0
    
    # Check if the user has rated or commented (for button text)
    user_has_rated = existing_rating is not None
    user_has_commented = existing_comment is not None
    
    due_date = None
    br = BorrowRequest.objects.filter(book=book, requester=request.user, status='approved').first()
    if br:
        due_date = br.due_date
            
    context = {
        'book': book,
        'avg_rating': avg_rating,
        'user_rating': existing_rating,  # Only the user's rating
        'comments': book.comments.all(),  # Keep comments as-is for now
        'rating_form': rating_form,
        'comment_form': comment_form,
        'user_has_rated': user_has_rated,
        'user_has_commented': user_has_commented,
        'due_date': due_date,
    }
    return render(request, 'home/book_detail.html', context)


@login_required
def collection_detail(request, collection_id):
    collection = get_object_or_404(Collection, pk=collection_id)
    if not collection.is_public:
        user = request.user
        if not (
            user == collection.creator or
            user.userprofile.user_type == "librarian" or
            user in collection.authorized_users.all()
        ):
            return redirect('patron_view')

    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    books_qs = collection.items.all()

    if q:
        books_qs = books_qs.filter(
            Q(title__icontains=q) |
            Q(author__icontains=q) |
            Q(subject__icontains=q)
        )

    subjects = (
        books_qs
        .exclude(subject__isnull=True)
        .exclude(subject__exact='')
        .values_list('subject', flat=True)
        .distinct()
        .order_by('subject')
    )

    if category:
        books_qs = books_qs.filter(subject=category)

    paginator = Paginator(books_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'home/collection_detail.html', {
        'collection': collection,
        'books': page_obj,
        'pagination': page_obj,
        'subjects': subjects,
        'q': q,
        'category': category,
    })

@login_required
def trending_books(request):
    books = Book.objects.all()
    books = sorted(books, key=lambda b: b.average_rating(), reverse=True)[:10]
    return render(request, 'trending/trending.html', {'books': books})

@login_required
def add_authorized_users(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if collection.creator != request.user and request.user.userprofile.user_type != 'librarian':
        raise Http404

    if collection.is_public:
        return redirect('home')

    if request.method == 'POST':
        form = AuthorizedUsersForm(request.POST, instance=collection)
        if form.is_valid():
            librarians = User.objects.filter(userprofile__user_type='librarian').values_list('id', flat=True)
            selected_patrons = form.cleaned_data['authorized_users'].values_list('id', flat=True)
            new_authorized_users = list(selected_patrons) + list(librarians)
            collection.authorized_users.set(new_authorized_users)
            return redirect('home')
    else:
        form = AuthorizedUsersForm(instance=collection)

    return render(request, 'home/add_authorized_users.html', {
        'form': form,
        'collection': collection,
    })

@login_required
def list_patrons(request):
    if request.user.userprofile.user_type != "librarian":
        messages.error(request, "Access_denied.")
        return redirect("home")

    all_users = UserProfile.objects.all()
    return render(request, "home/list_patrons.html", {"users": all_users})

@login_required
def manage_requests(request):
    if request.user.userprofile.user_type != "librarian":
        messages.error(request, "Access denied. Only librarians can manage requests.")
        return redirect('home')

    pending_borrows = BorrowRequest.objects.filter(status='pending')
    pending_collections = CollectionAccessRequest.objects.filter(status='pending')

    return render(request, 'home/manage_requests.html', {
        'pending_borrows': pending_borrows,
        'pending_collections': pending_collections,
    })

@login_required
def request_collection_access(request, collection_id):
    collection = get_object_or_404(Collection, pk=collection_id)
    user = request.user

    if user.userprofile.user_type != "patron":
        messages.error(request, "Only patrons can request access to private collections.")
        return redirect('collection_detail', collection_id=collection.id)

    if user in collection.authorized_users.all() or collection.creator == user:
        messages.info(request, "You already have access to this collection.")
        return redirect('collection_detail', collection_id=collection.id)

    existing_req = collection.access_requests.filter(requester=user, status='pending').first()
    if existing_req:
        messages.info(request, "Your request is already pending approval.")
        return redirect('collection_detail', collection_id=collection.id)

    CollectionAccessRequest.objects.create(collection=collection, requester=user)
    messages.success(request, f"Access request for '{collection.title}' sent successfully!")
    return redirect('collection_detail', collection_id=collection.id)

@login_required
def process_collection_request(request, request_id, action):
    if request.user.userprofile.user_type != "librarian":
        messages.error(request, "Access denied.")
        return redirect('home')

    access_req = get_object_or_404(CollectionAccessRequest, pk=request_id)

    if action == "approve":
        access_req.status = "approved"
        access_req.save()
        access_req.collection.authorized_users.add(access_req.requester)
        messages.success(request, f"Access for '{access_req.collection.title}' approved!")
    elif action == "deny":
        access_req.status = "denied"
        access_req.save()
        messages.info(request, f"Access for '{access_req.collection.title}' denied.")

    return redirect('manage_requests')

@login_required
def process_borrow_request(request, request_id, action):
    if request.user.userprofile.user_type != "librarian":
        messages.error(request, "Access denied.")
        return redirect('home')
    borrow_request = get_object_or_404(BorrowRequest, pk=request_id)

    if action == "approve":
        borrow_request.status = "approved"
        borrower_profile = borrow_request.requester.userprofile
        borrower_profile.borrowed_books.add(borrow_request.book)
        borrow_request.book.book_status = "borrowed"
        borrow_request.due_date = timezone.now().date() + timedelta(days=borrow_request.book.borrow_length)
        borrow_request.save()
        borrow_request.book.save()

        BorrowRequest.objects.filter(
            book=borrow_request.book,
            status='pending'
        ).exclude(pk=borrow_request.pk).update(status='denied')

        # print("TO CHECK: creating notification for", borrow_request.requester.username)
        Notification.objects.create(
            user = borrow_request.requester,
            message = f"Your borrow request for “{borrow_request.book.title}” has been approved!",
        )

        messages.success(request, f"Borrow request for '{borrow_request.book.title}' approved!")
    elif action == "deny":
        borrow_request.status = "denied"
        Notification.objects.create(
            user = borrow_request.requester,
            message = f"Your borrow request for “{borrow_request.book.title}” has been denied."
        )
        messages.info(request, f"Borrow request for '{borrow_request.book.title}' denied.")


    borrow_request.save()
    return redirect('manage_requests')

@require_POST
@login_required
def upgrade_to_librarian(request, user_id):
    if request.user.userprofile.user_type != "librarian":
        messages.error(request, "Access denied.")
        return redirect("home")

    if request.method == "POST":
        patron_profile = get_object_or_404(UserProfile, user_id=user_id, user_type="patron")
        patron_profile.user_type = "librarian"
        patron_profile.save()
        messages.success(request, f"{patron_profile.user.username} has been upgraded to librarian!")
    else:
        messages.error(request, "Invalid request method")
    return redirect("list_patrons")

@login_required
def all_collections(request):
    public_collections = Collection.objects.filter(is_public=True)
    authorized_collections = Collection.objects.filter(
        Q(authorized_users=request.user) |
        Q(is_public=True)
    ).distinct()
    return render(request, 'home/collection_list.html', {
        'collections': public_collections,
        'authorized_collections': authorized_collections
    })

