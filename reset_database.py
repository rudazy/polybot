"""
MongoDB Database Reset Script
⚠️ DANGEROUS: This will DELETE ALL DATA from MongoDB
Use this to completely wipe the database and start fresh
"""

import os
from pymongo import MongoClient
from datetime import datetime


def wipe_database():
    """
    Complete database wipe - deletes all documents from all collections
    """
    try:
        # Get MongoDB connection string from environment or use default
        connection_string = os.environ.get('MONGODB_URI')
        if not connection_string:
            connection_string = "mongodb+srv://luda:1234luda@cluster0.byvm5pb.mongodb.net/?appName=Cluster0"

        print("=" * 70)
        print("⚠️  MONGODB DATABASE WIPE SCRIPT")
        print("=" * 70)
        print(f"Connection: {connection_string[:50]}...")
        print("=" * 70)

        # Connect to MongoDB
        client = MongoClient(connection_string)
        db = client['polymarket_bot']

        print("\n🔍 Testing connection...")
        client.server_info()
        print("✅ Successfully connected to MongoDB Atlas!")

        # Get all collection names
        print("\n🔍 Discovering collections...")
        collection_names = db.list_collection_names()

        if not collection_names:
            print("📝 No collections found. Database is already empty.")
            return

        print(f"📋 Found {len(collection_names)} collections:")
        for name in collection_names:
            count = db[name].count_documents({})
            print(f"   - {name}: {count} documents")

        # Confirmation
        print("\n" + "=" * 70)
        print("⚠️  WARNING: THIS WILL DELETE ALL DATA!")
        print("=" * 70)
        print("This operation will permanently delete:")
        print("  - All users and accounts")
        print("  - All wallet data and private keys")
        print("  - All trade history")
        print("  - All settings and preferences")
        print("  - All points and activity logs")
        print("")
        print("This action CANNOT be undone!")
        print("=" * 70)

        # Ask for confirmation
        response = input("\nType 'DELETE EVERYTHING' to confirm: ")

        if response != "DELETE EVERYTHING":
            print("\n❌ Database wipe cancelled. No data was deleted.")
            return

        print("\n🗑️  Starting complete database wipe...")
        print("=" * 70)

        total_deleted = 0

        # Delete all documents from each collection
        for collection_name in collection_names:
            collection = db[collection_name]

            # Count documents before deletion
            count_before = collection.count_documents({})

            # Delete all documents
            result = collection.delete_many({})
            deleted_count = result.deleted_count
            total_deleted += deleted_count

            print(f"✅ Wiped collection: {collection_name:20} ({deleted_count} documents deleted)")

        print("=" * 70)
        print(f"✅ Complete database wipe successful!")
        print(f"📊 Total documents deleted: {total_deleted}")
        print(f"📝 Database is now empty - ready for fresh start")
        print(f"🕐 Timestamp: {datetime.now().isoformat()}")
        print("=" * 70)

        # Close connection
        client.close()
        print("\n✅ Database connection closed.")

    except Exception as error:
        print(f"\n❌ Database wipe failed!")
        print(f"Error: {error}")
        import traceback
        traceback.print_exc()
        return


def main():
    """Main entry point"""
    print("\n")
    wipe_database()
    print("\n")


if __name__ == "__main__":
    main()
