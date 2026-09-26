from django.db import models

class Hostel(models.Model):
    student_name = models.CharField(max_length=100)
    room_no = models.CharField(max_length=10)
    block = models.CharField(max_length=20)
    floor = models.IntegerField()
    warden_name = models.CharField(max_length=100)
    rent = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('Occupied', 'Occupied'), ('Vacant', 'Vacant'), ('Checked Out', 'Checked Out')])

    def __str__(self):
        return f"{self.student_name} - Room {self.room_no}"
