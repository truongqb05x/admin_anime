from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from src.pages.genres import genres_bp
from src.pages.actors import actors_bp
from src.pages.movies import movies_bp
from src.pages.episodes import episodes_bp
from src.pages.countries import countries_bp
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# DB Config
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'anime'
}

# Upload config
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DB connection helper
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"❌ DB Error: {e}")
        return None
app.get_db_connection = get_db_connection

# Register blueprints
app.register_blueprint(genres_bp)
app.register_blueprint(actors_bp)
app.register_blueprint(movies_bp)
app.register_blueprint(episodes_bp)
app.register_blueprint(countries_bp)  
# Routes render
@app.route('/')
def home():
    return render_template('theloai.html')

@app.route('/the-loai')
def the_loai_page():
    return render_template('theloai.html')

@app.route('/dien-vien')
def dien_vien_page():
    return render_template('dienvien.html')

@app.route('/phim')
def phim_page():
    return render_template('qlyphim.html')
@app.route('/quoc-gia')
def quoc_gia_page():
    return render_template('quocgia.html')

@app.route('/tap-phim')
def tap_phim_page():
    movie_id = request.args.get('movie_id', type=int)
    return render_template('tapphim.html', movie_id=movie_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)