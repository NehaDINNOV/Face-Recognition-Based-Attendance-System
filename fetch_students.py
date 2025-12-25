import sqlite3

def fetch_students():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        print("Students Table Data:")
        print("Roll Number | Name | Branch | Semester | Email | Password | Registration ID | Image Path")
        print("-" * 100)
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} | {row[7]}")
    else:
        print("No data found in students table.")

if __name__ == "__main__":
    fetch_students()
