from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import mysql.connector
from mysql.connector import Error

countries_bp = Blueprint('countries', __name__)

# Routes cho quản lý quốc gia
@countries_bp.route('/quoc-gia')
def countries_page():
    return render_template('quocgia.html')

# API lấy danh sách quốc gia
@countries_bp.route('/api/countries', methods=['GET'])
def get_countries():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='anime'
        )
        
        cursor = connection.cursor(dictionary=True)
        
        # Lấy tham số phân trang và tìm kiếm
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'name_asc')
        
        offset = (page - 1) * per_page
        
        # Xây dựng query cơ bản
        base_query = """
            SELECT c.*, COUNT(mc.movie_id) as movie_count
            FROM countries c
            LEFT JOIN movie_countries mc ON c.id = mc.country_id
        """
        
        count_query = "SELECT COUNT(*) as total FROM countries c"
        
        # Thêm điều kiện tìm kiếm
        if search:
            where_clause = " WHERE c.name LIKE %s"
            search_param = f"%{search}%"
            base_query += where_clause
            count_query += where_clause
        else:
            search_param = None
        
        # Thêm GROUP BY
        base_query += " GROUP BY c.id"
        
        # Thêm sắp xếp
        if sort_by == 'name_asc':
            base_query += " ORDER BY c.name ASC"
        elif sort_by == 'name_desc':
            base_query += " ORDER BY c.name DESC"
        elif sort_by == 'movies_asc':
            base_query += " ORDER BY movie_count ASC"
        elif sort_by == 'movies_desc':
            base_query += " ORDER BY movie_count DESC"
        elif sort_by == 'newest':
            base_query += " ORDER BY c.id DESC"
        elif sort_by == 'oldest':
            base_query += " ORDER BY c.id ASC"
        
        # Thêm phân trang
        base_query += " LIMIT %s OFFSET %s"
        
        # Thực thi query đếm tổng
        if search_param:
            cursor.execute(count_query, (search_param,))
        else:
            cursor.execute(count_query)
        
        total_count = cursor.fetchone()['total']
        
        # Thực thi query chính
        if search_param:
            cursor.execute(base_query, (search_param, per_page, offset))
        else:
            cursor.execute(base_query, (per_page, offset))
        
        countries = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'countries': countries,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# API thêm quốc gia mới
@countries_bp.route('/api/countries', methods=['POST'])
def add_country():
    connection = None
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'success': False, 'error': 'Tên quốc gia là bắt buộc'}), 400
        
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='anime'
        )
        
        cursor = connection.cursor()
        
        # Kiểm tra xem quốc gia đã tồn tại chưa
        cursor.execute("SELECT id FROM countries WHERE name = %s", (name,))
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'Quốc gia đã tồn tại'}), 400
        
        # Thêm quốc gia mới
        cursor.execute("INSERT INTO countries (name) VALUES (%s)", (name,))
        connection.commit()
        
        return jsonify({'success': True, 'message': 'Thêm quốc gia thành công'})
        
    except Error as e:
        if connection:
            connection.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# API cập nhật quốc gia
@countries_bp.route('/api/countries/<int:country_id>', methods=['PUT'])
def update_country(country_id):
    connection = None
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'success': False, 'error': 'Tên quốc gia là bắt buộc'}), 400
        
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='anime'
        )
        
        cursor = connection.cursor()
        
        # Kiểm tra xem quốc gia đã tồn tại chưa (trừ chính nó)
        cursor.execute("SELECT id FROM countries WHERE name = %s AND id != %s", (name, country_id))
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'Quốc gia đã tồn tại'}), 400
        
        # Cập nhật quốc gia
        cursor.execute("UPDATE countries SET name = %s WHERE id = %s", (name, country_id))
        connection.commit()
        
        return jsonify({'success': True, 'message': 'Cập nhật quốc gia thành công'})
        
    except Error as e:
        if connection:
            connection.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# API xóa quốc gia
@countries_bp.route('/api/countries/<int:country_id>', methods=['DELETE'])
def delete_country(country_id):
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='anime'
        )
        
        cursor = connection.cursor()
        
        # Kiểm tra xem quốc gia có đang được sử dụng không
        cursor.execute("SELECT COUNT(*) FROM movie_countries WHERE country_id = %s", (country_id,))
        movie_count = cursor.fetchone()[0]
        
        if movie_count > 0:
            return jsonify({
                'success': False, 
                'error': f'Không thể xóa quốc gia này vì có {movie_count} phim đang sử dụng'
            }), 400
        
        # Xóa quốc gia
        cursor.execute("DELETE FROM countries WHERE id = %s", (country_id,))
        connection.commit()
        
        return jsonify({'success': True, 'message': 'Xóa quốc gia thành công'})
        
    except Error as e:
        if connection:
            connection.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# API lấy thống kê
@countries_bp.route('/api/countries/stats', methods=['GET'])
def get_countries_stats():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='anime'
        )
        
        cursor = connection.cursor(dictionary=True)
        
        # Tổng số quốc gia
        cursor.execute("SELECT COUNT(*) as total_countries FROM countries")
        total_countries = cursor.fetchone()['total_countries']
        
        # Tổng số phim có quốc gia
        cursor.execute("""
            SELECT COUNT(DISTINCT movie_id) as total_movies 
            FROM movie_countries
        """)
        total_movies = cursor.fetchone()['total_movies']
        
        return jsonify({
            'success': True,
            'stats': {
                'total_countries': total_countries,
                'total_movies': total_movies
            }
        })
        
    except Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()