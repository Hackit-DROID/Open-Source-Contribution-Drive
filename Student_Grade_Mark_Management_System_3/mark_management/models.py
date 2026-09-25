"""
📘 models.py — Database Models for Marksheet Management System
✍️ Two models: Student & Marks
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ──────────────────────────────────────────────
# 🧑 Student Model
# ──────────────────────────────────────────────
class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: one student → many marks
    marks = db.relationship('Marks', backref='student', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Student {self.name} | {self.roll_no}>'


# ──────────────────────────────────────────────
# 📊 Marks Model
# ──────────────────────────────────────────────
class Marks(db.Model):
    __tablename__ = 'marks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    test1 = db.Column(db.Integer, nullable=False, default=0)   # Max 20
    test2 = db.Column(db.Integer, nullable=False, default=0)   # Max 20
    final_exam = db.Column(db.Integer, nullable=False, default=0)  # Max 60

    def total(self):
        """Total marks for this subject (out of 100)"""
        return self.test1 + self.test2 + self.final_exam

    def grade(self):
        """Grade based on total marks"""
        t = self.total()
        if t >= 90:
            return 'O'   # Outstanding
        elif t >= 80:
            return 'A+'
        elif t >= 70:
            return 'A'
        elif t >= 60:
            return 'B+'
        elif t >= 50:
            return 'B'
        elif t >= 40:
            return 'C'
        else:
            return 'F'   # Fail

    def is_pass(self):
        """Pass if total >= 40"""
        return self.total() >= 40

    def __repr__(self):
        return f'<Marks {self.subject} | Total: {self.total()}>'


# ──────────────────────────────────────────────
# 📋 Constants
# ──────────────────────────────────────────────
BRANCHES = [
    'Computer Science (CSE)',
    'Information Technology (IT)',
    'Electronics & Telecom (EXTC)',
    'Electronics (ECE)',
    'Mechanical Engineering',
    'Civil Engineering',
    'Electrical Engineering',
    'Chemical Engineering',
    'Artificial Intelligence & DS',
    'Biotechnology'
]

YEARS = [
    ('FY', 'First Year (FY)'),
    ('SY', 'Second Year (SY)'),
    ('TY', 'Third Year (TY)'),
    ('BTech', 'B.Tech Final Year')
]

SUBJECTS = [
    'Mathematics',
    'Physics',
    'Chemistry',
    'Computer Science',
    'English'
]
