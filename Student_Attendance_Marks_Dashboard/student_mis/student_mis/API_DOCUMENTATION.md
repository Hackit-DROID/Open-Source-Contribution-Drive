# Student MIS - API Documentation

## Overview

This document describes how to convert the current Django template-based application into a REST API for use with frontend frameworks like React, Vue, or Angular.

## Current Architecture

The current implementation uses Django's template system with server-side rendering. To convert to API:

### Option 1: Add Django REST Framework

#### Installation
```bash
pip install djangorestframework
pip install django-cors-headers  # For CORS support
```

#### Add to settings.py
```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'corsheaders',
    'students',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add at top
    ...
]

# CORS settings (adjust for production)
CORS_ALLOW_ALL_ORIGINS = True  # For development only

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}
```

## REST API Implementation

### Create serializers.py

```python
# students/serializers.py
from rest_framework import serializers
from .models import Student, Marks, Attendance


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['reg_no', 'name', 'email', 'branch', 'year', 
                  'gender', 'mobile', 'created_at', 'updated_at']
        read_only_fields = ['reg_no', 'created_at', 'updated_at']


class MarksSerializer(serializers.ModelSerializer):
    overall_percentage = serializers.SerializerMethodField()
    subject_totals = serializers.SerializerMethodField()
    
    class Meta:
        model = Marks
        fields = '__all__'
    
    def get_overall_percentage(self, obj):
        return obj.get_overall_percentage()
    
    def get_subject_totals(self, obj):
        return obj.get_all_totals()


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class StudentDetailSerializer(serializers.ModelSerializer):
    marks = MarksSerializer(read_only=True)
    attendance = AttendanceSerializer(read_only=True)
    
    class Meta:
        model = Student
        fields = ['reg_no', 'name', 'email', 'branch', 'year', 
                  'gender', 'mobile', 'marks', 'attendance']
```

### Create API Views

```python
# students/api_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Student, Marks, Attendance
from .serializers import (
    StudentSerializer, StudentDetailSerializer,
    MarksSerializer, AttendanceSerializer
)


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'reg_no'
    
    @action(detail=True, methods=['get'])
    def report(self, request, reg_no=None):
        """Get complete report for a student"""
        student = self.get_object()
        serializer = StudentDetailSerializer(student)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search students by name, reg_no, or email"""
        query = request.query_params.get('q', '')
        students = Student.objects.filter(
            Q(name__icontains=query) | 
            Q(reg_no__icontains=query) |
            Q(email__icontains=query)
        )
        serializer = self.get_serializer(students, many=True)
        return Response(serializer.data)


class MarksViewSet(viewsets.ModelViewSet):
    queryset = Marks.objects.all()
    serializer_class = MarksSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Marks.objects.all()
        student_reg = self.request.query_params.get('student', None)
        if student_reg:
            queryset = queryset.filter(student__reg_no=student_reg)
        return queryset


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Attendance.objects.all()
        student_reg = self.request.query_params.get('student', None)
        if student_reg:
            queryset = queryset.filter(student__reg_no=student_reg)
        return queryset
    
    def perform_update(self, serializer):
        instance = serializer.save()
        instance.update_percentage()
```

### Update URLs for API

```python
# students/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import StudentViewSet, MarksViewSet, AttendanceViewSet

router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'marks', MarksViewSet)
router.register(r'attendance', AttendanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

# In main urls.py, add:
# path('api/', include('students.api_urls')),
```

## API Endpoints

### Students API

#### List All Students
```
GET /api/students/
```

**Response:**
```json
[
    {
        "reg_no": "CSE001",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "branch": "CSE",
        "year": 3,
        "gender": "M",
        "mobile": "9876543210",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
    }
]
```

#### Get Single Student
```
GET /api/students/{reg_no}/
```

**Response:**
```json
{
    "reg_no": "CSE001",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "branch": "CSE",
    "year": 3,
    "gender": "M",
    "mobile": "9876543210"
}
```

#### Create Student
```
POST /api/students/
Content-Type: application/json

{
    "reg_no": "CSE003",
    "name": "New Student",
    "email": "new@example.com",
    "branch": "CSE",
    "year": 1,
    "gender": "M",
    "mobile": "9876543215",
    "password": "student123"
}
```

#### Update Student
```
PUT /api/students/{reg_no}/
PATCH /api/students/{reg_no}/  # Partial update
Content-Type: application/json

{
    "name": "Updated Name",
    "email": "updated@example.com"
}
```

#### Delete Student
```
DELETE /api/students/{reg_no}/
```

