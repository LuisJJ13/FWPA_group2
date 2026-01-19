"""
Standalone test to check MongoDB Atlas connection
Run with: python test_search.py
"""

from pymongo import MongoClient
from dotenv import load_dotenv
import os

def test_connection():
    print("=" * 60)
    print("MongoDB Atlas Connection Test")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    db_name = os.getenv('DATABASE_NAME')
    
    if not uri:
        print("❌ ERROR: MONGODB_URI not found in .env file")
        return
    
    if not db_name:
        print("❌ ERROR: DATABASE_NAME not found in .env file")
        return
    
    print(f"\n📍 Connection URI: {uri[:50]}... (truncated)")
    print(f"📍 Database Name: {db_name}")
    
    try:
        print("\n🔄 Attempting to connect...")
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        
        # Test connection
        print("🔄 Testing connection with ping...")
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # Get database
        db = client[db_name]
        
        # List all databases
        print("\n📚 Available databases:")
        for db_name_item in client.list_database_names():
            print(f"  - {db_name_item}")
        
        # List collections in your database
        print(f"\n📦 Collections in '{db_name}' database:")
        collections = db.list_collection_names()
        if collections:
            for coll in collections:
                count = db[coll].count_documents({})
                print(f"  - {coll}: {count} documents")
        else:
            print("  ⚠️  No collections found")
        
        # Test Medicine collection specifically
        print("\n💊 Testing 'Medicine' collection:")
        medicine_coll = db['Medicine']
        medicine_count = medicine_coll.count_documents({})
        print(f"  Total medicines: {medicine_count}")
        
        if medicine_count > 0:
            print("\n📋 Sample medicines (first 3):")
            for med in medicine_coll.find().limit(3):
                print(f"  - {med.get('name', 'Unknown')}")
                
            # Test search functionality
            print("\n🔍 Testing search for 'aspirin':")
            result = medicine_coll.find_one({
                'name': {'$regex': '^aspirin$', '$options': 'i'}
            })
            if result:
                print(f"  ✅ Found: {result.get('name')}")
            else:
                print("  ❌ Not found")
        else:
            print("  ⚠️  Collection is empty")
        
        client.close()
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        print("\n💡 Common fixes:")
        print("   1. Check if your IP is whitelisted in MongoDB Atlas Network Access")
        print("   2. Verify MONGODB_URI and DATABASE_NAME in .env file")
        print("   3. Check MongoDB Atlas cluster is running")
        print("   4. Verify username/password in connection string")
        print("=" * 60)

if __name__ == "__main__":
    test_connection()