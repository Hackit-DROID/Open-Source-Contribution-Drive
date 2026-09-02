# Student Management Information System (MIS)

A comprehensive web-based Student Management Information System built with Django (backend) and Bootstrap 5 (frontend).

## Features

### Admin Panel (Teacher/Admin)
- ✅ Add new students with complete details
- ✅ View, Edit, and Delete student records
- ✅ Add/Update marks for 5 subjects (ISE-1: 20%, Midterm: 20%, End-Term: 60%)
- ✅ Add/Update attendance percentage
- ✅ View comprehensive report cards
- ✅ Search students by name, register number, or email

### Student Panel
- ✅ Login using Register Number and Password
- ✅ View personal details
- ✅ View marks with subject-wise performance
- ✅ View attendance percentage
- ✅ Visual performance charts
- ✅ Print-friendly report cards

## Tech Stack

- **Backend**: Django 5.2.7
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Database**: SQLite3
- **Icons**: Font Awesome 6.4.0

## Database Models

### 1. Student (StudentInfo)
- name (CharField)
- reg_no (CharField, Primary Key, Unique)
- email (EmailField, Unique)
- branch (CharField with choices: CSE, ECE, ME, EE, CE)
- year (IntegerField with choices: 1, 2, 3, 4)
- gender (CharField with choices: M, F, O)
- mobile (CharField)
- password (CharField for student login)

### 2. Marks
- student (OneToOneField to Student)
- 5 subjects, each with:
  - subject_name (CharField)
  - ise1 (DecimalField) - 20% weightage
  - mid (DecimalField) - 20% weightage
  - end (DecimalField) - 60% weightage

### 3. Attendance
- student (OneToOneField to Student)
- attendance_percentage (DecimalField)
- total_classes (IntegerField)
- classes_attended (IntegerField)

## Installation and Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone or Download the Project
```bash
cd /home/user/student_mis
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
```

### Step 3: Activate Virtual Environment
**On Linux/Mac:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### Step 4: Install Dependencies
```bash
pip install django
```

### Step 5: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser (Admin)
```bash
python manage.py createsuperuser
# Or use the pre-created admin account:
# Username: admin
# Password: admin123
```

### Step 7: Run the Development Server
```bash
python manage.py runserver
```

### Step 8: Access the Application
- **Home Page**: http://127.0.0.1:8000/
- **Admin Login**: http://127.0.0.1:8000/admin-login/
- **Student Login**: http://127.0.0.1:8000/student-login/
- **Django Admin**: http://127.0.0.1:8000/admin/

## Default Credentials

### Admin/Teacher Login
- Username: `admin`
- Password: `admin123`

### Student Login
- Register Number: (Set by admin when adding student)
- Default Password: `student123`

## Usage Guide

### For Admin/Teacher

1. **Login**: Use admin credentials at `/admin-login/`
2. **Dashboard**: View statistics and quick actions
3. **Add Student**: Navigate to "Add Student" and fill in the form
4. **View Students**: See all students in a searchable table
5. **Add Marks**: Click on the marks icon for any student
6. **Add Attendance**: Click on the attendance icon for any student
7. **View Report**: Click on the eye icon to see complete report card
8. **Edit Student**: Click on the edit icon to modify student details
9. **Delete Student**: Click on the delete icon (with confirmation)

### For Students

1. **Login**: Use register number and password at `/student-login/`
2. **Dashboard**: View your complete academic information
3. **Personal Info**: See your contact and course details
4. **Marks**: View subject-wise marks and overall percentage
5. **Attendance**: See attendance percentage with visual indicators
6. **Print Report**: Use the print button to print your report card

## Project Structure

```
student_mis/
├── manage.py
├── db.sqlite3
├── student_mis_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── students/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── migrations/
    └── templates/
        └── students/
            ├── base.html
            ├── home.html
            ├── admin_login.html
            ├── student_login.html
            ├── admin_dashboard.html
            ├── student_list.html
            ├── add_student.html
            ├── edit_student.html
            ├── delete_student.html
            ├── add_marks.html
            ├── add_attendance.html
            ├── view_report.html
            └── student_dashboard.html
```

