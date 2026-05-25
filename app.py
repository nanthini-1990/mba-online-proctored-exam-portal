from flask import Flask, render_template
from flask import request, redirect
from flask import session, send_file
import sqlite3
from datetime import datetime
import pandas as pd
import random

app = Flask(__name__)
app.secret_key = "exam_secret_key"


# ================= HOME ================= #

@app.route("/")
def home():
    return render_template("home.html")


# ================= STUDENT LOGIN ================= #

@app.route("/student-login", methods=["GET", "POST"])
def student_login():

    if request.method == "POST":

        usn = request.form["usn"]
        password = request.form["password"]

        conn = sqlite3.connect("exam.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM students
        WHERE usn=? AND password=?
        """, (usn, password))

        student = cursor.fetchone()

        conn.close()

        if student:

            session["student_usn"] = usn

            return redirect("/instructions")

        else:
            return "Invalid USN or Password"

    return render_template("student_login.html")


# ================= INSTRUCTIONS ================= #

@app.route("/instructions")
def instructions():

    if "student_usn" not in session:
        return redirect("/student-login")

    return render_template("instructions.html")


# ================= START EXAM ================= #

@app.route("/start-exam")
def start_exam():

    if "student_usn" not in session:
        return redirect("/student-login")

    return redirect("/exam")


# ================= REGISTER ================= #

@app.route("/register")
def register():
    return render_template("register.html")


# ================= ADMIN LOGIN ================= #

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "Nanthini" and password == "1234":
            return redirect("/dashboard")

        return "Invalid Admin Login"

    return render_template("admin_login.html")


# ================= DASHBOARD ================= #

@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("exam.db")
    cursor = conn.cursor()

    # Results
    cursor.execute("""
    SELECT
        usn,
        student_name,
        marks,
        warnings,
        status,
        submission_time
    FROM results
    ORDER BY id DESC
    """)

    results = cursor.fetchall()

    # Total strength
    cursor.execute("""
    SELECT COUNT(*)
    FROM students
    """)

    total_students = cursor.fetchone()[0]

    # Attended students
    cursor.execute("""
    SELECT COUNT(DISTINCT usn)
    FROM results
    """)

    attended_students = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        results=results,
        total_students=total_students,
        attended_students=attended_students
    )


# ================= DOWNLOAD RESULTS ================= #

@app.route("/download-results")
def download_results():

    conn = sqlite3.connect("exam.db")

    query = """
    SELECT
        usn AS 'USN',
        student_name AS 'Student Name',
        marks AS 'Marks',
        warnings AS 'Warnings',
        status AS 'Status',
        submission_time AS 'Submission Time'
    FROM results
    ORDER BY id DESC
    """

    df = pd.read_sql_query(query, conn)

    file_name = "exam_results.xlsx"

    df.to_excel(file_name, index=False)

    conn.close()

    return send_file(
        file_name,
        as_attachment=True
    )


# ================= EXAM ================= #

@app.route("/exam")
def exam():

    if "student_usn" not in session:
        return redirect("/student-login")

    conn = sqlite3.connect("exam.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM questions
    """)

    all_questions = cursor.fetchall()

    # RANDOM 25 QUESTIONS
    questions = random.sample(
        list(all_questions),
        25
    )

    # SHUFFLE QUESTION ORDER
    random.shuffle(questions)

    # SAVE QUESTION IDS
    session["question_ids"] = [
        q["id"] for q in questions
    ]

    conn.close()

    return render_template(
        "exam.html",
        questions=questions
    )


# ================= SUBMIT EXAM ================= #

@app.route("/submit-exam", methods=["POST"])
def submit_exam():

    if "student_usn" not in session:
        return redirect("/student-login")

    usn = session["student_usn"]

    conn = sqlite3.connect("exam.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Student name
    cursor.execute("""
    SELECT student_name
    FROM students
    WHERE usn=?
    """, (usn,))

    student = cursor.fetchone()

    student_name = student["student_name"]

    # Get selected question ids
    question_ids = session.get(
        "question_ids",
        []
    )

    if not question_ids:
        conn.close()
        return "Question session expired."

    placeholders = ",".join(
        ["?"] * len(question_ids)
    )

    cursor.execute(f"""
    SELECT *
    FROM questions
    WHERE id IN ({placeholders})
    """, question_ids)

    questions = cursor.fetchall()

    # ================= EVALUATION ================= #

    score = 0

    for q in questions:

        question_id = q["id"]

        student_answer = request.form.get(
            f"question_{question_id}"
        )

        # Safe answer extraction
        try:
            db_answer = str(
                q["answer"]
            ).strip().upper()

        except:
            db_answer = ""

        # Convert:
        # "A) Something"
        # "A"
        # "A:"
        correct_answer = (
            db_answer[:1]
            .strip()
            .upper()
        )

        if (
            student_answer
            and
            student_answer.upper()
            ==
            correct_answer
        ):
            score += 1

    # ================= DETAILS ================= #

    warnings = int(
        request.form.get(
            "warnings",
            0
        )
    )

    auto_submitted = request.form.get(
        "auto_submitted",
        "No"
    )

    camera_status = request.form.get(
        "camera_status",
        "Available"
    )

    # ================= STATUS ================= #

    if warnings >= 3:
        status = "Auto Submitted"

    elif auto_submitted == "Yes":
        status = "Auto Submitted"

    elif camera_status == "No Camera":
        status = "No Camera Device"

    else:
        status = "Normal Submit"

    submission_time = datetime.now().strftime(
        "%d-%m-%Y %I:%M:%S %p"
    )

    # ================= SAVE RESULT ================= #

    cursor.execute("""
    INSERT INTO results
    (
        usn,
        student_name,
        marks,
        warnings,
        status,
        submission_time
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (

        usn,
        student_name,
        f"{score}/25",
        warnings,
        status,
        submission_time
    ))

    conn.commit()
    conn.close()

    session.clear()

    return render_template(
        "result.html",
        score=score
    )


# ================= LOGOUT ================= #

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ================= RUN APP ================= #

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )