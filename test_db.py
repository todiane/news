# test_db.py
import os
from sqlalchemy import create_engine

database_url = os.getenv('DATABASE_URL')
database_public_url = "postgresql://postgres:GADwoftjOLoEVRIUGWlptUMRYwTbxuFO@junction.proxy.rlwy.net:57674/railway"

print("Available Database URLs:")
print(f"Internal URL: {database_url}")
print(f"Public URL: {database_public_url}")

print("\nAttempting to connect using public URL...")
try:
    engine = create_engine(database_public_url)
    connection = engine.connect()
    print("Successfully connected to the database!")
    connection.close()
except Exception as e:
    print(f"Error connecting to database: {str(e)}")