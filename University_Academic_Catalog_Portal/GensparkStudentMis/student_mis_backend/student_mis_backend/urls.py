"""
URL configuration for student_mis_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# Import viewsets
from students.views import DepartmentViewSet, StudentViewSet
from courses.views import CourseViewSet, InstructorViewSet, CourseOfferingViewSet, EnrollmentViewSet
from attendance.views import AttendanceRecordViewSet, AttendanceSummaryViewSet
from grades.views import AssessmentTypeViewSet, AssessmentViewSet, GradeViewSet, GradeReportViewSet

# Create router and register viewsets
router = DefaultRouter()

# Students app
router.register(r'departments', DepartmentViewSet)
router.register(r'students', StudentViewSet)

# Courses app
router.register(r'courses', CourseViewSet)
router.register(r'instructors', InstructorViewSet)
router.register(r'course-offerings', CourseOfferingViewSet)
router.register(r'enrollments', EnrollmentViewSet)

# Attendance app
router.register(r'attendance-records', AttendanceRecordViewSet)
router.register(r'attendance-summaries', AttendanceSummaryViewSet)

# Grades app
router.register(r'assessment-types', AssessmentTypeViewSet)
router.register(r'assessments', AssessmentViewSet)
router.register(r'grades', GradeViewSet)
router.register(r'grade-reports', GradeReportViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
