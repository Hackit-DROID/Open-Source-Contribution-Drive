# Student Management Information System (MIS)

A comprehensive web-based Student Management Information System built with modern web technologies.

## Features

### 1. **Dashboard**
- Real-time statistics (Total Students, Courses, Average Attendance, Average Grade)
- Visual analytics with charts (Department distribution, Attendance trends)
- Recent student activities
- Quick overview of system status

### 2. **Student Management**
- Add, edit, view, and delete student records
- Complete student profiles (ID, name, email, phone, department, year, DOB, gender, address)
- Advanced search and filtering by name, ID, department, and year
- Student status tracking (active/inactive)

### 3. **Course Management**
- Create and manage courses
- Course details (code, name, department, credits, instructor, description)
- Track student enrollment numbers
- Course-wise organization

### 4. **Attendance Tracking**
- Mark attendance by course and date
- Visual attendance interface with checkboxes
- Load and save attendance records
- Historical attendance data
- Attendance percentage calculation

### 5. **Grade Management**
- Enter grades for different assessment types (Midterm, Final, Assignment, Quiz)
- Course-wise grade entry
- Grade tracking and calculation
- Support for 0-100 grading scale

### 6. **Reports**
- Student Report (complete student list with all details)
- Attendance Report (attendance statistics and analysis)
- Grade Report (grade distribution and performance metrics)
- Printable reports

## Technical Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **UI Framework**: Bootstrap 5
- **Icons**: Bootstrap Icons
- **Charts**: Chart.js
- **Data Storage**: LocalStorage (browser-based)

## Installation & Usage

### Method 1: Direct Browser Access
1. Open `index.html` in any modern web browser
2. The application will run locally with sample data

### Method 2: Local Web Server
1. Navigate to the project directory
2. Run a local server:
   ```bash
   # Python 3
   python3 -m http.server 8000
   
   # Python 2
   python -m SimpleHTTPServer 8000
   
   # Node.js (if http-server is installed)
   npx http-server -p 8000
   ```
3. Open browser and go to `http://localhost:8000`

## Sample Data

The application comes pre-loaded with sample data including:
- 5 sample students across different departments
- 4 sample courses
- Realistic student and course information

You can clear this data and start fresh by clearing browser localStorage.

## Features in Detail

### Dashboard Analytics
- **Department Distribution Chart**: Doughnut chart showing student distribution across departments
- **Attendance Trends**: Line chart displaying attendance percentages over time
- **Statistics Cards**: Real-time metrics with color-coded cards

### Student Management
- **Advanced Filtering**: Multi-criteria filtering (name, ID, department, year)
- **CRUD Operations**: Complete Create, Read, Update, Delete functionality
- **Data Validation**: Form validation for all required fields
- **Status Management**: Track active/inactive student status

### Attendance System
- **Date-based Tracking**: Record attendance for specific dates
- **Course-specific**: Mark attendance separately for each course
- **Bulk Operations**: Mark all students at once for a session
- **Persistence**: All attendance data saved to browser storage

### Grade Management
- **Multiple Assessment Types**: Support for various evaluation methods
- **Flexible Grading**: 0-100 scale with decimal support
- **Course-based Entry**: Enter grades organized by courses
- **Automatic Calculations**: Average grade calculation

### Reporting
- **Comprehensive Reports**: Detailed reports for students, attendance, and grades
- **Print Support**: Print-optimized report layouts
- **Export Ready**: Data formatted for easy export

## Data Persistence

All data is stored in browser's LocalStorage:
- **Students**: Complete student records
- **Courses**: Course information
- **Attendance**: Attendance records with date stamps
- **Grades**: Grade records with assessment types

**Note**: Data persists across browser sessions but is specific to each browser/device.

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Responsive Design

The application is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile devices

## Future Enhancements

Potential features for future versions:
- Backend integration (Node.js, Python, PHP)
- Database support (MySQL, MongoDB, PostgreSQL)
- User authentication and role-based access
- Email notifications
- Advanced analytics and data visualization
- PDF export functionality
- Bulk data import/export (CSV, Excel)
- Student portal for self-service
- Parent/guardian access
- Fee management
- Timetable management
- Library integration
- Hostel management

## Security Notes

- This is a client-side application for demonstration purposes
- For production use, implement proper backend with:
  - User authentication
  - Server-side validation
  - Database with proper security
  - HTTPS encryption
  - Access control mechanisms

## License

This is a demonstration project for educational purposes.

## Support

For questions or issues, please refer to the documentation or modify the code according to your needs.

---

**Built with ❤️ for Educational Institutions**