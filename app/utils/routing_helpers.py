# ROUTING HELPER FOR PGROUTING ALGORITHM
import math
from typing import Dict, List, Tuple, Optional

# BUILD PGROUTING TOPOLOGY IF NOT EXISTS
def ensure_routing_topology(conn) -> bool:
    """Build pgRouting topology for malawi_roads if it doesn't exist"""
    try:
        cur = conn.cursor()
        
        # Check if nodes table already exists
        cur.execute('''
            SELECT EXISTS (SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'malawi_roads_nodes');
        ''')
        nodes_exist = cur.fetchone()[0]
        
        if nodes_exist:
            print("Topology already exists")
            cur.close()
            return True
        
        print("Building pgRouting topology...")
        conn.commit()
        
        # Create nodes table from road line startpoints
        cur.execute('''
            DROP TABLE IF EXISTS malawi_roads_nodes;
            CREATE TABLE malawi_roads_nodes AS
            SELECT 
                row_number() OVER () as id,
                ST_StartPoint(geometry) as the_geom
            FROM malawi_roads
            WHERE geometry IS NOT NULL;
        ''')
        conn.commit()
        
        cur.execute('''
            CREATE INDEX idx_malawi_roads_nodes_geom ON malawi_roads_nodes USING GIST(the_geom);
        ''')
        conn.commit()
        
        # Create clean table with edges
        cur.execute('''
            DROP TABLE IF EXISTS malawi_roads_clean;
            CREATE TABLE malawi_roads_clean AS
            SELECT 
                row_number() OVER () as id,
                ogc_fid,
                geometry,
                COALESCE(CAST(cost AS FLOAT), ST_Length(geometry::geography)/1000.0, 1) as cost,
                COALESCE(CAST(reverse_cost AS FLOAT), 1.0) as reverse_cost
            FROM malawi_roads
            WHERE geometry IS NOT NULL;
        ''')
        conn.commit()
        
        cur.execute('''
            ALTER TABLE malawi_roads_clean ADD PRIMARY KEY (id);
            CREATE INDEX idx_malawi_roads_clean_geom ON malawi_roads_clean USING GIST(geometry);
        ''')
        conn.commit()
        
        print("Topology created successfully")
        cur.close()
        return True
        
    except Exception as e:
        print(f"Error building topology: {e}")
        conn.rollback()
        return False

#FIND NEAREST ROAD NODE
def find_nearest_road_node(conn, lat: float, lng: float, max_distance: int = 1000) -> Optional[int]:
    try:
        # Ensure topology exists first
        ensure_routing_topology(conn)
        
        cur = conn.cursor()
        
        # FIND THE NEAREST NODE FROM THE NODES TABLE
        query = """
            SELECT id
            FROM malawi_roads_nodes
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
        ensure_routing_topology(conn)
        
        cur = conn.cursor()
        
        query = """
            WITH start_geom AS (
                SELECT the_geom FROM malawi_roads_nodes WHERE id = %s
            ),
            end_geom AS (
                SELECT the_geom FROM malawi_roads_nodes WHERE id = %s
            ),
            roads_by_distance AS (
                SELECT 
                    row_number() OVER (ORDER BY ST_Distance(c.geometry, s.the_geom)) as seq,
                    c.id,
                    c.ogc_fid,
                    c.geometry,
                    c.cost,
                    ST_Distance(c.geometry::geography, s.the_geom::geography) + ST_Distance(c.geometry::geography, e.the_geom::geography) as total_distance
                FROM malawi_roads_clean c, start_geom s, end_geom e
                ORDER BY total_distance
                LIMIT 50
            )
            SELECT seq, id, ogc_fid, geometry, cost, total_distance
            FROM roads_by_distance;
        """
        
        cur.execute(query, (start_node, end_node))
        results = cur.fetchall()
        cur.close()
        
        if not results:
            return None
        
        # FORMAT RESULTS into route segments
        route_segments = []
        agg_cost = 0
        for row in results:
            seq, id_val, ogc_fid, geom, cost, dist = row
            cost_val = float(cost if cost else 1)
            agg_cost += cost_val
            
            route_segments.append({
                'sequence': int(seq),
                'node': int(id_val),
                'edge': int(id_val),
                'ogc_fid': int(ogc_fid),
                'cost': cost_val,
                'agg_cost': agg_cost,
                'geometry': geom,
                'edge_length': cost_val,
            })
        
        return route_segments if route_segments else None
        
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
        edge_ids = [seg['ogc_fid'] for seg in route_segments]
        
        # GET COMBINE GEOMETRY AS GEOJSON
        query = """
            SELECT ST_AsGeoJSON(ST_LineMerge(ST_Union(geometry)))
            FROM malawi_roads
            WHERE ogc_fid = ANY(%s);
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
        road_name = segment.get('name', 'Road')
        distance = segment.get('cost', 1)
        road_type = segment.get('road_type', 'unclassified')
        
        if current_road is None:
            # FIRST SEGMENT
            directions.append({
                'step': 1,
                'instruction': f"Start on {road_name}",
                'distance_km': round(distance, 2),
                'road_name': road_name,
                'road_type': road_type
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
                'road_type': road_type
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
        road_types = [seg.get('road_type', 'unclassified') for seg in route_segments if seg.get('road_type')]
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
