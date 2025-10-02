from flask import Blueprint, request, jsonify, current_app
import mysql.connector
from mysql.connector import Error
import os
import uuid
from werkzeug.utils import secure_filename

movies_bp = Blueprint('movies', __name__)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads/posters'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@movies_bp.route('/api/movies', methods=['GET'])
def get_movies():
    try:
        connection = current_app.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Lấy tham số filter
            genre_id = request.args.get('genre_id', type=int)
            country_id = request.args.get('country_id', type=int)
            release_year = request.args.get('release_year', type=int)
            movie_type = request.args.get('type')
            search = request.args.get('search', '')
            
            query = """
                SELECT 
                    m.id, m.title, m.slug, m.description, m.meta_description,
                    m.release_year, m.duration, m.poster_url, m.trailer_url,
                    m.video_url, m.is_series, m.is_featured, m.average_rating,
                    m.view_count, m.created_at, m.updated_at,
                    COALESCE(GROUP_CONCAT(DISTINCT g.name), '') as genres,
                    COALESCE(GROUP_CONCAT(DISTINCT c.name), '') as countries,
                    COUNT(DISTINCT e.id) as episode_count
                FROM movies m
                LEFT JOIN movie_genres mg ON m.id = mg.movie_id
                LEFT JOIN genres g ON mg.genre_id = g.id
                LEFT JOIN movie_countries mc ON m.id = mc.movie_id
                LEFT JOIN countries c ON mc.country_id = c.id
                LEFT JOIN episodes e ON m.id = e.movie_id
                WHERE 1=1
            """
            params = []
            
            if search:
                query += " AND m.title LIKE %s"
                params.append(f'%{search}%')
            
            if genre_id:
                query += " AND m.id IN (SELECT movie_id FROM movie_genres WHERE genre_id = %s)"
                params.append(genre_id)
            
            if country_id:
                query += " AND m.id IN (SELECT movie_id FROM movie_countries WHERE country_id = %s)"
                params.append(country_id)
            
            if release_year:
                query += " AND m.release_year = %s"
                params.append(release_year)
            
            if movie_type:
                if movie_type == 'series':
                    query += " AND m.is_series = TRUE"
                elif movie_type == 'movie':
                    query += " AND m.is_series = FALSE"
            
            query += " GROUP BY m.id ORDER BY m.created_at DESC"
            
            cursor.execute(query, params)
            movies = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return jsonify(movies)
        else:
            return jsonify({'error': 'Database connection failed'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500
@movies_bp.route('/api/movies/<int:movie_id>', methods=['GET'])
def get_movie(movie_id):
    try:
        connection = current_app.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT m.*, 
                       GROUP_CONCAT(DISTINCT g.name) as genres,
                       GROUP_CONCAT(DISTINCT g.id) as genre_ids,
                       GROUP_CONCAT(DISTINCT c.name) as countries,
                       GROUP_CONCAT(DISTINCT c.id) as country_ids,
                       GROUP_CONCAT(DISTINCT a.name) as actors,
                       GROUP_CONCAT(DISTINCT a.id) as actor_ids,
                       COUNT(DISTINCT e.id) as episode_count
                FROM movies m
                LEFT JOIN movie_genres mg ON m.id = mg.movie_id
                LEFT JOIN genres g ON mg.genre_id = g.id
                LEFT JOIN movie_countries mc ON m.id = mc.movie_id
                LEFT JOIN countries c ON mc.country_id = c.id
                LEFT JOIN movie_actors ma ON m.id = ma.movie_id
                LEFT JOIN actors a ON ma.actor_id = a.id
                LEFT JOIN episodes e ON m.id = e.movie_id
                WHERE m.id = %s
                GROUP BY m.id
            """, (movie_id,))
            
            movie = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            if movie:
                return jsonify(movie)
            else:
                return jsonify({'error': 'Movie not found'}), 404
        else:
            return jsonify({'error': 'Database connection failed'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500

@movies_bp.route('/api/movies', methods=['POST'])
def create_movie():
    try:
        connection = current_app.get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor()

        # Extract form data
        title = request.form.get('title')
        slug = request.form.get('slug')
        description = request.form.get('description')
        meta_description = request.form.get('meta_description')
        release_year = request.form.get('release_year', type=int)
        duration = request.form.get('duration', type=int)
        trailer_url = request.form.get('trailer_url')
        video_url = request.form.get('video_url')
        is_series = request.form.get('is_series') == 'true'
        is_featured = request.form.get('is_featured') == 'true'
        genre_ids = request.form.getlist('genre_ids[]')
        country_ids = request.form.getlist('country_ids[]')
        actor_ids = request.form.getlist('actor_ids[]')

        # Validate required fields
        if not title or not slug:
            return jsonify({'error': 'Title and slug are required'}), 400

        # Handle file upload
        poster_url = None
        if 'moviePosterFile' in request.files:
            file = request.files['moviePosterFile']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                poster_url = f"/{UPLOAD_FOLDER}/{unique_filename}"

        # Insert movie into database - ĐÚNG thứ tự với bảng movies
        cursor.execute("""
            INSERT INTO movies (
                title, slug, description, meta_description, 
                release_year, duration, poster_url, trailer_url, 
                video_url, is_series, is_featured
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            title, slug, 
            description if description else None, 
            meta_description if meta_description else None,
            release_year if release_year else None,
            duration if duration else None,
            poster_url,  # Có thể là None
            trailer_url if trailer_url else None,
            video_url if video_url else None,
            is_series,
            is_featured
        ))

        movie_id = cursor.lastrowid

        # Insert genres
        for genre_id in genre_ids:
            if genre_id:  # Chỉ thêm nếu genre_id không rỗng
                cursor.execute("INSERT INTO movie_genres (movie_id, genre_id) VALUES (%s, %s)", 
                              (movie_id, genre_id))

        # Insert countries
        for country_id in country_ids:
            if country_id:  # Chỉ thêm nếu country_id không rỗng
                cursor.execute("INSERT INTO movie_countries (movie_id, country_id) VALUES (%s, %s)", 
                              (movie_id, country_id))

        # Insert actors
        for actor_id in actor_ids:
            if actor_id:  # Chỉ thêm nếu actor_id không rỗng
                cursor.execute("INSERT INTO movie_actors (movie_id, actor_id) VALUES (%s, %s)", 
                              (movie_id, actor_id))

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'id': movie_id, 'message': 'Movie created successfully'}), 201

    except Error as e:
        if connection:
            connection.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({'error': f'Failed to process request: {str(e)}'}), 500
