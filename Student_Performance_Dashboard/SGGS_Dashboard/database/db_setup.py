import sqlite3
import random
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "sggs.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Students table
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        branch TEXT NOT NULL,
        year INTEGER NOT NULL,
        division TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        photo_url TEXT DEFAULT NULL
    )''')

    # Marks table
    c.execute('''CREATE TABLE IF NOT EXISTS marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        ise1 REAL DEFAULT 0,
        ise2 REAL DEFAULT 0,
        end_sem REAL DEFAULT 0,
        total REAL DEFAULT 0,
        grade TEXT DEFAULT 'F',
        FOREIGN KEY(student_id) REFERENCES students(id)
    )''')

    # Attendance table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        total_lectures INTEGER DEFAULT 0,
        attended INTEGER DEFAULT 0,
        percentage REAL DEFAULT 0,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )''')

    # Library table
    c.execute('''CREATE TABLE IF NOT EXISTS library (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        book_title TEXT NOT NULL,
        book_author TEXT NOT NULL,
        isbn TEXT NOT NULL,
        issue_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT DEFAULT NULL,
        status TEXT DEFAULT 'Issued',
        fine REAL DEFAULT 0,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )''')

    # Hostel table
    c.execute('''CREATE TABLE IF NOT EXISTS hostel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL UNIQUE,
        hostel_name TEXT NOT NULL,
        room_no TEXT NOT NULL,
        block TEXT NOT NULL,
        fee_paid REAL DEFAULT 0,
        fee_due REAL DEFAULT 0,
        admitted_date TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )''')

    conn.commit()
    conn.close()

