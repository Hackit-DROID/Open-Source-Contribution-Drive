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

# ─── Correlation Analytics (CR-637) ──────────────────────────────────────────

def compute_pearson_correlation(x_vals, y_vals):
    """Computes Pearson correlation coefficient between two numeric sequences."""
    if len(x_vals) < 2 or len(x_vals) != len(y_vals):
        return 0.0
    try:
        import numpy as np
        arr_x = np.array(x_vals, dtype=float)
        arr_y = np.array(y_vals, dtype=float)
        if np.std(arr_x) == 0 or np.std(arr_y) == 0:
            return 0.0
        corr = np.corrcoef(arr_x, arr_y)[0, 1]
        return float(corr) if not np.isnan(corr) else 0.0
    except ImportError:
        import math
        n = len(x_vals)
        mean_x = sum(x_vals) / n
        mean_y = sum(y_vals) / n
        diff_x = [x - mean_x for x in x_vals]
        diff_y = [y - mean_y for y in y_vals]
        denom = math.sqrt(sum(d * d for d in diff_x) * sum(d * d for d in diff_y))
        if denom == 0:
            return 0.0
        return sum(dx * dy for dx, dy in zip(diff_x, diff_y)) / denom


def get_attendance_performance_correlation(branch=None):
    """
    Computes correlation coefficient between attendance percentage and score,
    generates scatter plot data, and identifies high-risk students (<75% attendance AND <50% marks).
    """
    params = []
    where_clause = ""
    if branch:
        where_clause = "WHERE s.branch = ?"
        params.append(branch)

    sql = f"""
        SELECT s.id as student_id, s.name, s.roll_no, s.branch,
               ROUND(AVG(a.percentage), 2) as attendance_percentage,
               ROUND(AVG(m.total), 2) as marks_avg
        FROM students s
        JOIN attendance a ON s.id = a.student_id
        JOIN marks m ON s.id = m.student_id
        {where_clause}
        GROUP BY s.id
        ORDER BY s.roll_no ASC
    """
    rows = query_db(sql, params)
    scatter_data = []
    risk_students = []
    attendance_vals = []
    marks_vals = []

    for r in rows:
        att = float(r['attendance_percentage'] or 0.0)
        marks = float(r['marks_avg'] or 0.0)
        is_risk = att < 75.0 and marks < 50.0

        item = {
            'student_id': r['student_id'],
            'name': r['name'],
            'roll_no': r['roll_no'],
            'branch': r['branch'],
            'attendance_percentage': att,
            'marks_avg': marks,
            'is_risk': is_risk,
        }
        scatter_data.append(item)
        if is_risk:
            risk_students.append(item)
        attendance_vals.append(att)
        marks_vals.append(marks)

    corr = compute_pearson_correlation(attendance_vals, marks_vals)

    return {
        'correlation_coefficient': round(corr, 4),
        'scatter_plot_data': scatter_data,
        'risk_students': risk_students,
        'total_analyzed': len(scatter_data),
        'risk_count': len(risk_students),
    }


@app.route('/api/attendance_performance_correlation')
def attendance_performance_correlation():
    branch = request.args.get('branch', '')
    data = get_attendance_performance_correlation(branch=branch)
    return jsonify(data)

# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    seed_data()
    app.run(debug=True, port=5000)
