from flask import Blueprint, request, jsonify, current_app
import mysql.connector
from mysql.connector import Error

episodes_bp = Blueprint('episodes', __name__)

@episodes_bp.route('/api/episodes', methods=['GET'])
def get_episodes():
    try:
        connection = current_app.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            movie_id = request.args.get('movie_id', type=int)
            search = request.args.get('search', '')
            sort_by = request.args.get('sort_by', 'episode_asc')
            
            query = """
                SELECT e.*, m.title as movie_title, m.poster_url as movie_poster
                FROM episodes e
                JOIN movies m ON e.movie_id = m.id
                WHERE 1=1
            """
            params = []
            
            if movie_id:
                query += " AND e.movie_id = %s"
                params.append(movie_id)
            
            if search:
                query += " AND e.title LIKE %s"
                params.append(f'%{search}%')
            
            # Sắp xếp
            if sort_by == 'episode_asc':
                query += " ORDER BY e.episode_number ASC"
            elif sort_by == 'episode_desc':
                query += " ORDER BY e.episode_number DESC"
            elif sort_by == 'newest':
                query += " ORDER BY e.created_at DESC"
            elif sort_by == 'oldest':
                query += " ORDER BY e.created_at ASC"
            
            cursor.execute(query, params)
            episodes = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return jsonify(episodes)
        else:
            return jsonify({'error': 'Database connection failed'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500

@episodes_bp.route('/api/episodes/<int:episode_id>', methods=['GET'])
def get_episode(episode_id):
    try:
        connection = current_app.get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT e.*, m.title as movie_title, m.poster_url as movie_poster
                FROM episodes e
                JOIN movies m ON e.movie_id = m.id
                WHERE e.id = %s
            """, (episode_id,))
            
            episode = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            if episode:
                return jsonify(episode)
            else:
                return jsonify({'error': 'Episode not found'}), 404
        else:
            return jsonify({'error': 'Database connection failed'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500

@episodes_bp.route('/api/episodes', methods=['POST'])
def create_episode():
    try:
        data = request.json
        connection = current_app.get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            cursor.execute("""
                INSERT INTO episodes (movie_id, episode_number, title, duration, video_url)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                data['movie_id'],
                data['episode_number'],
                data.get('title'),
                data.get('duration'),
                data['video_url']
            ))
            
            episode_id = cursor.lastrowid
            connection.commit()
            
            cursor.close()
            connection.close()
            
            return jsonify({'id': episode_id, 'message': 'Episode created successfully'})
        else:
            return jsonify({'error': 'Database connection failed'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500

@episodes_bp.route('/api/episodes/<int:episode_id>', methods=['PUT'])
def update_episode(episode_id):
    try:
        data = request.json
        connection = current_app.get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            cursor.execute("""
                UPDATE episodes 
                SET movie_id = %s, episode_number = %s, title = %s, 
                    duration = %s, video_url = %s
                WHERE id = %s
            """, (
                data['movie_id'],
                data['episode_number'],
                data.get('title'),
                data.get('duration'),
                data['video_url'],
                episode_id
            ))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return jsonify({'message': 'Episode updated successfully'})
        else:
            return jsonify({'error': 'Database connection failed'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500

@episodes_bp.route('/api/episodes/<int:episode_id>', methods=['DELETE'])
def delete_episode(episode_id):
    try:
        connection = current_app.get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            cursor.execute("DELETE FROM episodes WHERE id = %s", (episode_id,))
            connection.commit()
            
            cursor.close()
            connection.close()
            
            return jsonify({'message': 'Episode deleted successfully'})
        else:
            return jsonify({'error': 'Database connection failed'}), 500
    except Error as e:
        return jsonify({'error': str(e)}), 500