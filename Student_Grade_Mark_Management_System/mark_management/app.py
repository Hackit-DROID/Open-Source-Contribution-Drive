"""
📘 app.py — Main Flask Application
Marksheet Management System
✍️ Dr. Balaji Shetty
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from models import db, Student, Marks, BRANCHES, YEARS, SUBJECTS
from opencode.llm import OpenCodeLLM
from collections import defaultdict

# ── Load environment variables ──
load_dotenv()

# ── Configuration Constants ──
DEFAULT_PAGE_SIZE = 25
DEFAULT_PORT = 5001
SECRET_KEY_DEFAULT = 'marksheet-secret-2024'
TEST1_MAX_MARKS = 20
TEST2_MAX_MARKS = 20
FINAL_EXAM_MAX_MARKS = 60
TOP_PERFORMERS_LIMIT = 10
GRADE_O_THRESHOLD = 90
GRADE_A_PLUS_THRESHOLD = 80
GRADE_A_THRESHOLD = 70
GRADE_B_PLUS_THRESHOLD = 60
GRADE_B_THRESHOLD = 50
GRADE_C_THRESHOLD = 40

# ── Initialize Flask ──
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', SECRET_KEY_DEFAULT)

# ── Initialize DB ──
db.init_app(app)

# ── Initialize LLM ──
llm = OpenCodeLLM()


# ════════════════════════════════════════════════
# 🏠 HOME — Index Page
# ════════════════════════════════════════════════
@app.route('/')
def index():
    student_count = Student.query.count()
    marks_count = Marks.query.count()
    branch_count = db.session.query(Student.branch).distinct().count()
    providers = llm.get_available_providers()

    return render_template('index.html',
                           student_count=student_count,
                           marks_count=marks_count,
                           branch_count=branch_count,
                           providers=providers)


# ════════════════════════════════════════════════
# ➕ ADD STUDENT
# ════════════════════════════════════════════════
@app.route('/add-student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        roll_no  = request.form.get('roll_no', '').strip()
        branch   = request.form.get('branch', '').strip()
        year     = request.form.get('year', '').strip()
        email    = request.form.get('email', '').strip()

        # Validate
        if not all([name, roll_no, branch, year]):
            flash('All fields except Email are required.', 'danger')
            return render_template('add_student.html', branches=BRANCHES, years=YEARS)

        # Check duplicate roll number
        existing = Student.query.filter_by(roll_no=roll_no).first()
        if existing:
            flash(f'Roll number "{roll_no}" already exists. Please use a unique roll number.', 'danger')
            return render_template('add_student.html', branches=BRANCHES, years=YEARS)

        student = Student(name=name, roll_no=roll_no, branch=branch, year=year, email=email)
        db.session.add(student)
        db.session.commit()

        flash(f'✅ Student "{name}" registered successfully! Now add their marks.', 'success')
        return redirect(url_for('add_marks', student_id=student.id))

    return render_template('add_student.html', branches=BRANCHES, years=YEARS)


# ════════════════════════════════════════════════
# 👥 STUDENTS LIST
# ════════════════════════════════════════════════
@app.route('/students')
def students_list():
    search = request.args.get('search', '').strip()
    branch = request.args.get('branch', '').strip()
    year   = request.args.get('year', '').strip()

    query = Student.query

    if search:
        query = query.filter(Student.name.ilike(f'%{search}%'))
    if branch:
        query = query.filter(Student.branch == branch)
    if year:
        query = query.filter(Student.year == year)

    students = query.order_by(Student.created_at.desc()).all()

    return render_template('students.html',
                           students=students,
                           branches=BRANCHES,
                           years=YEARS)


# ════════════════════════════════════════════════
# 📝 ADD / EDIT MARKS
# ════════════════════════════════════════════════
@app.route('/marks/<int:student_id>', methods=['GET', 'POST'])
def add_marks(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        # Delete old marks (to allow editing)
        Marks.query.filter_by(student_id=student_id).delete()

        for subject in SUBJECTS:
            try:
                t1    = int(request.form.get(f'{subject}_t1', 0))
                t2    = int(request.form.get(f'{subject}_t2', 0))
                final = int(request.form.get(f'{subject}_final', 0))
            except ValueError:
                flash(f'Invalid marks value for {subject}.', 'danger')
                return redirect(url_for('add_marks', student_id=student_id))

            # Validate ranges
            if not (0 <= t1 <= TEST1_MAX_MARKS and 0 <= t2 <= TEST2_MAX_MARKS and 0 <= final <= FINAL_EXAM_MAX_MARKS):
                flash(f'Marks out of range for {subject}! Test1/Test2: 0-{TEST1_MAX_MARKS}, Final: 0-{FINAL_EXAM_MAX_MARKS}', 'danger')
                return redirect(url_for('add_marks', student_id=student_id))

            mark = Marks(student_id=student_id, subject=subject,
                         test1=t1, test2=t2, final_exam=final)
            db.session.add(mark)

        db.session.commit()
        flash(f'✅ Marks saved for {student.name}!', 'success')
        return redirect(url_for('report', student_id=student_id))

    # Load existing marks for edit view
    existing_marks_list = Marks.query.filter_by(student_id=student_id).all()
    existing_marks = {m.subject: m for m in existing_marks_list}

    return render_template('add_marks.html',
                           student=student,
                           subjects=SUBJECTS,
                           existing_marks=existing_marks)


# ════════════════════════════════════════════════
# 📄 REPORT (with AI analysis)
# ════════════════════════════════════════════════
@app.route('/report/<int:student_id>')
def report(student_id):
    student = Student.query.get_or_404(student_id)
    marks   = Marks.query.filter_by(student_id=student_id).all()

    if not marks:
        flash('No marks found for this student. Please add marks first.', 'warning')
        return redirect(url_for('add_marks', student_id=student_id))

    total      = sum(m.total() for m in marks)
    percentage = (total / (len(marks) * 100)) * 100

    # Overall grade
    if percentage >= GRADE_O_THRESHOLD:        overall_grade = 'O'
    elif percentage >= GRADE_A_PLUS_THRESHOLD: overall_grade = 'A+'
    elif percentage >= GRADE_A_THRESHOLD:      overall_grade = 'A'
    elif percentage >= GRADE_B_PLUS_THRESHOLD: overall_grade = 'B+'
    elif percentage >= GRADE_B_THRESHOLD:      overall_grade = 'B'
    elif percentage >= GRADE_C_THRESHOLD:      overall_grade = 'C'
    else:                                      overall_grade = 'F'

    # Pass/Fail — all subjects must pass
    result = 'Pass' if all(m.is_pass() for m in marks) else 'Fail'

    # Build structured data for built-in analyzer
    student_data = {
        'name': student.name,
        'branch': student.branch,
        'year': student.year,
        'marks': [
            {
                'subject': m.subject,
                'test1': m.test1,
                'test2': m.test2,
                'final': m.final_exam,
                'total': m.total()
            }
            for m in marks
        ]
    }

    # Build AI prompt
    marks_summary = '\n'.join([
        f"  - {m.subject}: Test1={m.test1}/20, Test2={m.test2}/20, Final={m.final_exam}/60, Total={m.total()}/100"
        for m in marks
    ])
    prompt = f"""
