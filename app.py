from flask import Flask, render_template
import mysql.connector
from mysql.connector import Error
from src.pages.genres import genres_bp

app = Flask(__name__)

# Database config
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'anime'
}

# Hàm kết nối DB
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

# Gắn hàm này để file genres.py gọi
app.get_db_connection = get_db_connection

# Đăng ký blueprint
app.register_blueprint(genres_bp)

# Route giao diện
@app.route('/')
def home():
    return render_template('theloai.html')

@app.route('/the-loai')
def the_loai_page():
    return render_template('theloai.html')


if __name__ == '__main__':
    app.run(debug=True)
