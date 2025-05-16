from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
import pyodbc
import datetime
from config import MYSQL_CONFIG, MSSQL_CONFIG  # cấu hình DB riêng biệt

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # dùng cho flash message

# ======== KẾT NỐI CSDL ========

def get_mysql_conn():
    try:
        conn = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
            cursorclass=pymysql.cursors.DictCursor
        )
        print("MySQL connected 🎉")
        return conn
    except pymysql.MySQLError as e:
        print(f"MySQL connection error: {e}")
        return None

def get_mssql_conn():
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={MSSQL_CONFIG['server']};"
            f"DATABASE={MSSQL_CONFIG['database']};"
            f"UID={MSSQL_CONFIG['user']};"
            f"PWD={MSSQL_CONFIG['password']}"
        )
        print("MSSQL connected 🚀")
        return conn
    except pyodbc.Error as e:
        print(f"MSSQL connection error: {e}")
        return None

# ======== CRUD NHÂN VIÊN (MySQL) ========

def fetch_all_employees():
    conn = get_mysql_conn()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, department, title, status FROM employees")
            return cursor.fetchall()
    finally:
        conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/employees')
def employees():
    emps = fetch_all_employees()
    return render_template('employees.html', employees=emps)

@app.route('/add-employee', methods=['POST'])
def add_employee():
    data = {k: request.form.get(k) for k in ['name', 'department', 'title', 'status']}
    conn = get_mysql_conn()
    if not conn:
        flash("Kết nối database thất bại!", "error")
        return redirect(url_for('employees'))
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO employees (name, department, title, status) VALUES (%s, %s, %s, %s)",
                (data['name'], data['department'], data['title'], data['status'])
            )
        conn.commit()
        flash("Thêm nhân viên thành công! ✨", "success")
    except Exception as e:
        print(f"Add employee error: {e}")
        flash("Lỗi khi thêm nhân viên.", "error")
    finally:
        conn.close()
    return redirect(url_for('employees'))

@app.route('/update-employee/<int:emp_id>', methods=['GET', 'POST'])
def update_employee(emp_id):
    conn = get_mysql_conn()
    if not conn:
        flash("Kết nối database thất bại!", "error")
        return redirect(url_for('employees'))

    if request.method == 'GET':
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, department, title, status FROM employees WHERE id=%s", (emp_id,))
                emp = cursor.fetchone()
            if not emp:
                flash("Không tìm thấy nhân viên.", "error")
                return redirect(url_for('employees'))
            return render_template('edit_employee.html', employee=emp)
        finally:
            conn.close()

    # POST: cập nhật
    data = {k: request.form.get(k) for k in ['name', 'department', 'title', 'status']}
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE employees SET name=%s, department=%s, title=%s, status=%s WHERE id=%s",
                (data['name'], data['department'], data['title'], data['status'], emp_id)
            )
        conn.commit()
        flash("Cập nhật nhân viên thành công! 🔥", "success")
    except Exception as e:
        print(f"Update employee error: {e}")
        flash("Lỗi khi cập nhật nhân viên.", "error")
    finally:
        conn.close()
    return redirect(url_for('employees'))

@app.route('/delete-employee/<int:emp_id>')
def delete_employee(emp_id):
    conn = get_mysql_conn()
    if not conn:
        flash("Kết nối database thất bại!", "error")
        return redirect(url_for('employees'))
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM employees WHERE id=%s", (emp_id,))
        conn.commit()
        flash("Xóa nhân viên thành công! 💥", "success")
    except Exception as e:
        print(f"Delete employee error: {e}")
        flash("Lỗi khi xóa nhân viên.", "error")
    finally:
        conn.close()
    return redirect(url_for('employees'))

# ======== BẢNG LƯƠNG (SQL Server) ========

