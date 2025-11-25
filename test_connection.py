import psycopg2

# Try different configurations
configs = [
    {
        'dbname': 'health_facilities_db',
        'user': 'postgres',
        'password': '12345678',  # ← CHANGE THIS!
        'host': 'localhost',
        'port': 5432
    },
    {
        'dbname': 'postgres',  # Try connecting to default database
        'user': 'postgres',
        'password': '12345678',  # ← CHANGE THIS!
        'host': 'localhost',
        'port': 5432
    }
]

for i, config in enumerate(configs, 1):
    print(f"\n--- Test {i}: Trying to connect to '{config['dbname']}' ---")
    try:
        conn = psycopg2.connect(**config)
        print(f"✅ SUCCESS! Connected to {config['dbname']}")
        
        cur = conn.cursor()
        
        # List all databases
        cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = cur.fetchall()
        print(f"Available databases: {[db[0] for db in databases]}")
        
        # If connected to health_facilities_db, check for tables
        if config['dbname'] == 'health_facilities_db':
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            tables = cur.fetchall()
            print(f"Tables in database: {[t[0] for t in tables]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ FAILED: {e}")