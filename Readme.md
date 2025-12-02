# Malawi Health Facility Finder API

A Flask-based REST API for finding and routing to health facilities in Malawi using PostGIS and pgRouting.

## Features

- 🏥 Search and filter health facilities
- 📍 Find nearest facilities based on location
- 🗺️ Calculate optimal routes using pgRouting
- 📊 Get statistics and analytics
- 🌍 Geocoding for Malawi locations
- 🔍 Filter by district, facility type, and ownership

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL with PostGIS and pgRouting extensions
- **Data Source**: Malawi Ministry of Health Registry 2023

---

## API Endpoints

### 1. Home & Health Check

#### `GET /`
Get API information and available endpoints.

**Response:**
```json
{
  "message": "Malawi Health Facility Finder API",
  "version": "5.0",
  "data_source": "Ministry of Health - Official Registry 2023",
  "endpoints": { ... }
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Health Facility Finder API is running",
  "data_source": "Malawi Ministry of Health Registry 2023"
}
```

---

### 2. Facilities

#### `GET /api/facilities`
Get all health facilities with optional filters.

**Query Parameters:**
- `functional_only` (boolean, optional): Filter for functional facilities only (default: false)
- `district` (string, optional): Filter by district name
- `facility_type` (string, optional): Filter by facility type
- `ownership` (string, optional): Filter by ownership type

**Example Request:**
```
GET /api/facilities?functional_only=true&district=Lilongwe
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "code": "MH001",
      "name": "Kamuzu Central Hospital",
      "common_name": "KCH",
      "ownership": "Government",
      "facility_type": "Central Hospital",
      "status": "Functional",
      "zone": "Central",
      "district": "Lilongwe",
      "lat": -13.9626,
      "lng": 33.7741
    }
  ],
  "count": 1,
  "filters": {
    "functional_only": true,
    "district": "Lilongwe",
    "facility_type": null,
    "ownership": null
  }
}
```

#### `GET /api/facility/<id>`
Get detailed information about a specific facility.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "code": "MH001",
    "name": "Kamuzu Central Hospital",
    "common_name": "KCH",
    "ownership": "Government",
    "facility_type": "Central Hospital",
    "status": "Functional",
    "zone": "Central",
    "district": "Lilongwe",
    "lat": -13.9626,
    "lng": 33.7741,
    "services": [
      "Emergency Care",
      "Surgery",
      "Maternity",
      "Pediatrics"
    ],
    "working_hours": {
      "weekdays": "24/7",
      "weekends": "24/7"
    },
    "contact": {
      "phone": "+265 1 XXX XXX",
      "district_office": "Lilongwe District Health Office"
    }
  }
}
```

#### `POST /api/nearest`
Find nearest facilities to a given location.

**Request Body:**
```json
{
  "lat": -13.9626,
  "lng": 33.7741,
  "limit": 5,
  "functional_only": true,
  "district": "Lilongwe",
  "facility_type": "Health Centre",
  "ownership": "Government"
}
```

**Required Fields:**
- `lat` (float): Latitude
- `lng` (float): Longitude

**Optional Fields:**
- `limit` (integer): Number of results (1-50, default: 5)
- `functional_only` (boolean): Filter functional facilities (default: true)
- `district` (string): Filter by district
- `facility_type` (string): Filter by facility type
- `ownership` (string): Filter by ownership

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Area 25 Health Centre",
      "facility_type": "Health Centre",
      "district": "Lilongwe",
      "lat": -13.9800,
      "lng": 33.7900,
      "distance_km": 2.34,
      "services": ["OPD", "Maternity", "HIV Testing"],
      "working_hours": {
        "weekdays": "7:30 AM - 4:30 PM",
        "weekends": "Emergency only"
      }
    }
  ],
  "count": 1,
  "query_point": {
    "lat": -13.9626,
    "lng": 33.7741
  },
  "filters": { ... }
}
```

#### `GET /api/facility-types`
Get all available facility types with counts.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "facility_type": "Health Centre",
      "count": 450
    },
    {
      "facility_type": "Hospital",
      "count": 45
    }
  ]
}
```

#### `GET /api/ownerships`
Get all ownership types with counts.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "ownership": "Government",
      "count": 650
    },
    {
      "ownership": "CHAM",
      "count": 150
    }
  ]
}
```

---

### 3. Locations

