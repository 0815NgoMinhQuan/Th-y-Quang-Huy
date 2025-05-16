# Cấu hình MySQL
MYSQL_CONFIG = {
    'host': 'localhost',            # Hoặc '127.0.0.1' nếu MySQL chạy trên máy local
    'user': 'root',                 # Tên người dùng MySQL
    'password': 'khangtran23',      # Mật khẩu người dùng
    'database': 'human',            # Tên cơ sở dữ liệu MySQL
}

# Cấu hình SQL Server
MSSQL_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',   # Đảm bảo driver chính xác
    'server': 'LAPTOP-5L6A8SAQ,1433',              # Máy chủ SQL Server với cổng 1433
    'database': 'PayRoll',                         # Tên cơ sở dữ liệu SQL Server
    'user': 'adminnn',                             # Tên người dùng SQL Server
    'password': 'khangtran23',                     # Mật khẩu người dùng SQL Server
}