You are an academic performance analyst. Analyze this engineering student's marksheet:

Student: {student.name}
Branch: {student.branch}
Year: {student.year}
Overall: {total}/500 ({percentage:.1f}%)
Result: {result}

Subject-wise Marks:
{marks_summary}

Please provide:
1. A brief performance summary
2. Strongest and weakest subjects
3. Specific improvement tips for weak areas
4. A motivational message for the student

Keep the response friendly, structured, and encouraging.
"""

    ai_report, provider = llm.generate(prompt, provider='auto', student_data=student_data)

    return render_template('report.html',
                           student=student,
                           marks=marks,
                           total=total,
                           percentage=percentage,
                           overall_grade=overall_grade,
                           result=result,
                           ai_report=ai_report,
                           provider=provider)


# ════════════════════════════════════════════════
# 🔄 COMPARE AI MODELS
# ════════════════════════════════════════════════
@app.route('/compare/<int:student_id>')
def compare_report(student_id):
    student = Student.query.get_or_404(student_id)
    marks   = Marks.query.filter_by(student_id=student_id).all()

    if not marks:
        flash('No marks found. Please add marks first.', 'warning')
        return redirect(url_for('add_marks', student_id=student_id))

    total      = sum(m.total() for m in marks)
    percentage = (total / (len(marks) * 100)) * 100

    student_data = {
        'name': student.name,
        'branch': student.branch,
        'year': student.year,
        'marks': [
            {'subject': m.subject, 'test1': m.test1, 'test2': m.test2,
             'final': m.final_exam, 'total': m.total()}
            for m in marks
        ]
    }

    marks_summary = '\n'.join([
        f"  - {m.subject}: Total={m.total()}/100"
        for m in marks
    ])
    prompt = f"""
