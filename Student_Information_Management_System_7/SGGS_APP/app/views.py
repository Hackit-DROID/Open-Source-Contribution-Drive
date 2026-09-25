from django.shortcuts import render
from django.http import HttpResponse
from .models import Student
import numpy  as np


def show_toppers(request):
    students = Student.objects.all()

    # Subject toppers
    topper_phy = students.order_by('-phy').first()
    topper_chem = students.order_by('-chem').first()
    topper_math = students.order_by('-math').first()

    # Average per student
    student_averages = []
    for s in students:
        avg = (s.phy + s.chem + s.math) / 3
        student_averages.append({
            'student': s,
            'average': avg
        })

    # Overall topper by average
    overall_topper = max(student_averages, key=lambda x: x['average']) if student_averages else None

    context = {
        'students': students,
        'topper_phy': topper_phy,
        'topper_chem': topper_chem,
        'topper_math': topper_math,
        'student_averages': student_averages,
        'overall_topper': overall_topper,
    }

    return render(request, "show_toppers.html", context)

def hello_user(request):
    username = None
    message = "Welcome new user"
    
    if request.method == "POST":
        username = request.POST.get('username')
        if username:
            message = f"Hey {username}, welcome!!"
    
    return render(request, 'hello_user.html', {'message': message})


def view_numpy(request):
    numpy_operations = [
        {"operation": "array()", "description": "Creates a NumPy array from list, tuple, etc.", "example": "np.array([1,2,3])"},
        {"operation": "arange()", "description": "Creates an array with evenly spaced values.", "example": "np.arange(0,10,2)"},
        {"operation": "reshape()", "description": "Reshapes an array without changing data.", "example": "arr.reshape(2,3)"},
        {"operation": "zeros()", "description": "Creates an array filled with zeros.", "example": "np.zeros((3,3))"},
        {"operation": "ones()", "description": "Creates an array filled with ones.", "example": "np.ones((2,4))"},
        {"operation": "linspace()", "description": "Creates an array with linearly spaced values.", "example": "np.linspace(0,1,5)"},
        {"operation": "max()/min()", "description": "Returns max or min value of an array.", "example": "arr.max(), arr.min()"},
        {"operation": "sum()", "description": "Returns sum of all array elements.", "example": "arr.sum()"},
    ]
    return render(request, 'view_numpy.html', {'numpy_operations': numpy_operations})



from django.shortcuts import render
from .models import Student   # import your model
from django.http import HttpResponse


def view_student(request):
    # fetch all records from Student table
    students = Student.objects.all()

    # pass the records to the template
    return render(request, "view_student.html", {"students": students})



from django.shortcuts import render
from .models import Student

def search_student(request):
    query = request.GET.get('student_name', '')  # Get search input from GET
    if query:
        # Filter students whose name contains query (case-insensitive)
        students = Student.objects.filter(student_name__icontains=query)
    else:
        students = Student.objects.all()

    return render(request, 'search_student.html', {
        'students': students,
        'search_query': query  # fixed non-breaking space issue
    })

from django.http import HttpResponse

def home(request):
    html_content = """
    <!DOCTYPE html>
<html>
<head>
    <title>Student Portal - Home</title>
    <style>
        body {
            margin: 0;
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background-color: #f9fbfd; /* very light blue background */
            color: #333;
        }

        /* Navbar */
        .navbar {
            background: linear-gradient(90deg, #004e92, #000428);
            color: white;
            padding: 15px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 3px 8px rgba(0,0,0,0.2);
        }

        .navbar h2 {
            margin: 0;
            font-size: 24px;
            font-weight: bold;
        }

        .navbar a {
            color: white;
            text-decoration: none;
            margin-left: 20px;
            font-weight: 500;
            transition: color 0.3s;
        }

        .navbar a:hover {
            color: #ffd700; /* gold hover */
        }

        /* Hero Section */
        .hero {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 85vh;
            text-align: center;
            background: linear-gradient(135deg, #e0f7fa 0%, #e6eeff 100%);
            padding: 20px;
        }

        .hero h1 {
            font-size: 55px;
            color: #004e92;
            margin-bottom: 15px;
            text-shadow: 2px 2px 6px rgba(0,0,0,0.1);
        }

        .hero p {
            font-size: 22px;
            color: #333;
            margin-bottom: 50px;
        }

        /* Buttons Section */
        .hero-buttons {
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
            justify-content: center;
        }

        .hero-buttons a {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 220px;
            height: 120px;
            background: linear-gradient(135deg, #6dd5ed, #2193b0);
            color: white;
            font-weight: bold;
            font-size: 18px;
            text-decoration: none;
            border-radius: 14px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.15);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .hero-buttons a:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 25px rgba(0,0,0,0.25);
            background: linear-gradient(135deg, #2193b0, #6dd5ed);
        }

        /* Footer */
        .footer {
            background: #000428;
            color: white;
            text-align: center;
            padding: 12px;
            font-size: 14px;
        }

        @media (max-width: 768px) {
            .hero h1 {
                font-size: 36px;
            }
            .hero p {
                font-size: 16px;
            }
            .hero-buttons a {
                width: 160px;
                height: 100px;
                font-size: 15px;
            }
        }
    </style>
</head>
<body>

    <!-- Navbar -->
    <div class="navbar">
        <h2>Student Portal</h2>
        <div>
            <a href="/">Home</a>
            <a href="/view_student/">Students</a>
            <a href="/search_student/">Search</a>
            <a href="/show_toppers/">Toppers</a>
        </div>
    </div>

    <!-- Hero Section -->
    <div class="hero">
        <h1>Welcome to Student Portal</h1>
        <p>Explore students' details, view toppers, and discover more</p>
        <div class="hero-buttons">
            <a href="/hello_user/">👤 Hello User</a>
            <a href="/view_numpy/">📊 NumPy Table</a>
            <a href="/search_student/">🔍 Search Student</a>
            <a href="/view_student/">📋 All Students</a>
            <a href="/show_toppers/">🏆 View Toppers</a>
        </div>
    </div>

    <!-- Footer -->
    <div class="footer">
        © 2025 Student Portal | Designed with 💙 in Django
    </div>

</body>
</html>


    """
    return HttpResponse(html_content)


