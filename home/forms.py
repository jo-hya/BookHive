"""
References
* https://stackoverflow.com/questions/76647063/how-to-select-multiple-choices-for-a-field-in-django
* https://stackoverflow.com/questions/6195424/how-to-insert-a-checkbox-in-a-django-form
"""
from django import forms
from .models import UserProfile, Book, Collection, Rating, Comment
from django.contrib.auth.models import User


class ProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'age', 'location', 'university', 'date_joined', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'university': forms.TextInput(attrs={'class': 'form-control'}),
            'date_joined': forms.DateTimeInput(attrs={'class': 'form-control', 'readonly': True})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if profile.user:
            profile.user.first_name = self.cleaned_data.get('first_name', '')
            profile.user.last_name = self.cleaned_data.get('last_name', '')
            if commit:
                profile.user.save()
        if commit:
            profile.save()
        return profile

class PatronProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'age', 'location', 'university', 'date_joined', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'university': forms.TextInput(attrs={'class': 'form-control'}),
            'date_joined': forms.DateTimeInput(attrs={'class': 'form-control', 'readonly': True})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is not None and self.instance.user_type == 'patron': self.fields.pop('user_type', None)
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if profile.user:
            profile.user.first_name = self.cleaned_data.get('first_name', '')
            profile.user.last_name = self.cleaned_data.get('last_name', '')
            if commit:
                profile.user.save()
        if commit:
            profile.save()
        return profile
class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'subject', 'publication_year', 'description','book_picture','location', 'borrow_length']

        widgets = {
            'title':             forms.TextInput(attrs={'class': 'form-control'}),
            'author':            forms.TextInput(attrs={'class': 'form-control'}),
            'isbn':              forms.TextInput(attrs={'class': 'form-control'}),
            'subject':           forms.TextInput(attrs={'class': 'form-control'}),
            'publication_year':  forms.NumberInput(attrs={'class': 'form-control'}),
            'description':       forms.Textarea(   attrs={'class': 'form-control', 'rows': 4}),
            'book_picture':      forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'location':          forms.TextInput(attrs={'class': 'form-control'}),
            'borrow_length':     forms.NumberInput(attrs={'class': 'form-control'}),
            'collections':       forms.CheckboxSelectMultiple(),
        }
        
        labels = {
            'borrow_length': 'Borrow Length (days)',
        }
class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['title', 'description', 'items', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'items': forms.CheckboxSelectMultiple(),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Limit items to the librarian's own books
            self.fields['items'].queryset = Book.objects.filter(owner=user)

class AuthorizedUsersForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['authorized_users']
        widgets = {
            'authorized_users': forms.CheckboxSelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['authorized_users'].queryset = User.objects.filter(userprofile__user_type='patron')
        self.fields['authorized_users'].label_from_instance = lambda user: f"{user}"

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating']
        widgets = {'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'})}

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {'content': forms.Textarea(attrs={'rows': 3, 'maxlength': 1000, 'class': 'form-control'})}