## Key URLs

| URL | Description |
|-----|-------------|
| `/` | Home page with login options |
| `/admin-login/` | Admin/Teacher login |
| `/student-login/` | Student login |
| `/admin/dashboard/` | Admin dashboard |
| `/admin/students/` | List all students |
| `/admin/students/add/` | Add new student |
| `/admin/students/edit/<reg_no>/` | Edit student details |
| `/admin/students/delete/<reg_no>/` | Delete student |
| `/admin/students/marks/<reg_no>/` | Add/Update marks |
| `/admin/students/attendance/<reg_no>/` | Add/Update attendance |
| `/admin/students/report/<reg_no>/` | View report card |
| `/student/dashboard/` | Student dashboard |
| `/logout/` | Logout (both admin and student) |

## Features Breakdown

### Marks Calculation
- **ISE-1**: 20% weightage (out of 20 marks)
- **Midterm**: 20% weightage (out of 20 marks)
- **End-Term**: 60% weightage (out of 60 marks)
- **Total**: Sum of all three = 100 marks per subject
- **Overall Percentage**: Average of all 5 subjects

### Attendance Tracking
- Total classes conducted
- Classes attended by student
- Automatic percentage calculation: (Attended / Total) × 100
- Visual indicators for attendance below 75%

### Search Functionality
- Search students by name
- Search by register number
- Search by email
- Real-time filtering

## Bonus Features Implemented

- ✅ Search bar for students (by name, reg_no, email)
- ✅ Print-friendly report cards
- ✅ Responsive design (mobile-friendly)
- ✅ Visual performance indicators
- ✅ Color-coded attendance alerts
- ✅ Progress bars for performance visualization

## Screenshots and UI Features

- **Bootstrap 5** for modern, responsive design
- **Font Awesome** icons throughout the interface
- **Card-based layouts** for better organization
- **Color-coded statistics** for quick insights
- **Gradient backgrounds** for visual appeal
- **Table-based data display** with hover effects
- **Alert messages** for user feedback
- **Print-optimized** report layouts

## Security Features

- CSRF protection on all forms
- Login required decorators for admin views
- Session-based authentication for students
- Password protection for student accounts
- Unique register numbers and emails

## Customization

### Adding More Subjects
Edit `students/models.py` and add more subject fields in the `Marks` model.

### Changing Marks Weightage
Modify the `calculate_subject_total()` method in the `Marks` model.

### Adding More Branches
Update the `BRANCH_CHOICES` in the `Student` model.

### Customizing Colors
Edit the CSS variables in `base.html`:
```css
:root {
    --primary-color: #4e73df;
    --secondary-color: #858796;
    --success-color: #1cc88a;
    --danger-color: #e74a3b;
    --warning-color: #f6c23e;
    --info-color: #36b9cc;
}
```

## Troubleshooting

### Issue: Port already in use
```bash
python manage.py runserver 8080
```

### Issue: Database locked
```bash
python manage.py migrate --run-syncdb
```

### Issue: Static files not loading
```bash
python manage.py collectstatic
```

## Future Enhancements (Not Implemented)

- PDF generation for report cards
- Email notifications to students
- Bulk student import via CSV
- Grade calculation and GPA system
- Subject-wise attendance tracking
- Academic calendar integration
- Parent portal access
- Mobile app version

## Development Notes

- Default student password is `student123`
- Admin can change student passwords by editing student record
- All marks are stored with 2 decimal precision
- Attendance percentage is auto-calculated
- Register numbers cannot be changed after creation
- Deleting a student also deletes their marks and attendance

## Support and Contact

For issues or questions about this project:
- Check the Django documentation: https://docs.djangoproject.com/
- Bootstrap documentation: https://getbootstrap.com/docs/

## License

This project is created for educational purposes.

---

**Created with Django and Bootstrap** 🚀
