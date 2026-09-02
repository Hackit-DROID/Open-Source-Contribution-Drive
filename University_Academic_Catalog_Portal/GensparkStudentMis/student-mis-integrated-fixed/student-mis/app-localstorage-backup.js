// Initialize application
let students = [];
let courses = [];
let attendance = [];
let grades = [];
let currentStudentId = null;

// Load data from localStorage
function loadData() {
    students = JSON.parse(localStorage.getItem('students')) || [];
    courses = JSON.parse(localStorage.getItem('courses')) || [];
    attendance = JSON.parse(localStorage.getItem('attendance')) || [];
    grades = JSON.parse(localStorage.getItem('grades')) || [];
}

// Save data to localStorage
function saveData() {
    localStorage.setItem('students', JSON.stringify(students));
    localStorage.setItem('courses', JSON.stringify(courses));
    localStorage.setItem('attendance', JSON.stringify(attendance));
    localStorage.setItem('grades', JSON.stringify(grades));
}

// Initialize with sample data if empty
function initializeSampleData() {
    if (students.length === 0) {
        students = [
            {
                studentId: 'STU001', name: 'John Doe', email: 'john.doe@university.edu',
                phone: '555-0101', department: 'Computer Science', year: '2',
                dob: '2002-05-15', gender: 'Male', address: '123 Main St, City, State', status: 'active'
            },
            {
                studentId: 'STU002', name: 'Jane Smith', email: 'jane.smith@university.edu',
                phone: '555-0102', department: 'Engineering', year: '3',
                dob: '2001-08-22', gender: 'Female', address: '456 Oak Ave, City, State', status: 'active'
            },
            {
                studentId: 'STU003', name: 'Mike Johnson', email: 'mike.johnson@university.edu',
                phone: '555-0103', department: 'Business', year: '1',
                dob: '2003-02-10', gender: 'Male', address: '789 Pine Rd, City, State', status: 'active'
            },
            {
                studentId: 'STU004', name: 'Emily Brown', email: 'emily.brown@university.edu',
                phone: '555-0104', department: 'Computer Science', year: '4',
                dob: '2000-11-30', gender: 'Female', address: '321 Elm St, City, State', status: 'active'
            },
            {
                studentId: 'STU005', name: 'David Wilson', email: 'david.wilson@university.edu',
                phone: '555-0105', department: 'Arts', year: '2',
                dob: '2002-07-18', gender: 'Male', address: '654 Maple Dr, City, State', status: 'active'
            }
        ];

        courses = [
            {
                courseCode: 'CS101', courseName: 'Introduction to Programming',
                department: 'Computer Science', credits: 3, instructor: 'Prof. Alan Turing',
                description: 'Basic programming concepts', enrolled: 45
            },
            {
                courseCode: 'CS201', courseName: 'Data Structures',
                department: 'Computer Science', credits: 4, instructor: 'Prof. Grace Hopper',
                description: 'Advanced data structures', enrolled: 38
            },
            {
                courseCode: 'ENG101', courseName: 'Engineering Mathematics',
                department: 'Engineering', credits: 4, instructor: 'Prof. Isaac Newton',
                description: 'Mathematical foundations', enrolled: 52
            },
            {
                courseCode: 'BUS101', courseName: 'Business Administration',
                department: 'Business', credits: 3, instructor: 'Prof. Peter Drucker',
                description: 'Business management fundamentals', enrolled: 41
            }
        ];
        saveData();
    }
}

// Navigation
document.addEventListener('DOMContentLoaded', function() {
    loadData();
    initializeSampleData();
    
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            showSection(section);
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    showSection('dashboard');
    
    document.getElementById('searchStudent').addEventListener('input', filterStudents);
    document.getElementById('filterDepartment').addEventListener('change', filterStudents);
    document.getElementById('filterYear').addEventListener('change', filterStudents);
    document.getElementById('clearFilters').addEventListener('click', clearFilters);
    document.getElementById('loadAttendance').addEventListener('click', loadAttendanceList);
    document.getElementById('saveAttendance').addEventListener('click', saveAttendance);
    document.getElementById('loadGrades').addEventListener('click', loadGradesList);
    document.getElementById('saveGrades').addEventListener('click', saveGrades);
    document.getElementById('attendanceDate').valueAsDate = new Date();
    
    populateCourseDropdowns();
});

function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');
    
    switch(sectionId) {
        case 'dashboard': updateDashboard(); break;
        case 'students': displayStudents(); break;
        case 'courses': displayCourses(); break;
        case 'attendance': populateCourseDropdowns(); break;
        case 'grades': populateCourseDropdowns(); break;
    }
}

