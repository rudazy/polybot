"""
Database Wipe Script
Removes all users, wallets, and test data from the database
USE WITH CAUTION - THIS WILL DELETE ALL DATA!
"""

from mongodb_database import MongoDatabase

def wipe_database():
    """Wipe all users and wallets from the database"""
    try:
        db = MongoDatabase()

        print("=" * 60)
        print("DATABASE WIPE SCRIPT")
        print("=" * 60)
        print()

        # Count current data
        users_count = db.db['users'].count_documents({})
        wallets_count = db.db['wallets'].count_documents({})

        print(f"Current data in database:")
        print(f"  - Users: {users_count}")
        print(f"  - Wallets: {wallets_count}")
        print()

        if users_count == 0 and wallets_count == 0:
            print("✅ Database is already empty!")
            return

        # Confirm deletion
        print("⚠️  WARNING: This will DELETE ALL data!")
        print()
        confirm = input("Type 'DELETE ALL' to confirm: ")

        if confirm != "DELETE ALL":
            print("❌ Aborted. No data was deleted.")
            return

        print()
        print("Deleting data...")

        # Delete all users
        result_users = db.db['users'].delete_many({})
        print(f"✅ Deleted {result_users.deleted_count} users")

        # Delete all wallets
        result_wallets = db.db['wallets'].delete_many({})
        print(f"✅ Deleted {result_wallets.deleted_count} wallets")

        # Optional: Delete other collections if they exist
        try:
            result_activities = db.db['activities'].delete_many({})
            print(f"✅ Deleted {result_activities.deleted_count} activities")
        except:
            pass

        try:
            result_trades = db.db['trades'].delete_many({})
            print(f"✅ Deleted {result_trades.deleted_count} trades")
        except:
            pass

        try:
            result_bot_configs = db.db['bot_configs'].delete_many({})
            print(f"✅ Deleted {result_bot_configs.deleted_count} bot configs")
        except:
            pass

        print()
        print("=" * 60)
        print("✅ DATABASE WIPED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("All test accounts have been removed.")
        print("You can now start fresh with a clean database.")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    wipe_database()
