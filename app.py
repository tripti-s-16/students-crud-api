from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
from datetime import date

app = FastAPI(title="Students Database CRUD API")

# Create Database and Table
def init_db():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            dob TEXT,
            email TEXT,
            phone TEXT,
            course TEXT,
            address TEXT,
            enrollment_date TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Pydantic Models
class StudentCreate(BaseModel):
    student_id: str
    name: str
    dob: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[str] = None

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[str] = None

# Helper to get DB connection
def get_db():
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    return conn

# 1. CREATE - POST /students
@app.post("/students")
def create_student(student: StudentCreate):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO students (student_id, name, dob, email, phone, course, address, enrollment_date)
            VALUES (?,?,?,?,?,?,?,?)
        """, (student.student_id, student.name, student.dob, student.email, student.phone, student.course, student.address, student.enrollment_date))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return {"message": "Student created successfully", "id": new_id, "student": student}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Student ID already exists")

# 2. READ - GET /students (List / filter)
@app.get("/students")
def list_students(course: Optional[str] = None, name: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM students WHERE 1=1"
    params = []
    if course:
        query += " AND course LIKE?"
        params.append(f"%{course}%")
    if name:
        query += " AND name LIKE?"
        params.append(f"%{name}%")

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# 3. READ - GET /students/{student_id} (View one)
@app.get("/students/{student_id}")
def get_student(student_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id =?", (student_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return dict(row)

# 4. UPDATE - PUT /students/{student_id}
@app.put("/students/{student_id}")
def update_student(student_id: str, student: StudentUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id =?", (student_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    # Build dynamic update query
    updates = []
    params = []
    for field, value in student.dict(exclude_unset=True).items():
        if value is not None:
            updates.append(f"{field} =?")
            params.append(value)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(student_id)
    query = f"UPDATE students SET {', '.join(updates)} WHERE student_id =?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()
    return {"message": "Student updated successfully"}

# 5. DELETE - DELETE /students/{student_id}
@app.delete("/students/{student_id}")
def delete_student(student_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE student_id =?", (student_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted successfully"}

@app.get("/")
def home():
    return {"message": "Students Database CRUD API is running. Go to /docs for API documentation"}