@movies_bp.route('/api/movies/<int:movie_id>', methods=['PUT'])
def update_movie(movie_id):
    try:
        connection = current_app.get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor()

        # Extract form data
        title = request.form.get('title')
        slug = request.form.get('slug')
        description = request.form.get('description')
        meta_description = request.form.get('meta_description')
        release_year = request.form.get('release_year', type=int)
        duration = request.form.get('duration', type=int)
        trailer_url = request.form.get('trailer_url')
        video_url = request.form.get('video_url')
        is_series = request.form.get('is_series') == 'true'
        is_featured = request.form.get('is_featured') == 'true'
        genre_ids = request.form.getlist('genre_ids[]')
        country_ids = request.form.getlist('country_ids[]')
        actor_ids = request.form.getlist('actor_ids[]')

        # Validate required fields
        if not title or not slug:
            return jsonify({'error': 'Title and slug are required'}), 400

        # Handle file upload
        poster_url = None
        if 'moviePosterFile' in request.files:
            file = request.files['moviePosterFile']
            if file and file.filename != '' and allowed_file(file.filename):
                # Generate unique filename
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                poster_url = f"/{UPLOAD_FOLDER}/{unique_filename}"
        
        # Nếu không có file mới, giữ poster_url cũ
        if not poster_url:
            cursor.execute("SELECT poster_url FROM movies WHERE id = %s", (movie_id,))
            result = cursor.fetchone()
            poster_url = result[0] if result else None

        # Update movie in database - ĐÚNG thứ tự với bảng movies
        cursor.execute("""
            UPDATE movies 
            SET title = %s, slug = %s, description = %s, meta_description = %s,
                release_year = %s, duration = %s, poster_url = %s, trailer_url = %s,
                video_url = %s, is_series = %s, is_featured = %s
            WHERE id = %s
        """, (
            title, slug, 
            description if description else None, 
            meta_description if meta_description else None,
            release_year if release_year else None,
            duration if duration else None,
            poster_url,
            trailer_url if trailer_url else None,
            video_url if video_url else None,
            is_series,
            is_featured,
            movie_id
        ))

        # Update genres - chỉ xóa và thêm lại nếu có genre_ids
        cursor.execute("DELETE FROM movie_genres WHERE movie_id = %s", (movie_id,))
        for genre_id in genre_ids:
            if genre_id:
                cursor.execute("INSERT INTO movie_genres (movie_id, genre_id) VALUES (%s, %s)", 
                              (movie_id, genre_id))

        # Update countries - chỉ xóa và thêm lại nếu có country_ids
        cursor.execute("DELETE FROM movie_countries WHERE movie_id = %s", (movie_id,))
        for country_id in country_ids:
            if country_id:
                cursor.execute("INSERT INTO movie_countries (movie_id, country_id) VALUES (%s, %s)", 
                              (movie_id, country_id))

        # Update actors - chỉ xóa và thêm lại nếu có actor_ids
        cursor.execute("DELETE FROM movie_actors WHERE movie_id = %s", (movie_id,))
        for actor_id in actor_ids:
            if actor_id:
                cursor.execute("INSERT INTO movie_actors (movie_id, actor_id) VALUES (%s, %s)", 
                              (movie_id, actor_id))

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'message': 'Movie updated successfully'}), 200

    except Error as e:
        if connection:
            connection.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({'error': f'Failed to process request: {str(e)}'}), 500
@movies_bp.route('/api/movies/<int:movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    try:
        connection = current_app.get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            cursor.execute("DELETE FROM movies WHERE id = %s", (movie_id,))
            connection.commit()
            
            cursor.close()
            connection.close()
            
            return jsonify({'message': 'Movie deleted successfully'})
        else:
            return jsonify({'error': 'Database connection failed'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500