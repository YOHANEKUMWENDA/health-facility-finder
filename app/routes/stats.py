from flask import Blueprint, jsonify
from psycopg2.extras import RealDictCursor
from app.db import get_db_connection

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/api/stats', methods=['GET'])
def get_statistics():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        #EXECUTE QUERY
        cur.execute("""
            SELECT 
                COUNT(*) as total_facilities,
                COUNT(CASE WHEN status = 'Functional' THEN 1 END) as functional_facilities,
                COUNT(CASE WHEN status = 'Non-functional' THEN 1 END) as non_functional_facilities,
                COUNT(DISTINCT district) as total_districts,
                COUNT(DISTINCT type) as total_types,
                COUNT(DISTINCT ownership) as ownership_types
            FROM malawi_health_facilities
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
        """)
        
        stats = cur.fetchone()
        
        #EXECUTE QUERY
        cur.execute("""
            SELECT 
                type as facility_type,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'Functional' THEN 1 END) as functional
            FROM malawi_health_facilities
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY type
            ORDER BY total DESC;
        """)
        by_type = cur.fetchall()
        
        #EXECUTE QUERY
        cur.execute("""
            SELECT 
                district,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'Functional' THEN 1 END) as functional
            FROM malawi_health_facilities
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY district
            ORDER BY total DESC
            LIMIT 10;
        """)
        by_district = cur.fetchall()
        
        #EXECUTE QUERY
        cur.execute("""
            SELECT 
                ownership,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'Functional' THEN 1 END) as functional
            FROM malawi_health_facilities
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY ownership
            ORDER BY total DESC;
        """)
        by_ownership = cur.fetchall()
        
        #CLOSE CURSOR AND CONNECTION
        cur.close()
        conn.close()
        
        #RETURN JSON RESPONSE
        return jsonify({
            'success': True,
            'stats': stats,
            'by_type': by_type,
            'by_district': by_district,
            'by_ownership': by_ownership
        })
    except Exception as e:
        print(f"Error in get_statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
