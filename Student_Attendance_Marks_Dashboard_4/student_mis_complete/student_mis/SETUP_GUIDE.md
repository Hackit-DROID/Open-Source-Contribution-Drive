# Complete Setup Guide - Student MIS

## 🚀 Quick Start Commands

### For First Time Setup

```bash
# 1. Navigate to project directory
cd /home/user/student_mis

# 2. Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate  # On Windows

# 3. Install dependencies (if not done)
pip install django

# 4. Run database migrations
python manage.py makemigrations
python manage.py migrate

# 5. Create admin user (already done with username: admin, password: admin123)
# If you want to create another admin:
python manage.py createsuperuser

# 6. Populate sample data (optional)
python populate_sample_data.py

# 7. Start the development server
python manage.py runserver

# 8. Access the application at:
# http://127.0.0.1:8000/
```

## 📋 Common Commands

### Running the Server
```bash
# Default (localhost:8000)
python manage.py runserver

# Custom port
python manage.py runserver 8080

# Accessible from network
python manage.py runserver 0.0.0.0:8000
```

### Database Management
```bash
# Make migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (WARNING: Deletes all data)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser

# Create database backup
cp db.sqlite3 db.backup.sqlite3
```

### Django Shell
```bash
# Open Django shell
python manage.py shell

# Example operations in shell:
# >>> from students.models import Student
# >>> students = Student.objects.all()
# >>> print(students)
```

### Admin User Management
```bash
# Create superuser interactively
python manage.py createsuperuser

# Create superuser via script
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('teacher', 'teacher@example.com', 'teacher123')"
```

## 🔐 Default Login Credentials

### Admin Panel
- **URL**: http://127.0.0.1:8000/admin-login/
- **Username**: admin
- **Password**: admin123

### Django Admin
- **URL**: http://127.0.0.1:8000/admin/
- **Username**: admin
- **Password**: admin123

### Student Panel (Sample Data)
- **URL**: http://127.0.0.1:8000/student-login/
- **Register Number**: CSE001 (or CSE002, ECE001, ME001, EE001)
- **Password**: student123

## 📁 Project File Structure

```
student_mis/
│
├── manage.py                      # Django management script
├── db.sqlite3                     # SQLite database
├── README.md                      # Main documentation
├── SETUP_GUIDE.md                # This file
├── populate_sample_data.py       # Sample data script
│
├── venv/                         # Virtual environment
│
├── student_mis_project/          # Main project folder
│   ├── __init__.py
│   ├── settings.py               # Project settings
│   ├── urls.py                   # Main URL configuration
│   ├── wsgi.py                   # WSGI configuration
│   └── asgi.py
│
└── students/                     # Students app
    ├── __init__.py
    ├── admin.py                  # Django admin configuration
    ├── apps.py
    ├── models.py                 # Database models
    ├── views.py                  # View functions
    ├── urls.py                   # App URL routing
    ├── tests.py
    │
    ├── migrations/               # Database migrations
    │   ├── __init__.py
    │   └── 0001_initial.py
    │
    └── templates/                # HTML templates
        └── students/
            ├── base.html
            ├── home.html
            ├── admin_login.html
            ├── student_login.html
            ├── admin_dashboard.html
            ├── student_dashboard.html
            ├── student_list.html
            ├── add_student.html
            ├── edit_student.html
            ├── delete_student.html
            ├── add_marks.html
            ├── add_attendance.html
            └── view_report.html
```

## 🎯 Testing the Application

### Step-by-Step Testing

1. **Start the Server**
   ```bash
   python manage.py runserver
   ```

2. **Test Home Page**
   - Open: http://127.0.0.1:8000/
   - Should see login options for Admin and Student

3. **Test Admin Login**
   - Click "Admin Login" or go to: http://127.0.0.1:8000/admin-login/
   - Login with: admin / admin123
   - Should redirect to admin dashboard

4. **Test Student Management**
   - Click "View All Students"
   - Should see 5 sample students (if sample data loaded)
   - Try searching for a student
   - Click on action buttons (Edit, View Report, Add Marks, etc.)

5. **Test Adding a New Student**
   - Click "Add New Student"
   - Fill in the form with test data
   - Submit and verify student is added

6. **Test Marks Entry**
   - From student list, click marks icon for any student
   - Enter marks for all 5 subjects
   - Save and verify calculation

7. **Test Attendance**
   - From student list, click attendance icon
   - Enter total classes and attended classes
   - Save and verify percentage calculation

8. **Test Report Card**
   - From student list, click eye icon to view report
   - Should see complete student information
   - Test print functionality

9. **Test Student Login**
   - Logout from admin
   - Go to: http://127.0.0.1:8000/student-login/
   - Login with: CSE001 / student123
   - Should see student dashboard with all details

10. **Test Search Feature**
    - In student list, use search bar
    - Try searching by name, register number, or email

## 🛠️ Troubleshooting

### Problem: Server won't start

