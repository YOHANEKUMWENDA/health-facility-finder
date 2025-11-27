from flask import Blueprint, jsonify

main_bp = Blueprint('main', __name__)

#DEFAULT HOME ROUTE
@main_bp.route('/')
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

#HEALTH CHECK ROUTE
@main_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Health Facility Finder API is running',
        'data_source': 'Malawi Ministry of Health Registry 2023'
    })
