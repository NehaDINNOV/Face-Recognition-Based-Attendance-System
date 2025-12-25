import sqlite3

def fetch_faculty():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faculty")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        print("Faculty Table Data:")
        print("ID | Name | Department | Email | Registration ID | Password")
        print("-" * 80)
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
    else:
        print("No data found in faculty table.")

if __name__ == "__main__":
    fetch_faculty()