def seed_data():
    conn = get_connection()
    c = conn.cursor()

    # Check if already seeded
    c.execute("SELECT COUNT(*) FROM students")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    branches = ['Computer Engineering', 'Mechanical Engineering', 'Civil Engineering', 'Electronics Engineering', 'Information Technology']
    divisions = ['A', 'B', 'C']
    years = [1, 2, 3, 4]
    hostels = ['Saraswati Hostel', 'Vivekananda Hostel', 'APJ Hostel', 'Shivaji Hostel']
    blocks = ['A-Block', 'B-Block', 'C-Block', 'D-Block']

    subjects_by_branch = {
        'Computer Engineering': ['Data Structures', 'DBMS', 'Operating Systems', 'Computer Networks', 'Software Engineering'],
        'Mechanical Engineering': ['Thermodynamics', 'Fluid Mechanics', 'Machine Design', 'Manufacturing', 'Heat Transfer'],
        'Civil Engineering': ['Structural Analysis', 'Geotechnical Engineering', 'Surveying', 'Hydraulics', 'Construction Management'],
        'Electronics Engineering': ['Digital Electronics', 'Analog Circuits', 'Signals & Systems', 'VLSI Design', 'Microprocessors'],
        'Information Technology': ['Web Technologies', 'Cloud Computing', 'Cybersecurity', 'AI & ML', 'Mobile Computing']
    }

    books_pool = [
        ('Introduction to Algorithms', 'Cormen et al.', '978-0262033848'),
        ('Clean Code', 'Robert C. Martin', '978-0132350884'),
        ('Database Systems', 'Ramakrishnan', '978-0072465631'),
        ('Operating System Concepts', 'Silberschatz', '978-1119800361'),
        ('Computer Networks', 'Tanenbaum', '978-0132126953'),
        ('The Pragmatic Programmer', 'Hunt & Thomas', '978-0135957059'),
        ('Design Patterns', 'Gang of Four', '978-0201633610'),
        ('Fluid Mechanics', 'Frank White', '978-0073398273'),
        ('Structural Analysis', 'Hibbeler', '978-0134610672'),
        ('Digital Electronics', 'Floyd', '978-0132359238'),
    ]

    student_names = [
        'Aarav Sharma', 'Priya Patel', 'Rahul Gupta', 'Sneha Desai', 'Amit Kumar',
        'Pooja Joshi', 'Vikram Singh', 'Ananya Rao', 'Rohan Mehta', 'Kavya Nair',
        'Arjun Reddy', 'Ishaan Verma', 'Diya Shah', 'Karan Malhotra', 'Meera Iyer',
        'Aditya Bose', 'Simran Kaur', 'Nikhil Shetty', 'Riya Tiwari', 'Siddharth Jain',
        'Tanvi Kulkarni', 'Dev Mishra', 'Shruti Agarwal', 'Yash Thakur', 'Nisha Pillai',
        'Harsh Bajaj', 'Aditi Dubey', 'Manish Chaudhary', 'Kritika Saxena', 'Vivek Pandey',
        'Swati Goyal', 'Pranav Nanda', 'Anjali Bhat', 'Suraj Rane', 'Pallavi Ghosh',
        'Mohit Sharma', 'Divya Tripathi', 'Akash Srivastava', 'Neha Patil', 'Rajat Kapoor'
    ]

    def get_grade(total):
        if total >= 75: return 'O'
        elif total >= 65: return 'A+'
        elif total >= 55: return 'A'
        elif total >= 50: return 'B+'
        elif total >= 45: return 'B'
        elif total >= 40: return 'C'
        else: return 'F'

    hostel_students = random.sample(range(len(student_names)), 22)

    for i, name in enumerate(student_names):
        branch = random.choice(branches)
        year = random.choice(years)
        roll_no = f"SGGS{2020+year}{str(i+1).zfill(3)}"
        email = f"{name.lower().replace(' ', '.')}{i+1}@sggs.ac.in"

        c.execute('''INSERT INTO students (roll_no, name, branch, year, division, email, phone)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (roll_no, name, branch, year, random.choice(divisions),
                   email, f"9{random.randint(100000000,999999999)}"))

        student_id = c.lastrowid
        subjects = subjects_by_branch[branch]

        for subject in subjects:
            ise1 = round(random.uniform(8, 30), 1)
            ise2 = round(random.uniform(8, 30), 1)
            end_sem = round(random.uniform(20, 70), 1)
            total = round((ise1/30)*20 + (ise2/30)*20 + (end_sem/70)*60, 1)
            grade = get_grade(total)
            c.execute('''INSERT INTO marks (student_id, subject, ise1, ise2, end_sem, total, grade)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (student_id, subject, ise1, ise2, end_sem, total, grade))

            total_lec = random.randint(40, 60)
            attended = random.randint(int(total_lec * 0.5), total_lec)
            percentage = round((attended / total_lec) * 100, 1)
            c.execute('''INSERT INTO attendance (student_id, subject, total_lectures, attended, percentage)
                         VALUES (?, ?, ?, ?, ?)''',
                      (student_id, subject, total_lec, attended, percentage))

        # Library
        num_books = random.randint(0, 3)
        for _ in range(num_books):
            book = random.choice(books_pool)
            issue_day = random.randint(1, 28)
            issue_month = random.randint(1, 11)
            issue_date = f"2024-{str(issue_month).zfill(2)}-{str(issue_day).zfill(2)}"
            due_date = f"2024-{str(issue_month+1).zfill(2)}-{str(issue_day).zfill(2)}"
            status = random.choice(['Issued', 'Issued', 'Returned', 'Overdue'])
            return_date = None
            fine = 0
            if status == 'Returned':
                return_date = due_date
            elif status == 'Overdue':
                fine = round(random.uniform(10, 100), 2)
            c.execute('''INSERT INTO library (student_id, book_title, book_author, isbn, issue_date, due_date, return_date, status, fine)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (student_id, book[0], book[1], book[2], issue_date, due_date, return_date, status, fine))

        # Hostel
        if i in hostel_students:
            hostel_name = random.choice(hostels)
            room_no = f"{random.randint(100, 500)}"
            block = random.choice(blocks)
            fee_paid = random.choice([30000, 45000, 60000])
            fee_due = random.choice([0, 0, 5000, 15000])
            c.execute('''INSERT INTO hostel (student_id, hostel_name, room_no, block, fee_paid, fee_due, admitted_date)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (student_id, hostel_name, room_no, block, fee_paid, fee_due, "2024-06-01"))

    conn.commit()
    conn.close()
    print("Database seeded successfully!")

if __name__ == "__main__":
    init_db()
    seed_data()
