from django import forms

from .models import Book, Category


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'category', 'description', 'total_copies', 'available_copies']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
