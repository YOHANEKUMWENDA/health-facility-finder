# ROUTING HELPER FOR PGROUTING ALGORITHM
import math
from typing import Dict, List, Tuple, Optional

#FIND NEAREST ROAD NODE
def find_nearest_road_node(conn, lat: float, lng: float, max_distance: int = 1000) -> Optional[int]:
    try:
        cur = conn.cursor()
        
        # FIND THE NEAREST NODE WITHIN MAX_DISTANCE
        query = """
            SELECT id
            FROM malawi_roads_vertices_pgr
            ORDER BY the_geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            LIMIT 1;
        """
        
        cur.execute(query, (lng, lat))
        result = cur.fetchone()
        cur.close()
        
        if result:
            return result[0]
        return None
        
    except Exception as e:
        print(f"Error finding nearest road node: {e}")
        return None

# CALCULATE ROUTE BETWEEN TWO NODES
def calculate_route(conn, start_node: int, end_node: int, algorithm: str = 'dijkstra') -> Optional[List[Dict]]:
    try:
        cur = conn.cursor()
        
        if algorithm == 'astar':
            # A* ALGORITHM
            query = """
                SELECT 
                    route.seq,
                    route.node,
                    route.edge,
                    route.cost,
                    route.agg_cost,
                    roads.geom,
                    roads.name,
                    roads.highway as road_type,
                    roads.maxspeed
                FROM pgr_astar(
                    'SELECT gid as id, source, target, cost, reverse_cost, 
                     x1, y1, x2, y2 FROM malawi_roads',
                    %s, %s, directed := false
                ) AS route
                LEFT JOIN malawi_roads AS roads ON route.edge = roads.gid
                ORDER BY route.seq;
            """
        else:
            # DIJKSTRA ALGORITHM
            query = """
                SELECT 
                    route.seq,
                    route.node,
                    route.edge,
                    route.cost,
                    route.agg_cost,
                    roads.geom,
                    roads.name,
                    roads.highway as road_type,
                    roads.maxspeed
                FROM pgr_dijkstra(
                    'SELECT gid as id, source, target, cost, reverse_cost FROM malawi_roads',
                    %s, %s, directed := false
                ) AS route
                LEFT JOIN malawi_roads AS roads ON route.edge = roads.gid
                ORDER BY route.seq;
            """
        
        cur.execute(query, (start_node, end_node))
        results = cur.fetchall()
        cur.close()
        
        if not results:
            return None
        
        # FORMAT RESULTS
        route_segments = []
        for row in results:
            if row[2] is not None:
                route_segments.append({
                    'sequence': row[0],
                    'node': row[1],
                    'edge': row[2],
                    'cost': float(row[3]) if row[3] else 0,
                    'agg_cost': float(row[4]) if row[4] else 0,
                    'geometry': row[5],
                    'name': row[6] or 'Unnamed Road',
                    'road_type': row[7] or 'unclassified',
                    'maxspeed': row[8]
                })
        
        return route_segments
        
    except Exception as e:
        print(f"Error calculating route: {e}")
        return None

#FORMAT ROUTE SEGMENTS TO GEOJSON LINESTRING
def format_route_geometry(conn, route_segments: List[Dict]) -> Dict:
    try:
        if not route_segments:
            return None
        
        cur = conn.cursor()
        
        # COLLECT EDGE IDS
        edge_ids = [seg['edge'] for seg in route_segments]
        
        # GET COMBINE GEOMETRY AS GEOJSON
        query = """
            SELECT ST_AsGeoJSON(ST_LineMerge(ST_Union(geom)))
            FROM malawi_roads
            WHERE gid = ANY(%s);
        """
        
        cur.execute(query, (edge_ids,))
        result = cur.fetchone()
        cur.close()
        
        if result and result[0]:
            import json
            geometry = json.loads(result[0])
            return {
                'type': 'Feature',
                'geometry': geometry,
                'properties': {
                    'total_distance_km': round(route_segments[-1]['agg_cost'], 2),
                    'segments': len(route_segments)
                }
            }
        
        return None
        
    except Exception as e:
        print(f"Error formatting route geometry: {e}")
        return None

#CALCULATE TRAVEL TIME
def estimate_travel_time(distance_km: float, road_type: str = 'unclassified') -> float:
    # AVERAGE SPEED BY ROAD TYPE
    speed_map = {
        'motorway': 100,
        'trunk': 80,
        'primary': 60,
        'secondary': 50,
        'tertiary': 40,
        'residential': 30,
        'unclassified': 30,
        'track': 20
    }
    
    avg_speed = speed_map.get(road_type, 30)
    time_hours = distance_km / avg_speed
    time_minutes = time_hours * 60
    
    return round(time_minutes, 1)

#GENERATE TURN-BY-TURN DIRECTION FROM ROUTE SEGMENTS
def generate_directions(route_segments: List[Dict]) -> List[Dict]:

    if not route_segments:
        return []
    
    directions = []
    current_road = None
    segment_distance = 0
    
    for i, segment in enumerate(route_segments):
        road_name = segment['name']
        distance = segment['cost']
        
        if current_road is None:
            # FIRST SEGMENT
            directions.append({
                'step': 1,
                'instruction': f"Start on {road_name}",
                'distance_km': round(distance, 2),
                'road_name': road_name,
                'road_type': segment['road_type']
            })
            current_road = road_name
            segment_distance = distance
        elif road_name != current_road:
            # ROAD CHANGE
            directions.append({
                'step': len(directions) + 1,
                'instruction': f"Continue onto {road_name}",
                'distance_km': round(distance, 2),
                'road_name': road_name,
                'road_type': segment['road_type']
            })
            current_road = road_name
            segment_distance = distance
        else:
            #ACCUMULATIVE DISTANCE
            segment_distance += distance
    
    # FINAL INSTRUCTION
    if directions:
        directions.append({
            'step': len(directions) + 1,
            'instruction': "You have arrived at your destination",
            'distance_km': 0,
            'road_name': '',
            'road_type': ''
        })
    
    return directions

#CALCULATE COMPLETE ROUTE (GEOMETRY, DISTANCE, TIME, DIRECTION)
def calculate_route_with_details(conn, start_lat: float, start_lng: float, 
                                 end_lat: float, end_lng: float, 
                                 algorithm: str = 'dijkstra') -> Optional[Dict]:
  
    # FIND NEAREST NODE
    start_node = find_nearest_road_node(conn, start_lat, start_lng)
    end_node = find_nearest_road_node(conn, end_lat, end_lng)
    
    if not start_node or not end_node:
        return None
    
    # CCALCULATE ROUTE
    route_segments = calculate_route(conn, start_node, end_node, algorithm)
    
    if not route_segments:
        return None
    
    # GET ROUTE GEOMETRY
    geometry = format_route_geometry(conn, route_segments)
    
    # CALCULATE TOTAL DISTANCE
    total_distance = route_segments[-1]['agg_cost'] if route_segments else 0
    
    # ESTIMATE TRAVEL TIME
    avg_road_type = 'unclassified'
    if route_segments:
        road_types = [seg['road_type'] for seg in route_segments if seg['road_type']]
        if road_types:
            avg_road_type = max(set(road_types), key=road_types.count)
    
    travel_time = estimate_travel_time(total_distance, avg_road_type)
    
    # GENERATE DIRECTIONS
    directions = generate_directions(route_segments)
    
    return {
        'geometry': geometry,
        'distance_km': round(total_distance, 2),
        'estimated_time_minutes': travel_time,
        'directions': directions,
        'algorithm': algorithm,
        'start_node': start_node,
        'end_node': end_node
    }