@app.route('/payroll')
def payroll():
    conn = get_mssql_conn()
    if not conn:
        flash("Không thể kết nối SQL Server.", "error")
        return redirect(url_for('home'))
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.EmployeeID, e.FirstName, e.LastName, e.Position,
                   e.Salary, e.HireDate, p.bonus,
                   (e.Salary + ISNULL(p.bonus, 0)) AS TotalSalary
            FROM dbo.employees e
            LEFT JOIN dbo.payroll p ON e.EmployeeID = p.employee_id
        """)
        rows = cursor.fetchall()

        employees = [{
            'EmployeeID': r[0],
            'FirstName': r[1],
            'LastName': r[2],
            'Position': r[3],
            'Salary': r[4],
            'HireDate': r[5],
            'Bonus': r[6] if r[6] else 0,
            'TotalSalary': r[7]
        } for r in rows]

        total_payroll = sum(emp['TotalSalary'] for emp in employees)

        if not employees:
            flash("Không có dữ liệu bảng lương.", "error")
            return redirect(url_for('home'))

        return render_template('payroll.html', employees=employees, total_payroll=total_payroll)
    except Exception as e:
        print(f"Payroll query error: {e}")
        flash("Lỗi lấy dữ liệu bảng lương.", "error")
        return redirect(url_for('home'))
    finally:
        conn.close()

# ======== CHẤM CÔNG (SQL Server) ========

@app.route('/attendance')
def attendance():
    date_str = request.args.get('date')
    try:
        selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.date.today()
    except Exception:
        selected_date = datetime.date.today()

    conn = get_mssql_conn()
    attendance_list = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EmployeeID, FirstName, LastName, Date, ClockInTime, ClockOutTime, HoursWorked
                FROM dbo.attendance
                WHERE CAST(Date AS DATE) = ?
            """, (selected_date,))
            rows = cursor.fetchall()
            attendance_list = [{
                'EmployeeID': r[0],
                'FirstName': r[1],
                'LastName': r[2],
                'Date': r[3],
                'ClockInTime': r[4],
                'ClockOutTime': r[5],
                'HoursWorked': r[6]
            } for r in rows]
        except Exception as e:
            print(f"Attendance fetch error: {e}")
        finally:
            conn.close()

    return render_template('attendance.html', attendance=attendance_list, selected_date=selected_date)

@app.route('/attendance/<int:employee_id>/clockin', methods=['POST'])
def clock_in(employee_id):
    conn = get_mssql_conn()
    if not conn:
        flash("Không thể kết nối DB.", "error")
        return redirect(url_for('attendance'))

    try:
        cursor = conn.cursor()
        today = datetime.date.today()
        now = datetime.datetime.now()

        cursor.execute("""
            SELECT AttendanceID, ClockInTime FROM dbo.attendance
            WHERE EmployeeID = ? AND CAST(Date AS DATE) = ?
        """, (employee_id, today))
        record = cursor.fetchone()

        if record and record[1] is not None:
            flash("Bạn đã điểm danh vào hôm nay rồi!", "warning")
        elif record:
            cursor.execute("""
                UPDATE dbo.attendance SET ClockInTime = ? WHERE AttendanceID = ?
            """, (now, record[0]))
            conn.commit()
            flash("Điểm danh vào thành công!", "success")
        else:
            cursor.execute("""
                INSERT INTO dbo.attendance (EmployeeID, Date, ClockInTime) VALUES (?, ?, ?)
            """, (employee_id, today, now))
            conn.commit()
            flash("Điểm danh vào thành công!", "success")
    except Exception as e:
        print(f"Clock in error: {e}")
        flash("Lỗi khi điểm danh vào.", "error")
    finally:
        conn.close()
    return redirect(url_for('attendance'))

@app.route('/attendance/<int:employee_id>/clockout', methods=['POST'])
def clock_out(employee_id):
    conn = get_mssql_conn()
    if not conn:
        flash("Không thể kết nối DB.", "error")
        return redirect(url_for('attendance'))

    try:
        cursor = conn.cursor()
        today = datetime.date.today()
        now = datetime.datetime.now()

        cursor.execute("""
            SELECT AttendanceID, ClockInTime, ClockOutTime FROM dbo.attendance
            WHERE EmployeeID = ? AND CAST(Date AS DATE) = ?
        """, (employee_id, today))
        record = cursor.fetchone()

        if not record or record[1] is None:
            flash("Bạn chưa điểm danh vào hôm nay.", "warning")
        elif record[2] is not None:
            flash("Bạn đã điểm danh ra hôm nay rồi!", "warning")
        else:
            clock_in_time = record[1]
            hours_worked = (now - clock_in_time).total_seconds() / 3600.0
            cursor.execute("""
                UPDATE dbo.attendance SET ClockOutTime = ?, HoursWorked = ? WHERE AttendanceID = ?
            """, (now, round(hours_worked, 2), record[0]))
            conn.commit()
            flash("Điểm danh ra thành công!", "success")
    except Exception as e:
        print(f"Clock out error: {e}")
        flash("Lỗi khi điểm danh ra.", "error")
    finally:
        conn.close()
    return redirect(url_for('attendance'))

if __name__ == '__main__':
    app.run(debug=True)
