"""
Security test suite for Role-Based Access Control (RBAC) in
University_Course_Enrollment_Portal_7.

Verifies:
- UserRole enumeration and get_user_role detection.
- role_required decorator enforces permissions and returns HTTP 403.
- RoleBasedAccessMiddleware blocks administrative endpoints for non-admins.
- Admin users have full access.
- Role permission boundaries are strictly validated.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock

# Configure Django settings before importing Django components
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "university_portal.settings")
PROJECT_ROOT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
)
sys.path.insert(0, PROJECT_ROOT)

import django
django.setup()

from manage import (
    UserRole,
    get_user_role,
    role_required,
    RoleBasedAccessMiddleware,
)


def _make_user(is_authenticated=True, is_superuser=False, is_staff=False, groups=None):
    """Helper to create a mock Django user."""
    user = MagicMock()
    user.is_authenticated = is_authenticated
    user.is_superuser = is_superuser
    user.is_staff = is_staff
    if groups is None:
        user.groups.filter.return_value.exists.return_value = False
    else:
        user.groups.filter.return_value.exists.return_value = ("student" in groups)
    return user


def _make_request(user=None, path="/"):
    """Helper to create a mock Django request."""
    request = MagicMock()
    request.user = user
    request.path = path
    return request


class TestUserRole(unittest.TestCase):
    """Test UserRole enum definitions."""

    def test_roles_exist(self):
        self.assertEqual(UserRole.ADMIN.value, "admin")
        self.assertEqual(UserRole.STUDENT.value, "student")
        self.assertEqual(UserRole.USER.value, "user")


class TestGetUserRole(unittest.TestCase):
    """Test get_user_role role detection logic."""

    def test_unauthenticated_returns_none(self):
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

    def test_regular_authenticated_user_is_user(self):
        user = _make_user()
        self.assertEqual(get_user_role(user), UserRole.USER)


class TestRoleRequiredDecorator(unittest.TestCase):
    """Test role_required view decorator security boundaries."""

    def test_unauthenticated_user_returns_403(self):
        @role_required([UserRole.ADMIN])
        def view(request):
            return "SUCCESS"

        request = _make_request(user=_make_user(is_authenticated=False))
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_none_user_returns_403(self):
        @role_required([UserRole.ADMIN])
        def view(request):
            return "SUCCESS"

        request = _make_request(user=None)
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_role_returns_403(self):
        @role_required([UserRole.ADMIN])
        def view(request):
            return "SUCCESS"

        user = _make_user()  # Regular USER role
        request = _make_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_student_role_denied_admin_endpoint(self):
        @role_required([UserRole.ADMIN])
        def view(request):
            return "SUCCESS"

        student = _make_user(groups=["student"])
        request = _make_request(user=student)
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_authorized_admin_accesses_view(self):
        @role_required([UserRole.ADMIN])
        def view(request):
            return "SUCCESS"

        admin = _make_user(is_staff=True)
        request = _make_request(user=admin)
        response = view(request)
        self.assertEqual(response, "SUCCESS")

    def test_multiple_allowed_roles(self):
        @role_required([UserRole.ADMIN, UserRole.STUDENT])
        def view(request):
            return "SUCCESS"

        student = _make_user(groups=["student"])
        request = _make_request(user=student)
        self.assertEqual(view(request), "SUCCESS")

        regular_user = _make_user()
        request_regular = _make_request(user=regular_user)
        self.assertEqual(view(request_regular).status_code, 403)


class TestRoleBasedAccessMiddleware(unittest.TestCase):
    """Test RoleBasedAccessMiddleware boundary enforcement."""

    def setUp(self):
        self.get_response = MagicMock(return_value="PASSED")
        self.middleware = RoleBasedAccessMiddleware(self.get_response)

    def test_public_path_accessible_by_all(self):
        user = _make_user()
        request = _make_request(user=user, path="/courses/")
        response = self.middleware(request)
        self.assertEqual(response, "PASSED")

    def test_unauthenticated_blocked_on_add_path(self):
        user = _make_user(is_authenticated=False)
        request = _make_request(user=user, path="/add_department/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_blocked_on_delete_path(self):
        user = _make_user(is_authenticated=False)
        request = _make_request(user=user, path="/delete_course/CS-101/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

    def test_regular_user_blocked_on_add_path(self):
        user = _make_user()
        request = _make_request(user=user, path="/add_student/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

    def test_student_blocked_on_delete_path(self):
        user = _make_user(groups=["student"])
        request = _make_request(user=user, path="/delete_instructor/10/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

    def test_admin_allowed_on_add_path(self):
        user = _make_user(is_superuser=True)
        request = _make_request(user=user, path="/add_course/")
        response = self.middleware(request)
        self.assertEqual(response, "PASSED")

    def test_admin_allowed_on_delete_path(self):
        user = _make_user(is_staff=True)
        request = _make_request(user=user, path="/delete_section/1/")
        response = self.middleware(request)
        self.assertEqual(response, "PASSED")

    def test_admin_path_detection_logic(self):
        self.assertTrue(self.middleware._is_admin_path("/add_department/"))
        self.assertTrue(self.middleware._is_admin_path("/delete_student/1/"))
        self.assertFalse(self.middleware._is_admin_path("/students/"))
        self.assertFalse(self.middleware._is_admin_path("/instructors/"))


if __name__ == "__main__":
    unittest.main()
