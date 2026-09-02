from django.core.management.base import BaseCommand
from portal.models import *

class Command(BaseCommand):
    help = 'Populate database with university data'

    def handle(self, *args, **options):
        # Clear existing data
        self.stdout.write('Clearing existing data...')
        Prereq.objects.all().delete()
        Advisor.objects.all().delete()
        Teaches.objects.all().delete()
        Takes.objects.all().delete()
        Section.objects.all().delete()
        TimeSlot.objects.all().delete()
        Student.objects.all().delete()
        Instructor.objects.all().delete()
        Course.objects.all().delete()
        Classroom.objects.all().delete()
        Department.objects.all().delete()
        
        self.stdout.write('Inserting all university data...')

        # Insert departments
        departments = [
            ('Biology', 'Watson', 90000),
            ('Comp. Sci.', 'Taylor', 100000),
            ('Elec. Eng.', 'Taylor', 85000),
            ('Finance', 'Painter', 120000),
            ('History', 'Painter', 50000),
            ('Music', 'Packard', 80000),
            ('Physics', 'Watson', 70000)
        ]
        
        for dept_name, building, budget in departments:
            Department.objects.create(dept_name=dept_name, building=building, budget=budget)
        self.stdout.write('Departments inserted')

        # Insert classrooms
        classrooms = [
            ('Packard', '101', 500),
            ('Painter', '514', 10),
            ('Taylor', '3128', 70),
            ('Watson', '100', 30),
            ('Watson', '120', 50)
        ]
        
        for building, room_no, capacity in classrooms:
            Classroom.objects.create(building=building, room_no=room_no, capacity=capacity)

        # Insert courses
        courses = [
            ('BIO-101', 'Intro. to Biology', 'Biology', 4),
            ('BIO-301', 'Genetics', 'Biology', 4),
            ('BIO-399', 'Computational Biology', 'Biology', 3),
            ('CS-101', 'Intro. to Computer Science', 'Comp. Sci.', 4),
            ('CS-190', 'Game Design', 'Comp. Sci.', 4),
            ('CS-315', 'Robotics', 'Comp. Sci.', 3),
            ('CS-319', 'Image Processing', 'Comp. Sci.', 3),
            ('CS-347', 'Database System Concepts', 'Comp. Sci.', 3),
            ('EE-181', 'Intro. to Digital Systems', 'Elec. Eng.', 3),
            ('FIN-201', 'Investment Banking', 'Finance', 3),
            ('HIS-351', 'World History', 'History', 3),
            ('MU-199', 'Music Video Production', 'Music', 3),
            ('PHY-101', 'Physical Principles', 'Physics', 4)
        ]
        
        for course_id, title, dept_name, credits in courses:
            dept = Department.objects.get(dept_name=dept_name)
            Course.objects.create(course_id=course_id, title=title, dept_name=dept, credits=credits)

        # Insert instructors
        instructors = [
            (10101, 'Srinivasan', 'Comp. Sci.', 65000),
            (12121, 'Wu', 'Finance', 90000),
            (15151, 'Mozart', 'Music', 40000),
            (22222, 'Einstein', 'Physics', 95000),
            (32343, 'El Said', 'History', 60000),
            (33456, 'Gold', 'Physics', 87000),
            (45565, 'Katz', 'Comp. Sci.', 75000),
            (58583, 'Califieri', 'History', 62000),
            (76543, 'Singh', 'Finance', 80000),
            (76766, 'Crick', 'Biology', 72000),
            (83821, 'Brandt', 'Comp. Sci.', 92000),
            (98345, 'Kim', 'Elec. Eng.', 80000)
        ]
        
        for ID, name, dept_name, salary in instructors:
            dept = Department.objects.get(dept_name=dept_name)
            Instructor.objects.create(ID=ID, name=name, dept_name=dept, salary=salary)

        # Insert students
        students = [
            (128, 'Zhang', 'Comp. Sci.', 102),
            (12345, 'Shankar', 'Comp. Sci.', 32),
            (19991, 'Brandt', 'History', 80),
            (23121, 'Chavez', 'Finance', 110),
            (44553, 'Peltier', 'Physics', 56),
            (45678, 'Levy', 'Physics', 46),
            (54321, 'Williams', 'Comp. Sci.', 54),
            (55739, 'Sanchez', 'Music', 38),
            (70557, 'Snow', 'Physics', 0),
            (76543, 'Brown', 'Comp. Sci.', 58),
            (76653, 'Aoi', 'Elec. Eng.', 60),
            (98765, 'Bourikas', 'Elec. Eng.', 98),
            (98988, 'Tanaka', 'Biology', 120)
        ]
        
        for ID, name, dept_name, tot_cred in students:
            dept = Department.objects.get(dept_name=dept_name)
            Student.objects.create(ID=ID, name=name, dept_name=dept, tot_cred=tot_cred)

        # Insert time slots
        time_slots = [
            (31, 'M', 8, 9), (32, 'W', 8, 9), (33, 'F', 8, 9),
            (34, 'M', 9, 10), (35, 'W', 9, 10), (36, 'F', 9, 10),
            (37, 'M', 11, 12), (38, 'W', 11, 12), (39, 'F', 11, 12),
            (40, 'M', 13, 14), (41, 'W', 13, 14), (42, 'F', 13, 14),
            (43, 'T', 10, 11), (44, 'R', 10, 11), (45, 'T', 14, 15)
        ]
        
        for time_slot_id, day, start_time, end_time in time_slots:
            TimeSlot.objects.create(time_slot_id=time_slot_id, day=day, start_time=start_time, end_time=end_time)

        # Insert sections
        sections = [
            ('BIO-101', '1', 'Summer', 2009, 'Painter', '514', 31),
            ('BIO-301', '1', 'Summer', 2010, 'Painter', '514', 32),
            ('CS-101', '1', 'Fall', 2010, 'Packard', '101', 34),
            ('CS-101', '1', 'Spring', 2010, 'Packard', '101', 33),
            ('CS-190', '1', 'Spring', 2009, 'Taylor', '3128', 35),
            ('CS-190', '2', 'Spring', 2009, 'Taylor', '3128', 36),
            ('CS-315', '1', 'Spring', 2010, 'Taylor', '3128', 37),
            ('CS-319', '1', 'Spring', 2010, 'Watson', '120', 38),
            ('CS-319', '2', 'Spring', 2010, 'Watson', '100', 39),
            ('CS-347', '1', 'Fall', 2009, 'Taylor', '3128', 40),
            ('EE-181', '1', 'Spring', 2009, 'Taylor', '3128', 41),
            ('FIN-201', '1', 'Spring', 2010, 'Packard', '101', 42),
            ('HIS-351', '1', 'Spring', 2010, 'Painter', '514', 43),
            ('MU-199', '1', 'Spring', 2010, 'Packard', '101', 44),
            ('PHY-101', '1', 'Fall', 2009, 'Watson', '100', 45)
        ]
        
        for course_id, sec_id, semester, year, building, room_no, time_slot_id in sections:
            course = Course.objects.get(course_id=course_id)
            Section.objects.create(course_id=course, sec_id=sec_id, semester=semester, year=year, 
                                 building=building, room_no=room_no, time_slot_id=time_slot_id)

        # Insert teaches records
        teaches_data = [
            (10101, 'CS-101', '1', 'Fall', 2010),
            (10101, 'CS-315', '1', 'Spring', 2010),
            (10101, 'CS-347', '1', 'Fall', 2009),
            (12121, 'FIN-201', '1', 'Spring', 2010),
            (15151, 'MU-199', '1', 'Spring', 2010),
            (22222, 'PHY-101', '1', 'Fall', 2009),
            (32343, 'HIS-351', '1', 'Spring', 2010),
            (45565, 'CS-101', '1', 'Spring', 2010),
            (45565, 'CS-319', '1', 'Spring', 2010),
            (76766, 'BIO-101', '1', 'Summer', 2009),
            (76766, 'BIO-301', '1', 'Summer', 2010),
            (83821, 'CS-190', '1', 'Spring', 2009),
            (83821, 'CS-190', '2', 'Spring', 2009),
            (83821, 'CS-319', '2', 'Spring', 2010),
            (98345, 'EE-181', '1', 'Spring', 2009)
        ]
        
        for ID, course_id, sec_id, semester, year in teaches_data:
            instructor = Instructor.objects.get(ID=ID)
            Teaches.objects.create(ID=instructor, course_id=course_id, sec_id=sec_id, 
                                 semester=semester, year=year)

        # Insert takes records
        takes_data = [
            (128, 'CS-101', '1', 'Fall', 2010, 'A'),
            (128, 'CS-347', '1', 'Fall', 2009, 'A-'),
            (12345, 'CS-101', '1', 'Fall', 2010, 'C'),
            (12345, 'CS-190', '2', 'Spring', 2009, 'A'),
            (12345, 'CS-315', '1', 'Spring', 2010, 'A'),
            (12345, 'CS-347', '1', 'Fall', 2009, 'B'),
            (19991, 'HIS-351', '1', 'Spring', 2010, 'B'),
            (23121, 'FIN-201', '1', 'Spring', 2010, 'C+'),
            (44553, 'PHY-101', '1', 'Fall', 2009, 'B-'),
            (45678, 'CS-101', '1', 'Fall', 2010, 'F'),
            (45678, 'CS-319', '1', 'Spring', 2010, 'B+'),
            (54321, 'CS-101', '1', 'Spring', 2010, 'B'),
            (54321, 'CS-190', '2', 'Spring', 2009, 'A-'),
            (55739, 'MU-199', '1', 'Spring', 2010, 'A-'),
            (76543, 'CS-101', '1', 'Fall', 2010, 'A'),
            (76653, 'EE-181', '1', 'Spring', 2009, 'C-'),
            (98765, 'CS-101', '1', 'Fall', 2010, 'B'),
            (98765, 'CS-315', '1', 'Spring', 2010, 'A'),
            (98988, 'BIO-101', '1', 'Summer', 2009, 'A'),
            (98988, 'BIO-301', '1', 'Summer', 2010, 'F')
        ]
        
        for ID, course_id, sec_id, semester, year, grade in takes_data:
            student = Student.objects.get(ID=ID)
            Takes.objects.create(ID=student, course_id=course_id, sec_id=sec_id, 
                               semester=semester, year=year, grade=grade)

        # Insert advisor records
        advisor_data = [
            (128, 45565),
            (12345, 10101),
            (23121, 76543),
            (44553, 22222),
            (45678, 22222),
            (76543, 45565),
            (76653, 98345),
            (98988, 76766),
            (98765, 98345)
        ]
        
        for s_id, i_id in advisor_data:
            student = Student.objects.get(ID=s_id)
            instructor = Instructor.objects.get(ID=i_id)
            Advisor.objects.create(s_id=student, i_id=instructor)

        # Insert prereq records
        prereq_data = [
            ('BIO-301', 'BIO-101'),
            ('BIO-399', 'BIO-101'),
            ('CS-190', 'CS-101'),
            ('CS-315', 'CS-101'),
            ('CS-319', 'CS-101'),
            ('CS-347', 'CS-101'),
            ('EE-181', 'PHY-101')
        ]
        
        for course_id, prereq_id in prereq_data:
            course = Course.objects.get(course_id=course_id)
            prereq_course = Course.objects.get(course_id=prereq_id)
            Prereq.objects.create(course_id=course, prereq_id=prereq_course)

        self.stdout.write(self.style.SUCCESS('Successfully populated database with all university data'))