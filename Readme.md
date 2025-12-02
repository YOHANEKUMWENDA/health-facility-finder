🏥 Health Facility Finder – Backend

Backend service for the Health Facility Finder, a GIS-powered system that helps users locate the nearest health facilities using spatial queries, PostGIS, and pgRouting.
This backend is built with Flask, PostgreSQL/PostGIS, and pgRouting to support geospatial search, routing, and facility data management.

📌 Project Purpose
The Health Facility Finder backend provides APIs that allow users to:
Find the nearest health facilities based on coordinates
Retrieve facility details and categories
Calculate shortest routes to a selected health facility (using pgRouting)
Store and manage facility geospatial data
Power the frontend web app with geospatial intelligence
The project applies important GIS concepts such as spatial indexing, geocoding, nearest-neighbor search, and network routing.

🗺️ GIS Components Used
1. PostGIS (Geospatial Extension for PostgreSQL)
  Stores facility points as GEOGRAPHY or GEOMETRY
  Provides spatial functions like ST_Distance, ST_DWithin, ST_ClosestPoint

2. Spatial Indexing (GIST Index)
  Improves performance of spatial queries, especially nearest facility search.

3. Nearest Facility Search
   
4. pgRouting
  Enables:
  Shortest path routing (e.g., Dijkstra)
  Distance and travel time calculations
  Generating paths from user location to facilities

🧰 Tech Stack
-----------------------------------------------------------------------
Component	                       |                 Technology
------------------------------------------------------------------------
  Backend                        |            Framework	Flask (Python)
  Database	                     |            PostgreSQL
  Geospatial                     |            Engine	PostGIS
  Routing Engine	               |            pgRouting
  ORM	                           |            SQLAlchemy / Psycopg2
  Environment	                   |            Python 3.x
