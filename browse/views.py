"""
References
* https://stackoverflow.com/questions/75658458/django-how-to-redirect-back-to-search-page-and-include-query-terms
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from home.models import Book, BorrowRequest, Collection, CollectionAccessRequest, Notification

def browse_home(request):
    q           = request.GET.get('q', '').strip()
    category    = request.GET.get('category', '').strip()
    filter_type = request.GET.get('type', 'books')

    books_qs       = Book.objects.all()
    collections_qs = Collection.objects.all()

    if not request.user.is_authenticated:
        collections_qs = collections_qs.filter(is_public=True)
        books_qs = books_qs.exclude(collections__is_public=False).distinct()

    if q:
        books_qs = books_qs.filter(
            Q(title__icontains=q) |
            Q(author__icontains=q) |
            Q(subject__icontains=q) |
            Q(isbn__icontains=q)
        )
        collections_qs = collections_qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q)
        )

    if category:
        books_qs = books_qs.filter(subject=category)

    if not request.user.is_authenticated or (hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == "patron"):
        books_qs = books_qs.exclude(collections__is_public=False).distinct()

    books_qs = books_qs.order_by('title')
    subjects = (
        Book.objects
            .exclude(subject__isnull=True)
            .exclude(subject__exact='')
            .values_list('subject', flat=True)
            .distinct()
            .order_by('subject')
    )
    
    filter_type = request.GET.get('type', 'all')

    paginator = Paginator(books_qs, 9)
    page_obj  = paginator.get_page(request.GET.get('page'))

    if request.method == 'POST' and request.user.is_authenticated:
        if 'book_id' in request.POST:
            book = get_object_or_404(Book, pk=request.POST['book_id'])
            if book.borrow_requests.filter(requester=request.user, status='pending').exists():
                messages.info(request, f"You already requested to borrow '{book.title}'.")
            else:
                BorrowRequest.objects.create(book=book, requester=request.user)
                messages.success(request,
                    f"Borrow request for '{book.title}' submitted and pending approval."
                )

        elif 'collection_id' in request.POST:
            coll = get_object_or_404(Collection, pk=request.POST['collection_id'])
            up   = getattr(request.user, 'userprofile', None)
            if not up or up.user_type != 'patron':
                messages.error(request, "Only patrons can request collection access.")
            elif coll.is_public or request.user == coll.creator or request.user in coll.authorized_users.all():
                messages.info(request, "You already have access to that collection.")
            else:
                if coll.access_requests.filter(requester=request.user, status='pending').exists():
                    messages.info(request, "You already have a pending access request for that collection.")
                else:
                    CollectionAccessRequest.objects.create(collection=coll, requester=request.user)
                    messages.success(request,
                        f"Access request for '{coll.title}' submitted and pending approval."
                    )

        return redirect('browse')

    context = {
        'books':       page_obj       if filter_type in ('all', 'books') else None,
        'collections': collections_qs if filter_type in ('all', 'collections') else None,
        'filter_type': filter_type,
        'q':           q,
        'category':    category,
        'subjects':    subjects,
        'pagination':  page_obj,
    }
    return render(request, 'browse/browse.html', context)

def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    return render(request, 'browse/book_detail.html', {'book': book})