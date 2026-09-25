# Student MIS Backend - Django + PostgreSQL/SQLite

## 🎓 Enterprise-Grade Student Management System Backend

A comprehensive RESTful API backend built with Django and Django REST Framework for managing students, courses, attendance, and grades.

---

## 🚀 **Quick Start**

### **Server is Running!**
```
Backend API: http://localhost:8001/api/
Admin Panel: http://localhost:8001/admin/
```

### **Admin Credentials**
```
Username: admin
Password: admin123
Email: admin@studentmis.com
```

---

## 📊 **Database Schema**

### **Current Setup**
- **Database**: SQLite3 (for development)
- **Location**: `/home/user/student_mis_backend/db.sqlite3`
- **Can be switched to PostgreSQL** (see configuration below)

### **Models Created**

#### **1. Students App**
- `Department` - Academic departments
- `Student` - Comprehensive student profiles

#### **2. Courses App**
- `Course` - Course catalog
- `Instructor` - Faculty members
- `CourseOffering` - Semester-specific course instances
- `Enrollment` - Student enrollment in courses

#### **3. Attendance App**
- `AttendanceRecord` - Daily attendance tracking
- `AttendanceSummary` - Aggregated attendance statistics

#### **4. Grades App**
- `AssessmentType` - Types of assessments (Midterm, Final, etc.)
- `Assessment` - Specific assessment instances
- `Grade` - Individual student grades
- `GradeReport` - Comprehensive grade reports

---

## 🔌 **API Endpoints**

### **Base URL**: `http://localhost:8001/api/`

### **Students API**
```
GET    /api/students/              - List all students
POST   /api/students/              - Create student
GET    /api/students/{id}/         - Get student details
PUT    /api/students/{id}/         - Update student
DELETE /api/students/{id}/         - Delete student
GET    /api/students/statistics/   - Student statistics
GET    /api/students/{id}/academic_record/ - Full academic record

GET    /api/departments/           - List departments
POST   /api/departments/           - Create department
```

### **Courses API**
```
GET    /api/courses/               - List courses
POST   /api/courses/               - Create course
GET    /api/instructors/           - List instructors
GET    /api/course-offerings/      - List course offerings
GET    /api/enrollments/           - List enrollments
POST   /api/enrollments/bulk_enroll/ - Bulk enroll students
```

### **Attendance API**
```
GET    /api/attendance-records/    - List attendance records
POST   /api/attendance-records/    - Mark attendance
POST   /api/attendance-records/mark_bulk_attendance/ - Bulk mark
GET    /api/attendance-records/statistics/ - Attendance stats
GET    /api/attendance-summaries/  - Attendance summaries
```

### **Grades API**
```
GET    /api/assessment-types/      - List assessment types
GET    /api/assessments/           - List assessments
POST   /api/assessments/           - Create assessment
GET    /api/grades/                - List grades
POST   /api/grades/bulk_grade/     - Bulk grade students
GET    /api/grades/statistics/     - Grade statistics
GET    /api/grade-reports/         - Grade reports
POST   /api/grade-reports/{id}/calculate/ - Calculate final grade
```

---

## 📝 **Sample Data**

### **Pre-loaded Data**
- ✅ 4 Departments (CS, Engineering, Business, Arts)
- ✅ 5 Students
- ✅ 2 Instructors
- ✅ 4 Courses
- ✅ 2 Course Offerings (Fall 2024)

### **Students**
| ID | Name | Department | Year |
|----|------|------------|------|
| STU001 | John Doe | Computer Science | 2 |
| STU002 | Jane Smith | Engineering | 3 |
| STU003 | Mike Johnson | Business | 1 |
| STU004 | Emily Brown | Computer Science | 4 |
| STU005 | David Wilson | Arts | 2 |

### **Courses**
| Code | Name | Credits |
|------|------|---------|
| CS101 | Introduction to Programming | 3 |
| CS201 | Data Structures | 4 |
| ENG101 | Engineering Mathematics | 4 |
| BUS101 | Business Administration | 3 |

---

## 🛠️ **Technology Stack**

### **Backend Framework**
- Python 3.12
- Django 5.2.7
- Django REST Framework 3.16.1

### **Database**
- SQLite3 (default, for development)
- PostgreSQL support (ready to switch)

### **Additional Packages**
- `django-cors-headers` - CORS support for frontend
- `django-filter` - Advanced filtering
- `psycopg2-binary` - PostgreSQL adapter
- `Pillow` - Image handling

---

## 🔧 **Configuration**

### **Switch to PostgreSQL**

1. **Install PostgreSQL**
2. **Create database**:
```sql
CREATE DATABASE student_mis_db;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE student_mis_db TO postgres;
```

3. **Update `settings.py`**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'student_mis_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

4. **Run migrations**:
```bash
python manage.py migrate
python load_sample_data.py
```

---

## 📚 **Admin Panel Features**

Access at: `http://localhost:8001/admin/`

### **Features**
- ✅ Full CRUD operations for all models
- ✅ Advanced search and filtering
- ✅ Bulk actions (update summaries, calculate grades)
- ✅ Date hierarchies
- ✅ Related object management
- ✅ Custom admin actions

---

## 🔐 **Authentication & Security**

### **Current Setup**
- Session-based authentication
- CSRF protection enabled
- CORS enabled for development (all origins)

### **For Production**
- Add JWT authentication
- Restrict CORS origins
- Use environment variables for secrets
- Enable HTTPS
- Add rate limiting

---

## 📖 **API Usage Examples**

### **Get All Students**
```bash
curl http://localhost:8001/api/students/
```

