# Quick Start Guide - Student MIS

## 🚀 Getting Started in 3 Steps

### Step 1: Access the Application
The server is already running! Open your browser and navigate to:
```
http://localhost:8000
```

### Step 2: Explore Pre-loaded Data
The application comes with sample data:
- **5 Students** - John Doe, Jane Smith, Mike Johnson, Emily Brown, David Wilson
- **4 Courses** - CS101, CS201, ENG101, BUS101

### Step 3: Start Using Features

## 📋 Quick Feature Guide

### Adding a New Student
1. Click "Students" in the navigation
2. Click the "+ Add Student" button
3. Fill in the form with student details
4. Click "Save Student"

### Managing Courses
1. Click "Courses" in navigation
2. Click "+ Add Course" button
3. Enter course information
4. Save to add to the system

### Marking Attendance
1. Go to "Attendance" section
2. Select a course from dropdown
3. Choose the date
4. Click "Load Students"
5. Check/uncheck present students
6. Click "Save" to record attendance

### Entering Grades
1. Navigate to "Grades"
2. Select a course
3. Choose assessment type (Midterm, Final, Assignment, Quiz)
4. Click "Load Students"
5. Enter grades (0-100)
6. Click "Save"

### Viewing Dashboard
- Click "Dashboard" to see:
  - Total students and courses
  - Average attendance percentage
  - Average grade
  - Department distribution chart
  - Attendance trends
  - Recent students list

### Generating Reports
1. Go to "Reports" section
2. Choose report type:
   - Student Report
   - Attendance Report
   - Grade Report
3. Click "Generate"
4. Click "Print" to print or save as PDF

## 🔍 Search & Filter

In the Students section:
- **Search**: Type student name or ID in search box
- **Filter by Department**: Use department dropdown
- **Filter by Year**: Select academic year
- **Clear**: Reset all filters

## ⚙️ Technical Details

### Data Storage
- All data is stored in browser's LocalStorage
- Data persists between sessions
- Each browser/device has independent data

### Clear All Data
To start fresh:
1. Open browser console (F12)
2. Type: `localStorage.clear()`
3. Refresh the page

### Export Data (Manual)
1. Open browser console (F12)
2. Type: `console.log(localStorage)`
3. Copy the data for backup

## 🎨 User Interface

### Navigation Bar
- **Dashboard** - Overview and analytics
- **Students** - Student management
- **Courses** - Course management
- **Attendance** - Attendance tracking
- **Grades** - Grade management
- **Reports** - Generate reports

### Color Coding
- **Blue** - Primary actions and students
- **Green** - Success and courses
- **Yellow** - Warnings and attendance
- **Info** - Information and grades
- **Red** - Delete actions

## 💡 Tips

1. **Always save after making changes** - Click the save button to persist data
2. **Use filters for large datasets** - Makes finding students easier
3. **Regular backups** - Export localStorage data periodically
4. **Check dashboard regularly** - Monitor overall system health
5. **Mark attendance on time** - Keep records up to date

## 🐛 Troubleshooting

### Can't see my data
- Check if you're using the same browser
- Verify data wasn't cleared from localStorage

### Changes not saving
- Check browser console for errors (F12)
- Ensure you clicked the "Save" button

### Server not accessible
- Check if server is running on port 8000
- Try: `http://localhost:8000` or `http://127.0.0.1:8000`

### Charts not displaying
- Ensure internet connection (Chart.js loads from CDN)
- Check browser console for errors

## 📱 Mobile Access

The application is responsive and works on mobile devices:
- Navigate using the hamburger menu (≡)
- All features available on mobile
- Touch-friendly interface

## 🔐 Security Note

This is a demonstration application:
- No user authentication
- Data stored client-side only
- Not suitable for production without backend
- Recommended for learning and prototyping

## ⭐ Sample Credentials

Sample student IDs you can use:
- STU001 - John Doe
- STU002 - Jane Smith
- STU003 - Mike Johnson
- STU004 - Emily Brown
- STU005 - David Wilson

Sample courses:
- CS101 - Introduction to Programming
- CS201 - Data Structures
- ENG101 - Engineering Mathematics
- BUS101 - Business Administration

---

**Enjoy using Student MIS! 🎓**