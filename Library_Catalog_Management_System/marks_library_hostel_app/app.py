from flask import Flask, render_template, request
from models import db, Student, Marks
from opencode.llm import OpenCodeLLM

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marks.db'
db.init_app(app)

llm = OpenCodeLLM()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        branch = request.form["branch"]
        year = request.form["year"]

        student = Student(name=name, branch=branch, year=year)
        db.session.add(student)
        db.session.commit()

        return "Student Added!"

    return render_template("index.html")


@app.route("/add_marks/<int:student_id>", methods=["POST"])
def add_marks(student_id):
    subjects = ["Math", "Physics", "Chemistry", "CS", "English"]

    for sub in subjects:
        m = Marks(
            student_id=student_id,
            subject=sub,
            test1=int(request.form[f"{sub}_t1"]),
            test2=int(request.form[f"{sub}_t2"]),
            final=int(request.form[f"{sub}_final"])
        )
        db.session.add(m)

    db.session.commit()
    return "Marks Added!"


@app.route("/report/<int:student_id>")
def report(student_id):
    student = Student.query.get(student_id)
    marks = Marks.query.filter_by(student_id=student_id).all()

    total = sum([m.total() for m in marks])

    prompt = f"""
    Student: {student.name}
    Total Marks: {total}
    Give performance analysis and improvement tips.
    """

    ai_report = llm.generate(prompt)

    return render_template("report.html",
                           student=student,
                           marks=marks,
                           total=total,
                           ai_report=ai_report)


if __name__ == "__main__":
    app.run(debug=True)