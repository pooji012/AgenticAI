"""Set up SQLite database with sample employee data."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "hr_database.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS employees")
    cur.execute("""
        CREATE TABLE employees (
            emp_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            date_of_joining TEXT NOT NULL,
            salary REAL NOT NULL,
            manager TEXT,
            location TEXT,
            leave_balance INTEGER DEFAULT 20,
            status TEXT DEFAULT 'Active'
        )
    """)

    employees = [
        (1001, "Rahul Sharma", "Engineering", "Senior Software Engineer", "rahul.sharma@company.com", "9876543210", "2020-03-15", 1500000, "Priya Mehta", "Bangalore", 18, "Active"),
        (1002, "Ananya Gupta", "Engineering", "Software Engineer", "ananya.gupta@company.com", "9876543211", "2022-07-01", 1000000, "Priya Mehta", "Bangalore", 20, "Active"),
        (1003, "Priya Mehta", "Engineering", "Engineering Manager", "priya.mehta@company.com", "9876543212", "2018-01-10", 2500000, "Vikram Singh", "Bangalore", 15, "Active"),
        (1004, "Amit Patel", "HR", "HR Manager", "amit.patel@company.com", "9876543213", "2019-06-20", 1800000, "Vikram Singh", "Mumbai", 12, "Active"),
        (1005, "Sneha Reddy", "HR", "HR Executive", "sneha.reddy@company.com", "9876543214", "2023-01-15", 800000, "Amit Patel", "Mumbai", 22, "Active"),
        (1006, "Vikram Singh", "Management", "CTO", "vikram.singh@company.com", "9876543215", "2015-04-01", 5000000, None, "Bangalore", 10, "Active"),
        (1007, "Deepika Nair", "Finance", "Finance Manager", "deepika.nair@company.com", "9876543216", "2019-11-05", 2000000, "Vikram Singh", "Chennai", 16, "Active"),
        (1008, "Arjun Kumar", "Finance", "Accountant", "arjun.kumar@company.com", "9876543217", "2021-08-20", 900000, "Deepika Nair", "Chennai", 19, "Active"),
        (1009, "Kavitha Iyer", "Marketing", "Marketing Lead", "kavitha.iyer@company.com", "9876543218", "2020-02-14", 1600000, "Vikram Singh", "Mumbai", 14, "Active"),
        (1010, "Rajesh Verma", "Engineering", "DevOps Engineer", "rajesh.verma@company.com", "9876543219", "2021-05-10", 1400000, "Priya Mehta", "Bangalore", 17, "Active"),
        (1011, "Meera Joshi", "Engineering", "QA Engineer", "meera.joshi@company.com", "9876543220", "2022-09-01", 1100000, "Priya Mehta", "Hyderabad", 21, "Active"),
        (1012, "Suresh Babu", "Sales", "Sales Manager", "suresh.babu@company.com", "9876543221", "2018-12-01", 1700000, "Vikram Singh", "Delhi", 8, "Active"),
        (1013, "Pooja Desai", "Sales", "Sales Executive", "pooja.desai@company.com", "9876543222", "2023-06-15", 700000, "Suresh Babu", "Delhi", 20, "Active"),
        (1014, "Nikhil Rao", "Engineering", "Data Engineer", "nikhil.rao@company.com", "9876543223", "2021-03-22", 1300000, "Priya Mehta", "Bangalore", 16, "Active"),
        (1015, "Lakshmi Pillai", "HR", "Recruiter", "lakshmi.pillai@company.com", "9876543224", "2022-11-10", 850000, "Amit Patel", "Mumbai", 19, "Active"),
    ]

    cur.executemany(
        "INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        employees,
    )

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH} with {len(employees)} employees.")


if __name__ == "__main__":
    init_db()
