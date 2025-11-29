from flask import Blueprint, jsonify, request
from psycopg2.extras import RealDictCursor
from app.db import get_db_connection
from app.utils.routing_helpers import (
    find_nearest_road_node,
    calculate_route_with_details,
    estimate_travel_time
)

routing_bp = Blueprint('routing', __name__)

#ROUTE FOR A SINGLE FACILITY
@routing_bp.route('/api/route', methods=['POST'])
def calculate_single_route():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # VALIDATE REQUIRED FIELDS
        required_fields = ['start_lat', 'start_lng', 'facility_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        start_lat = float(data['start_lat'])
        start_lng = float(data['start_lng'])
        facility_id = int(data['facility_id'])
        algorithm = data.get('algorithm', 'dijkstra')
        
        # VALIDATE ALGORITHM
        if algorithm not in ['dijkstra', 'astar']:
            return jsonify({'success': False, 'error': 'Invalid algorithm. Use "dijkstra" or "astar"'}), 400
        
        # GET DATABASE CONNECTION
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        #GET FACILITY DETAILS
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
        cur.close()
        
        if not facility:
            conn.close()
            return jsonify({'success': False, 'error': 'Facility not found'}), 404
        
        # CALCULATE ROUTE
        route_info = calculate_route_with_details(
            conn, 
            start_lat, 
            start_lng,
            facility['lat'],
            facility['lng'],
            algorithm
        )
        
        conn.close()
        
        if not route_info:
            return jsonify({
                'success': False, 
                'error': 'Could not calculate route. No road network path found between locations.'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'facility': facility,
                'route': route_info
            }
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        print(f"Error in calculate_single_route: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

#MULTIPLE ROUTES FOR FACILITIES
@routing_bp.route('/api/routes/multiple', methods=['POST'])
def calculate_multiple_routes():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # VALIDATE REQUIRED FIELDS
        required_fields = ['start_lat', 'start_lng', 'facility_ids']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        start_lat = float(data['start_lat'])
        start_lng = float(data['start_lng'])
        facility_ids = data['facility_ids']
        algorithm = data.get('algorithm', 'dijkstra')
        limit = min(int(data.get('limit', 5)), 10)  # MAX 10 FACILITIES
        
        if not isinstance(facility_ids, list) or len(facility_ids) == 0:
            return jsonify({'success': False, 'error': 'facility_ids must be a non-empty array'}), 400
        
        # LIMIT NUMBER OF FACILITIES
        facility_ids = facility_ids[:limit]
        
        # GET DATABASE CONNECTION
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        # GET ALL FACILITIES
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
            WHERE gid = ANY(%s);
        """, (facility_ids,))
        
        facilities = cur.fetchall()
        cur.close()
        
        if not facilities:
            conn.close()
            return jsonify({'success': False, 'error': 'No facilities found'}), 404
        
        # CALCULATE ROUTES TO ALL FACILITIES
        results = []
        for facility in facilities:
            route_info = calculate_route_with_details(
                conn,
                start_lat,
                start_lng,
                facility['lat'],
                facility['lng'],
                algorithm
            )
            
            if route_info:
                results.append({
                    'facility': facility,
                    'route': route_info
                })
        
        conn.close()
        
        # SORT BY TRAVEL TIME
        results.sort(key=lambda x: x['route']['estimated_time_minutes'])
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results),
            'sorted_by': 'travel_time'
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        print(f"Error in calculate_multiple_routes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

#ROUTE OPTMISATION
@routing_bp.route('/api/route/optimize', methods=['POST'])
def optimize_multi_facility_route():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # VALIDATE REQUIRED FIELDS
        required_fields = ['start_lat', 'start_lng', 'facility_ids']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        start_lat = float(data['start_lat'])
        start_lng = float(data['start_lng'])
        facility_ids = data['facility_ids']
        return_to_start = data.get('return_to_start', False)
        
        if not isinstance(facility_ids, list) or len(facility_ids) < 2:
            return jsonify({'success': False, 'error': 'facility_ids must contain at least 2 facilities'}), 400
        
        if len(facility_ids) > 10:
            return jsonify({'success': False, 'error': 'Maximum 10 facilities allowed for route optimization'}), 400
        
        #GET DATABASE CONNECTION
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        # GET ALL FACILITIES
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
            WHERE gid = ANY(%s);
        """, (facility_ids,))
        
        facilities = cur.fetchall()
        cur.close()
        
        if len(facilities) < 2:
            conn.close()
            return jsonify({'success': False, 'error': 'At least 2 valid facilities required'}), 404
        
        # FIND NEAREST ROAD FOR START LOCATION
        start_node = find_nearest_road_node(conn, start_lat, start_lng)
        
        if not start_node:
            conn.close()
            return jsonify({'success': False, 'error': 'Could not find road network near start location'}), 404
        
        # BUILD DISTANCE MATRIX BETWEEN ALL POINTS (START + FACILITIES)
        # FOR SIMPLICITY, WE'LL USE A GREEDY NEAREST-NEIGHBOR APPROACH
        unvisited = list(facilities)
        current_lat, current_lng = start_lat, start_lng
        optimized_order = []
        routes = []
        total_distance = 0
        total_time = 0
        
        # GREEDY NEAREST NEIGBOUR ALGORITHM
        while unvisited:
            nearest_facility = None
            nearest_route = None
            min_distance = float('inf')
            
            for facility in unvisited:
                route_info = calculate_route_with_details(
                    conn,
                    current_lat,
                    current_lng,
                    facility['lat'],
                    facility['lng'],
                    'dijkstra'
                )
                
                if route_info and route_info['distance_km'] < min_distance:
                    min_distance = route_info['distance_km']
                    nearest_facility = facility
                    nearest_route = route_info
            
            if nearest_facility:
                optimized_order.append(nearest_facility['id'])
                routes.append({
                    'from': {'lat': current_lat, 'lng': current_lng},
                    'to': nearest_facility,
                    'route': nearest_route
                })
                total_distance += nearest_route['distance_km']
                total_time += nearest_route['estimated_time_minutes']
                
                current_lat = nearest_facility['lat']
                current_lng = nearest_facility['lng']
                unvisited.remove(nearest_facility)
            else:
                break
        
        # RETURN TO START IF REQUESTED
        if return_to_start and optimized_order:
            return_route = calculate_route_with_details(
                conn,
                current_lat,
                current_lng,
                start_lat,
                start_lng,
                'dijkstra'
            )
            
            if return_route:
                routes.append({
                    'from': {'lat': current_lat, 'lng': current_lng},
                    'to': {'lat': start_lat, 'lng': start_lng},
                    'route': return_route
                })
                total_distance += return_route['distance_km']
                total_time += return_route['estimated_time_minutes']
        
        conn.close()
        
        #RETURN JSON RESPONSE
        return jsonify({
            'success': True,
            'data': {
                'optimized_order': optimized_order,
                'total_distance_km': round(total_distance, 2),
                'total_time_minutes': round(total_time, 1),
                'routes': routes,
                'return_to_start': return_to_start
            }
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        print(f"Error in optimize_multi_facility_route: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
