// =============================================================================
// STUDENT MIS - BACKEND INTEGRATED VERSION
// This version uses Django REST API instead of LocalStorage
// =============================================================================

// API Configuration
const API_BASE_URL = 'http://localhost:8001/api';
const API_ENDPOINTS = {
    students: `${API_BASE_URL}/students/`,
    departments: `${API_BASE_URL}/departments/`,
    courses: `${API_BASE_URL}/courses/`,
    instructors: `${API_BASE_URL}/instructors/`,
    courseOfferings: `${API_BASE_URL}/course-offerings/`,
    enrollments: `${API_BASE_URL}/enrollments/`,
    attendance: `${API_BASE_URL}/attendance/`,
    attendanceSummary: `${API_BASE_URL}/attendance-summary/`,
    assessmentTypes: `${API_BASE_URL}/assessment-types/`,
    assessments: `${API_BASE_URL}/assessments/`,
    grades: `${API_BASE_URL}/grades/`,
    gradeReports: `${API_BASE_URL}/grade-reports/`,
};

// Global State
let students = [];
let departments = [];
let courses = [];
let instructors = [];
let courseOfferings = [];
let enrollments = [];
let attendance = [];
let grades = [];
let currentStudentId = null;
let isLoading = false;

// =============================================================================
// API HELPER FUNCTIONS
// =============================================================================

/**
 * Generic API call function with error handling
 */
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        showLoading(true);
        const response = await fetch(url, options);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        showLoading(false);
        return result;
    } catch (error) {
        showLoading(false);
        console.error('API Error:', error);
        showAlert(`Error: ${error.message}`, 'danger');
        throw error;
    }
}

/**
 * Show/hide loading indicator
 */
function showLoading(show) {
    isLoading = show;
    const loader = document.getElementById('loadingIndicator');
    if (loader) {
        loader.style.display = show ? 'block' : 'none';
    }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// =============================================================================
// DATA LOADING FUNCTIONS
// =============================================================================

/**
 * Load all data from API
 */
async function loadAllData() {
    try {
        await Promise.all([
            loadStudents(),
            loadDepartments(),
            loadCourses(),
            loadInstructors(),
            loadCourseOfferings(),
            loadEnrollments(),
            loadAttendanceRecords(),
            loadGradesData()
        ]);
        console.log('All data loaded successfully');
    } catch (error) {
        console.error('Error loading data:', error);
        showAlert('Failed to load some data. Please refresh the page.', 'warning');
    }
}

/**
 * Load students from API
 */
async function loadStudents() {
    try {
        const response = await apiCall(API_ENDPOINTS.students);
        students = response.results || response;
        return students;
    } catch (error) {
        console.error('Error loading students:', error);
        students = [];
        return [];
    }
}

/**
 * Load departments from API
 */
async function loadDepartments() {
    try {
        const response = await apiCall(API_ENDPOINTS.departments);
        departments = response.results || response;
        return departments;
    } catch (error) {
        console.error('Error loading departments:', error);
        departments = [];
        return [];
    }
}

/**
 * Load courses from API
 */
async function loadCourses() {
    try {
        const response = await apiCall(API_ENDPOINTS.courses);
        courses = response.results || response;
        return courses;
    } catch (error) {
        console.error('Error loading courses:', error);
        courses = [];
        return [];
    }
}

/**
 * Load instructors from API
 */
async function loadInstructors() {
    try {
        const response = await apiCall(API_ENDPOINTS.instructors);
        instructors = response.results || response;
        return instructors;
    } catch (error) {
        console.error('Error loading instructors:', error);
        instructors = [];
        return [];
    }
}

/**
 * Load course offerings from API
 */
async function loadCourseOfferings() {
    try {
        const response = await apiCall(API_ENDPOINTS.courseOfferings);
        courseOfferings = response.results || response;
        return courseOfferings;
    } catch (error) {
        console.error('Error loading course offerings:', error);
        courseOfferings = [];
        return [];
    }
}

/**
 * Load enrollments from API
 */
async function loadEnrollments() {
    try {
        const response = await apiCall(API_ENDPOINTS.enrollments);
        enrollments = response.results || response;
        return enrollments;
    } catch (error) {
        console.error('Error loading enrollments:', error);
        enrollments = [];
        return [];
    }
}

/**
 * Load attendance records from API
 */
async function loadAttendanceRecords() {
    try {
        const response = await apiCall(API_ENDPOINTS.attendance);
        attendance = response.results || response;
        return attendance;
    } catch (error) {
        console.error('Error loading attendance:', error);
        attendance = [];
        return [];
    }
}

/**
 * Load grades from API
 */
async function loadGradesData() {
    try {
        const response = await apiCall(API_ENDPOINTS.grades);
        grades = response.results || response;
        return grades;
    } catch (error) {
        console.error('Error loading grades:', error);
        grades = [];
        return [];
    }
}

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', async function() {
    // Add loading indicator to page
    addLoadingIndicator();
    
    // Load all data from API
    await loadAllData();
    
    // Setup navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            showSection(section);
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Show dashboard by default
    showSection('dashboard');
    
    // Setup event listeners
    const searchStudent = document.getElementById('searchStudent');
    const filterDepartment = document.getElementById('filterDepartment');
    const filterYear = document.getElementById('filterYear');
    const clearFilters = document.getElementById('clearFilters');
    
    if (searchStudent) searchStudent.addEventListener('input', filterStudents);
    if (filterDepartment) filterDepartment.addEventListener('change', filterStudents);
    if (filterYear) filterYear.addEventListener('change', filterStudents);
    if (clearFilters) clearFilters.addEventListener('click', clearFilters);
    
    const loadAttendanceBtn = document.getElementById('loadAttendance');
    const saveAttendanceBtn = document.getElementById('saveAttendance');
    const loadGradesBtn = document.getElementById('loadGrades');
    const saveGradesBtn = document.getElementById('saveGrades');
    
    if (loadAttendanceBtn) loadAttendanceBtn.addEventListener('click', loadAttendanceList);
    if (saveAttendanceBtn) saveAttendanceBtn.addEventListener('click', saveAttendance);
    if (loadGradesBtn) loadGradesBtn.addEventListener('click', loadGradesList);
    if (saveGradesBtn) saveGradesBtn.addEventListener('click', saveGrades);
    
    const attendanceDate = document.getElementById('attendanceDate');
    if (attendanceDate) attendanceDate.valueAsDate = new Date();
    
    populateCourseDropdowns();
    populateDepartmentDropdowns();
});

