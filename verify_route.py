import requests
import json
import time

BASE_URL = 'http://127.0.0.1:5000/api'

def test_route_calculation():
    print("Testing /api/route endpoint...")
    
    # Wait for server to start
    print("Waiting for server to be ready...")
    for i in range(10):
        try:
            requests.get(f"{BASE_URL}/facilities?limit=1")
            print("Server is ready!")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    else:
        print("Server failed to start in time.")
        return

    # Use a known location 
    try:
        facilities_resp = requests.get(f"{BASE_URL}/facilities?limit=1")
        facilities_data = facilities_resp.json()
        
        if not facilities_data['success'] or not facilities_data['data']:
            print("Failed to get facilities for testing.")
            return
            
        facility = facilities_data['data'][0]
        facility_id = facility['id']
        facility_name = facility['name']
        print(f"Target facility: {facility_name} (ID: {facility_id})")
        
        # Mock user location
        user_lat = -13.9626
        user_lng = 33.7741
        
        payload = {
            'start_lat': user_lat,
            'start_lng': user_lng,
            'facility_id': facility_id,
            'algorithm': 'dijkstra'
        }
        
        print("Requesting route...")
        route_resp = requests.post(f"{BASE_URL}/route", json=payload)
        route_data = route_resp.json()
        
        if route_data['success']:
            print("✅ Route calculation successful!")
            route = route_data['data']['route']
            print(f"Distance: {route['distance_km']} km")
            print(f"Time: {route['estimated_time_minutes']} min")
            print(f"Segments: {len(route['directions'])}")
            print("Geometry present:", 'geometry' in route)
        else:
            print("❌ Route calculation failed.")
            print("Error:", route_data.get('error'))
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")

if __name__ == "__main__":
    test_route_calculation()