function updateDashboard() {
    document.getElementById('totalStudents').textContent = students.length;
    document.getElementById('totalCourses').textContent = courses.length;
    document.getElementById('avgAttendance').textContent = calculateAverageAttendance() + '%';
    document.getElementById('avgGrade').textContent = calculateAverageGrade();
    displayRecentStudents();
    updateCharts();
}

function calculateAverageAttendance() {
    if (attendance.length === 0) return 0;
    const total = attendance.reduce((sum, record) => sum + (record.present ? 1 : 0), 0);
    return Math.round((total / attendance.length) * 100);
}

function calculateAverageGrade() {
    if (grades.length === 0) return 0;
    const total = grades.reduce((sum, record) => sum + parseFloat(record.grade), 0);
    return (total / grades.length).toFixed(2);
}

function displayRecentStudents() {
    const tbody = document.getElementById('recentStudentsTable');
    const recentStudents = students.slice(0, 5);
    
    if (recentStudents.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No students found</td></tr>';
        return;
    }
    
    tbody.innerHTML = recentStudents.map(student => `
        <tr>
            <td>${student.studentId}</td>
            <td>${student.name}</td>
            <td>${student.department}</td>
            <td>Year ${student.year}</td>
            <td><span class="badge status-${student.status}">${student.status}</span></td>
        </tr>
    `).join('');
}

