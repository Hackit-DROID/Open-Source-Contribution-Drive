#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import functools
from enum import Enum


class UserRole(Enum):
    """Enumeration of available user roles."""
    ADMIN = "admin"
    STUDENT = "student"
    USER = "user"


def get_user_role(user):
    """
    Determine the role of a given user.

    Returns the UserRole based on user attributes:
    - Superusers and staff members are ADMIN.
    - Users in the 'student' group are STUDENT.
    - All other authenticated users are USER.
    - Unauthenticated users return None.
    """
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser or user.is_staff:
        return UserRole.ADMIN
    if user.groups.filter(name="student").exists():
        return UserRole.STUDENT
    return UserRole.USER


def role_required(allowed_roles):
    """
    Decorator that restricts view access to users with specific roles.

    Args:
        allowed_roles: A list or collection of UserRole values that are permitted
                       to access the decorated view.

    Returns:
        HTTP 403 Forbidden if the user is unauthenticated or lacks the required role.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from django.http import HttpResponseForbidden

            if not request.user or not request.user.is_authenticated:
                return HttpResponseForbidden(
                    "Access denied: authentication required."
                )

            user_role = get_user_role(request.user)
            if user_role not in allowed_roles:
                return HttpResponseForbidden(
                    "Access denied: insufficient permissions for this role."
                )

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class RoleBasedAccessMiddleware:
    """
    Middleware that enforces role-based access control on administrative endpoints.

    Restricts administrative mutation endpoints (add/delete paths) to ADMIN role.
    Returns HTTP 403 Forbidden for unauthorized role access attempts.
    """

    ADMIN_PATH_KEYWORDS = ["/add_", "/delete_"]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.http import HttpResponseForbidden

        if self._is_admin_path(request.path):
            if not request.user or not request.user.is_authenticated:
                return HttpResponseForbidden(
                    "Access denied: authentication required."
                )
            user_role = get_user_role(request.user)
            if user_role != UserRole.ADMIN:
                return HttpResponseForbidden(
                    "Access denied: administrative role privileges required."
                )

        return self.get_response(request)

    def _is_admin_path(self, path):
        """Determine whether a path is an administrative mutation route."""
        return any(keyword in path for keyword in self.ADMIN_PATH_KEYWORDS)


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'university_portal.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
