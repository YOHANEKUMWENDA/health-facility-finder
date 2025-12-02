from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 70)
    print("Malawi Health Facility Finder API")
    print("Data Source: Ministry of Health Registry 2023")
    print("=" * 70)
    print("NEW FEATURES:")
    print("  - Location search with geocoding")
    print("  - Service information by facility type")
    print("  - Working hours display")
    print("  - User location detection")
    print("  - Route optimization")
    print("=" * 70)
    print("API running on: http://127.0.0.1:5000")
    print("=" * 70)
    app.run(debug=True, port=5000)
