import sqlite3
import pandas as pd

# ================= DATABASE ================= #

conn = sqlite3.connect("exam.db")
cursor = conn.cursor()


# ================= STUDENTS TABLE ================= #

cursor.execute("""

CREATE TABLE IF NOT EXISTS students (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    usn TEXT UNIQUE,

    student_name TEXT,

    email TEXT,

    password TEXT
)

""")


# ================= QUESTIONS TABLE ================= #

cursor.execute("""

CREATE TABLE IF NOT EXISTS questions (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    question TEXT,

    option_a TEXT,

    option_b TEXT,

    option_c TEXT,

    option_d TEXT,

    answer TEXT

)

""")


# ================= RESULTS TABLE ================= #

cursor.execute("""

CREATE TABLE IF NOT EXISTS results (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    usn TEXT,

    student_name TEXT,

    marks TEXT,

    warnings INTEGER,

    status TEXT,

    submission_time TEXT

)

""")


# ================= IMPORT STUDENTS ================= #

file_path = "Student datasets.xlsx"

df = pd.read_excel(file_path)


for index, row in df.iterrows():

    usn = str(row["USN"]).strip()
    name = str(row["Student Name "]).strip()
    email = str(row["Email"]).strip()
    password = str(row["Password"]).strip()

    try:

        cursor.execute("""

        INSERT INTO students
        (
            usn,
            student_name,
            email,
            password
        )

        VALUES (?, ?, ?, ?)

        """, (

            usn,
            name,
            email,
            password

        ))

    except:
        pass


conn.commit()
conn.close()

print("Database Created Successfully")