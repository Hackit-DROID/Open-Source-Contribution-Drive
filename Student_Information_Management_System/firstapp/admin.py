from django.contrib import admin
from .models import *
from firstapp.models import Student,Admission,Feedback,marks
# Register your models here.

# admin.site.register(BloodBank)
# admin.site.register(Demand)
# admin.site.register(Donor)
admin.site.register(Student)
admin.site.register(Admission)
admin.site.register(Feedback)
admin.site.register(marks)

# Register your models here.
