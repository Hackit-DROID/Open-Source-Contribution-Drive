from flask import Flask, render_template, jsonify, request
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from database.db_setup import init_db, seed_data, get_connection

app = Flask(__name__)

# ─── Helpers ────────────────────────────────────────────────────────────────

def query_db(sql, args=(), one=False):
    conn = get_connection()
    cur = conn.execute(sql, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# ─── Routes ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student/<int:student_id>')
def student_detail(student_id):
    return render_template('student_detail.html', student_id=student_id)

# ─── API ────────────────────────────────────────────────────────────────────

@app.route('/api/dashboard_stats')
def dashboard_stats():
    total_students = query_db("SELECT COUNT(*) as c FROM students", one=True)['c']
    hostel_students = query_db("SELECT COUNT(*) as c FROM hostel", one=True)['c']
    library_issued = query_db("SELECT COUNT(*) as c FROM library WHERE status='Issued'", one=True)['c']
    overdue = query_db("SELECT COUNT(*) as c FROM library WHERE status='Overdue'", one=True)['c']
    low_attendance = query_db(
        "SELECT COUNT(DISTINCT student_id) as c FROM attendance WHERE percentage < 75", one=True)['c']
    avg_marks = query_db("SELECT ROUND(AVG(total),1) as c FROM marks", one=True)['c']

    branch_dist = query_db(
        "SELECT branch, COUNT(*) as count FROM students GROUP BY branch ORDER BY count DESC")
    grade_dist = query_db(
        "SELECT grade, COUNT(*) as count FROM marks GROUP BY grade ORDER BY grade")
    attendance_dist = query_db('''
        SELECT
          CASE
            WHEN percentage >= 75 THEN "75%+"
            WHEN percentage >= 60 THEN "60-74%"
            ELSE "Below 60%"
          END as range,
          COUNT(*) as count
        FROM attendance GROUP BY range
    ''')

    return jsonify({
        'total_students': total_students,
        'hostel_students': hostel_students,
        'day_scholars': total_students - hostel_students,
        'library_issued': library_issued,
        'overdue_books': overdue,
        'low_attendance': low_attendance,
        'avg_marks': avg_marks,
        'branch_dist': [dict(r) for r in branch_dist],
        'grade_dist': [dict(r) for r in grade_dist],
        'attendance_dist': [dict(r) for r in attendance_dist],
    })

@app.route('/api/students')
def get_students():
    search = request.args.get('search', '')
    branch = request.args.get('branch', '')
    year = request.args.get('year', '')
    hostel_filter = request.args.get('hostel', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    offset = (page - 1) * per_page

    where_clauses = []
    params = []

    if search:
        where_clauses.append("(s.name LIKE ? OR s.roll_no LIKE ? OR s.email LIKE ?)")
        params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if branch:
        where_clauses.append("s.branch = ?")
        params.append(branch)
    if year:
        where_clauses.append("s.year = ?")
        params.append(int(year))
    if hostel_filter == 'hostel':
        where_clauses.append("h.id IS NOT NULL")
    elif hostel_filter == 'day':
        where_clauses.append("h.id IS NULL")

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    count_sql = f"""
        SELECT COUNT(*) as c FROM students s
        LEFT JOIN hostel h ON s.id = h.student_id
        {where_sql}
    """
    total = query_db(count_sql, params, one=True)['c']

    sql = f"""
        SELECT s.*, 
               h.hostel_name, h.room_no, h.block,
               ROUND(AVG(m.total), 1) as avg_marks,
               ROUND(AVG(a.percentage), 1) as avg_attendance,
               COUNT(DISTINCT CASE WHEN l.status='Issued' THEN l.id END) as books_issued
        FROM students s
        LEFT JOIN hostel h ON s.id = h.student_id
        LEFT JOIN marks m ON s.id = m.student_id
        LEFT JOIN attendance a ON s.id = a.student_id
        LEFT JOIN library l ON s.id = l.student_id
        {where_sql}
        GROUP BY s.id
        ORDER BY s.name ASC
        LIMIT ? OFFSET ?
    """
    rows = query_db(sql, params + [per_page, offset])

    return jsonify({
        'students': [dict(r) for r in rows],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })

@app.route('/api/student/<int:student_id>')
def get_student(student_id):
    student = query_db("SELECT * FROM students WHERE id=?", [student_id], one=True)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    marks = query_db("SELECT * FROM marks WHERE student_id=?", [student_id])
    attendance = query_db("SELECT * FROM attendance WHERE student_id=?", [student_id])
    library = query_db("SELECT * FROM library WHERE student_id=? ORDER BY issue_date DESC", [student_id])
    hostel = query_db("SELECT * FROM hostel WHERE student_id=?", [student_id], one=True)

    return jsonify({
        'student': dict(student),
        'marks': [dict(m) for m in marks],
        'attendance': [dict(a) for a in attendance],
        'library': [dict(l) for l in library],
        'hostel': dict(hostel) if hostel else None
    })

@app.route('/api/branches')
def get_branches():
    rows = query_db("SELECT DISTINCT branch FROM students ORDER BY branch")
    return jsonify([r['branch'] for r in rows])

@app.route('/api/top_students')
def top_students():
    rows = query_db("""
        SELECT s.name, s.roll_no, s.branch, ROUND(AVG(m.total),1) as avg
        FROM students s JOIN marks m ON s.id = m.student_id
        GROUP BY s.id ORDER BY avg DESC LIMIT 5
    """)
    return jsonify([dict(r) for r in rows])

@app.route('/api/attendance_alerts')
def attendance_alerts():
    rows = query_db("""
        SELECT s.name, s.roll_no, s.branch,
               ROUND(AVG(a.percentage),1) as avg_att
        FROM students s JOIN attendance a ON s.id = a.student_id
        GROUP BY s.id
        HAVING avg_att < 75
        ORDER BY avg_att ASC LIMIT 8
    """)
    return jsonify([dict(r) for r in rows])

# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    seed_data()
    app.run(debug=True, port=5000)
