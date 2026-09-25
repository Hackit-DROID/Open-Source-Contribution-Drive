from django.db import models
class Student(models.Model):
         Student_name = models.CharField(max_length=122)
         Reg_No = models.CharField(max_length=122)
         Address= models.CharField(max_length=122)
         Taluka = models.CharField(max_length=122)
         District = models.CharField(max_length=122)
         State = models.CharField(max_length=122)
         Photo = models.ImageField(upload_to='images')  
         Pincode = models.IntegerField(max_length=6)
       
         def __str__(self):
             return self.Student_name

class Admission(models.Model):
    Reg_no = models.CharField( max_length=120)
    Student_name = models.CharField( max_length=120)
    Branch = models.CharField( max_length=50)
    
    Class = models.CharField( max_length= 50)
    Year = models.IntegerField( max_length= 10)
    Date_of_admission = models.IntegerField (max_length= 20)
    Semester = models.CharField (max_length= 20)
    Student = models.ForeignKey(Student, blank=True,null=True, on_delete=models.CASCADE)

    def __str__(self):
	    return self.Reg_no
    
  

class marks(models.Model):

    Reg_no = models.CharField(max_length=12) 
    Subject = models.CharField(max_length=122) 
    Student = models.ForeignKey(Student, blank=True,null=True, on_delete=models.CASCADE)
    marks = models.IntegerField(max_length=122)
    Semester = models.CharField(max_length=122)
    Year = models.IntegerField(max_length=122)
    def __str__(self):
             return self.Reg_no

class Feedback(models.Model):
    Reg_no=models.CharField(max_length=12)
    Subject=models.CharField(max_length=122)
    Feedback=models.TextField()
    def __str__(self):
             return self.Reg_no
  

# Create your models here.
