from django.shortcuts import render
from django.db.models import Avg, Max
from .models import Student
import numpy as np


def student_list(request):
    students = Student.objects.all()
    return render(request, "student_list.html", {"students": students})


def topper_view(request):
    # Subject toppers
    math_topper = Student.objects.order_by("-math").first()
    phy_topper = Student.objects.order_by("-phy").first()
    chem_topper = Student.objects.order_by("-chem").first()

    # Add a total and average per student
    for student in Student.objects.all():
        student.total = student.math + student.phy + student.chem
        student.average = round(student.total / 3, 2)

    # Class topper (highest average)
    class_topper = max(Student.objects.all(), key=lambda s: (s.math + s.phy + s.chem) / 3)

    # Class average per subject
    subject_averages = Student.objects.aggregate(
        avg_math=Avg("math"),
        avg_phy=Avg("phy"),
        avg_chem=Avg("chem"),
    )

    context = {
        "math_topper": math_topper,
        "phy_topper": phy_topper,
        "chem_topper": chem_topper,
        "class_topper": class_topper,
        "subject_averages": subject_averages,
    }
    return render(request, "topper.html", context)


from django.http import HttpResponse

# Example view to display a message
def home(request):
    return render(request, "home.html")


# Another example view
def show_message(request):
    return HttpResponse("<h1>This is displayed on the frontend!</h1>")



def view_numpy(request):
    # Sample arrays
    array_a = np.array([1, 2, 3, 4, 5])
    array_b = np.arange(5, 11)  # 5,6,7,8,9,10
    array_2d = np.array([[1,2,3],[4,5,6],[7,8,9]])

    # Prepare results (convert ndarrays to lists)
    results = {
        # Basic arrays
        "array_a": array_a.tolist(),
        "array_b": array_b.tolist(),
        "array_2d": array_2d.tolist(),

        # Shapes and dimensions
        "shape_array_a": array_a.shape,
        "shape_array_b": array_b.shape,
        "shape_array_2d": array_2d.shape,
        "ndim_array_2d": array_2d.ndim,
        "size_array_2d": array_2d.size,

        # Statistics
        "sum_array_a": int(array_a.sum()),
        "mean_array_b": float(array_b.mean()),
        "max_array_2d": int(array_2d.max()),
        "min_array_2d": int(array_2d.min()),
        "average_array_2d": float(array_2d.mean()),

        # Transformations
        "array_2d_transpose": array_2d.T.tolist(),
        "array_a_squared": (array_a**2).tolist(),
        "array_b_sorted": np.sort(array_b).tolist(),
        "array_b_descending": np.sort(array_b)[::-1].tolist(),

        # Random numbers
        "random_array": np.random.randint(0, 100, size=5).tolist(),

        # Linear algebra
        "dot_product": int(np.dot(array_a[:3], array_2d[:,0])),

        # Stacking
        "stacked_arrays": np.vstack([array_a, array_b[:5]]).tolist(),

        # Slicing
        "array_a_slice": array_a[1:4].tolist(),
    }

    return render(request, "view_numpy.html", {"results": results})



def view_sggs(request):
    return render(request, "sggs.html")



def view_search_database_by_name(request):
    student = None
    query = ""
    message = ""

    if request.method == "POST":
        query = request.POST.get("search_name", "").strip()

        if query:
            try:
                student = Student.objects.get(student_name__iexact=query)

                # Calculate total and average
                student.total = student.math + student.phy + student.chem
                student.average = round(student.total / 3, 2)
            except Student.DoesNotExist:
                message = f"No record found for '{query}'"
        else:
            message = "Please enter a student name."

    context = {
        "student": student,
        "query": query,
        "message": message,
    }
    return render(request, "search_database_by_name.html", context)