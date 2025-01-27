# test_mysql.py
import pymysql

def test_mysql_connection():
    try:
        # Attempt to connect to the database
        connection = pymysql.connect(
            host='localhost',
            user='djangify_newsapi',
            password='DQwuNbJxL8UtuyhrmWtf',
            database='djangify_newsap125'
        )
        
        print("✅ Successfully connected to MySQL!")
        
        # Create a cursor
        with connection.cursor() as cursor:
            # Test a simple query
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL version: {version[0]}")
            
        connection.close()
        print("✅ Connection closed successfully!")
        
    except pymysql.Error as e:
        print("❌ Failed to connect to MySQL!")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mysql_connection()