#### Get Student Report
```
GET /api/students/{reg_no}/report/
```

**Response:**
```json
{
    "reg_no": "CSE001",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "branch": "CSE",
    "year": 3,
    "gender": "M",
    "mobile": "9876543210",
    "marks": {
        "student": "CSE001",
        "subject1_name": "Mathematics",
        "subject1_ise1": "18.00",
        "subject1_mid": "17.50",
        "subject1_end": "52.00",
        "overall_percentage": 87.5,
        "subject_totals": {
            "subject1": 87.5,
            "subject2": 92.0,
            "subject3": 83.5,
            "subject4": 96.5,
            "subject5": 89.5
        }
    },
    "attendance": {
        "student": "CSE001",
        "attendance_percentage": "85.00",
        "total_classes": 100,
        "classes_attended": 85
    }
}
```

#### Search Students
```
GET /api/students/search/?q=john
```

### Marks API

#### Get Marks for Student
```
GET /api/marks/?student=CSE001
```

#### Add/Update Marks
```
POST /api/marks/
PUT /api/marks/{student_reg_no}/
Content-Type: application/json

{
    "student": "CSE001",
    "subject1_name": "Mathematics",
    "subject1_ise1": 18.0,
    "subject1_mid": 17.5,
    "subject1_end": 52.0,
    "subject2_name": "Physics",
    "subject2_ise1": 19.0,
    "subject2_mid": 18.0,
    "subject2_end": 55.0,
    ...
}
```

### Attendance API

#### Get Attendance for Student
```
GET /api/attendance/?student=CSE001
```

#### Add/Update Attendance
```
POST /api/attendance/
PUT /api/attendance/{student_reg_no}/
Content-Type: application/json

{
    "student": "CSE001",
    "total_classes": 100,
    "classes_attended": 85
}
```

**Response:**
```json
{
    "student": "CSE001",
    "attendance_percentage": "85.00",
    "total_classes": 100,
    "classes_attended": 85,
    "updated_at": "2025-01-15T12:00:00Z"
}
```

## Authentication

### Session Authentication (Default)
- Login via Django admin or custom login endpoint
- Session cookie maintained across requests

### Token Authentication

#### Get Token
```python
# Add to urls.py
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    ...
    path('api/token/', obtain_auth_token),
]
```

**Request:**
```
POST /api/token/
Content-Type: application/json

{
    "username": "admin",
    "password": "admin123"
}
```

**Response:**
```json
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

**Using Token:**
```
GET /api/students/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

## React Integration Example

```javascript
// API Service
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

class StudentService {
    constructor() {
        this.api = axios.create({
            baseURL: API_URL,
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        // Add token to requests
        const token = localStorage.getItem('token');
        if (token) {
            this.api.defaults.headers.common['Authorization'] = `Token ${token}`;
        }
    }
    
    // Get all students
    async getStudents() {
        const response = await this.api.get('/students/');
        return response.data;
    }
    
    // Get single student
    async getStudent(regNo) {
        const response = await this.api.get(`/students/${regNo}/`);
        return response.data;
    }
    
    // Create student
    async createStudent(studentData) {
        const response = await this.api.post('/students/', studentData);
        return response.data;
    }
    
    // Update student
    async updateStudent(regNo, studentData) {
        const response = await this.api.put(`/students/${regNo}/`, studentData);
        return response.data;
    }
    
    // Delete student
    async deleteStudent(regNo) {
        await this.api.delete(`/students/${regNo}/`);
    }
    
    // Get student report
    async getStudentReport(regNo) {
        const response = await this.api.get(`/students/${regNo}/report/`);
        return response.data;
    }
    
    // Search students
    async searchStudents(query) {
        const response = await this.api.get(`/students/search/?q=${query}`);
        return response.data;
    }
}

export default new StudentService();
```

## Testing API with cURL

```bash
# Get all students
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/students/

# Create student
curl -X POST \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reg_no": "CSE003",
    "name": "Test Student",
    "email": "test@example.com",
    "branch": "CSE",
    "year": 1,
    "gender": "M",
    "mobile": "9876543216"
  }' \
  http://localhost:8000/api/students/

# Get student report
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/students/CSE001/report/
```

## Error Responses

```json
// 400 Bad Request
{
    "field_name": [
        "This field is required."
    ]
}

// 404 Not Found
{
    "detail": "Not found."
}

// 401 Unauthorized
{
    "detail": "Authentication credentials were not provided."
}
```

---

**Note**: This is a complete API specification. To implement, follow the steps in "Option 1: Add Django REST Framework" section.
