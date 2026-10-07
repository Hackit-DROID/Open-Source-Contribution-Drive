from django.db import models

class Department(models.Model):
    dept_name = models.CharField(max_length=20, primary_key=True)
    building = models.CharField(max_length=20, db_index=True)
    budget = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['building'], name='dept_building_idx'),
        ]

    def __str__(self):
        return self.dept_name

class Classroom(models.Model):
    building = models.CharField(max_length=20)
    room_no = models.CharField(max_length=20)
    capacity = models.IntegerField()

    class Meta:
        unique_together = ('building', 'room_no')

    def __str__(self):
        return f"{self.building} {self.room_no}"

class Course(models.Model):
    course_id = models.CharField(max_length=10, primary_key=True)
    title = models.CharField(max_length=50, db_index=True)
    dept_name = models.ForeignKey(Department, on_delete=models.CASCADE, db_index=True)
    credits = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['title'], name='course_title_idx'),
            models.Index(fields=['dept_name'], name='course_dept_idx'),
        ]

    def __str__(self):
        return f"{self.course_id} - {self.title}"

class Instructor(models.Model):
    ID = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30, db_index=True)
    dept_name = models.ForeignKey(Department, on_delete=models.CASCADE, db_index=True)
    salary = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['name'], name='instructor_name_idx'),
            models.Index(fields=['dept_name'], name='instructor_dept_idx'),
        ]

    def __str__(self):
        return self.name

class Student(models.Model):
    ID = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30, db_index=True)
    dept_name = models.ForeignKey(Department, on_delete=models.CASCADE, db_index=True)
    tot_cred = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['name'], name='student_name_idx'),
            models.Index(fields=['dept_name'], name='student_dept_idx'),
        ]

    def __str__(self):
        return self.name

class TimeSlot(models.Model):
    time_slot_id = models.IntegerField(db_index=True)
    day = models.CharField(max_length=10)
    start_time = models.IntegerField()
    end_time = models.IntegerField()

    class Meta:
        unique_together = ('time_slot_id', 'day', 'start_time')
        indexes = [
            models.Index(fields=['time_slot_id'], name='timeslot_id_idx'),
        ]

    def __str__(self):
        return f"Slot {self.time_slot_id} - {self.day} {self.start_time}-{self.end_time}"

class Section(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE, db_index=True)
    sec_id = models.CharField(max_length=10)
    semester = models.CharField(max_length=6)
    year = models.IntegerField()
    building = models.CharField(max_length=20)
    room_no = models.CharField(max_length=20)
    time_slot_id = models.IntegerField(db_index=True)

    class Meta:
        unique_together = ('course_id', 'sec_id', 'semester', 'year')
        indexes = [
            models.Index(fields=['course_id'], name='section_course_idx'),
            models.Index(fields=['time_slot_id'], name='section_timeslot_idx'),
        ]

    def __str__(self):
        return f"{self.course_id} - {self.sec_id} ({self.semester} {self.year})"

class Takes(models.Model):
    ID = models.ForeignKey(Student, on_delete=models.CASCADE, db_index=True)
    course_id = models.CharField(max_length=10, db_index=True)
    sec_id = models.CharField(max_length=10)
    semester = models.CharField(max_length=6)
    year = models.IntegerField()
    grade = models.CharField(max_length=2)

    class Meta:
        unique_together = ('ID', 'course_id', 'sec_id', 'semester', 'year')
        indexes = [
            models.Index(fields=['ID'], name='takes_student_idx'),
            models.Index(fields=['course_id'], name='takes_course_idx'),
        ]

class Teaches(models.Model):
    ID = models.ForeignKey(Instructor, on_delete=models.CASCADE, db_index=True)
    course_id = models.CharField(max_length=10, db_index=True)
    sec_id = models.CharField(max_length=10)
    semester = models.CharField(max_length=6)
    year = models.IntegerField()

    class Meta:
        unique_together = ('ID', 'course_id', 'sec_id', 'semester', 'year')
        indexes = [
            models.Index(fields=['ID'], name='teaches_inst_idx'),
            models.Index(fields=['course_id'], name='teaches_course_idx'),
        ]

class Advisor(models.Model):
    s_id = models.ForeignKey(Student, on_delete=models.CASCADE, primary_key=True)
    i_id = models.ForeignKey(Instructor, on_delete=models.CASCADE)

class Prereq(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='prerequisites')
    prereq_id = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='required_for')

    class Meta:
        unique_together = ('course_id', 'prereq_id')