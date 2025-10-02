from flask import Blueprint, request, jsonify, current_app
from mysql.connector import Error
from werkzeug.utils import secure_filename
import os

actors_bp = Blueprint('actors', __name__)

# Helper: check file upload type
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@actors_bp.route('/api/actors', methods=['GET'])
def get_actors():
    connection = current_app.get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.id, a.name, a.photo_url, COUNT(ma.movie_id) as movie_count,
                   GROUP_CONCAT(m.title ORDER BY m.title SEPARATOR ', ') as notable_movies
            FROM actors a
            LEFT JOIN movie_actors ma ON a.id = ma.actor_id
            LEFT JOIN movies m ON ma.movie_id = m.id
            GROUP BY a.id
        """)
        actors = cursor.fetchall()
        return jsonify(actors)
    except Error as e:
        print(f"Error fetching actors: {e}")
        return jsonify({'error': 'Failed to fetch actors'}), 500
    finally:
        cursor.close()
        connection.close()


@actors_bp.route('/api/actors', methods=['POST'])
def add_actor():
    if request.is_json:
        data = request.get_json()
        name = data.get('name')
        photo_url = data.get('photo_url')
        movie_ids = data.get('movie_ids') or []
    else:
        name = request.form.get('name') or request.form.get('actor_name')
        photo_url = request.form.get('photo_url')
        movie_ids = request.form.getlist('movie_ids') or request.form.getlist('movie_ids[]') or []

    if isinstance(movie_ids, str):
        movie_ids = [m.strip() for m in movie_ids.split(',') if m.strip()]

    if not name:
        return jsonify({'error': 'Actor name is required'}), 400

    # Handle upload
    if 'photo' in request.files:
        file = request.files['photo']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            photo_url = f"/{file_path}"

    connection = current_app.get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO actors (name, photo_url) VALUES (%s, %s)", (name, photo_url))
        actor_id = cursor.lastrowid

        for movie_id in movie_ids:
            try:
                mid = int(movie_id)
                cursor.execute("INSERT INTO movie_actors (movie_id, actor_id) VALUES (%s, %s)", (mid, actor_id))
            except ValueError:
                pass

        connection.commit()
        return jsonify({'message': 'Actor added successfully', 'id': actor_id}), 201
    except Error as e:
        print(f"Error adding actor: {e}")
        return jsonify({'error': 'Failed to add actor'}), 500
    finally:
        cursor.close()
        connection.close()


@actors_bp.route('/api/actors/<int:id>', methods=['PUT'])
def update_actor(id):
    name = request.form.get('name')
    photo_url = request.form.get('photo_url')
    movie_ids = request.form.getlist('movie_ids')

    if not name:
        return jsonify({'error': 'Actor name is required'}), 400

    if 'photo' in request.files:
        file = request.files['photo']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            photo_url = f"/{file_path}"

    connection = current_app.get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE actors SET name = %s, photo_url = %s WHERE id = %s", (name, photo_url, id))
        if cursor.rowcount == 0:
            return jsonify({'error': 'Actor not found'}), 404

        cursor.execute("DELETE FROM movie_actors WHERE actor_id = %s", (id,))
        for movie_id in movie_ids:
            cursor.execute("INSERT INTO movie_actors (movie_id, actor_id) VALUES (%s, %s)", (movie_id, id))

        connection.commit()
        return jsonify({'message': 'Actor updated successfully'})
    except Error as e:
        print(f"Error updating actor: {e}")
        return jsonify({'error': 'Failed to update actor'}), 500
    finally:
        cursor.close()
        connection.close()


@actors_bp.route('/api/actors/<int:id>', methods=['DELETE'])
def delete_actor(id):
    connection = current_app.get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM actors WHERE id = %s", (id,))
        if cursor.rowcount == 0:
            return jsonify({'error': 'Actor not found'}), 404
        connection.commit()
        return jsonify({'message': 'Actor deleted successfully'})
    except Error as e:
        print(f"Error deleting actor: {e}")
        return jsonify({'error': 'Failed to delete actor'}), 500
    finally:
        cursor.close()
        connection.close()


@actors_bp.route('/api/movies', methods=['GET'])
def get_movies():
    connection = current_app.get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, title FROM movies")
        movies = cursor.fetchall()
        return jsonify(movies)
    except Error as e:
        print(f"Error fetching movies: {e}")
        return jsonify({'error': 'Failed to fetch movies'}), 500
    finally:
        cursor.close()
        connection.close()
