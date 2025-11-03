#!/usr/bin/env python3
"""
Database Wipe Script - Uses existing mongodb_database.py
"""

import sys
from mongodb_database import MongoDatabase
from datetime import datetime


def wipe_all_data():
    """Wipe all data from MongoDB"""
    print("\n" + "=" * 70)
    print("⚠️  MONGODB DATABASE COMPLETE WIPE")
    print("=" * 70)

    # Initialize database connection
    try:
        db = MongoDatabase()
        print("✅ Connected to MongoDB successfully!")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    # Get all collections
    try:
        collection_names = db.db.list_collection_names()

        if not collection_names:
            print("\n📝 Database is already empty!")
            db.close()
            return

        print(f"\n📋 Found {len(collection_names)} collections:")
        total_docs = 0
        for name in collection_names:
            count = db.db[name].count_documents({})
            total_docs += count
            print(f"   - {name:20} {count:6} documents")

        print(f"\n📊 Total documents to delete: {total_docs}")

        # Warning
        print("\n" + "=" * 70)
        print("⚠️  WARNING: THIS WILL PERMANENTLY DELETE:")
        print("   - All user accounts")
        print("   - All wallet data")
        print("   - All trade history")
        print("   - All settings")
        print("   - All points and activity")
        print("\nTHIS CANNOT BE UNDONE!")
        print("=" * 70)

        # Confirmation
        response = input("\nType 'YES' to proceed with deletion: ")

        if response != "YES":
            print("\n❌ Cancelled. No data was deleted.")
            db.close()
            return

        # Delete everything
        print("\n🗑️  Deleting all data...\n")
        deleted_total = 0

        for name in collection_names:
            result = db.db[name].delete_many({})
            deleted_count = result.deleted_count
            deleted_total += deleted_count
            print(f"✅ {name:20} - Deleted {deleted_count} documents")

        print("\n" + "=" * 70)
        print(f"✅ DATABASE WIPE COMPLETE!")
        print(f"📊 Total deleted: {deleted_total} documents")
        print(f"🕐 Timestamp: {datetime.now().isoformat()}")
        print(f"📝 Database is now empty and ready for fresh data")
        print("=" * 70)

        db.close()
        print("\n✅ Database connection closed.\n")

    except Exception as e:
        print(f"\n❌ Error during wipe: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    wipe_all_data()
