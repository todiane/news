# backend/app/db_test.py
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import pymysql

# Database connection details
DB_USER = "djangify_newsapi"
DB_PASSWORD = "DQwuNbJxL8UtuyhrmWtf"
DB_HOST = "localhost"
DB_NAME = "djangify_newsap125"

# Create database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

def test_connection():
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Try to connect
        with engine.connect() as connection:
            print("✅ Successfully connected to the database!")
            
            # Test if we can execute a query
            result = connection.execute("SELECT DATABASE();")
            db_name = result.scalar()
            print(f"✅ Connected to database: {db_name}")
            
            # Test if we can create a table
            connection.execute("CREATE TABLE IF NOT EXISTS test_connection (id INT);")
            print("✅ Successfully created test table!")
            
            # Clean up - drop the test table
            connection.execute("DROP TABLE test_connection;")
            print("✅ Successfully cleaned up test table!")
            
    except SQLAlchemyError as e:
        print("❌ Database connection failed!")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_connection()