"""
Simple MongoDB Database Reset Script
Wipes all data using direct MongoDB connection
"""

import sys
import os

# Try importing with better error handling
try:
    from pymongo import MongoClient
except ImportError as e:
    print(f"ERROR: Could not import pymongo: {e}")
    print("Installing pymongo...")
    os.system("pip install --force-reinstall pymongo")
    from pymongo import MongoClient

from datetime import datetime


def main():
    print("\n" + "=" * 70)
    print("⚠️  MONGODB DATABASE WIPE SCRIPT")
    print("=" * 70)

    # Connection string
    connection_string = os.environ.get('MONGODB_URI', "mongodb+srv://luda:1234luda@cluster0.byvm5pb.mongodb.net/?appName=Cluster0")

    print(f"\nConnecting to MongoDB...")

    try:
        # Connect
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        db = client['polymarket_bot']

        # Test connection
        client.server_info()
        print("✅ Connected successfully!")

        # List collections
        collections = db.list_collection_names()

        if not collections:
            print("\n📝 Database is already empty!")
            client.close()
            return

        print(f"\n📋 Found {len(collections)} collections:")
        total_docs = 0
        for name in collections:
            count = db[name].count_documents({})
            total_docs += count
            print(f"   - {name}: {count} documents")

        print(f"\n📊 Total documents: {total_docs}")

        # Confirm
        print("\n" + "=" * 70)
        print("⚠️  WARNING: THIS WILL DELETE ALL DATA!")
        print("=" * 70)
        response = input("\nType 'YES' to confirm deletion: ")

        if response != "YES":
            print("\n❌ Cancelled. No data was deleted.")
            client.close()
            return

        # Delete all
        print("\n🗑️  Deleting all data...")
        deleted_total = 0

        for name in collections:
            result = db[name].delete_many({})
            deleted_total += result.deleted_count
            print(f"✅ Deleted {result.deleted_count} docs from {name}")

        print("\n" + "=" * 70)
        print(f"✅ SUCCESS! Deleted {deleted_total} documents total")
        print(f"🕐 {datetime.now().isoformat()}")
        print("=" * 70)

        client.close()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
