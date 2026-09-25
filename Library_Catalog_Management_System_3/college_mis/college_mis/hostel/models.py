from django.db import models
from student.models import Student  # only if you want a relation

class Hostel(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    room_no = models.CharField(max_length=10)
    block = models.CharField(max_length=50)
    warden_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.student.name} - Room {self.room_no}"
