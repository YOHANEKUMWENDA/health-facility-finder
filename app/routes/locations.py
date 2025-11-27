from flask import Blueprint, jsonify, request
from psycopg2.extras import RealDictCursor
from app.db import get_db_connection

locations_bp = Blueprint('locations', __name__)

@locations_bp.route('/api/districts', methods=['GET'])
def get_districts():
    try:
        #GET DATABASE CONNECTION
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
        #CREATE CURSOR AND EXECUTE QUERY
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
        
        #GET DISTRICTS FROM DATABASE
        districts = cur.fetchall()
        
        #CLOSE CURSOR AND CONNECTION
        cur.close()
        conn.close()    
        
        #RETURN JSON RESPONSE
        return jsonify({'success': True, 'data': districts})
    except Exception as e:
        print(f"Error in get_districts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

#GEOCODING FOR MALAWI LOCATION - SEARCHES KNOWN LOCATIONS AND DATABASE
@locations_bp.route('/api/geocode', methods=['POST'])
def geocode_location():
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
                
                # SEARCH FOR DISTRICT IN DATABASE
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
                
                #IF NOT FOUND, TRY PARTIAL MATCH
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
        
        # IF NOT FOUND RETURN SUCCES = FALSE
        return jsonify({
            'success': False,
            'error': f'Location "{location}" not found. Try district names like: Lilongwe, Blantyre, Mzuzu, Rumphi, Karonga, etc.'
        }), 404
            
    except Exception as e:
        print(f"Error in geocode_location: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
