# Student360 — Student Performance Analysis & Management Platform

**Student360** is a production-style, 360-degree **Student Performance Analysis and Management Platform** built with **Python 3.11+**, **Django 5.1**, **Django REST Framework**, **Bootstrap 5**, **Chart.js**, **Pandas**, **Scikit-Learn**, and **ReportLab**.

The platform moves beyond traditional exam marks to evaluate students across **7 pillars of performance**:
1. **Academic Performance** (40%)
2. **Attendance Rate** (15%)
3. **Behaviour & Conduct** (15%)
4. **Class Participation** (10%)
5. **Assignments Completion & Quality** (5%)
6. **Improvement Trajectory Index** (10%)
7. **Achievements & Special Points** (5%)

---

## Key Features

- **Holistic Performance Index (HPI) Engine**: Dynamically calculates student scores using configurable weights defined by school administrators.
- **Student of the Month Algorithm**: Automatically filters eligible students and ranks top performers per Class and Division, with an Admin approval workflow.
- **AI At-Risk Detection Engine**: Rule-based multi-indicator analysis flagging `LOW`, `MEDIUM`, or `HIGH` risk levels with actionable intervention recommendations.
- **Role-Based Access Control**:
  - **Admin**: Master data management, performance weights configuration, Student of the Month review, at-risk monitoring, school-wide analytics, bulk CSV import, report center.
  - **Teacher**: Fast bulk marks entry grid, one-click daily attendance register, behaviour logging, assignment tracking, class analytics.
  - **Student**: Personal 360 dashboard featuring HPI gauge, 7-pillar radar chart, marks, attendance, teacher remarks timeline, and awards cabinet.
  - **Parent**: Child progress overview, attendance history, marks breakdown, and notifications.
- **Fast Data Entry**: One-click daily attendance register and rapid exam marks entry table.
- **Reports & Exporting**: ReportLab PDF 360 Progress Cards, Excel (.xlsx), and CSV exports.
- **REST APIs & OpenAPI / Swagger Docs**: Interactive Swagger documentation rendered at `http://127.0.0.1:8000/api/docs/`.
- **Demo Seed Data**: Built-in `seed_data` command populates 1 Admin, 10 Teachers, 5 Classes, 3 Divisions, 10 Subjects, 105 Students, Parents, Exams, Marks, Attendance, Behaviour logs, Achievements, and HPI Scores.

---

## Default Demo Credentials

| Role | Username | Password |
|---|---|---|
| **School Admin** | `admin` | `admin123` |
| **Teacher** | `teacher1` | `teacher123` |
| **Student** | `student1` | `student123` |
| **Parent** | `parent1` | `parent123` |

---

## Quick Local Setup Guide

### Step 1 — Navigate to Project Directory & Activate Virtual Environment
```bash
cd "C:\Users\Daksh Shah\.gemini\antigravity\scratch\Student360"
```

### Step 2 — Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4 — Seed Realistic Demo Data
```bash
python manage.py seed_data
```

### Step 5 — Run Automated Test Suite
```bash
python manage.py test
```

### Step 6 — Start Local Server
```bash
python manage.py runserver
```

Open your web browser and visit:
- **Main Web Application**: [http127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Swagger API Documentation**: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **Django Admin Interface**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Technology Stack

- **Primary Language**: Python 3.11+ / Python 3.14
- **Backend Framework**: Django 5.1 & Django REST Framework
- **Analytics & Exporters**: Pandas, NumPy, Scikit-Learn, OpenPyXL, ReportLab
- **Database**: SQLite (default for instant setup) with PostgreSQL configuration in `settings.py` via `.env`
- **Frontend UI**: HTML5, CSS3, JavaScript, Bootstrap 5, Font Awesome 6, Chart.js
- **API Documentation**: drf-spectacular (OpenAPI 3 / Swagger UI)
