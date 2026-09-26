# 🏠 Hostel Room Allocation & Management System

[![Framework](https://img.shields.io/badge/Framework-Django%205.x-green?logo=django)](https://djangoproject.com)
[![Styling](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC?logo=tailwind-css)](https://tailwindcss.com)
[![Event](https://img.shields.io/badge/Event-HackIT%20Commit%20Rush-8A2BE2)](https://github.com/Hackit-DROID)
[![Security](https://img.shields.io/badge/Secrets%20Scan-Passed-success)](../../.env.example)

A full-featured campus MIS module for managing hostel room allocations, resident students, occupancy statuses, floor superintendents, and rental collections.

---

## ✨ Features

- **📊 Live KPI Analytics Cards**: Instant view of Total Rooms, Occupied Rooms, Vacancy Rate (%), and Expected Monthly Rent.
- **🔍 Multi-Parameter Search & Filtering**:
  - Full-text search across student names, room numbers, block names, and warden names.
  - Quick status filtering (`Occupied` vs `Vacant`).
  - Block/Wing filter dropdown and multi-field sorting (by room number, rent, floor, student).
- **📥 CSV Data Export**: One-click download of all room allocations as a formatted `.csv` spreadsheet for warden records and audit compliance.
- **🛏️ 1-Click "Vacate Room" Action**: Instantly deallocate rooms and mark them available without having to navigate into complex forms.
- **🎨 Modern Dark UI / UX**: Polished Tailwind CSS design with color-coded status badges, responsive tables, and intuitive modals.
- **🔔 User Feedback Notifications**: Clear flash toast alerts on creation, edits, vacating, and deletion of allocations using `django.contrib.messages`.
- **⚙️ Admin Dashboard Integration**: Registered `Hostel` model with custom `ModelAdmin` (`list_display`, `list_filter`, `search_fields`, `list_editable`).
- **🔐 Hardened Security**: Centralized configuration reading `SECRET_KEY` and `DEBUG` via environment variables (`python-dotenv`).
- **🧪 100% Automated Unit Test Coverage**: Full suite covering models, forms, views, CSV export, and vacancy logic.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Django 5.x
- **Database**: SQLite (default) / PostgreSQL compliant
- **Frontend**: HTML5, Tailwind CSS, Google Fonts (*Plus Jakarta Sans*)
- **Environment Management**: `python-dotenv`

---

## ⚡ Quick Start

### 1. Navigate to Project Directory

```bash
cd Hostel_Room_Allocation_System/DASHBOARD/schooldashboard
```

### 2. Install Dependencies

```bash
pip install -r ../../requirements.txt
```

### 3. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Run the Test Suite

```bash
python manage.py test hostel
```

### 5. Launch the Development Server

```bash
python manage.py runserver
```

Visit the dashboard in your browser at:
`http://127.0.0.1:8000/hostel/`

---

## 🌐 URL Routes Reference

| Route | View Name | Description |
|---|---|---|
| `/hostel/` | `hostel_display` | Main Dashboard with KPI cards, search, filters & room table |
| `/hostel/add/` | `hostel_add` | Allocate new hostel room to a student |
| `/hostel/edit/<pk>/` | `hostel_edit` | Edit room details, rent, or occupancy status |
| `/hostel/delete/<pk>/` | `hostel_delete` | Confirm and remove an allocation record |
| `/hostel/vacate/<pk>/` | `hostel_vacate` | One-click action to vacate room and reset status |
| `/hostel/export/csv/` | `hostel_export_csv` | Export allocations to a downloadable CSV spreadsheet |
| `/admin/` | `admin:index` | Django administrative interface |

---

## 📜 Contributing Guidelines

This project follows the **HackIT Commit Rush** open source standards:
- Secrets are never hardcoded; always managed through `.env`.
- Clean PEP 8 Python formatting.
- PRs should include concise commit messages (e.g. `feat: Add analytics KPI cards and search filtering`).
