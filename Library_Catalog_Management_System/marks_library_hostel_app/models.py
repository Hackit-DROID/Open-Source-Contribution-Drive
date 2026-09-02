from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    branch = db.Column(db.String(50))
    year = db.Column(db.String(10))

class Marks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer)
    
    subject = db.Column(db.String(50))
    test1 = db.Column(db.Integer)
    test2 = db.Column(db.Integer)
    final = db.Column(db.Integer)

    def total(self):
        return self.test1 + self.test2 + self.final