#### `GET /api/districts`
Get all districts with facility counts.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "district": "Lilongwe",
      "count": 120
    },
    {
      "district": "Blantyre",
      "count": 95
    }
  ]
}
```

#### `POST /api/geocode`
Convert location name to coordinates (geocoding).

**Request Body:**
```json
{
  "location": "Lilongwe"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "lat": -13.9626,
    "lng": 33.7741,
    "name": "Lilongwe",
    "facility_count": 120
  }
}
```

**Supported Locations:**
- All 28 districts of Malawi
- Major cities: Lilongwe, Blantyre, Mzuzu, Zomba
- Partial name matching supported

---

### 4. Routing (pgRouting)

#### `POST /api/route`
Calculate shortest path from user location to a specific facility.

**Request Body:**
```json
{
  "start_lat": -13.9626,
  "start_lng": 33.7741,
  "facility_id": 1,
  "algorithm": "dijkstra"
}
```

**Required Fields:**
- `start_lat` (float): Starting latitude
- `start_lng` (float): Starting longitude
- `facility_id` (integer): Target facility ID

**Optional Fields:**
- `algorithm` (string): Routing algorithm - "dijkstra" or "astar" (default: "dijkstra")

**Response:**
```json
{
  "success": true,
  "data": {
    "facility": {
      "id": 1,
      "name": "Kamuzu Central Hospital",
      "lat": -13.9800,
      "lng": 33.7900
    },
    "route": {
      "geometry": {
        "type": "Feature",
        "geometry": {
          "type": "LineString",
          "coordinates": [
            [33.7741, -13.9626],
            [33.7750, -13.9650],
            [33.7900, -13.9800]
          ]
        },
        "properties": {
          "total_distance_km": 2.34,
          "segments": 5
        }
      },
      "distance_km": 2.34,
      "estimated_time_minutes": 8.5,
      "directions": [
        {
          "step": 1,
          "instruction": "Start on Independence Drive",
          "distance_km": 1.2,
          "road_name": "Independence Drive",
          "road_type": "primary"
        },
        {
          "step": 2,
          "instruction": "Continue onto Kamuzu Procession Road",
          "distance_km": 1.14,
          "road_name": "Kamuzu Procession Road",
          "road_type": "primary"
        },
        {
          "step": 3,
          "instruction": "You have arrived at your destination",
          "distance_km": 0,
          "road_name": "",
          "road_type": ""
        }
      ],
      "algorithm": "dijkstra",
      "start_node": 1234,
      "end_node": 5678
    }
  }
}
```

#### `POST /api/routes/multiple`
Calculate routes to multiple facilities and compare travel times.

**Request Body:**
```json
{
  "start_lat": -13.9626,
  "start_lng": 33.7741,
  "facility_ids": [1, 2, 3, 4, 5],
  "algorithm": "dijkstra",
  "limit": 5
}
```

**Required Fields:**
- `start_lat` (float): Starting latitude
- `start_lng` (float): Starting longitude
- `facility_ids` (array): Array of facility IDs to route to

**Optional Fields:**
- `algorithm` (string): "dijkstra" or "astar" (default: "dijkstra")
- `limit` (integer): Maximum facilities to process (1-10, default: 5)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "facility": {
        "id": 2,
        "name": "Area 25 Health Centre",
        "lat": -13.9800,
        "lng": 33.7900
      },
      "route": {
        "geometry": { ... },
        "distance_km": 2.34,
        "estimated_time_minutes": 8.5,
        "directions": [ ... ]
      }
    },
    {
      "facility": {
        "id": 1,
        "name": "Kamuzu Central Hospital",
        "lat": -13.9850,
        "lng": 33.7950
      },
      "route": {
        "geometry": { ... },
        "distance_km": 3.12,
        "estimated_time_minutes": 11.2,
        "directions": [ ... ]
      }
    }
  ],
  "count": 2,
  "sorted_by": "travel_time"
}
```

**Note:** Results are automatically sorted by travel time (fastest first).

#### `POST /api/route/optimize`
Optimize route for visiting multiple facilities (Traveling Salesman Problem).

**Request Body:**
```json
{
  "start_lat": -13.9626,
  "start_lng": 33.7741,
  "facility_ids": [1, 2, 3, 4],
  "return_to_start": false
}
```

**Required Fields:**
- `start_lat` (float): Starting latitude
- `start_lng` (float): Starting longitude
- `facility_ids` (array): Array of facility IDs to visit (2-10 facilities)

**Optional Fields:**
- `return_to_start` (boolean): Whether to return to starting point (default: false)

