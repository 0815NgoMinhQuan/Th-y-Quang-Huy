from flask import Flask, render_template, request, jsonify, redirect, url_for
import pymysql
import pyodbc
from config import MYSQL_CONFIG, MSSQL_CONFIG

app = Flask(__name__)

# ====== KẾT NỐI DATABASE ======

# Kết nối tới MySQL (dùng cho PAYROLL)
def mysql_conn():
    try:
        conn = pymysql.connect(
            host=MYSQL_CONFIG['localhost'],  # Kiểm tra host đúng
            user=MYSQL_CONFIG['root'],       # Kiểm tra user đúng
            password=MYSQL_CONFIG['Quan@@0815'],  # Kiểm tra mật khẩu đúng
            database=MYSQL_CONFIG['payroll']    # Kiểm tra tên cơ sở dữ liệu đúng
        )
        print("Kết nối thành công!")
        return conn
    except Exception as e:
        print(f"Lỗi kết nối: {e}")
        return None
    

# Kết nối tới SQL Server (dùng cho HUMAN_2025)
def mssql_conn():
    connection = pyodbc.connect(
    f"DRIVER={MSSQL_CONFIG['driver']};"
    f"SERVER={MSSQL_CONFIG['server']};"
    f"DATABASE={MSSQL_CONFIG['database']};"
    f"Trusted_Connection={MSSQL_CONFIG['trusted_connection']}"
)
    return connection

# ====== TRANG CHÍNH ======

@app.route('/')
def dashboard():
    return render_template('index.html')

# ====== TRUY VẤN NHÂN VIÊN (MySQL) ======

# Trả về toàn bộ danh sách nhân viên với đầy đủ thông tin
def get_all_employees_from_db():
    conn = mysql_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, department, title, status FROM employees")
    employees = cursor.fetchall()
    conn.close()
    return employees

# Route hiển thị danh sách nhân viên (giao diện web)
@app.route('/employees')
def show_employees():
    employees = get_all_employees_from_db()
    return render_template("employees.html", employees=employees)

# API thêm nhân viên từ form HTML (dùng method POST)
@app.route('/add-employee', methods=['POST'])
def add_employee():
    name = request.form['name']
    department = request.form['department']
    title = request.form['title']
    status = request.form['status']

    conn = mysql_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employees (name, department, title, status) VALUES (%s, %s, %s, %s)",
        (name, department, title, status)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('show_employees'))

# API cập nhật nhân viên (sửa thông tin từ form)
@app.route('/update-employee/<int:id>', methods=['POST'])
def update_employee(id):
    name = request.form['name']
    department = request.form['department']
    title = request.form['title']
    status = request.form['status']

    conn = mysql_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE employees SET name=%s, department=%s, title=%s, status=%s WHERE id=%s",
        (name, department, title, status, id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('show_employees'))

# API xoá nhân viên (GET từ nút bấm)
@app.route('/delete-employee/<int:id>')
def delete_employee(id):
    conn = mysql_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('show_employees'))

# ====== QUẢN LÝ LƯƠNG & CHẤM CÔNG (SQL Server) ======

@app.route('/payroll')
def get_payroll():
    conn = mssql_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT employee_id, salary, bonus FROM payroll")
    rows = cursor.fetchall()
    conn.close()
    return jsonify({'data': [tuple(r) for r in rows]})

@app.route('/attendance')
def get_attendance():
    conn = mssql_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance")
    rows = cursor.fetchall()
    conn.close()
    return jsonify({'data': [tuple(r) for r in rows]})

# ====== BÁO CÁO & CẢNH BÁO ======

@app.route('/reports')
def reports():
    conn = mysql_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT department, COUNT(*) FROM employees GROUP BY department")
    result = cursor.fetchall()
    conn.close()
    return jsonify({'summary': result})

@app.route('/alerts', methods=['POST'])
def send_alerts():
    data = request.json
    print("ALERT:", data['message'])  # Có thể thay bằng gửi email, log, gửi cảnh báo
    return {'status': 'Alert received'}

# cảnh báo từ SQL Server
@app.route('/alerts-sqlserver', methods=['POST'])
def send_alerts_sqlserver():
    conn = mssql_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts WHERE status='new'")
    rows = cursor.fetchall()
    for row in rows:
        # Xử lý cảnh báo (gửi email, log, v.v.)
        print("ALERT:", row)
        # Cập nhật trạng thái cảnh báo
        cursor.execute("UPDATE alerts SET status='processed' WHERE id=?", (row[0],))
    conn.commit()
    conn.close()
    return {'status': 'Alerts processed'}
# cảnh báo từ MySQL
@app.route('/alerts-mysql', methods=['POST'])
def send_alerts_mysql():
    conn = mysql_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts WHERE status='new'")
    rows = cursor.fetchall()
    for row in rows:
        # Xử lý cảnh báo (gửi email, log, v.v.)
        print("ALERT:", row)
        # Cập nhật trạng thái cảnh báo
        cursor.execute("UPDATE alerts SET status='processed' WHERE id=%s", (row[0],))
    conn.commit()
    conn.close()
    return {'status': 'Alerts processed'}

# ====== MAIN ======

if __name__ == '__main__':
    app.run(debug=True)