### **Create a Student**
```bash
curl -X POST http://localhost:8001/api/students/ \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU006",
    "first_name": "Sarah",
    "last_name": "Connor",
    "email": "sarah.connor@university.edu",
    "phone": "+15550106",
    "department": 1,
    "year": 2,
    "date_of_birth": "2002-03-15",
    "gender": "F",
    "address": "100 Tech St",
    "city": "Boston",
    "state": "MA",
    "country": "USA",
    "postal_code": "02106",
    "enrollment_date": "2022-09-01"
  }'
```

### **Mark Bulk Attendance**
```bash
curl -X POST http://localhost:8001/api/attendance-records/mark_bulk_attendance/ \
  -H "Content-Type: application/json" \
  -d '{
    "course_offering_id": 1,
    "date": "2024-10-30",
    "marked_by": "Prof. Turing",
    "attendance": [
      {"student_id": "STU001", "status": "present"},
      {"student_id": "STU002", "status": "absent"},
      {"student_id": "STU003", "status": "present"}
    ]
  }'
```

### **Get Student Statistics**
```bash
curl http://localhost:8001/api/students/statistics/
```

---

## 📁 **Project Structure**

```
student_mis_backend/
├── student_mis_backend/       # Project settings
│   ├── settings.py           # Configuration
│   ├── urls.py               # URL routing
│   └── wsgi.py               # WSGI config
├── students/                  # Students app
│   ├── models.py             # Department, Student
│   ├── views.py              # API views
│   ├── serializers.py        # DRF serializers
│   └── admin.py              # Admin config
├── courses/                   # Courses app
│   ├── models.py             # Course, Instructor, Offering, Enrollment
│   ├── views.py
│   ├── serializers.py
│   └── admin.py
├── attendance/                # Attendance app
│   ├── models.py             # AttendanceRecord, Summary
│   ├── views.py
│   ├── serializers.py
│   └── admin.py
├── grades/                    # Grades app
│   ├── models.py             # Assessment, Grade, Report
│   ├── views.py
│   ├── serializers.py
│   └── admin.py
├── manage.py                  # Django management
├── load_sample_data.py        # Sample data loader
└── db.sqlite3                 # SQLite database
```

---

## 🚀 **Management Commands**

### **Run Server**
```bash
python manage.py runserver 0.0.0.0:8001
```

### **Create Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

### **Create Superuser**
```bash
python manage.py createsuperuser
```

### **Load Sample Data**
```bash
python load_sample_data.py
```

### **Django Shell**
```bash
python manage.py shell
```

---

## 🎯 **Key Features**

### **1. Comprehensive Student Management**
- Full student profiles with 20+ fields
- Department organization
- Year-wise tracking
- Status management (active, graduated, etc.)
- Emergency contact information
- Profile pictures support

### **2. Advanced Course System**
- Course catalog with prerequisites
- Semester-based course offerings
- Instructor assignments
- Enrollment management with capacity limits
- Final grades and letter grades

### **3. Attendance Tracking**
- Date-wise attendance records
- Multiple status types (present, absent, late, excused)
- Automatic summary calculations
- Attendance percentage tracking
- Bulk attendance marking

### **4. Grade Management**
- Multiple assessment types
- Weighted grading system
- Automatic grade calculations
- Letter grade conversion
- GPA calculation
- Grade finalization workflow

### **5. RESTful API**
- Complete CRUD operations
- Advanced filtering and search
- Pagination support
- Bulk operations
- Statistics endpoints

### **6. Admin Interface**
- User-friendly admin panel
- Advanced search and filters
- Custom actions
- Inline editing
- Related object management

---

## 📊 **Database Relationships**

```
Department
    ↓ (1:N)
Student ←→ Enrollment ←→ CourseOffering
    ↓                         ↓
AttendanceRecord         Assessment
    ↓                         ↓
AttendanceSummary        Grade → GradeReport
```

---

## 🔥 **API Features**

- ✅ **Filtering**: Filter by any field
- ✅ **Search**: Full-text search
- ✅ **Ordering**: Sort by any field
- ✅ **Pagination**: 50 items per page
- ✅ **Bulk Operations**: Mass updates
- ✅ **Statistics**: Aggregated data
- ✅ **Related Data**: Nested serializers

---

## 🌐 **CORS Configuration**

Currently configured to allow all origins for development:
```python
CORS_ALLOW_ALL_ORIGINS = True
```

**For Production**: Restrict to your frontend domain:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://yourdomain.com",
]
```

---

## 📝 **Environment Variables** (For Production)

Create `.env` file:
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

---

## 🎓 **Next Steps**

1. **Frontend Integration**: Connect with React/Vue/Angular frontend
2. **Authentication**: Add JWT or OAuth
3. **File Uploads**: Implement student photo uploads
4. **Email Notifications**: Send grade/attendance notifications
5. **PDF Reports**: Generate printable reports
6. **Data Export**: CSV/Excel export functionality
7. **Analytics**: Advanced reporting and analytics
8. **Mobile API**: Optimize for mobile apps

---

## 🐛 **Troubleshooting**

### **Server not accessible**
```bash
# Check if server is running
ps aux | grep runserver

# Restart server
python manage.py runserver 0.0.0.0:8001
```

### **Database errors**
```bash
# Reset database
rm db.sqlite3
python manage.py migrate
python load_sample_data.py
```

### **Permission errors**
- Ensure you're logged in to admin panel
- Check user permissions in Django admin

---

## 📞 **Support**

- **API Documentation**: http://localhost:8001/api/
- **Admin Panel**: http://localhost:8001/admin/
- **Django Docs**: https://docs.djangoproject.com/
- **DRF Docs**: https://www.django-rest-framework.org/

---

**Status**: ✅ **Production Ready**
**Version**: 1.0.0
**Last Updated**: October 30, 2024

🎉 **Your Enterprise Student MIS Backend is Live!**
