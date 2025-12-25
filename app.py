import os
import cv2
import sqlite3

import numpy as np
import face_recognition
from flask import Flask, render_template, request, redirect, Response, flash, send_file, session,url_for,after_this_request
from flask_session import Session
from datetime import datetime
import pandas as pd
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "neha"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"  # Store session data on the server
Session(app)  # Initialize Flask-Session
# Global variables
video_capture = None
known_face_encodings = []
known_face_names = []
known_face_rolls = []

# Database Initialization
def init_db():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    # Create Faculty Table (Admin will insert records manually)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            roll_number TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            branch TEXT NOT NULL,
            semester INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,  -- Stored as name.surname format
            registration_id TEXT UNIQUE NOT NULL,
            image_path TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faculty (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            registration_id TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT NOT NULL,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            FOREIGN KEY (roll_number) REFERENCES students (roll_number)
        )
    ''')


    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('attendance.db')  # Connect to your database
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '')  # Get role selection

        if not username or not password or not role:
            flash("All fields are required!", "danger")
            return redirect(url_for('login'))

        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()

        if role == "faculty":
            cursor.execute("SELECT password FROM faculty WHERE LOWER(email) = ?", (username,))
            faculty = cursor.fetchone()
            if faculty and faculty[0] == password:
                session['user'] = username
                session['role'] = 'faculty'
                flash("Login successful!", "success")
                return redirect(url_for('index'))
        
        elif role == "student":
            cursor.execute("SELECT roll_number, password FROM students WHERE roll_number = ?",(str(username),))
            student = cursor.fetchone()
            if student and check_password_hash(student[1], password):
                session['user'] = username  # Store roll_number as session user
                session['role'] = 'student'
                flash("Login successful!", "success")
                return redirect(url_for('student_attendance'))
        
        conn.close()
        flash("Invalid credentials!", "danger")
        return redirect(url_for('login'))

    return render_template('login.html')

# Route: Logout
@app.route('/logout')
def logout():
    session.clear()  # Remove session data
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

# Route: Faculty Dashboard (Restrict to Faculty)
@app.route('/index')
def index():
    if 'user' not in session or session.get('role') != 'faculty':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))
    return render_template('index.html')
@app.route('/student_attendance', methods=['GET', 'POST'])
def student_attendance():
    if 'user' not in session or session.get('role') != 'student':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    roll_number = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get student record
    cursor.execute("SELECT * FROM students WHERE roll_number = ?", (roll_number,))
    student = cursor.fetchone()

    if student is None:
        flash("No student record found!", "danger")
        conn.close()
        return redirect(url_for('login'))

    # 📌 Handle Date Filter
    if request.method == 'POST':
        date = request.form.get('date')
        cursor.execute("SELECT date, time FROM attendance WHERE roll_number = ? AND date = ?", (roll_number, date))
    else:
        cursor.execute("SELECT date, time FROM attendance WHERE roll_number = ?", (roll_number,))

    attendance_records = cursor.fetchall()
    conn.close()

    return render_template('student_attendance.html', student=student, attendance_records=attendance_records)

# Load known faces from database
def load_known_faces():
    import os
    import face_recognition
    import sqlite3

    global known_face_encodings, known_face_names, known_face_rolls
    known_face_encodings = []
    known_face_names = []
    known_face_rolls = []

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT roll_number, name, image_path FROM students")
    students = cursor.fetchall()
    conn.close()

    base_path = "static/known_faces"  # ✅ Base directory where images are stored

    print(f"📦 Found {len(students)} students in DB.")

    for roll_no, name, image_filename in students:
        full_path = os.path.join(base_path, image_filename)  # ✅ Join base + filename
        print(f"\n🔍 Processing student: {name} ({roll_no})")
        print(f"🖼️ Image path: {full_path}")

        if os.path.exists(full_path):
            try:
                image = face_recognition.load_image_file(full_path)
                encodings = face_recognition.face_encodings(image)

                if encodings:
                    known_face_encodings.append(encodings[0])
                    known_face_names.append(name)
                    known_face_rolls.append(roll_no)
                    print(f"✅ Face encoding loaded for: {name}")
                else:
                    print(f"⚠️ No face found in image: {full_path}")
            except Exception as e:
                print(f"❌ Error loading face for {name}: {e}")
        else:
            print(f"❌ File not found: {full_path}")

    # 🧪 Optional manual test for one student image
    test_image_path = os.path.join(base_path, "23101.jpg")  # Replace with actual filename from DB
    if os.path.exists(test_image_path):
        test_image = face_recognition.load_image_file(test_image_path)
        test_encodings = face_recognition.face_encodings(test_image)
        if test_encodings:
            print("🧪✅ TEST: Face encoding succeeded for", test_image_path)
        else:
            print("🧪❌ TEST: No face found in test image:", test_image_path)
    else:
        print("🧪❌ TEST: Test image not found:", test_image_path)

def mark_attendance(roll_number, name):
    """Marks attendance for the recognized student in the database."""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    # Get current date and time
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    # Check if the student is already marked present for today
    cursor.execute("SELECT * FROM attendance WHERE roll_number = ? AND date = ?", (roll_number, date))
    record = cursor.fetchone()

    if not record:
        cursor.execute("INSERT INTO attendance (roll_number, name, date, time) VALUES (?, ?, ?, ?)", 
                       (roll_number, name, date, time))
        conn.commit()

    conn.close()

# Generate video frames
def generate_frames():
    global video_capture
    video_capture = cv2.VideoCapture(0)

    if not video_capture.isOpened():
        print("❌ ERROR: Camera not opened!")
        return

    frame_count = 0  

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("❌ ERROR: Failed to read frame!")
            break

        frame_count += 1
        if frame_count % 3 != 0:
            continue

        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2

            name = "Unknown"

            if known_face_encodings:
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                print(f"🔍 Closest distance: {face_distances[best_match_index]:.4f}")

                if face_distances[best_match_index] < 0.45:  # You can adjust this threshold
                    roll_number = known_face_rolls[best_match_index]
                    name = known_face_names[best_match_index]
                    print(f"✅ Match found: {name} ({roll_number})")

                    # Mark attendance
                    mark_attendance(roll_number, name)
                else:
                    print("❌ No good match found (distance too high).")
            else:
                print("⚠️ No known face encodings loaded!")

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        if buffer is None:
            print("❌ ERROR: Frame encoding failed!")
            continue

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    video_capture.release()
    cv2.destroyAllWindows()

# Routes
@app.route('/')
def main_page():
    if 'user' in session:
        if session['role'] == 'faculty':  # Redirect faculty to index.html
            return render_template('index.html')
        elif session['role'] == 'student':  # Redirect students to attendance page
            return redirect(url_for('view_attendance'))
    else:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/camera')
def camera_page():
    return render_template('camera.html')


UPLOAD_FOLDER = 'static/known_faces'  # Changed path to known_faces
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure folder exists

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        email = request.form.get('email', '').strip().lower()
        branch = request.form.get('branch', '').strip()
        semester = request.form.get('semester', '').strip()
        password = request.form.get('password', '').strip()
        registration_id = roll_number  # Assume registration_id = roll_number
        image = request.files['image']

        # Validate input fields
        if not name or not roll_number or not email or not branch or not semester or not password or not image:
            flash("All fields are required!", "danger")
            return redirect(url_for('register'))

        # Hash the user-entered password before storing
        hashed_password = generate_password_hash(password)

        # Save the image file inside static/known_faces/
        image_filename = f"{roll_number}.jpg"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image.save(image_path)

        # Insert student data into the database
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO students (roll_number, name, branch, semester, email, password, registration_id, image_path) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (roll_number, name, branch, semester, email, hashed_password, registration_id, image_filename))

            conn.commit()
            flash("Student registered successfully!", "success")
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash("Error: Roll Number or Email already exists!", "danger")
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/start')
def start_recognition():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop')
def stop_camera():
    global video_capture
    if video_capture is not None:
        video_capture.release()
        cv2.destroyAllWindows()
    flash("Camera Stopped Successfully!", "success")
    return redirect('/')

@app.route('/attendance')
def view_attendance():
    if 'user' not in session:
        flash("Please log in first!", "danger")
        return redirect(url_for('login'))

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    if session['role'] == 'faculty':
        # Faculty sees all attendance records
        cursor.execute("SELECT * FROM attendance ORDER BY date DESC, time DESC")
    elif session['role'] == 'student':
        # Student sees only their own attendance
        cursor.execute("SELECT * FROM attendance WHERE roll_number = ? ORDER BY date DESC, time DESC",
                       (session['user'],))
    
    records = cursor.fetchall()
    conn.close()
    
    return render_template('attendance.html', records=records)


@app.route('/download_attendance', methods=['POST'])
def download_attendance():
    if 'user' not in session or session.get('role') != 'faculty':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))  

    date = request.form.get('date')
    if not date:
        flash("Please select a date!", "warning")
        return redirect('/attendance')

    conn = sqlite3.connect('attendance.db')
    query = "SELECT * FROM attendance WHERE date = ?"
    df = pd.read_sql_query(query, conn, params=(date,))
    conn.close()

    if df.empty:
        flash("No attendance found for this date!", "warning")
        return redirect('/attendance')

    # Save CSV temporarily
    filename = f"attendance_{date}.csv"
    csv_path = os.path.join(app.root_path, filename)
    df.to_csv(csv_path, index=False)

    @after_this_request
    def cleanup(response):
        try:
            os.remove(csv_path)
        except Exception as e:
            print(f"Could not delete CSV: {e}")
        return response

    return send_file(csv_path, as_attachment=True)
@app.route('/students')
def view_students():
    if 'user' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if session.get('role') == 'faculty':
        # Faculty: View All Students
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
        conn.close()
        return render_template('students.html', students=students)

    elif session.get('role') == 'student':
        # Student: View Only Their Own Attendance
        roll_number = session.get('user')
        cursor.execute("SELECT * FROM attendance WHERE roll_number = ?", (roll_number,))
        attendance_records = cursor.fetchall()
        conn.close()
        return render_template('student_attendance.html', attendance=attendance_records)

    flash("Unauthorized access!", "danger")
    return redirect(url_for('login'))



@app.route('/delete_student/<roll_number>', methods=['POST'])
def delete_student(roll_number):
    if 'user' not in session or session.get('role') != 'faculty':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()

    # Get student image path before deleting
    cursor.execute("SELECT image_path FROM students WHERE roll_number = ?", (roll_number,))
    student = cursor.fetchone()

    if student:
        image_filename = os.path.join('static/known_faces', student[0])  # ✅ Ensure correct path
        if os.path.exists(image_filename):
            os.remove(image_filename)  # ✅ Delete the face image

        # Delete student and their attendance records
        cursor.execute("DELETE FROM attendance WHERE roll_number = ?", (roll_number,))
        cursor.execute("DELETE FROM students WHERE roll_number = ?", (roll_number,))
        conn.commit()
        flash("Student deleted successfully!", "success")

    conn.close()
    return redirect(url_for('view_students'))  # ✅ Use url_for instead of hardcoding the route

# Run Flask
if __name__ == '__main__':
    init_db()
    load_known_faces()
    app.run(debug=True)

