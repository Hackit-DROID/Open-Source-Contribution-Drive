"""
Security test suite for Role-Based Access Control (RBAC) in
University_Course_Enrollment_Portal_3.

Verifies that:
- The role_required decorator blocks unauthorized access with HTTP 403.
- The RoleBasedAccessMiddleware blocks admin paths for non-admin users.
- Admin users can access all endpoints.
- Unauthenticated users are denied access.
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Configure Django settings before any Django imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "university_portal.settings")

# Ensure the project root is on sys.path
PROJECT_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
)
sys.path.insert(0, PROJECT_ROOT)

import django
django.setup()

# Import RBAC components from manage.py
from manage import (
    UserRole,
    get_user_role,
    role_required,
    RoleBasedAccessMiddleware,
)


def _make_user(is_authenticated=True, is_superuser=False, is_staff=False,
               groups=None):
    """Create a mock Django user object."""
    user = MagicMock()
    user.is_authenticated = is_authenticated
    user.is_superuser = is_superuser
    user.is_staff = is_staff
    if groups is None:
        user.groups.filter.return_value.exists.return_value = False
    else:
        user.groups.filter.return_value.exists.return_value = (
            "student" in groups
        )
    return user


def _make_request(user=None, path="/"):
    """Create a mock Django request object."""
    request = MagicMock()
    request.user = user
    request.path = path
    return request


class TestUserRole(unittest.TestCase):
    """Test the UserRole enumeration."""

    def test_roles_exist(self):
        self.assertEqual(UserRole.ADMIN.value, "admin")
        self.assertEqual(UserRole.STUDENT.value, "student")
        self.assertEqual(UserRole.USER.value, "user")


class TestGetUserRole(unittest.TestCase):
    """Test the get_user_role function."""

    def test_unauthenticated_user_returns_none(self):
        user = _make_user(is_authenticated=False)
        self.assertIsNone(get_user_role(user))

    def test_none_user_returns_none(self):
        self.assertIsNone(get_user_role(None))

    def test_superuser_is_admin(self):
        user = _make_user(is_superuser=True)
        self.assertEqual(get_user_role(user), UserRole.ADMIN)

    def test_staff_is_admin(self):
        user = _make_user(is_staff=True)
        self.assertEqual(get_user_role(user), UserRole.ADMIN)

    def test_student_group_is_student(self):
        user = _make_user(groups=["student"])
        self.assertEqual(get_user_role(user), UserRole.STUDENT)

    def test_regular_user_is_user(self):
        user = _make_user()
        self.assertEqual(get_user_role(user), UserRole.USER)


class TestRoleRequiredDecorator(unittest.TestCase):
    """Test the role_required view decorator."""

    def test_unauthenticated_gets_403(self):
        """Unauthenticated users receive HTTP 403."""
        @role_required([UserRole.ADMIN])
        def my_view(request):
            return "OK"

        user = _make_user(is_authenticated=False)
        request = _make_request(user=user)
        response = my_view(request)
        self.assertEqual(response.status_code, 403)

    def test_wrong_role_gets_403(self):
        """Users without the required role receive HTTP 403."""
        @role_required([UserRole.ADMIN])
        def my_view(request):
            return "OK"

        user = _make_user()  # Regular USER role
        request = _make_request(user=user)
        response = my_view(request)
        self.assertEqual(response.status_code, 403)

    def test_correct_role_passes(self):
        """Users with the required role can access the view."""
        @role_required([UserRole.ADMIN])
        def my_view(request):
            return "OK"

        user = _make_user(is_superuser=True)
        request = _make_request(user=user)
        response = my_view(request)
        self.assertEqual(response, "OK")

    def test_multiple_allowed_roles(self):
        """Multiple roles can be allowed for a single view."""
        @role_required([UserRole.ADMIN, UserRole.STUDENT])
        def my_view(request):
            return "OK"

        student_user = _make_user(groups=["student"])
        request = _make_request(user=student_user)
        response = my_view(request)
        self.assertEqual(response, "OK")

    def test_student_denied_admin_only(self):
        """Student role is denied when only ADMIN is allowed."""
        @role_required([UserRole.ADMIN])
        def my_view(request):
            return "OK"

        student_user = _make_user(groups=["student"])
        request = _make_request(user=student_user)
        response = my_view(request)
        self.assertEqual(response.status_code, 403)

    def test_none_user_gets_403(self):
        """None user receives HTTP 403."""
        @role_required([UserRole.ADMIN])
        def my_view(request):
            return "OK"

        request = _make_request(user=None)
        response = my_view(request)
        self.assertEqual(response.status_code, 403)


class TestRoleBasedAccessMiddleware(unittest.TestCase):
    """Test the RoleBasedAccessMiddleware."""

    def setUp(self):
        self.get_response = MagicMock(return_value="OK")
        self.middleware = RoleBasedAccessMiddleware(self.get_response)

    def test_non_admin_path_allowed_for_all(self):
        """Non-admin paths are accessible to all users."""
        user = _make_user()  # Regular user
        request = _make_request(user=user, path="/courses/")
        response = self.middleware(request)
        self.assertEqual(response, "OK")

    def test_admin_path_blocked_for_regular_user(self):
        """Admin paths return 403 for non-admin users."""
        user = _make_user()  # Regular USER role
        request = _make_request(user=user, path="/add_department/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

    def test_admin_path_allowed_for_admin(self):
        """Admin paths are accessible to admin users."""
        user = _make_user(is_superuser=True)
        request = _make_request(user=user, path="/add_department/")
        response = self.middleware(request)
        self.assertEqual(response, "OK")

    def test_delete_path_blocked_for_student(self):
        """Delete endpoints return 403 for student users."""
        user = _make_user(groups=["student"])
        request = _make_request(user=user, path="/delete_course/CS101/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

    def test_delete_path_allowed_for_admin(self):
        """Delete endpoints are accessible to admin users."""
        user = _make_user(is_staff=True)
        request = _make_request(user=user, path="/delete_student/1/")
        response = self.middleware(request)
        self.assertEqual(response, "OK")

    def test_unauthenticated_blocked_on_admin_path(self):
        """Unauthenticated users are blocked on admin paths."""
        user = _make_user(is_authenticated=False)
        request = _make_request(user=user, path="/add_instructor/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

    def test_home_path_allowed_unauthenticated(self):
        """Non-admin paths allow even unauthenticated users."""
        user = _make_user(is_authenticated=False)
        request = _make_request(user=user, path="/")
        response = self.middleware(request)
        self.assertEqual(response, "OK")

    def test_is_admin_path_detection(self):
        """Verify internal admin path detection logic."""
        self.assertTrue(self.middleware._is_admin_path("/add_department/"))
        self.assertTrue(self.middleware._is_admin_path("/delete_student/1/"))
        self.assertFalse(self.middleware._is_admin_path("/courses/"))
        self.assertFalse(self.middleware._is_admin_path("/"))
        self.assertFalse(self.middleware._is_admin_path("/students/"))


if __name__ == "__main__":
    unittest.main()
