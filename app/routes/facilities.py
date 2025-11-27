from flask import Blueprint, jsonify, request
from psycopg2.extras import RealDictCursor
from app.db import get_db_connection
from app.utils.helpers import get_services_by_type, get_working_hours, get_contact_info

facilities_bp = Blueprint('facilities', __name__)

@facilities_bp.route('/api/facilities', methods=['GET'])
def get_all_facilities():
    try:
        functional_only = request.args.get('functional_only', 'false').lower() == 'true'
        district = request.args.get('district', None)
        facility_type = request.args.get('facility_type', None)
        ownership = request.args.get('ownership', None)
        
        #GET DATABASE CONNECTION
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                gid as id,
                code,
                name,
                "common nam" as common_name,
                ownership,
                type as facility_type,
                status,
                zone,
                district,
                latitude as lat,
                longitude as lng
            FROM malawi_health_registry
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND name IS NOT NULL
        """
        
        params = []
        
        if functional_only:
            query += " AND status = 'Functional'"
        if district:
            query += " AND district = %s"
            params.append(district)
        if facility_type:
            query += " AND type = %s"
            params.append(facility_type)
        if ownership:
            query += " AND ownership = %s"
            params.append(ownership)
        
        query += " ORDER BY name;"
        
        cur.execute(query, params)
        facilities = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': facilities,
            'count': len(facilities),
            'filters': {
                'functional_only': functional_only,
                'district': district,
                'facility_type': facility_type,
                'ownership': ownership
            }
        })
    except Exception as e:
        print(f"Error in get_all_facilities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

#GET DETAILED INFO ABOUT SPECIFIC FACILITY
@facilities_bp.route('/api/facility/<int:facility_id>', methods=['GET'])
def get_facility_details(facility_id):
    try:
        #GET DATABASE CONNECTION
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT 
                gid as id,
                code,
                name,
                "common nam" as common_name,
                ownership,
                type as facility_type,
                status,
                zone,
                district,
                latitude as lat,
                longitude as lng
            FROM malawi_health_registry
            WHERE gid = %s;
        """, (facility_id,))
        
        facility = cur.fetchone()
        
        if facility:
            # MOCK SERVICE
            facility['services'] = get_services_by_type(facility['facility_type'])
            facility['working_hours'] = get_working_hours(facility['facility_type'])
            facility['contact'] = get_contact_info(facility['district'])
        
        #CLOSE DATABASE CONNECTION
        cur.close()
        conn.close()
        
        #RETURN FACILITY DETAILS
        if facility:
            return jsonify({'success': True, 'data': facility})
        else:
            return jsonify({'success': False, 'error': 'Facility not found'}), 404
            
    except Exception as e:
        print(f"Error in get_facility_details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

#GET FACILITY TYPES
@facilities_bp.route('/api/facility-types', methods=['GET'])
def get_facility_types():
    try:
        #GET DATABASE CONNECTION
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        #GET FACILITY TYPES
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT DISTINCT type as facility_type, COUNT(*) as count
            FROM malawi_health_registry
            WHERE type IS NOT NULL 
            AND latitude IS NOT NULL 
            AND longitude IS NOT NULL
            GROUP BY type
            ORDER BY type;
        """)
        
        types = cur.fetchall()
        
        #CLOSE DATABASE CONNECTION
        cur.close()
        conn.close()
        
        #RETURN FACILITY TYPES (JSON RESPONSE)
        return jsonify({'success': True, 'data': types})
    except Exception as e:
        print(f"Error in get_facility_types: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

#GET FACILITY OWNERSHIPS
@facilities_bp.route('/api/ownerships', methods=['GET'])
def get_ownerships():
    try:
        #GET DATABASE CONNECTION
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500

        #GET FACILITY OWNERSHIPS    
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT DISTINCT ownership, COUNT(*) as count
            FROM malawi_health_registry
            WHERE ownership IS NOT NULL 
            AND latitude IS NOT NULL 
            AND longitude IS NOT NULL
            GROUP BY ownership
            ORDER BY ownership;
        """)
        
        ownerships = cur.fetchall()

        #CLOSE DATABASE CONNECTION
        cur.close()
        conn.close()
        
        #RETURN FACILITY OWNERSHIPS (JSON RESPONSE)
        return jsonify({'success': True, 'data': ownerships})
    except Exception as e:
        print(f"Error in get_ownerships: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

#GET NEAREST FACILITIES
@facilities_bp.route('/api/nearest', methods=['POST'])
def find_nearest_facilities():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
            
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
        limit = int(data.get('limit', 5))
        functional_only = data.get('functional_only', True)
        district = data.get('district', None)
        facility_type = data.get('facility_type', None)
        ownership = data.get('ownership', None)
        
        if limit < 1 or limit > 50:
            limit = 5
        
        #GET DATABASE CONNECTION
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                gid as id,
                code,
                name,
                "common nam" as common_name,
                ownership,
                type as facility_type,
                status,
                zone,
                district,
                latitude as lat,
                longitude as lng,
                ROUND(
                    CAST(
                        ST_Distance(
                            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                            ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                        ) / 1000 AS numeric
                    ), 2
                ) as distance_km
            FROM malawi_health_registry
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL
            AND name IS NOT NULL
        """
        
        params = [lng, lat]
        
        if functional_only:
            query += " AND status = 'Functional'"
        if district:
            query += " AND district = %s"
            params.append(district)
        if facility_type:
            query += " AND type = %s"
            params.append(facility_type)
        if ownership:
            query += " AND ownership = %s"
            params.append(ownership)
        
        query += """
            ORDER BY ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) <-> 
                     ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            LIMIT %s;
        """
        
        params.extend([lng, lat, limit])
        cur.execute(query, params)
        facilities = cur.fetchall()
        
        # ADD WORKING HOURS
        for facility in facilities:
            facility['services'] = get_services_by_type(facility['facility_type'])
            facility['working_hours'] = get_working_hours(facility['facility_type'])
        
        #CLOSE DATABASE CONNECTION
        cur.close()
        conn.close()
        
        #RETURN FACILITIES (JSON RESPONSE)
        return jsonify({
            'success': True,
            'data': facilities,
            'count': len(facilities),
            'query_point': {'lat': lat, 'lng': lng},
            'filters': {
                'functional_only': functional_only,
                'district': district,
                'facility_type': facility_type,
                'ownership': ownership
            }
        })
    except Exception as e:
        print(f"Error in find_nearest_facilities: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
