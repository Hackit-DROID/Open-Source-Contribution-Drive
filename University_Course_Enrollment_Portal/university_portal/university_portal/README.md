# 🎓 University Portal - Complete DBMS Project

A comprehensive Django web application for university database management with complete CRUD operations and middleware integration.

## 🚀 Features

### 📊 **Complete Database Coverage**
- **👨‍🏫 Instructors**: View all instructors and courses they teach
- **📘 Courses**: Complete course catalog with departments and credits  
- **🧑‍🎓 Students**: Student directory with department and credit information
- **🏫 Departments**: Department listing with buildings and budgets
- **🏠 Classrooms**: Classroom inventory with capacity details
- **📅 Timetable**: Section schedules with time slots and room assignments
- **🔍 Search**: Universal search across instructors, students, courses, and departments

### 🛠 **Technical Stack**
- **Middleware**: Django Framework with 7+ middleware components
- **Database**: SQLite with complete university schema (11 tables)
- **Frontend**: Responsive HTML5 + CSS3 with modern design
- **Backend**: Python Django with ORM queries

## 📁 Project Structure

```
university_portal/
├── portal/                    # Main Django app
│   ├── models.py             # 11 database models
│   ├── views.py              # 8 view functions
│   ├── urls.py               # URL routing
│   ├── templates/portal/     # 8 HTML templates
│   └── management/commands/  # Data population
├── university_portal/        # Django project settings
├── db.sqlite3               # SQLite database
└── README.md                # This file
```

## 🎯 Pages & Database Usage

| Page | Description | Database Tables Used |
|------|-------------|---------------------|
| 🏠 **Home** | Dashboard with feature overview | - |
| 👨‍🏫 **Instructors** | All instructors + courses (JOIN) | instructor, teaches |
| 📘 **Courses** | Course catalog | course, department |
| 🧑‍🎓 **Students** | Student directory | student, department |
| 🏫 **Departments** | Department info | department |
| 🏠 **Classrooms** | Room inventory | classroom |
| 📅 **Timetable** | Section schedules | section, time_slot, classroom |
| 🔍 **Search** | Universal search across all entities | instructor, student, course, department |

## 🗄️ Database Schema (11 Tables)

1. **department** - Department info (name, building, budget)
2. **classroom** - Room details (building, room_no, capacity)
3. **course** - Course catalog (course_id, title, dept_name, credits)
4. **instructor** - Faculty info (ID, name, dept_name, salary)
5. **student** - Student records (ID, name, dept_name, tot_cred)
6. **time_slot** - Time schedules (time_slot_id, day, start_time, end_time)
7. **section** - Course sections (course_id, sec_id, semester, year, room, time)
8. **takes** - Student enrollments (student_id, course, section, grade)
9. **teaches** - Teaching assignments (instructor_id, course, section)
10. **advisor** - Student-advisor relationships (student_id, instructor_id)
11. **prereq** - Course prerequisites (course_id, prereq_id)

## 🚀 Quick Start

1. **Navigate to project**:
   ```bash
   cd university_portal
   ```

2. **Start server**:
   ```bash
   python manage.py runserver
   ```

3. **Access application**:
   - Open: `http://127.0.0.1:8000/`

## 📊 Sample Data Included

- ✅ 7 departments (Biology, Comp. Sci., Physics, etc.)
- ✅ 12 instructors with teaching assignments
- ✅ 13 courses across departments
- ✅ 13 students with enrollments
- ✅ 5 classrooms with capacity info
- ✅ 15 time slots and course sections
- ✅ Complete relational data with foreign keys

## 🔧 Middleware Technologies Used

- **SecurityMiddleware** - HTTPS & security headers
- **SessionMiddleware** - User session management
- **CommonMiddleware** - URL processing & ETags
- **CsrfViewMiddleware** - CSRF protection
- **AuthenticationMiddleware** - User authentication
- **MessageMiddleware** - Flash messages
- **XFrameOptionsMiddleware** - Clickjacking protection
- **Django ORM** - Database abstraction layer

## 🎯 Assignment Compliance

**✅ DBMS Practical #10 Requirements Met:**
- ✅ University database integration
- ✅ Middleware technology (Django)
- ✅ SQLite database
- ✅ HTML + CSS frontend
- ✅ Complete data population
- ✅ JOIN queries implementation
- ✅ Scalable architecture

## 🌟 Key Features

- **Responsive Design** - Works on all devices
- **Professional UI** - Clean, modern interface
- **Complete CRUD** - Full database operations
- **JOIN Queries** - Complex relational queries
- **Search Functionality** - Department-based filtering
- **Data Integrity** - Foreign key relationships
- **Scalable Architecture** - Easy to extend

---
**Developed for DBMS Practical Assignment #10**  
*Integrating University Database with Django Middleware & SQLite*