#!/usr/bin/env python3
"""
FORCE Database Wipe Script - NO CONFIRMATION REQUIRED
⚠️ DANGEROUS: Immediately deletes all data from MongoDB
Use for Railway deployment or automated wipes
"""

import sys
import os
from datetime import datetime


def force_wipe_database():
    """
    Force wipe all data from MongoDB without confirmation
    ⚠️ USE WITH CAUTION!
    """
    try:
        # Import after function starts to avoid import errors
        from mongodb_database import MongoDatabase

        print("\n" + "=" * 70)
        print("⚠️  FORCE DATABASE WIPE - NO CONFIRMATION")
        print("=" * 70)

        # Initialize database connection
        db = MongoDatabase()
        print("✅ Connected to MongoDB successfully!")

        # Get all collections
        collection_names = db.db.list_collection_names()

        if not collection_names:
            print("\n📝 Database is already empty!")
            db.close()
            return True

        print(f"\n📋 Found {len(collection_names)} collections")
        total_docs = 0

        for name in collection_names:
            count = db.db[name].count_documents({})
            total_docs += count
            print(f"   - {name:20} {count:6} documents")

        print(f"\n📊 Total documents to delete: {total_docs}")

        # Delete everything WITHOUT confirmation
        print("\n🗑️  Deleting all data (NO CONFIRMATION)...\n")
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
        print(f"📝 Database is now empty")
        print("=" * 70)

        db.close()
        print("\n✅ Database connection closed.\n")
        return True

    except Exception as e:
        print(f"\n❌ Database wipe failed!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n⚠️  WARNING: This script will IMMEDIATELY delete all data!")
    print("⚠️  NO CONFIRMATION REQUIRED - Use with caution!\n")

    success = force_wipe_database()
    sys.exit(0 if success else 1)
