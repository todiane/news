import redis
import sys
import time
from datetime import datetime

def test_redis_connection():
    """Test Redis connectivity and basic operations"""
    
    print("\n=== Redis Connection Test ===\n")
    
    # Connection settings
    REDIS_CONFIG = {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'decode_responses': True  # For readable string responses
    }
    
    try:
        # Test 1: Basic Connection
        print("Test 1: Attempting Redis connection...")
        r = redis.Redis(**REDIS_CONFIG)
        pong = r.ping()
        print(f"Connection successful! Redis responded: {pong}")
        print(f"Redis version: {r.info()['redis_version']}")
        
        # Test 2: Basic Operations
        print("\nTest 2: Testing basic Redis operations...")
        test_key = "test_key"
        test_value = f"test_value_{datetime.now()}"
        
        # Set value
        r.set(test_key, test_value)
        retrieved_value = r.get(test_key)
        print(f"Set and Get operation successful!")
        print(f"Stored: {test_value}")
        print(f"Retrieved: {retrieved_value}")
        
        # Test 3: Expiration
        print("\nTest 3: Testing key expiration...")
        exp_key = "exp_test"
        r.set(exp_key, "will expire", ex=2)
        print("Value before expiration:", r.get(exp_key))
        time.sleep(2.5)
        print("Value after expiration:", r.get(exp_key))
        
        # Test 4: Performance
        print("\nTest 4: Testing Redis performance...")
        start_time = time.time()
        for i in range(1000):
            r.set(f"perf_test_{i}", f"value_{i}")
        end_time = time.time()
        print(f"Performed 1000 write operations in {end_time - start_time:.2f} seconds")
        
        # Cleanup
        r.delete(test_key)
        print("\nCleanup completed")
        
        # Memory Usage
        memory_info = r.info('memory')
        print(f"\nRedis memory usage: {memory_info['used_memory_human']}")
        
        print("\n✅ All Redis tests completed successfully!")
        
    except redis.ConnectionError as e:
        print(f"\n❌ Redis Connection Error: {e}")
        print("\nPossible solutions:")
        print("1. Verify Redis is running")
        print("2. Check if Redis is bound to localhost")
        print("3. Verify port 6379 is not blocked")
        print("4. Check Redis password if authentication is required")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_redis_connection()
    