**Response:**
```json
{
  "success": true,
  "data": {
    "optimized_order": [2, 1, 3, 4],
    "total_distance_km": 15.67,
    "total_time_minutes": 45.3,
    "return_to_start": false,
    "routes": [
      {
        "from": {
          "lat": -13.9626,
          "lng": 33.7741
        },
        "to": {
          "id": 2,
          "name": "Area 25 Health Centre",
          "lat": -13.9800,
          "lng": 33.7900
        },
        "route": {
          "geometry": { ... },
          "distance_km": 2.34,
          "estimated_time_minutes": 8.5,
          "directions": [ ... ]
        }
      },
      {
        "from": {
          "lat": -13.9800,
          "lng": 33.7900
        },
        "to": {
          "id": 1,
          "name": "Kamuzu Central Hospital",
          "lat": -13.9850,
          "lng": 33.7950
        },
        "route": {
          "geometry": { ... },
          "distance_km": 0.78,
          "estimated_time_minutes": 3.2,
          "directions": [ ... ]
        }
      }
    ]
  }
}
```

**Algorithm:** Uses greedy nearest-neighbor approach for route optimization.

---

### 5. Statistics

#### `GET /api/stats`
Get comprehensive statistics about health facilities.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_facilities": 850,
    "functional_facilities": 720,
    "non_functional_facilities": 130,
    "total_districts": 28,
    "total_types": 8,
    "ownership_types": 5
  },
  "by_type": [
    {
      "facility_type": "Health Centre",
      "total": 450,
      "functional": 390
    },
    {
      "facility_type": "Hospital",
      "total": 45,
      "functional": 42
    }
  ],
  "by_district": [
    {
      "district": "Lilongwe",
      "total": 120,
      "functional": 105
    },
    {
      "district": "Blantyre",
      "total": 95,
      "functional": 82
    }
  ],
  "by_ownership": [
    {
      "ownership": "Government",
      "total": 650,
      "functional": 550
    },
    {
      "ownership": "CHAM",
      "total": 150,
      "functional": 130
    }
  ]
}
```

---

## Error Handling

All endpoints return errors in the following format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (missing or invalid parameters)
- `404` - Not Found (facility or route not found)
- `500` - Internal Server Error (database connection or server error)

---

## Database Requirements

### Required PostgreSQL Extensions:
- **PostGIS**: For spatial operations
- **pgRouting**: For route calculation

### Required Tables:
1. **malawi_health_registry**: Health facilities data
   - Columns: gid, code, name, common_name, ownership, type, status, zone, district, latitude, longitude

2. **malawi_roads**: Road network for routing
   - Columns: gid, source, target, cost, reverse_cost, geom, name, highway, maxspeed, x1, y1, x2, y2

3. **malawi_roads_vertices_pgr**: Road network vertices (auto-generated by pgRouting)

---

## Setup & Installation

### 1. Install Dependencies
```bash
pip install flask flask-cors psycopg2-binary
```

### 2. Database Setup
```sql
-- Enable extensions
CREATE EXTENSION postgis;
CREATE EXTENSION pgrouting;

-- Import your data
-- (Import malawi_health_registry and malawi_roads tables)

-- Create routing topology
SELECT pgr_createTopology('malawi_roads', 0.0001, 'geom', 'gid');
```

### 3. Environment Variables
Create a `.env` file or set environment variables:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=malawi_health
DB_USER=postgres
DB_PASSWORD=your_password
```

### 4. Run the Application
```bash
python run.py
```

The API will be available at `http://localhost:5000`

---

## Usage Examples

### Find Nearest Hospital
```bash
curl -X POST http://localhost:5000/api/nearest \
  -H "Content-Type: application/json" \
  -d '{
    "lat": -15.7861,
    "lng": 35.0058,
    "limit": 3,
    "facility_type": "Hospital",
    "functional_only": true
  }'
```

### Calculate Route to Facility
```bash
curl -X POST http://localhost:5000/api/route \
  -H "Content-Type: application/json" \
  -d '{
    "start_lat": -15.7861,
    "start_lng": 35.0058,
    "facility_id": 1,
    "algorithm": "dijkstra"
  }'
```

### Geocode Location
```bash
curl -X POST http://localhost:5000/api/geocode \
  -H "Content-Type: application/json" \
  -d '{"location": "Mzuzu"}'
```

---

## Performance Notes

- **Route Calculation**: Typically completes in < 1 second
- **Nearest Facility Search**: Uses PostGIS spatial indexing for fast queries
- **Route Optimization**: Limited to 10 facilities maximum to ensure reasonable response times

---

## Version History

**v5.0** (Current)
- Added pgRouting integration
- Route calculation endpoints
- Multi-facility route optimization
- Turn-by-turn directions

**v4.0**
- Geocoding support
- Enhanced filtering
- Services and working hours information

---

## License

Data Source: Malawi Ministry of Health - Official Registry 2023

## Support

For issues or questions, please contact the development team.
