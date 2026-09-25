# 🎯 How to Access Django Admin Panel

## What is the Admin Panel?

The Django Admin Panel at `http://localhost:8001/admin/` is a powerful web interface that lets you:
- ✅ View and manage all database records
- ✅ Add, edit, delete students, courses, grades, attendance
- ✅ Search and filter data easily
- ✅ No coding required - just point and click!

---

## 📥 Step-by-Step Setup (5-10 Minutes)

### Prerequisites
- Python 3.8+ installed on your computer
- Basic command line knowledge

### Step 1: Download the Backend
Download the file: `student_mis_backend.tar.gz` (75 KB)

### Step 2: Extract the Archive
```bash
# On Windows (using Command Prompt or PowerShell):
tar -xzf student_mis_backend.tar.gz
cd student_mis_backend

# On Mac/Linux:
tar -xzf student_mis_backend.tar.gz
cd student_mis_backend
```

### Step 3: Install Required Packages
```bash
pip install django djangorestframework django-cors-headers django-filter pillow
```

**Note**: This installs:
- Django 5.2+ (Web framework)
- Django REST Framework (API toolkit)
- Django CORS Headers (Cross-origin support)
- Django Filter (Advanced filtering)
- Pillow (Image processing)

### Step 4: Run Database Migrations (Already Done, But Just in Case)
```bash
python manage.py migrate
```

### Step 5: Create Admin User (If Needed)
```bash
# The database already has an admin user, but if you need to create a new one:
python manage.py createsuperuser
```

### Step 6: Start the Django Server
```bash
python manage.py runserver 8001
```

You should see:
```
Starting development server at http://127.0.0.1:8001/
Quit the server with CTRL-BREAK.
```

### Step 7: Access the Admin Panel
1. Open your web browser
2. Go to: **http://localhost:8001/admin/**
3. Login with:
   - **Username**: `admin`
   - **Password**: `admin123`

---

## 🎨 What You'll See in the Admin Panel

After logging in, you'll see sections for:

### 📚 STUDENTS
- **Departments** - View/edit all departments (Computer Science, Engineering, etc.)
- **Students** - Manage student records with all details

### 📖 COURSES
- **Courses** - All available courses (CS101, ENG101, etc.)
- **Instructors** - Teacher/professor information
- **Course offerings** - Specific course instances (Fall 2024, Spring 2025, etc.)
- **Enrollments** - Student course registrations

### ✅ ATTENDANCE
- **Attendance records** - Individual attendance entries
- **Attendance summaries** - Student attendance statistics

### 📊 GRADES
- **Assessment types** - Quiz, Exam, Assignment, Project
- **Assessments** - Specific graded items
- **Grades** - Individual student grades
- **Grade reports** - Overall student performance

---

## 🔧 Common Admin Panel Actions

### Adding a New Student
1. Click "Students" → "Add student"
2. Fill in the form:
   - Student ID (e.g., STU006)
   - First name, Last name
   - Email, phone
   - Date of birth
   - Select department
   - Choose enrollment status
3. Click "Save"

### Enrolling a Student in a Course
1. Click "Enrollments" → "Add enrollment"
2. Select student from dropdown
3. Select course offering
4. Set enrollment date
5. Click "Save"

### Recording Attendance
1. Click "Attendance records" → "Add attendance record"
2. Select enrollment (student + course)
3. Choose date
4. Set status (Present/Absent/Late/Excused)
5. Click "Save"

### Adding Grades
1. Click "Grades" → "Add grade"
2. Select enrollment
3. Select assessment
4. Enter score
5. Add feedback (optional)
6. Click "Save"

---

## 🌐 API Access

Once the server is running, you can also access:

### API Endpoints
- **Base URL**: http://localhost:8001/api/
- **API Root**: http://localhost:8001/api/ (lists all endpoints)

### Example Endpoints
- Students: http://localhost:8001/api/students/
- Courses: http://localhost:8001/api/courses/
- Attendance: http://localhost:8001/api/attendance/
- Grades: http://localhost:8001/api/grades/

### Testing with Browser
Just paste the URLs above into your browser to see JSON data!

---

## 🔒 Security Notes

**Important**: The current setup is for **development only**!

For production use, you should:
- Change the admin password
- Use a strong SECRET_KEY in settings.py
- Switch from SQLite to PostgreSQL
- Enable HTTPS
- Configure proper CORS settings
- Set DEBUG = False in settings.py

---

## 🆘 Troubleshooting

### Problem: "Port 8001 is already in use"
**Solution**: 
```bash
# Use a different port
python manage.py runserver 8002

# Then access at http://localhost:8002/admin/
```

### Problem: "ModuleNotFoundError: No module named 'rest_framework'"
**Solution**: Install packages again
```bash
pip install django djangorestframework django-cors-headers django-filter pillow
```

### Problem: "Admin login doesn't work"
**Solution**: Create a new superuser
```bash
python manage.py createsuperuser
```

### Problem: "Database is locked"
**Solution**: Make sure no other process is using the database
```bash
# Close any other terminals running Django
# Then restart the server
python manage.py runserver 8001
```

---

## 📱 Sample Data Included

The database already contains:

### Departments (4)
- Computer Science (CSC)
- Engineering (ENG)
- Business Administration (BUS)
- Arts & Humanities (ART)

### Students (5)
- STU001: John Smith (Computer Science)
- STU002: Emma Johnson (Engineering)
- STU003: Michael Brown (Business)
- STU004: Sarah Davis (Computer Science)
- STU005: James Wilson (Arts)

### Courses (4)
- CS101: Introduction to Programming
- CS201: Data Structures
- ENG101: Engineering Fundamentals
- BUS101: Business Basics

### Instructors (2)
- Prof. Alan Turing
- Prof. Grace Hopper

You can view, edit, or delete this data through the admin panel!

---

## 🎓 Next Steps

1. **Explore the Admin Panel** - Click around and see what's possible
2. **Add Your Own Data** - Create students, courses, etc.
3. **Test the API** - Visit the API URLs in your browser
4. **Integrate with Frontend** - Connect the HTML frontend to use this backend
5. **Customize** - Modify models, add fields, change behavior

---

## 📞 Need Help?

The admin panel is intuitive, but if you get stuck:
- Django has excellent documentation: https://docs.djangoproject.com/
- Most actions are self-explanatory with helpful tooltips
- You can always delete test data and start fresh

---

**Happy Managing! 🚀**

The admin panel is one of Django's best features - it gives you a powerful database management interface without writing any frontend code!