**Error**: "Port already in use"
```bash
# Solution: Use a different port
python manage.py runserver 8080
```

**Error**: "No module named 'django'"
```bash
# Solution: Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Then install Django
pip install django
```

### Problem: Static files not loading

```bash
# Add to settings.py
STATICFILES_DIRS = [BASE_DIR / 'static']

# Collect static files
python manage.py collectstatic
```

### Problem: Database errors

```bash
# Reset database
rm db.sqlite3
rm -rf students/migrations/000*.py  # Keep __init__.py

# Recreate
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Problem: "CSRF verification failed"

- Clear browser cookies
- Make sure {% csrf_token %} is in all forms
- Check ALLOWED_HOSTS in settings.py

### Problem: Template not found

```bash
# Verify TEMPLATES setting in settings.py
TEMPLATES = [
    {
        'DIRS': [],
        'APP_DIRS': True,  # Must be True
    }
]

# Make sure app is in INSTALLED_APPS
INSTALLED_APPS = [
    ...
    'students',
]
```

## 🔧 Customization Guide

### Change Color Scheme

Edit `students/templates/students/base.html`, find CSS variables:

```css
:root {
    --primary-color: #4e73df;      /* Change to your brand color */
    --secondary-color: #858796;
    --success-color: #1cc88a;
    --danger-color: #e74a3b;
    --warning-color: #f6c23e;
    --info-color: #36b9cc;
}
```

### Add More Subject Fields

1. Edit `students/models.py` - Add subject6, subject7, etc.
2. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
3. Update forms in templates to include new subjects

### Change Marks Weightage

Edit `students/models.py`, find `calculate_subject_total()`:

```python
def calculate_subject_total(self, subject_num):
    ise1 = getattr(self, f'subject{subject_num}_ise1')
    mid = getattr(self, f'subject{subject_num}_mid')
    end = getattr(self, f'subject{subject_num}_end')
    # Change these multipliers:
    return (ise1 * 0.2) + (mid * 0.2) + (end * 0.6)
```

### Add More Branches

Edit `students/models.py`, find `BRANCH_CHOICES`:

```python
BRANCH_CHOICES = [
    ('CSE', 'Computer Science Engineering'),
    ('ECE', 'Electronics and Communication Engineering'),
    ('ME', 'Mechanical Engineering'),
    ('EE', 'Electrical Engineering'),
    ('CE', 'Civil Engineering'),
    ('IT', 'Information Technology'),  # Add new branches
    ('AI', 'Artificial Intelligence'),
]
```

## 📊 Database Schema

### Student Table
```sql
CREATE TABLE students_student (
    reg_no VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200),
    email VARCHAR(254) UNIQUE,
    branch VARCHAR(10),
    year INTEGER,
    gender VARCHAR(1),
    mobile VARCHAR(15),
    password VARCHAR(128),
    created_at DATETIME,
    updated_at DATETIME
);
```

### Marks Table
```sql
CREATE TABLE students_marks (
    student_id VARCHAR(50) PRIMARY KEY,
    subject1_name VARCHAR(100),
    subject1_ise1 DECIMAL(5,2),
    subject1_mid DECIMAL(5,2),
    subject1_end DECIMAL(5,2),
    -- ... similar for subjects 2-5
    updated_at DATETIME,
    FOREIGN KEY (student_id) REFERENCES students_student(reg_no)
);
```

### Attendance Table
```sql
CREATE TABLE students_attendance (
    student_id VARCHAR(50) PRIMARY KEY,
    attendance_percentage DECIMAL(5,2),
    total_classes INTEGER,
    classes_attended INTEGER,
    updated_at DATETIME,
    FOREIGN KEY (student_id) REFERENCES students_student(reg_no)
);
```

## 🚀 Deployment Considerations

### For Production Use

1. **Change SECRET_KEY** in settings.py
2. **Set DEBUG = False**
3. **Configure ALLOWED_HOSTS**
4. **Use PostgreSQL instead of SQLite**
5. **Set up proper static files serving**
6. **Use environment variables for sensitive data**
7. **Enable HTTPS**
8. **Set up proper backup system**

### Sample Production Settings

```python
# settings.py for production
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Use PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'student_mis_db',
        'USER': 'db_user',
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static files
STATIC_ROOT = '/var/www/student_mis/static/'
```

## 📚 Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Bootstrap 5 Docs**: https://getbootstrap.com/docs/5.3/
- **Font Awesome Icons**: https://fontawesome.com/icons
- **Python Virtual Environments**: https://docs.python.org/3/tutorial/venv.html

## ✅ Checklist Before Going Live

- [ ] Change SECRET_KEY
- [ ] Set DEBUG = False
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up database backups
- [ ] Change default admin password
- [ ] Remove sample data
- [ ] Test all functionality
- [ ] Set up error logging
- [ ] Configure email notifications (if needed)
- [ ] Set up HTTPS/SSL
- [ ] Create user documentation

---

**Happy Coding! 🎓**
