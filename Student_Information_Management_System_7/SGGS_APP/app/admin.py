from django.contrib import admin
from .models import Student
# 
class StudentAdmin(admin.ModelAdmin):
    #show all fields explicitly
    list_display = ('regno','student_name','branch','phy','chem','math')

    #Add search functionality
    search_fields = ['student_name','branch']

    #Add filter options
    list_filter = ['branch']

    #Register model with custom admin
admin.site.register(Student, StudentAdmin)

