from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from .models import Student, Marks, Attendance


def home(request):
    """Home page with login options"""
    return render(request, 'students/home.html')


def admin_login(request):
    """Admin/Teacher Login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not authorized')
    
    return render(request, 'students/admin_login.html')


def student_login(request):
    """Student Login"""
    if request.method == 'POST':
        reg_no = request.POST.get('reg_no')
        password = request.POST.get('password')
        
        try:
            student = Student.objects.get(reg_no=reg_no)
            if student.password == password:
                request.session['student_id'] = student.reg_no
                messages.success(request, 'Logged in successfully!')
                return redirect('student_dashboard')
            else:
                messages.error(request, 'Invalid password')
        except Student.DoesNotExist:
            messages.error(request, 'Student not found')
    
    return render(request, 'students/student_login.html')


def logout_view(request):
    """Logout for both admin and student"""
    if 'student_id' in request.session:
        del request.session['student_id']
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('home')


@login_required
def admin_dashboard(request):
    """Admin Dashboard"""
    total_students = Student.objects.count()
    context = {
        'total_students': total_students,
    }
    return render(request, 'students/admin_dashboard.html', context)


@login_required
def student_list(request):
    """View all students with search functionality"""
    search_query = request.GET.get('search', '')
    
    if search_query:
        students = Student.objects.filter(
            Q(name__icontains=search_query) | 
            Q(reg_no__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    else:
        students = Student.objects.all()
    
    context = {
        'students': students,
        'search_query': search_query,
    }
    return render(request, 'students/student_list.html', context)


@login_required
def add_student(request):
    """Add new student"""
    if request.method == 'POST':
        try:
            student = Student(
                name=request.POST.get('name'),
                reg_no=request.POST.get('reg_no'),
                email=request.POST.get('email'),
                branch=request.POST.get('branch'),
                year=int(request.POST.get('year')),
                gender=request.POST.get('gender'),
                mobile=request.POST.get('mobile'),
                password=request.POST.get('password', 'student123')
            )
            student.save()
            
            # Create empty marks and attendance records
            Marks.objects.create(student=student)
            Attendance.objects.create(student=student)
            
            messages.success(request, f'Student {student.name} added successfully!')
            return redirect('student_list')
        except Exception as e:
            messages.error(request, f'Error adding student: {str(e)}')
    
    return render(request, 'students/add_student.html')


@login_required
def edit_student(request, reg_no):
    """Edit student details"""
    student = get_object_or_404(Student, reg_no=reg_no)
    
    if request.method == 'POST':
        try:
            student.name = request.POST.get('name')
            student.email = request.POST.get('email')
            student.branch = request.POST.get('branch')
            student.year = int(request.POST.get('year'))
            student.gender = request.POST.get('gender')
            student.mobile = request.POST.get('mobile')
            student.save()
            
            messages.success(request, 'Student details updated successfully!')
            return redirect('student_list')
        except Exception as e:
            messages.error(request, f'Error updating student: {str(e)}')
    
    context = {'student': student}
    return render(request, 'students/edit_student.html', context)


@login_required
def delete_student(request, reg_no):
    """Delete student"""
    student = get_object_or_404(Student, reg_no=reg_no)
    
    if request.method == 'POST':
        student_name = student.name
        student.delete()
        messages.success(request, f'Student {student_name} deleted successfully!')
        return redirect('student_list')
    
    context = {'student': student}
    return render(request, 'students/delete_student.html', context)


@login_required
def add_marks(request, reg_no):
    """Add/Update marks for a student"""
    student = get_object_or_404(Student, reg_no=reg_no)
    marks, created = Marks.objects.get_or_create(student=student)
    
    if request.method == 'POST':
        try:
            # Subject 1
            marks.subject1_name = request.POST.get('subject1_name')
            marks.subject1_ise1 = float(request.POST.get('subject1_ise1', 0))
            marks.subject1_mid = float(request.POST.get('subject1_mid', 0))
            marks.subject1_end = float(request.POST.get('subject1_end', 0))
            
            # Subject 2
            marks.subject2_name = request.POST.get('subject2_name')
            marks.subject2_ise1 = float(request.POST.get('subject2_ise1', 0))
            marks.subject2_mid = float(request.POST.get('subject2_mid', 0))
            marks.subject2_end = float(request.POST.get('subject2_end', 0))
            
            # Subject 3
            marks.subject3_name = request.POST.get('subject3_name')
            marks.subject3_ise1 = float(request.POST.get('subject3_ise1', 0))
            marks.subject3_mid = float(request.POST.get('subject3_mid', 0))
            marks.subject3_end = float(request.POST.get('subject3_end', 0))
            
            # Subject 4
            marks.subject4_name = request.POST.get('subject4_name')
            marks.subject4_ise1 = float(request.POST.get('subject4_ise1', 0))
            marks.subject4_mid = float(request.POST.get('subject4_mid', 0))
            marks.subject4_end = float(request.POST.get('subject4_end', 0))
            
            # Subject 5
            marks.subject5_name = request.POST.get('subject5_name')
            marks.subject5_ise1 = float(request.POST.get('subject5_ise1', 0))
            marks.subject5_mid = float(request.POST.get('subject5_mid', 0))
            marks.subject5_end = float(request.POST.get('subject5_end', 0))
            
            marks.save()
            messages.success(request, 'Marks updated successfully!')
            return redirect('student_list')
        except Exception as e:
            messages.error(request, f'Error updating marks: {str(e)}')
    
    context = {
        'student': student,
        'marks': marks
    }
    return render(request, 'students/add_marks.html', context)


@login_required
def add_attendance(request, reg_no):
    """Add/Update attendance for a student"""
    student = get_object_or_404(Student, reg_no=reg_no)
    attendance, created = Attendance.objects.get_or_create(student=student)
    
    if request.method == 'POST':
        try:
            attendance.total_classes = int(request.POST.get('total_classes', 0))
            attendance.classes_attended = int(request.POST.get('classes_attended', 0))
            attendance.update_percentage()
            
            messages.success(request, 'Attendance updated successfully!')
            return redirect('student_list')
        except Exception as e:
            messages.error(request, f'Error updating attendance: {str(e)}')
    
    context = {
        'student': student,
        'attendance': attendance
    }
    return render(request, 'students/add_attendance.html', context)


@login_required
def view_report(request, reg_no):
    """View complete report card for a student"""
    student = get_object_or_404(Student, reg_no=reg_no)
    marks = Marks.objects.filter(student=student).first()
    attendance = Attendance.objects.filter(student=student).first()
    
    subject_totals = marks.get_all_totals() if marks else {}
    overall_percentage = marks.get_overall_percentage() if marks else 0
    
    context = {
        'student': student,
        'marks': marks,
        'attendance': attendance,
        'subject_totals': subject_totals,
        'overall_percentage': overall_percentage,
    }
    return render(request, 'students/view_report.html', context)


def student_dashboard(request):
    """Student Dashboard"""
    if 'student_id' not in request.session:
        messages.error(request, 'Please login first')
        return redirect('student_login')
    
    reg_no = request.session['student_id']
    student = get_object_or_404(Student, reg_no=reg_no)
    marks = Marks.objects.filter(student=student).first()
    attendance = Attendance.objects.filter(student=student).first()
    
    subject_totals = marks.get_all_totals() if marks else {}
    overall_percentage = marks.get_overall_percentage() if marks else 0
    
    context = {
        'student': student,
        'marks': marks,
        'attendance': attendance,
        'subject_totals': subject_totals,
        'overall_percentage': overall_percentage,
    }
    return render(request, 'students/student_dashboard.html', context)