function updateCharts() {
    const deptCounts = students.reduce((acc, student) => {
        acc[student.department] = (acc[student.department] || 0) + 1;
        return acc;
    }, {});
    
    const deptCtx = document.getElementById('departmentChart');
    if (window.deptChart) window.deptChart.destroy();
    
    window.deptChart = new Chart(deptCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(deptCounts),
            datasets: [{
                data: Object.values(deptCounts),
                backgroundColor: ['rgba(13,110,253,0.8)', 'rgba(25,135,84,0.8)', 'rgba(255,193,7,0.8)', 'rgba(220,53,69,0.8)', 'rgba(13,202,240,0.8)']
            }]
        },
        options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { position: 'bottom' } } }
    });
    
    const attCtx = document.getElementById('attendanceChart');
    if (window.attChart) window.attChart.destroy();
    
    window.attChart = new Chart(attCtx, {
        type: 'line',
        data: {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            datasets: [{
                label: 'Attendance %',
                data: [85, 88, 82, 90],
                borderColor: 'rgba(13,110,253,1)',
                backgroundColor: 'rgba(13,110,253,0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: { responsive: true, maintainAspectRatio: true, scales: { y: { beginAtZero: true, max: 100 } }, plugins: { legend: { display: false } } }
    });
}

function displayStudents(filteredStudents = null) {
    const tbody = document.getElementById('studentsTableBody');
    const studentsToDisplay = filteredStudents || students;
    
    if (studentsToDisplay.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">No students found</td></tr>';
        return;
    }
    
    tbody.innerHTML = studentsToDisplay.map(student => `
        <tr>
            <td>${student.studentId}</td>
            <td>${student.name}</td>
            <td>${student.email}</td>
            <td>${student.department}</td>
            <td>Year ${student.year}</td>
            <td>${student.phone}</td>
            <td><span class="badge status-${student.status}">${student.status}</span></td>
            <td>
                <button class="btn btn-sm btn-info btn-action" onclick="viewStudent('${student.studentId}')"><i class="bi bi-eye"></i></button>
                <button class="btn btn-sm btn-warning btn-action" onclick="editStudent('${student.studentId}')"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-danger btn-action" onclick="deleteStudent('${student.studentId}')"><i class="bi bi-trash"></i></button>
            </td>
        </tr>
    `).join('');
}

function saveStudent() {
    const form = document.getElementById('studentForm');
    const formData = new FormData(form);
    const student = {
        studentId: formData.get('studentId'), name: formData.get('name'), email: formData.get('email'),
        phone: formData.get('phone'), department: formData.get('department'), year: formData.get('year'),
        dob: formData.get('dob'), gender: formData.get('gender'), address: formData.get('address'), status: 'active'
    };
    
    if (students.some(s => s.studentId === student.studentId && currentStudentId !== student.studentId)) {
        alert('Student ID already exists!');
        return;
    }
    
    if (currentStudentId) {
        const index = students.findIndex(s => s.studentId === currentStudentId);
        students[index] = student;
    } else {
        students.push(student);
    }
    
    saveData();
    const modal = bootstrap.Modal.getInstance(document.getElementById('addStudentModal'));
    modal.hide();
    form.reset();
    displayStudents();
    updateDashboard();
    showAlert('Student saved successfully!', 'success');
}

function editStudent(studentId) {
    const student = students.find(s => s.studentId === studentId);
    if (!student) return;
    
    const form = document.getElementById('studentForm');
    Object.keys(student).forEach(key => {
        const input = form.elements[key];
        if (input) input.value = student[key];
    });
    
    const modal = new bootstrap.Modal(document.getElementById('addStudentModal'));
    document.querySelector('#addStudentModal .modal-title').textContent = 'Edit Student';
    modal.show();
    currentStudentId = studentId;
}

function deleteStudent(studentId) {
    if (confirm('Are you sure you want to delete this student?')) {
        students = students.filter(s => s.studentId !== studentId);
        saveData();
        displayStudents();
        updateDashboard();
        showAlert('Student deleted successfully!', 'success');
    }
}

function viewStudent(studentId) {
    const student = students.find(s => s.studentId === studentId);
    if (!student) return;
    
    alert(`Student Details:\n\nID: ${student.studentId}\nName: ${student.name}\nEmail: ${student.email}\nDepartment: ${student.department}\nYear: ${student.year}\nPhone: ${student.phone}\nDOB: ${student.dob}\nGender: ${student.gender}\nAddress: ${student.address}`);
}

function filterStudents() {
    const searchTerm = document.getElementById('searchStudent').value.toLowerCase();
    const deptFilter = document.getElementById('filterDepartment').value;
    const yearFilter = document.getElementById('filterYear').value;
    
    let filtered = students.filter(student => {
        const matchesSearch = student.name.toLowerCase().includes(searchTerm) || student.studentId.toLowerCase().includes(searchTerm);
        const matchesDept = !deptFilter || student.department === deptFilter;
        const matchesYear = !yearFilter || student.year === yearFilter;
        return matchesSearch && matchesDept && matchesYear;
    });
    
    displayStudents(filtered);
}

function clearFilters() {
    document.getElementById('searchStudent').value = '';
    document.getElementById('filterDepartment').value = '';
    document.getElementById('filterYear').value = '';
    displayStudents();
}

function displayCourses() {
    const tbody = document.getElementById('coursesTableBody');
    
    if (courses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No courses found</td></tr>';
        return;
    }
    
    tbody.innerHTML = courses.map(course => `
        <tr>
            <td>${course.courseCode}</td>
            <td>${course.courseName}</td>
            <td>${course.department}</td>
            <td>${course.credits}</td>
            <td>${course.instructor}</td>
            <td>${course.enrolled || 0}</td>
            <td>
                <button class="btn btn-sm btn-warning btn-action" onclick="editCourse('${course.courseCode}')"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-danger btn-action" onclick="deleteCourse('${course.courseCode}')"><i class="bi bi-trash"></i></button>
            </td>
        </tr>
    `).join('');
}

function saveCourse() {
    const form = document.getElementById('courseForm');
    const formData = new FormData(form);
    const course = {
        courseCode: formData.get('courseCode'), courseName: formData.get('courseName'),
        department: formData.get('department'), credits: parseInt(formData.get('credits')),
        instructor: formData.get('instructor'), description: formData.get('description'), enrolled: 0
    };
    
    if (courses.some(c => c.courseCode === course.courseCode)) {
        alert('Course code already exists!');
        return;
    }
    
    courses.push(course);
    saveData();
    const modal = bootstrap.Modal.getInstance(document.getElementById('addCourseModal'));
    modal.hide();
    form.reset();
    displayCourses();
    populateCourseDropdowns();
    updateDashboard();
    showAlert('Course added successfully!', 'success');
}

function editCourse(courseCode) { alert('Edit course - to be implemented'); }
function deleteCourse(courseCode) {
    if (confirm('Are you sure?')) {
        courses = courses.filter(c => c.courseCode !== courseCode);
        saveData();
        displayCourses();
        populateCourseDropdowns();
        updateDashboard();
        showAlert('Course deleted!', 'success');
    }
}

function populateCourseDropdowns() {
    ['attendanceCourse', 'gradeCourse'].forEach(dropdownId => {
        const dropdown = document.getElementById(dropdownId);
        if (dropdown) {
            dropdown.innerHTML = '<option value="">Choose course...</option>' +
                courses.map(course => `<option value="${course.courseCode}">${course.courseCode} - ${course.courseName}</option>`).join('');
        }
    });
}

function loadAttendanceList() {
    const courseCode = document.getElementById('attendanceCourse').value;
    const date = document.getElementById('attendanceDate').value;
    
    if (!courseCode || !date) {
        alert('Please select course and date');
        return;
    }
    
    document.getElementById('attendanceList').innerHTML = `
        <table class="table table-striped">
            <thead><tr><th>Student ID</th><th>Name</th><th>Department</th><th class="text-center">Present</th></tr></thead>
            <tbody>
                ${students.map(student => {
                    const attRecord = attendance.find(a => a.studentId === student.studentId && a.courseCode === courseCode && a.date === date);
                    return `<tr>
                        <td>${student.studentId}</td>
                        <td>${student.name}</td>
                        <td>${student.department}</td>
                        <td class="text-center">
                            <input type="checkbox" class="form-check-input attendance-checkbox" data-student-id="${student.studentId}" ${attRecord && attRecord.present ? 'checked' : ''}>
                        </td>
                    </tr>`;
                }).join('')}
            </tbody>
        </table>
    `;
}

function saveAttendance() {
    const courseCode = document.getElementById('attendanceCourse').value;
    const date = document.getElementById('attendanceDate').value;
    
    if (!courseCode || !date) {
        alert('Please select course and date');
        return;
    }
    
    document.querySelectorAll('.attendance-checkbox').forEach(checkbox => {
        const studentId = checkbox.getAttribute('data-student-id');
        attendance = attendance.filter(a => !(a.studentId === studentId && a.courseCode === courseCode && a.date === date));
        attendance.push({ studentId, courseCode, date, present: checkbox.checked });
    });
    
    saveData();
    updateDashboard();
    showAlert('Attendance saved!', 'success');
}

function loadGradesList() {
    const courseCode = document.getElementById('gradeCourse').value;
    const assessmentType = document.getElementById('assessmentType').value;
    
    if (!courseCode) {
        alert('Please select a course');
        return;
    }
    
    document.getElementById('gradesList').innerHTML = `
        <table class="table table-striped">
            <thead><tr><th>Student ID</th><th>Name</th><th>Department</th><th>Grade (0-100)</th></tr></thead>
            <tbody>
                ${students.map(student => {
                    const gradeRecord = grades.find(g => g.studentId === student.studentId && g.courseCode === courseCode && g.assessmentType === assessmentType);
                    return `<tr>
                        <td>${student.studentId}</td>
                        <td>${student.name}</td>
                        <td>${student.department}</td>
                        <td><input type="number" class="form-control grade-input" min="0" max="100" data-student-id="${student.studentId}" value="${gradeRecord ? gradeRecord.grade : ''}" placeholder="Enter grade"></td>
                    </tr>`;
                }).join('')}
            </tbody>
        </table>
    `;
}

function saveGrades() {
    const courseCode = document.getElementById('gradeCourse').value;
    const assessmentType = document.getElementById('assessmentType').value;
    
    if (!courseCode) {
        alert('Please select a course');
        return;
    }
    
    document.querySelectorAll('.grade-input').forEach(input => {
        const studentId = input.getAttribute('data-student-id');
        const grade = input.value;
        
        if (grade !== '') {
            grades = grades.filter(g => !(g.studentId === studentId && g.courseCode === courseCode && g.assessmentType === assessmentType));
            grades.push({ studentId, courseCode, assessmentType, grade: parseFloat(grade) });
        }
    });
    
    saveData();
    updateDashboard();
    showAlert('Grades saved!', 'success');
}

function generateStudentReport() {
    document.getElementById('reportTitle').textContent = 'Student Report';
    document.getElementById('reportContent').innerHTML = `
        <h4>Total Students: ${students.length}</h4>
        <table class="table table-bordered mt-3">
            <thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Year</th><th>Email</th><th>Phone</th><th>Status</th></tr></thead>
            <tbody>${students.map(s => `<tr><td>${s.studentId}</td><td>${s.name}</td><td>${s.department}</td><td>Year ${s.year}</td><td>${s.email}</td><td>${s.phone}</td><td>${s.status}</td></tr>`).join('')}</tbody>
        </table>
    `;
    document.getElementById('reportOutput').classList.remove('d-none');
}

function generateAttendanceReport() {
    document.getElementById('reportTitle').textContent = 'Attendance Report';
    document.getElementById('reportContent').innerHTML = `
        <h4>Overall Attendance: ${calculateAverageAttendance()}%</h4>
        <p>Total Records: ${attendance.length}</p>
        <div class="alert alert-info"><i class="bi bi-info-circle"></i> Detailed attendance analysis displayed here.</div>
    `;
    document.getElementById('reportOutput').classList.remove('d-none');
}

function generateGradeReport() {
    document.getElementById('reportTitle').textContent = 'Grade Report';
    document.getElementById('reportContent').innerHTML = `
        <h4>Average Grade: ${calculateAverageGrade()}</h4>
        <p>Total Grade Records: ${grades.length}</p>
        <div class="alert alert-info"><i class="bi bi-info-circle"></i> Detailed grade distribution displayed here.</div>
    `;
    document.getElementById('reportOutput').classList.remove('d-none');
}

function printReport() { window.print(); }

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 3000);
}

document.getElementById('addStudentModal').addEventListener('hidden.bs.modal', function () {
    document.getElementById('studentForm').reset();
    document.querySelector('#addStudentModal .modal-title').textContent = 'Add New Student';
    currentStudentId = null;
});

document.getElementById('addCourseModal').addEventListener('hidden.bs.modal', function () {
    document.getElementById('courseForm').reset();
});
