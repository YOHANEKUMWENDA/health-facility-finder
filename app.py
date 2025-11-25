from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'dbname': 'health_facilities_db',
    'user': 'progress',
    'password': 'dayire',
    'host': 'localhost',
    'port': 5432
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def home():
    return jsonify({
        'message': 'Malawi Health Facility Finder API',
        'version': '5.0',
        'data_source': 'Ministry of Health - Official Registry 2023',
        'new_features': [
            'Geocoding for location search',
            'Route optimization',
            'Services information',
            'Working hours',
            'User location detection'
        ],
        'endpoints': {
            'GET /api/facilities': 'Get all facilities with filters',
            'GET /api/districts': 'Get list of all districts',
            'GET /api/facility-types': 'Get list of all facility types',
            'GET /api/ownerships': 'Get list of ownership types',
            'POST /api/nearest': 'Find nearest facilities',
            'POST /api/geocode': 'Convert address to coordinates',
            'POST /api/route': 'Get optimized route to facility',
            'GET /api/facility/<id>': 'Get facility details with services',
            'GET /api/stats': 'Get statistics',
            'GET /health': 'Health check'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Health Facility Finder API is running',
        'data_source': 'Malawi Ministry of Health Registry 2023'
    })

@app.route('/api/districts', methods=['GET'])
def get_districts():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT DISTINCT district, COUNT(*) as count
            FROM malawi_health_registry
            WHERE district IS NOT NULL 
            AND latitude IS NOT NULL 
            AND longitude IS NOT NULL
            GROUP BY district
            ORDER BY district;
        """)
        
        districts = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'data': districts})
    except Exception as e:
        print(f"Error in get_districts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/facility-types', methods=['GET'])
def get_facility_types():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
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
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'data': types})
    except Exception as e:
        print(f"Error in get_facility_types: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ownerships', methods=['GET'])
def get_ownerships():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
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
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'data': ownerships})
    except Exception as e:
        print(f"Error in get_ownerships: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/facility/<int:facility_id>', methods=['GET'])
def get_facility_details(facility_id):
    """Get detailed information about a specific facility including services"""
    try:
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
            # Add mock services based on facility type
            facility['services'] = get_services_by_type(facility['facility_type'])
            facility['working_hours'] = get_working_hours(facility['facility_type'])
            facility['contact'] = get_contact_info(facility['district'])
        
        cur.close()
        conn.close()
        
        if facility:
            return jsonify({'success': True, 'data': facility})
        else:
            return jsonify({'success': False, 'error': 'Facility not found'}), 404
            
    except Exception as e:
        print(f"Error in get_facility_details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_services_by_type(facility_type):
    """Return services based on facility type"""
    services = {
        'Hospital': [
            'Emergency Services',
            'Inpatient Care',
            'Outpatient Services',
            'Surgery',
            'Maternity Services',
            'Laboratory Services',
            'Pharmacy',
            'X-Ray/Imaging',
            'Ambulance Services'
        ],
        'Health Centre': [
            'Outpatient Services',
            'Maternity Services',
            'Child Health Services',
            'HIV Testing & Treatment',
            'TB Services',
            'Pharmacy',
            'Laboratory Services'
        ],
        'Clinic': [
            'Basic Consultation',
            'Immunization',
            'Family Planning',
            'Antenatal Care',
            'HIV Testing',
            'Minor Treatments'
        ],
        'Dispensary': [
            'Basic Consultation',
            'Medication Distribution',
            'Immunization',
            'First Aid'
        ]
    }
    return services.get(facility_type, ['General Health Services'])

def get_working_hours(facility_type):
    """Return working hours based on facility type"""
    if facility_type == 'Hospital':
        return {
            'weekdays': '24 Hours',
            'weekends': '24 Hours',
            'emergency': '24/7 Available'
        }
    elif facility_type in ['Health Centre', 'Clinic']:
        return {
            'weekdays': '7:30 AM - 4:30 PM',
            'saturday': '7:30 AM - 12:00 PM',
            'sunday': 'Closed',
            'emergency': 'Limited emergency services'
        }
    else:
        return {
            'weekdays': '8:00 AM - 4:00 PM',
            'weekends': 'Closed',
            'emergency': 'Refer to nearest hospital'
        }

def get_contact_info(district):
    """Return mock contact information"""
    return {
        'phone': '+265 1 XXX XXX',
        'email': f'{district.lower().replace(" ", "")}@health.gov.mw',
        'district_office': f'{district} District Health Office'
    }

@app.route('/api/facilities', methods=['GET'])
def get_all_facilities():
    try:
        functional_only = request.args.get('functional_only', 'false').lower() == 'true'
        district = request.args.get('district', None)
        facility_type = request.args.get('facility_type', None)
        ownership = request.args.get('ownership', None)
        
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

@app.route('/api/nearest', methods=['POST'])
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
        
        # Add services and hours to each facility
        for facility in facilities:
            facility['services'] = get_services_by_type(facility['facility_type'])
            facility['working_hours'] = get_working_hours(facility['facility_type'])
        
        cur.close()
        conn.close()
        
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

@app.route('/api/geocode', methods=['POST'])
def geocode_location():
    """Geocoding for Malawi locations - searches known locations and database"""
    try:
        data = request.get_json()
        location = data.get('location', '').strip()
        
        if not location:
            return jsonify({'success': False, 'error': 'Location cannot be empty'}), 400
        
        # Comprehensive list of all Malawi districts and major cities
        locations = {
            # Major cities
            'lilongwe': {'lat': -13.9626, 'lng': 33.7741, 'name': 'Lilongwe'},
            'blantyre': {'lat': -15.7861, 'lng': 35.0058, 'name': 'Blantyre'},
            'mzuzu': {'lat': -11.4597, 'lng': 34.0201, 'name': 'Mzuzu'},
            'zomba': {'lat': -15.3860, 'lng': 35.3188, 'name': 'Zomba'},
            
            # All 28 districts of Malawi
            'balaka': {'lat': -14.9833, 'lng': 34.9500, 'name': 'Balaka'},
            'blantyre district': {'lat': -15.7861, 'lng': 35.0058, 'name': 'Blantyre'},
            'chikwawa': {'lat': -16.0369, 'lng': 34.7986, 'name': 'Chikwawa'},
            'chiradzulu': {'lat': -15.6833, 'lng': 35.1333, 'name': 'Chiradzulu'},
            'chitipa': {'lat': -9.7036, 'lng': 33.2697, 'name': 'Chitipa'},
            'dedza': {'lat': -14.3779, 'lng': 34.3333, 'name': 'Dedza'},
            'dowa': {'lat': -13.6500, 'lng': 33.9333, 'name': 'Dowa'},
            'karonga': {'lat': -9.9333, 'lng': 33.9333, 'name': 'Karonga'},
            'kasungu': {'lat': -13.0333, 'lng': 33.4833, 'name': 'Kasungu'},
            'likoma': {'lat': -12.0583, 'lng': 34.7333, 'name': 'Likoma'},
            'lilongwe district': {'lat': -13.9626, 'lng': 33.7741, 'name': 'Lilongwe'},
            'machinga': {'lat': -14.9667, 'lng': 35.5167, 'name': 'Machinga'},
            'mangochi': {'lat': -14.4784, 'lng': 35.2644, 'name': 'Mangochi'},
            'mchinji': {'lat': -13.8000, 'lng': 32.9000, 'name': 'Mchinji'},
            'mulanje': {'lat': -16.0167, 'lng': 35.5000, 'name': 'Mulanje'},
            'mwanza': {'lat': -15.6103, 'lng': 34.5269, 'name': 'Mwanza'},
            'mzimba': {'lat': -11.9000, 'lng': 33.6000, 'name': 'Mzimba'},
            'neno': {'lat': -15.4000, 'lng': 34.6167, 'name': 'Neno'},
            'nkhata bay': {'lat': -11.6061, 'lng': 34.2931, 'name': 'Nkhata Bay'},
            'nkhotakota': {'lat': -12.9167, 'lng': 34.3000, 'name': 'Nkhotakota'},
            'nsanje': {'lat': -16.9200, 'lng': 35.2628, 'name': 'Nsanje'},
            'ntcheu': {'lat': -14.8167, 'lng': 34.6333, 'name': 'Ntcheu'},
            'ntchisi': {'lat': -13.5167, 'lng': 33.9167, 'name': 'Ntchisi'},
            'phalombe': {'lat': -15.8000, 'lng': 35.6500, 'name': 'Phalombe'},
            'rumphi': {'lat': -10.8833, 'lng': 33.8500, 'name': 'Rumphi'},
            'salima': {'lat': -13.7804, 'lng': 34.4360, 'name': 'Salima'},
            'thyolo': {'lat': -16.0667, 'lng': 35.1333, 'name': 'Thyolo'},
            'zomba district': {'lat': -15.3860, 'lng': 35.3188, 'name': 'Zomba'},
            
            # Alternative spellings
            'nkatabay': {'lat': -11.6061, 'lng': 34.2931, 'name': 'Nkhata Bay'},
            'mzimba north': {'lat': -11.4000, 'lng': 33.6000, 'name': 'Mzimba'},
            'mzimba south': {'lat': -12.2000, 'lng': 33.6000, 'name': 'Mzimba'},
        }
        
        location_key = location.lower().strip()
        
        # First, check hardcoded locations
        if location_key in locations:
            result = locations[location_key]
            return jsonify({'success': True, 'data': result})
        
        # If not found, search in database for district
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                
                # Search for matching district in database
                cur.execute("""
                    SELECT 
                        district,
                        AVG(latitude) as lat,
                        AVG(longitude) as lng,
                        COUNT(*) as facility_count
                    FROM malawi_health_registry
                    WHERE LOWER(district) = LOWER(%s)
                    AND latitude IS NOT NULL 
                    AND longitude IS NOT NULL
                    GROUP BY district
                    LIMIT 1;
                """, (location,))
                
                district_result = cur.fetchone()
                
                if district_result:
                    result = {
                        'lat': float(district_result['lat']),
                        'lng': float(district_result['lng']),
                        'name': district_result['district'],
                        'facility_count': district_result['facility_count']
                    }
                    cur.close()
                    conn.close()
                    return jsonify({'success': True, 'data': result})
                
                # If still not found, try partial match
                cur.execute("""
                    SELECT 
                        district,
                        AVG(latitude) as lat,
                        AVG(longitude) as lng,
                        COUNT(*) as facility_count
                    FROM malawi_health_registry
                    WHERE LOWER(district) LIKE LOWER(%s)
                    AND latitude IS NOT NULL 
                    AND longitude IS NOT NULL
                    GROUP BY district
                    LIMIT 1;
                """, (f'%{location}%',))
                
                partial_result = cur.fetchone()
                cur.close()
                conn.close()
                
                if partial_result:
                    result = {
                        'lat': float(partial_result['lat']),
                        'lng': float(partial_result['lng']),
                        'name': partial_result['district'],
                        'facility_count': partial_result['facility_count']
                    }
                    return jsonify({'success': True, 'data': result})
                    
            except Exception as db_error:
                print(f"Database search error: {db_error}")
                if conn:
                    conn.close()
        
        # If nothing found
        return jsonify({
            'success': False,
            'error': f'Location "{location}" not found. Try district names like: Lilongwe, Blantyre, Mzuzu, Rumphi, Karonga, etc.'
        }), 404
            
    except Exception as e:
        print(f"Error in geocode_location: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                COUNT(*) as total_facilities,
                COUNT(CASE WHEN status = 'Functional' THEN 1 END) as functional_facilities,
                COUNT(CASE WHEN status = 'Non-functional' THEN 1 END) as non_functional_facilities,
                COUNT(DISTINCT district) as total_districts,
                COUNT(DISTINCT type) as total_types,
                COUNT(DISTINCT ownership) as ownership_types
            FROM malawi_health_registry
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
        """)
        
        stats = cur.fetchone()
        
        cur.execute("""
            SELECT 
                type as facility_type,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'Functional' THEN 1 END) as functional
            FROM malawi_health_registry
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY type
            ORDER BY total DESC;
        """)
        by_type = cur.fetchall()
        
        cur.execute("""
            SELECT 
                district,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'Functional' THEN 1 END) as functional
            FROM malawi_health_registry
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY district
            ORDER BY total DESC
            LIMIT 10;
        """)
        by_district = cur.fetchall()
        
        cur.execute("""
            SELECT 
                ownership,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'Functional' THEN 1 END) as functional
            FROM malawi_health_registry
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY ownership
            ORDER BY total DESC;
        """)
        by_ownership = cur.fetchall()
        
        cur.close()
        conn.close()
        
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

if __name__ == '__main__':
    print("=" * 70)
    print("Malawi Health Facility Finder API - Version 5.0")
    print("Data Source: Ministry of Health Registry 2023")
    print("=" * 70)
    print("✨ NEW FEATURES:")
    print("  - Location search with geocoding")
    print("  - Service information by facility type")
    print("  - Working hours display")
    print("  - User location detection")
    print("  - Route optimization")
    print("=" * 70)
    print("API running on: http://127.0.0.1:5000")
    print("=" * 70)
    app.run(debug=True, port=5000)