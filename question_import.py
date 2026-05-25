import sqlite3
import re


conn = sqlite3.connect("exam.db")
cursor = conn.cursor()


# ================= DELETE OLD QUESTIONS ================= #

cursor.execute("""
DELETE FROM questions
""")


# ================= READ QUESTION BANK ================= #

with open(
    "question_bank.txt",
    "r",
    encoding="utf-8"
) as file:

    data = file.read()


# ================= SPLIT QUESTIONS ================= #

question_blocks = re.split(
    r"Q\d+\.",
    data
)[1:]


# ================= INSERT QUESTIONS ================= #

for block in question_blocks:

    lines = [

        line.strip()

        for line in block.strip().split("\n")

        if line.strip()

    ]

    if len(lines) >= 6:

        question = lines[0]

        option_a = lines[1]
        option_b = lines[2]
        option_c = lines[3]
        option_d = lines[4]

        answer_line = lines[5]

        answer = (
            answer_line
            .replace("Answer:", "")
            .strip()[0]
            .upper()
        )

        cursor.execute("""

        INSERT INTO questions
        (
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            answer
        )

        VALUES (?, ?, ?, ?, ?, ?)

        """, (

            question,
            option_a,
            option_b,
            option_c,
            option_d,
            answer

        ))


conn.commit()
conn.close()

print("100 Questions Imported Successfully")