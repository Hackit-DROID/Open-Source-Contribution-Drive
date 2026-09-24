from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def student_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_student():
            return HttpResponseForbidden("This page is for students only.")
        return view_func(request, *args, **kwargs)
    return _wrapped


def librarian_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_librarian():
            return HttpResponseForbidden("This page is for librarians only.")
        return view_func(request, *args, **kwargs)
    return _wrapped