Analyze this student's marksheet:
Name: {student.name} | Branch: {student.branch} | Year: {student.year}
Overall: {total}/500 ({percentage:.1f}%)
Subjects: {marks_summary}
Give a performance analysis with improvement tips.
"""

    reports = llm.generate_comparison(prompt, student_data=student_data)

    return render_template('compare.html',
                           student=student,
                           reports=reports,
                           total=total,
                           percentage=percentage)


# ════════════════════════════════════════════════
# 📊 DASHBOARD
# ════════════════════════════════════════════════
@app.route('/dashboard')
def dashboard():
    all_students = Student.query.all()
    total_students = len(all_students)

    with_marks    = sum(1 for s in all_students if len(s.marks) > 0)
    without_marks = total_students - with_marks

    # Branch counts
    branch_counts = defaultdict(int)
    for s in all_students:
        branch_counts[s.branch] += 1
    branch_counts = dict(sorted(branch_counts.items(), key=lambda x: x[1], reverse=True))

    # Year counts
    year_counts = defaultdict(int)
    for s in all_students:
        year_counts[s.year] += 1

    # Average percentage per student
    percentages = []
    top_performers = []
    for s in all_students:
        if s.marks:
            total = sum(m.total() for m in s.marks)
            pct   = (total / (len(s.marks) * 100)) * 100
            percentages.append(pct)
            top_performers.append({
                'id': s.id,
                'name': s.name,
                'branch': s.branch,
                'year': s.year,
                'total': total,
                'percentage': pct
            })

    avg_percentage = sum(percentages) / len(percentages) if percentages else 0.0
    top_performers = sorted(top_performers, key=lambda x: x['percentage'], reverse=True)[:TOP_PERFORMERS_LIMIT]

    # Subject-wise average
    subject_totals  = defaultdict(int)
    subject_counts  = defaultdict(int)
    all_marks = Marks.query.all()
    for m in all_marks:
        subject_totals[m.subject] += m.total()
        subject_counts[m.subject] += 1

    subject_avg = {
        sub: subject_totals[sub] / subject_counts[sub]
        for sub in SUBJECTS
        if subject_counts[sub] > 0
    }

    stats = {
        'total_students': total_students,
        'with_marks':     with_marks,
        'without_marks':  without_marks,
        'branch_counts':  branch_counts,
        'year_counts':    dict(year_counts),
        'avg_percentage': avg_percentage,
        'top_performers': top_performers,
        'subject_avg':    subject_avg,
    }

    return render_template('dashboard.html', stats=stats)


# ════════════════════════════════════════════════
# 🗑️ DELETE STUDENT
# ════════════════════════════════════════════════
@app.route('/delete/<int:student_id>')
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    name = student.name
    db.session.delete(student)
    db.session.commit()
    flash(f'🗑️ Student "{name}" has been deleted.', 'danger')
    return redirect(url_for('students_list'))


# ════════════════════════════════════════════════
# 🚀 Run App
# ════════════════════════════════════════════════
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Database tables created.")
        print(f"🤖 Available AI Providers: {llm.get_available_providers()}")
    app.run(debug=True, port=DEFAULT_PORT)
