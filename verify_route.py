import urllib.request
import json
import sys

API_BASE_URL = 'http://127.0.0.1:5000/api'

def test_route():
    print("Fetching facilities...")
    try:
        with urllib.request.urlopen(f"{API_BASE_URL}/facilities") as response:
            data = json.loads(response.read().decode())
            if not data['success'] or not data['data']:
                print("Failed to fetch facilities")
                return False
            
            facility = data['data'][0]
            print(f"Target facility: {facility['name']} (ID: {facility['id']})")
            
            start_lat = float(facility['lat']) - 0.05
            start_lng = float(facility['lng']) - 0.05
            
            payload = {
                "start_lat": start_lat,
                "start_lng": start_lng,
                "facility_id": facility['id'],
                "algorithm": "dijkstra"
            }
            
            req = urllib.request.Request(
                f"{API_BASE_URL}/route",
                data=json.dumps(payload).encode(),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            print("Calculating route...")
            with urllib.request.urlopen(req) as route_response:
                route_data = json.loads(route_response.read().decode())
                
                if route_data['success']:
                    geometry = route_data['data']['route']['geometry']
                    if geometry and geometry['type'] == 'Feature':
                        print("SUCCESS: Route geometry returned!")
                        print(f"Distance: {route_data['data']['route']['distance_km']} km")
                        return True
                    else:
                        print("FAILURE: Route geometry missing or invalid")
                        print(json.dumps(route_data, indent=2))
                        return False
                else:
                    print(f"FAILURE: API returned error: {route_data.get('error')}")
                    return False
                    
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if test_route():
        sys.exit(0)
    else:
        sys.exit(1)
