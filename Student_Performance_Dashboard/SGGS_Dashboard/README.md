# SGGS Institute – Student Management Dashboard

A professional Flask-based dashboard for managing student data across Hostel, Library, and Academic modules.

## 📁 Project Structure
```
SGGS_Dashboard/
├── app.py                  ← Flask application (main entry point)
├── requirements.txt        ← Python dependencies
├── database/
│   ├── db_setup.py         ← SQLite DB init + seed data
│   └── sggs.db             ← Auto-generated SQLite database
├── templates/
│   └── index.html          ← Main dashboard HTML
└── static/
    ├── css/
    │   └── dashboard.css   ← All styles
    └── js/
        └── dashboard.js    ← Frontend logic + chart rendering
```

## 🚀 How to Run

### Step 1 – Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 – Run the app
```bash
python app.py
```

### Step 3 – Open in browser
```
http://localhost:5000
```

The database (`sggs.db`) will be **auto-created and seeded** with 40 sample students on first run.

---

## ✨ Features

| Module       | Features |
|-------------|----------|
| **Dashboard** | Live stats, branch/grade/attendance charts, top performers, attendance alerts |
| **Students**  | Search, filter by branch/year/hostel, paginated table |
| **Marks**     | ISE1, ISE2, End-Sem marks, total, grade per subject |
| **Attendance**| Per-subject attendance with visual progress bars |
| **Library**   | Book issue/return records, overdue detection, fine tracking |
| **Hostel**    | Room, block, fee paid/due info per resident |

---

## 🗄️ Database Tables

- `students` – Core student info
- `marks` – ISE1, ISE2, End-Sem per subject
- `attendance` – Subject-wise lecture attendance
- `library` – Book issue records
- `hostel` – Hostel allocation info

---

## 🛠️ Tech Stack

- **Backend**: Python 3 + Flask
- **Database**: SQLite (via `sqlite3`)
- **Frontend**: HTML5, CSS3, Vanilla JS
- **Charts**: Chart.js v4
- **Icons**: Font Awesome 6