/**
 * Add loading indicator to page
 */
function addLoadingIndicator() {
    const loader = document.createElement('div');
    loader.id = 'loadingIndicator';
    loader.className = 'position-fixed top-50 start-50 translate-middle';
    loader.style.display = 'none';
    loader.style.zIndex = '10000';
    loader.innerHTML = `
        <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    document.body.appendChild(loader);
}

// =============================================================================
// NAVIGATION
// =============================================================================

function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    switch(sectionId) {
        case 'dashboard': updateDashboard(); break;
        case 'students': displayStudents(); break;
        case 'courses': displayCourses(); break;
        case 'attendance': populateCourseDropdowns(); break;
        case 'grades': populateCourseDropdowns(); break;
    }
}

// =============================================================================
// DASHBOARD FUNCTIONS
// =============================================================================

async function updateDashboard() {
    // Reload data to get latest stats
    await loadAllData();
    
    document.getElementById('totalStudents').textContent = students.length;
    document.getElementById('totalCourses').textContent = courses.length;
    document.getElementById('avgAttendance').textContent = calculateAverageAttendance() + '%';
    document.getElementById('avgGrade').textContent = calculateAverageGrade();
    displayRecentStudents();
    updateCharts();
}

function calculateAverageAttendance() {
    if (attendance.length === 0) return 0;
    const presentCount = attendance.filter(record => 
        record.status === 'present' || record.status === 'P'
    ).length;
    return Math.round((presentCount / attendance.length) * 100);
}

function calculateAverageGrade() {
    if (grades.length === 0) return '0.00';
    const total = grades.reduce((sum, record) => sum + parseFloat(record.score || 0), 0);
    return (total / grades.length).toFixed(2);
}

function displayRecentStudents() {
    const tbody = document.getElementById('recentStudentsTable');
    if (!tbody) return;
    
    const recentStudents = students.slice(0, 5);
    
    if (recentStudents.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No students found</td></tr>';
        return;
    }
    
    tbody.innerHTML = recentStudents.map(student => {
        const deptName = getDepartmentName(student.department);
        return `
            <tr>
                <td>${student.student_id}</td>
                <td>${student.first_name} ${student.last_name}</td>
                <td>${deptName}</td>
                <td>Year ${student.year || 'N/A'}</td>
                <td><span class="badge status-${student.status || 'active'}">${student.status || 'active'}</span></td>
            </tr>
        `;
    }).join('');
}

function getDepartmentName(deptId) {
    const dept = departments.find(d => d.id === deptId);
    return dept ? dept.name : 'Unknown';
}

function updateCharts() {
    // Department distribution chart
    const deptCounts = {};
    students.forEach(student => {
        const deptName = getDepartmentName(student.department);
        deptCounts[deptName] = (deptCounts[deptName] || 0) + 1;
    });
    
    const deptCtx = document.getElementById('departmentChart');
    if (deptCtx) {
        if (window.deptChart) window.deptChart.destroy();
        
        window.deptChart = new Chart(deptCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(deptCounts),
                datasets: [{
                    data: Object.values(deptCounts),
                    backgroundColor: [
                        'rgba(13,110,253,0.8)', 
                        'rgba(25,135,84,0.8)', 
                        'rgba(255,193,7,0.8)', 
                        'rgba(220,53,69,0.8)', 
                        'rgba(13,202,240,0.8)'
                    ]
                }]
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: true, 
                plugins: { legend: { position: 'bottom' } } 
            }
        });
    }
    
    // Attendance trend chart
    const attCtx = document.getElementById('attendanceChart');
    if (attCtx) {
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
            options: { 
                responsive: true, 
                maintainAspectRatio: true, 
                scales: { y: { beginAtZero: true, max: 100 } }, 
                plugins: { legend: { display: false } } 
            }
        });
    }
}

// =============================================================================
// STUDENT MANAGEMENT FUNCTIONS
// =============================================================================

function displayStudents(filteredStudents = null) {
    const tbody = document.getElementById('studentsTableBody');
    if (!tbody) return;
    
    const studentsToDisplay = filteredStudents || students;
    
    if (studentsToDisplay.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">No students found</td></tr>';
        return;
    }
    
    tbody.innerHTML = studentsToDisplay.map(student => {
        const deptName = getDepartmentName(student.department);
        return `
            <tr>
                <td>${student.student_id}</td>
                <td>${student.first_name} ${student.last_name}</td>
                <td>${student.email}</td>
                <td>${deptName}</td>
                <td>Year ${student.year || 'N/A'}</td>
                <td>${student.phone || 'N/A'}</td>
                <td><span class="badge status-${student.status}">${student.status}</span></td>
                <td>
                    <button class="btn btn-sm btn-info btn-action" onclick="viewStudent('${student.student_id}')"><i class="bi bi-eye"></i></button>
                    <button class="btn btn-sm btn-warning btn-action" onclick="editStudent('${student.student_id}')"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-danger btn-action" onclick="deleteStudent('${student.student_id}')"><i class="bi bi-trash"></i></button>
                </td>
            </tr>
        `;
    }).join('');
}

async function saveStudent() {
    const form = document.getElementById('studentForm');
    if (!form) return;
    
    const formData = new FormData(form);
    
    // Map frontend form fields to backend API fields
    const studentData = {
        student_id: formData.get('studentId'),
        first_name: formData.get('name').split(' ')[0],
        last_name: formData.get('name').split(' ').slice(1).join(' ') || formData.get('name').split(' ')[0],
        email: formData.get('email'),
        phone: formData.get('phone'),
        date_of_birth: formData.get('dob'),
        gender: formData.get('gender'),
        address: formData.get('address'),
        department: parseInt(formData.get('department')), // Department ID
        year: parseInt(formData.get('year')),
        status: formData.get('status') || 'enrolled'
    };
    
    try {
        if (currentStudentId) {
            // Update existing student
            await apiCall(`${API_ENDPOINTS.students}${currentStudentId}/`, 'PATCH', studentData);
            showAlert('Student updated successfully!', 'success');
        } else {
            // Create new student
            await apiCall(API_ENDPOINTS.students, 'POST', studentData);
            showAlert('Student created successfully!', 'success');
        }
        
        // Reload students
        await loadStudents();
        
        // Close modal and reset form
        const modal = bootstrap.Modal.getInstance(document.getElementById('addStudentModal'));
        if (modal) modal.hide();
        form.reset();
        currentStudentId = null;
        
        // Refresh display
        displayStudents();
        updateDashboard();
        
    } catch (error) {
        console.error('Error saving student:', error);
    }
}

async function editStudent(studentId) {
    const student = students.find(s => s.student_id === studentId);
    if (!student) return;
    
    const form = document.getElementById('studentForm');
    if (!form) return;
    
    // Populate form with student data
    form.elements['studentId'].value = student.student_id;
    form.elements['name'].value = `${student.first_name} ${student.last_name}`;
    form.elements['email'].value = student.email;
    form.elements['phone'].value = student.phone || '';
    form.elements['department'].value = student.department;
    form.elements['year'].value = student.year || '';
    form.elements['dob'].value = student.date_of_birth || '';
    form.elements['gender'].value = student.gender || '';
    form.elements['address'].value = student.address || '';
    form.elements['status'].value = student.status;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('addStudentModal'));
    document.querySelector('#addStudentModal .modal-title').textContent = 'Edit Student';
    modal.show();
    
    currentStudentId = studentId;
}

async function deleteStudent(studentId) {
    if (!confirm('Are you sure you want to delete this student?')) return;
    
    try {
        await apiCall(`${API_ENDPOINTS.students}${studentId}/`, 'DELETE');
        showAlert('Student deleted successfully!', 'success');
        
        // Reload students
        await loadStudents();
        displayStudents();
        updateDashboard();
        
    } catch (error) {
        console.error('Error deleting student:', error);
    }
}

function viewStudent(studentId) {
    const student = students.find(s => s.student_id === studentId);
    if (!student) return;
    
    const deptName = getDepartmentName(student.department);
    alert(`Student Details:\n\nID: ${student.student_id}\nName: ${student.first_name} ${student.last_name}\nEmail: ${student.email}\nDepartment: ${deptName}\nYear: ${student.year}\nPhone: ${student.phone || 'N/A'}\nDOB: ${student.date_of_birth || 'N/A'}\nGender: ${student.gender || 'N/A'}\nAddress: ${student.address || 'N/A'}\nStatus: ${student.status}`);
}

function filterStudents() {
    const searchTerm = document.getElementById('searchStudent')?.value.toLowerCase() || '';
    const deptFilter = document.getElementById('filterDepartment')?.value || '';
    const yearFilter = document.getElementById('filterYear')?.value || '';
    
    const filtered = students.filter(student => {
        const matchesSearch = searchTerm === '' || 
            student.student_id.toLowerCase().includes(searchTerm) ||
            `${student.first_name} ${student.last_name}`.toLowerCase().includes(searchTerm) ||
            student.email.toLowerCase().includes(searchTerm);
        
        const matchesDept = deptFilter === '' || student.department === parseInt(deptFilter);
        const matchesYear = yearFilter === '' || student.year === parseInt(yearFilter);
        
        return matchesSearch && matchesDept && matchesYear;
    });
    
    displayStudents(filtered);
}

function clearFilters() {
    const searchStudent = document.getElementById('searchStudent');
    const filterDepartment = document.getElementById('filterDepartment');
    const filterYear = document.getElementById('filterYear');
    
    if (searchStudent) searchStudent.value = '';
    if (filterDepartment) filterDepartment.value = '';
    if (filterYear) filterYear.value = '';
    
    displayStudents();
}

// =============================================================================
// COURSE MANAGEMENT FUNCTIONS
// =============================================================================

function displayCourses() {
    const tbody = document.getElementById('coursesTableBody');
    if (!tbody) return;
    
    if (courses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">No courses found</td></tr>';
        return;
    }
    
    tbody.innerHTML = courses.map(course => {
        const deptName = getDepartmentName(course.department);
        return `
            <tr>
                <td>${course.code}</td>
                <td>${course.name}</td>
                <td>${deptName}</td>
                <td>${course.credits}</td>
                <td>${course.description || 'N/A'}</td>
                <td>
                    <button class="btn btn-sm btn-info btn-action" onclick="viewCourse(${course.id})"><i class="bi bi-eye"></i></button>
                    <button class="btn btn-sm btn-warning btn-action" onclick="editCourse(${course.id})"><i class="bi bi-pencil"></i></button>
                    <button class="btn btn-sm btn-danger btn-action" onclick="deleteCourse(${course.id})"><i class="bi bi-trash"></i></button>
                </td>
            </tr>
        `;
    }).join('');
}

function viewCourse(courseId) {
    const course = courses.find(c => c.id === courseId);
    if (!course) return;
    
    const deptName = getDepartmentName(course.department);
    alert(`Course Details:\n\nCode: ${course.code}\nName: ${course.name}\nDepartment: ${deptName}\nCredits: ${course.credits}\nDescription: ${course.description || 'N/A'}`);
}

function editCourse(courseId) {
    showAlert('Course editing feature - to be implemented', 'info');
}

async function deleteCourse(courseId) {
    if (!confirm('Are you sure you want to delete this course?')) return;
    
    try {
        await apiCall(`${API_ENDPOINTS.courses}${courseId}/`, 'DELETE');
        showAlert('Course deleted successfully!', 'success');
        await loadCourses();
        displayCourses();
    } catch (error) {
        console.error('Error deleting course:', error);
    }
}

// =============================================================================
// ATTENDANCE FUNCTIONS
// =============================================================================

function populateCourseDropdowns() {
    const attendanceCourseSelect = document.getElementById('attendanceCourse');
    const gradesCourseSelect = document.getElementById('gradesCourse');
    
    const courseOptions = courseOfferings.map(offering => {
        const course = courses.find(c => c.id === offering.course);
        const courseName = course ? course.name : 'Unknown Course';
        return `<option value="${offering.id}">${courseName} (${offering.semester} ${offering.year})</option>`;
    }).join('');
    
    if (attendanceCourseSelect) {
        attendanceCourseSelect.innerHTML = '<option value="">Select Course</option>' + courseOptions;
    }
    
    if (gradesCourseSelect) {
        gradesCourseSelect.innerHTML = '<option value="">Select Course</option>' + courseOptions;
    }
}

function populateDepartmentDropdowns() {
    const filterDepartment = document.getElementById('filterDepartment');
    const studentFormDepartment = document.querySelector('#studentForm select[name="department"]');
    
    const deptOptions = departments.map(dept => 
        `<option value="${dept.id}">${dept.name}</option>`
    ).join('');
    
    if (filterDepartment) {
        filterDepartment.innerHTML = '<option value="">All Departments</option>' + deptOptions;
    }
    
    if (studentFormDepartment) {
        studentFormDepartment.innerHTML = '<option value="">Select Department</option>' + deptOptions;
    }
}

async function loadAttendanceList() {
    const courseOfferingId = document.getElementById('attendanceCourse')?.value;
    const date = document.getElementById('attendanceDate')?.value;
    
    if (!courseOfferingId) {
        showAlert('Please select a course', 'warning');
        return;
    }
    
    // Get enrollments for this course offering
    const courseEnrollments = enrollments.filter(e => e.course_offering === parseInt(courseOfferingId));
    
    const container = document.getElementById('attendanceList');
    if (!container) return;
    
    if (courseEnrollments.length === 0) {
        container.innerHTML = '<p class="text-center">No students enrolled in this course</p>';
        return;
    }
    
    container.innerHTML = courseEnrollments.map(enrollment => {
        const student = students.find(s => s.id === enrollment.student);
        if (!student) return '';
        
        return `
            <div class="attendance-item">
                <span>${student.student_id} - ${student.first_name} ${student.last_name}</span>
                <div class="btn-group" role="group">
                    <input type="radio" class="btn-check" name="attendance_${enrollment.id}" id="present_${enrollment.id}" value="present" checked>
                    <label class="btn btn-outline-success" for="present_${enrollment.id}">Present</label>
                    
                    <input type="radio" class="btn-check" name="attendance_${enrollment.id}" id="absent_${enrollment.id}" value="absent">
                    <label class="btn btn-outline-danger" for="absent_${enrollment.id}">Absent</label>
                    
                    <input type="radio" class="btn-check" name="attendance_${enrollment.id}" id="late_${enrollment.id}" value="late">
                    <label class="btn btn-outline-warning" for="late_${enrollment.id}">Late</label>
                    
                    <input type="radio" class="btn-check" name="attendance_${enrollment.id}" id="excused_${enrollment.id}" value="excused">
                    <label class="btn btn-outline-info" for="excused_${enrollment.id}">Excused</label>
                </div>
            </div>
        `;
    }).join('');
}

async function saveAttendance() {
    const courseOfferingId = document.getElementById('attendanceCourse')?.value;
    const date = document.getElementById('attendanceDate')?.value;
    
    if (!courseOfferingId || !date) {
        showAlert('Please select course and date', 'warning');
        return;
    }
    
    const courseEnrollments = enrollments.filter(e => e.course_offering === parseInt(courseOfferingId));
    
    try {
        const attendanceRecords = [];
        
        for (const enrollment of courseEnrollments) {
            const statusElement = document.querySelector(`input[name="attendance_${enrollment.id}"]:checked`);
            if (statusElement) {
                const record = {
                    enrollment: enrollment.id,
                    date: date,
                    status: statusElement.value,
                    notes: ''
                };
                attendanceRecords.push(record);
            }
        }
        
        // Save each attendance record
        for (const record of attendanceRecords) {
            await apiCall(API_ENDPOINTS.attendance, 'POST', record);
        }
        
        showAlert(`Attendance saved for ${attendanceRecords.length} students!`, 'success');
        await loadAttendanceRecords();
        
    } catch (error) {
        console.error('Error saving attendance:', error);
    }
}

// =============================================================================
// GRADES FUNCTIONS
// =============================================================================

async function loadGradesList() {
    const courseOfferingId = document.getElementById('gradesCourse')?.value;
    
    if (!courseOfferingId) {
        showAlert('Please select a course', 'warning');
        return;
    }
    
    const courseEnrollments = enrollments.filter(e => e.course_offering === parseInt(courseOfferingId));
    
    const container = document.getElementById('gradesList');
    if (!container) return;
    
    if (courseEnrollments.length === 0) {
        container.innerHTML = '<p class="text-center">No students enrolled in this course</p>';
        return;
    }
    
    container.innerHTML = courseEnrollments.map(enrollment => {
        const student = students.find(s => s.id === enrollment.student);
        if (!student) return '';
        
        return `
            <div class="grade-item">
                <span>${student.student_id} - ${student.first_name} ${student.last_name}</span>
                <div class="input-group" style="width: 200px;">
                    <input type="number" class="form-control" id="grade_${enrollment.id}" min="0" max="100" placeholder="Grade">
                    <span class="input-group-text">%</span>
                </div>
            </div>
        `;
    }).join('');
}

async function saveGrades() {
    const courseOfferingId = document.getElementById('gradesCourse')?.value;
    
    if (!courseOfferingId) {
        showAlert('Please select course', 'warning');
        return;
    }
    
    const courseEnrollments = enrollments.filter(e => e.course_offering === parseInt(courseOfferingId));
    
    showAlert('Grades saving functionality requires assessment setup in admin panel', 'info');
}

// =============================================================================
// MODAL HANDLERS
// =============================================================================

// Reset form when modal is closed
document.getElementById('addStudentModal')?.addEventListener('hidden.bs.modal', function() {
    document.getElementById('studentForm')?.reset();
    document.querySelector('#addStudentModal .modal-title').textContent = 'Add New Student';
    currentStudentId = null;
});

// Handle form submission
document.getElementById('studentForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    saveStudent();
});

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Format date to readable string
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

/**
 * Get status badge class
 */
function getStatusClass(status) {
    const statusMap = {
        'active': 'success',
        'enrolled': 'success',
        'inactive': 'secondary',
        'suspended': 'danger',
        'graduated': 'info'
    };
    return statusMap[status?.toLowerCase()] || 'secondary';
}

console.log('Student MIS - Backend Integrated Version Loaded Successfully!');
console.log('API Base URL:', API_BASE_URL);
console.log('Ready to connect to Django backend...');
