from flask import Blueprint, jsonify, request, current_app

genres_bp = Blueprint('genres', __name__)

# GET all genres
@genres_bp.route('/api/genres', methods=['GET'])
def get_genres():
    connection = current_app.get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name, description FROM genres")
        genres = cursor.fetchall()

        # thêm thống kê phim + view
        for genre in genres:
            cursor.execute("""
                SELECT COUNT(mg.movie_id) as movie_count, SUM(m.view_count) as view_count
                FROM movie_genres mg
                JOIN movies m ON mg.movie_id = m.id
                WHERE mg.genre_id = %s
            """, (genre['id'],))
            result = cursor.fetchone()
            genre['movie_count'] = result['movie_count'] or 0
            genre['view_count'] = result['view_count'] or 0

        return jsonify(genres)
    finally:
        cursor.close()
        connection.close()


# POST add new genre
@genres_bp.route('/api/genres', methods=['POST'])
def add_genre():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')

    if not name:
        return jsonify({'error': 'Genre name is required'}), 400

    connection = current_app.get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO genres (name, description) VALUES (%s, %s)", (name, description))
        connection.commit()
        return jsonify({'message': 'Genre added successfully'}), 201
    finally:
        cursor.close()
        connection.close()


# PUT update genre
@genres_bp.route('/api/genres/<int:id>', methods=['PUT'])
def update_genre(id):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')

    if not name:
        return jsonify({'error': 'Genre name is required'}), 400

    connection = current_app.get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE genres SET name=%s, description=%s WHERE id=%s", (name, description, id))
        if cursor.rowcount == 0:
            return jsonify({'error': 'Genre not found'}), 404
        connection.commit()
        return jsonify({'message': 'Genre updated successfully'})
    finally:
        cursor.close()
        connection.close()


# DELETE genre
@genres_bp.route('/api/genres/<int:id>', methods=['DELETE'])
def delete_genre(id):
    connection = current_app.get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM genres WHERE id=%s", (id,))
        if cursor.rowcount == 0:
            return jsonify({'error': 'Genre not found'}), 404
        connection.commit()
        return jsonify({'message': 'Genre deleted successfully'})
    finally:
        cursor.close()
        connection.close()
