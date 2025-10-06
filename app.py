from flask import Flask, render_template, jsonify, request
import mysql.connector
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'm',
}

# Cấu hình upload file
UPLOAD_FOLDER = 'public/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except Error as e:
        print("Lỗi kết nối MySQL:", e)
    return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bophim')
def bophim():
    return render_template('bophim.html')
@app.route('/tapphim')
def tapphim():
    return render_template('tapphim.html')
# API cho danh sách anime
@app.route('/api/anime', methods=['GET'])
def get_anime_list():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Lấy tham số từ query string
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        year = request.args.get('year', '')
        featured = request.args.get('featured', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Xây dựng query
        query = """
            SELECT a.*, 
                   GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') as categories
            FROM anime a
            LEFT JOIN anime_categories ac ON a.id = ac.anime_id
            LEFT JOIN categories c ON ac.category_id = c.id
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (a.title LIKE %s OR a.slug LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        if status:
            query += " AND a.status = %s"
            params.append(status)
            
        if year:
            query += " AND a.release_year = %s"
            params.append(year)
            
        if featured:
            query += " AND a.featured = %s"
            params.append(featured.lower() == 'true')
        
        query += " GROUP BY a.id"
        
        # Thêm sắp xếp
        if sort_by in ['title', 'rating', 'total_views', 'created_at']:
            order = 'DESC' if sort_order == 'desc' else 'ASC'
            query += f" ORDER BY a.{sort_by} {order}"
        
        # Thêm phân trang
        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        anime_list = cursor.fetchall()
        
        # Đếm tổng số bản ghi
        count_query = "SELECT COUNT(DISTINCT a.id) as total FROM anime a WHERE 1=1"
        count_params = []
        
        if search:
            count_query += " AND (a.title LIKE %s OR a.slug LIKE %s)"
            count_params.extend([f'%{search}%', f'%{search}%'])
        
        if status:
            count_query += " AND a.status = %s"
            count_params.append(status)
            
        if year:
            count_query += " AND a.release_year = %s"
            count_params.append(year)
            
        if featured:
            count_query += " AND a.featured = %s"
            count_params.append(featured.lower() == 'true')
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()['total']
        
        return jsonify({
            'anime': anime_list,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API lấy thông tin chi tiết anime
@app.route('/api/anime/<int:anime_id>', methods=['GET'])
def get_anime(anime_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM anime WHERE id = %s"
        cursor.execute(query, (anime_id,))
        anime = cursor.fetchone()
        
        if not anime:
            return jsonify({'error': 'Anime not found'}), 404
            
        return jsonify(anime)
        
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API thêm anime mới
@app.route('/api/anime', methods=['POST'])
def create_anime():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title') or not data.get('slug'):
            return jsonify({'error': 'Title and slug are required'}), 400
        
        cursor = connection.cursor()
        
        query = """
            INSERT INTO anime (
                title, slug, description, poster_image, cover_image,
                release_year, status, total_episodes, duration_per_episode,
                studio, director, author, country, featured,
                meta_title, meta_description, meta_keywords
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            data.get('title'),
            data.get('slug'),
            data.get('description'),
            data.get('poster_image'),
            data.get('cover_image'),
            data.get('release_year'),
            data.get('status', 'ongoing'),
            data.get('total_episodes', 0),
            data.get('duration_per_episode'),
            data.get('studio'),
            data.get('director'),
            data.get('author'),
            data.get('country', 'Nhật Bản'),
            data.get('featured', False),
            data.get('meta_title'),
            data.get('meta_description'),
            data.get('meta_keywords')
        )
        
        cursor.execute(query, values)
        anime_id = cursor.lastrowid
        connection.commit()
        
        return jsonify({'id': anime_id, 'message': 'Anime created successfully'}), 201
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API cập nhật anime
@app.route('/api/anime/<int:anime_id>', methods=['PUT'])
def update_anime(anime_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.get_json()
        
        cursor = connection.cursor()
        
        query = """
            UPDATE anime SET
                title = %s, slug = %s, description = %s, poster_image = %s,
                cover_image = %s, release_year = %s, status = %s,
                total_episodes = %s, duration_per_episode = %s, studio = %s,
                director = %s, author = %s, country = %s, featured = %s,
                meta_title = %s, meta_description = %s, meta_keywords = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        values = (
            data.get('title'),
            data.get('slug'),
            data.get('description'),
            data.get('poster_image'),
            data.get('cover_image'),
            data.get('release_year'),
            data.get('status'),
            data.get('total_episodes'),
            data.get('duration_per_episode'),
            data.get('studio'),
            data.get('director'),
            data.get('author'),
            data.get('country'),
            data.get('featured'),
            data.get('meta_title'),
            data.get('meta_description'),
            data.get('meta_keywords'),
            anime_id
        )
        
        cursor.execute(query, values)
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Anime not found'}), 404
            
        return jsonify({'message': 'Anime updated successfully'})
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API xóa anime
@app.route('/api/anime/<int:anime_id>', methods=['DELETE'])
def delete_anime(anime_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        query = "DELETE FROM anime WHERE id = %s"
        cursor.execute(query, (anime_id,))
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Anime not found'}), 404
            
        return jsonify({'message': 'Anime deleted successfully'})
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API lấy danh sách categories
@app.route('/api/categories', methods=['GET'])
def get_categories():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT id, name, slug FROM categories ORDER BY name"
        cursor.execute(query)
        categories = cursor.fetchall()
        
        return jsonify(categories)
        
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API lấy categories của anime
@app.route('/api/anime/<int:anime_id>/categories', methods=['GET'])
def get_anime_categories(anime_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT c.id, c.name 
            FROM categories c
            INNER JOIN anime_categories ac ON c.id = ac.category_id
            WHERE ac.anime_id = %s
        """
        cursor.execute(query, (anime_id,))
        categories = cursor.fetchall()
        
        return jsonify(categories)
        
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API cập nhật categories cho anime
@app.route('/api/anime/<int:anime_id>/categories', methods=['POST', 'PUT'])
def update_anime_categories(anime_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.get_json()
        category_ids = data.get('category_ids', [])
        
        cursor = connection.cursor()
        
        # Xóa categories hiện tại
        delete_query = "DELETE FROM anime_categories WHERE anime_id = %s"
        cursor.execute(delete_query, (anime_id,))
        
        # Thêm categories mới
        if category_ids:
            insert_query = "INSERT INTO anime_categories (anime_id, category_id) VALUES (%s, %s)"
            for category_id in category_ids:
                cursor.execute(insert_query, (anime_id, category_id))
        
        connection.commit()
        
        return jsonify({'message': 'Categories updated successfully'})
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API upload file
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Thêm timestamp để tránh trùng tên
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file.save(filepath)
        
        # Trả về URL tương đối
        file_url = f"/static/uploads/{filename}"
        return jsonify({'url': file_url})
    
    return jsonify({'error': 'File type not allowed'}), 400
# API lấy danh sách seasons của anime
@app.route('/api/anime/<int:anime_id>/seasons', methods=['GET'])
def get_anime_seasons(anime_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT s.*, COUNT(e.id) as episode_count
            FROM seasons s
            LEFT JOIN episodes e ON s.id = e.season_id
            WHERE s.anime_id = %s
            GROUP BY s.id
            ORDER BY s.season_number
        """
        cursor.execute(query, (anime_id,))
        seasons = cursor.fetchall()
        
        return jsonify(seasons)
        
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API tạo season mới
@app.route('/api/anime/<int:anime_id>/seasons', methods=['POST'])
def create_season(anime_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.get_json()
        
        cursor = connection.cursor()
        
        query = """
            INSERT INTO seasons (anime_id, season_number, name, episode_count, release_year)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        values = (
            anime_id,
            data.get('season_number'),
            data.get('name'),
            data.get('episode_count', 0),
            data.get('release_year')
        )
        
        cursor.execute(query, values)
        season_id = cursor.lastrowid
        connection.commit()
        
        return jsonify({'id': season_id, 'message': 'Season created successfully'})
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API lấy thông tin anime
@app.route('/api/anime/<int:anime_id>', methods=['GET'])
def get_anime_details(anime_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM anime WHERE id = %s"
        cursor.execute(query, (anime_id,))
        anime = cursor.fetchone()
        
        if not anime:
            return jsonify({'error': 'Anime not found'}), 404
            
        return jsonify(anime)
        
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API lấy danh sách episodes
@app.route('/api/episodes', methods=['GET'])
def get_episodes():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Lấy tham số
        season_id = request.args.get('season_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        
        # Xây dựng query
        query = """
            SELECT e.*, s.season_number, a.title as anime_title
            FROM episodes e
            JOIN seasons s ON e.season_id = s.id
            JOIN anime a ON s.anime_id = a.id
            WHERE 1=1
        """
        params = []
        
        if season_id:
            query += " AND e.season_id = %s"
            params.append(season_id)
        
        if search:
            query += " AND (e.title LIKE %s OR e.description LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        # Đếm tổng số bản ghi
        count_query = "SELECT COUNT(*) as total FROM episodes e WHERE 1=1"
        count_params = []
        
        if season_id:
            count_query += " AND e.season_id = %s"
            count_params.append(season_id)
        
        if search:
            count_query += " AND (e.title LIKE %s OR e.description LIKE %s)"
            count_params.extend([f'%{search}%', f'%{search}%'])
        
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()['total']
        
        # Thêm phân trang và sắp xếp
        query += " ORDER BY e.episode_number LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor.execute(query, params)
        episodes = cursor.fetchall()
        
        return jsonify({
            'episodes': episodes,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API tạo episode mới
@app.route('/api/episodes', methods=['POST'])
def create_episode():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('season_id') or not data.get('episode_number') or not data.get('video_url'):
            return jsonify({'error': 'Season ID, episode number and video URL are required'}), 400
        
        cursor = connection.cursor()
        
        # Kiểm tra xem episode number đã tồn tại chưa
        check_query = "SELECT id FROM episodes WHERE season_id = %s AND episode_number = %s"
        cursor.execute(check_query, (data.get('season_id'), data.get('episode_number')))
        existing_episode = cursor.fetchone()
        
        if existing_episode:
            return jsonify({'error': 'Episode number already exists for this season'}), 400
        
        query = """
            INSERT INTO episodes (
                season_id, episode_number, title, description, video_url,
                thumbnail_url, duration, views, release_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            data.get('season_id'),
            data.get('episode_number'),
            data.get('title'),
            data.get('description'),
            data.get('video_url'),
            data.get('thumbnail_url'),
            data.get('duration'),
            data.get('views', 0),
            data.get('release_date')
        )
        
        cursor.execute(query, values)
        episode_id = cursor.lastrowid
        
        # Cập nhật episode count trong season
        update_season_query = """
            UPDATE seasons SET episode_count = (
                SELECT COUNT(*) FROM episodes WHERE season_id = %s
            ) WHERE id = %s
        """
        cursor.execute(update_season_query, (data.get('season_id'), data.get('season_id')))
        
        connection.commit()
        
        return jsonify({'id': episode_id, 'message': 'Episode created successfully'}), 201
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API cập nhật episode
@app.route('/api/episodes/<int:episode_id>', methods=['PUT'])
def update_episode(episode_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.get_json()
        
        cursor = connection.cursor()
        
        # Kiểm tra episode tồn tại
        check_query = "SELECT season_id FROM episodes WHERE id = %s"
        cursor.execute(check_query, (episode_id,))
        existing_episode = cursor.fetchone()
        
        if not existing_episode:
            return jsonify({'error': 'Episode not found'}), 404
        
        old_season_id = existing_episode['season_id']
        new_season_id = data.get('season_id', old_season_id)
        
        # Kiểm tra episode number trùng (nếu có thay đổi)
        if data.get('episode_number'):
            check_duplicate_query = """
                SELECT id FROM episodes 
                WHERE season_id = %s AND episode_number = %s AND id != %s
            """
            cursor.execute(check_duplicate_query, (new_season_id, data.get('episode_number'), episode_id))
            duplicate_episode = cursor.fetchone()
            
            if duplicate_episode:
                return jsonify({'error': 'Episode number already exists for this season'}), 400
        
        query = """
            UPDATE episodes SET
                season_id = %s, episode_number = %s, title = %s, description = %s,
                video_url = %s, thumbnail_url = %s, duration = %s, release_date = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        values = (
            new_season_id,
            data.get('episode_number'),
            data.get('title'),
            data.get('description'),
            data.get('video_url'),
            data.get('thumbnail_url'),
            data.get('duration'),
            data.get('release_date'),
            episode_id
        )
        
        cursor.execute(query, values)
        
        # Cập nhật episode count cho season cũ và mới (nếu có thay đổi season)
        if old_season_id != new_season_id:
            update_season_query = """
                UPDATE seasons SET episode_count = (
                    SELECT COUNT(*) FROM episodes WHERE season_id = %s
                ) WHERE id IN (%s, %s)
            """
            cursor.execute(update_season_query, (old_season_id, old_season_id, new_season_id))
        else:
            update_season_query = """
                UPDATE seasons SET episode_count = (
                    SELECT COUNT(*) FROM episodes WHERE season_id = %s
                ) WHERE id = %s
            """
            cursor.execute(update_season_query, (new_season_id, new_season_id))
        
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Episode not found'}), 404
            
        return jsonify({'message': 'Episode updated successfully'})
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API xóa episode
@app.route('/api/episodes/<int:episode_id>', methods=['DELETE'])
def delete_episode(episode_id):
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        
        # Lấy season_id trước khi xóa
        get_season_query = "SELECT season_id FROM episodes WHERE id = %s"
        cursor.execute(get_season_query, (episode_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': 'Episode not found'}), 404
        
        season_id = result['season_id']
        
        # Xóa episode
        delete_query = "DELETE FROM episodes WHERE id = %s"
        cursor.execute(delete_query, (episode_id,))
        
        # Cập nhật episode count trong season
        update_season_query = """
            UPDATE seasons SET episode_count = (
                SELECT COUNT(*) FROM episodes WHERE season_id = %s
            ) WHERE id = %s
        """
        cursor.execute(update_season_query, (season_id, season_id))
        
        connection.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Episode not found'}), 404
            
        return jsonify({'message': 'Episode deleted successfully'})
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# API import episodes từ Excel
@app.route('/api/episodes/import', methods=['POST'])
def import_episodes():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        data = request.get_json()
        episodes_data = data.get('episodes', [])
        season_id = data.get('season_id')
        action = data.get('action', 'add')  # add, update, replace
        
        if not season_id:
            return jsonify({'error': 'Season ID is required'}), 400
        
        cursor = connection.cursor()
        results = {
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # Nếu là replace, xóa tất cả episodes cũ trong season
        if action == 'replace':
            delete_query = "DELETE FROM episodes WHERE season_id = %s"
            cursor.execute(delete_query, (season_id,))
        
        for index, episode_data in enumerate(episodes_data):
            try:
                episode_number = episode_data.get('episode_number')
                video_url = episode_data.get('video_url')
                
                if not episode_number or not video_url:
                    results['failed'] += 1
                    results['errors'].append(f"Dòng {index + 1}: Số tập và URL video là bắt buộc")
                    continue
                
                # Kiểm tra episode đã tồn tại chưa
                if action == 'update' or action == 'replace':
                    check_query = "SELECT id FROM episodes WHERE season_id = %s AND episode_number = %s"
                    cursor.execute(check_query, (season_id, episode_number))
                    existing_episode = cursor.fetchone()
                    
                    if existing_episode and action == 'update':
                        # Update episode hiện có
                        update_query = """
                            UPDATE episodes SET
                                title = %s, description = %s, video_url = %s,
                                duration = %s, release_date = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """
                        cursor.execute(update_query, (
                            episode_data.get('title'),
                            episode_data.get('description'),
                            video_url,
                            episode_data.get('duration'),
                            episode_data.get('release_date'),
                            existing_episode['id']
                        ))
                    else:
                        # Thêm episode mới
                        insert_query = """
                            INSERT INTO episodes (
                                season_id, episode_number, title, description, video_url, duration, release_date
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(insert_query, (
                            season_id,
                            episode_number,
                            episode_data.get('title'),
                            episode_data.get('description'),
                            video_url,
                            episode_data.get('duration'),
                            episode_data.get('release_date')
                        ))
                else:
                    # Chỉ thêm mới
                    insert_query = """
                        INSERT INTO episodes (
                            season_id, episode_number, title, description, video_url, duration, release_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (
                        season_id,
                        episode_number,
                        episode_data.get('title'),
                        episode_data.get('description'),
                        video_url,
                        episode_data.get('duration'),
                        episode_data.get('release_date')
                    ))
                
                results['successful'] += 1
                
            except Error as e:
                results['failed'] += 1
                results['errors'].append(f"Dòng {index + 1}: {str(e)}")
                continue
        
        # Cập nhật episode count trong season
        update_season_query = """
            UPDATE seasons SET episode_count = (
                SELECT COUNT(*) FROM episodes WHERE season_id = %s
            ) WHERE id = %s
        """
        cursor.execute(update_season_query, (season_id, season_id))
        
        connection.commit()
        
        return jsonify({
            'message': f'Import completed: {results["successful"]} thành công, {results["failed"]} thất bại',
            'results': results
        })
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
if __name__ == '__main__':
    app.run(debug=True, port=5000)