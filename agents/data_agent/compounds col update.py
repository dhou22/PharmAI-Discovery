# Database Schema Update Script
# Run this to add missing columns to your existing compounds table

import psycopg2
import os
import logging

def update_database_schema():
    """Update database schema to add missing columns"""
    
    # Database connection parameters
    connection_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'mediagent'),
        'user': os.getenv('DB_USER', 'admin'),
        'password': os.getenv('DB_PASSWORD', 'mediagent2025')
    }
    
    # SQL commands to add missing columns
    schema_updates = [
        {
            'description': 'Add pref_name column',
            'sql': 'ALTER TABLE compounds ADD COLUMN IF NOT EXISTS pref_name TEXT;'
        },
        {
            'description': 'Add bioactivities_count column',
            'sql': 'ALTER TABLE compounds ADD COLUMN IF NOT EXISTS bioactivities_count INTEGER DEFAULT 0;'
        },
        {
            'description': 'Update existing records to set bioactivities_count to 0',
            'sql': 'UPDATE compounds SET bioactivities_count = 0 WHERE bioactivities_count IS NULL;'
        }
    ]
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**connection_params)
        
        with conn.cursor() as cur:
            # Check current table structure
            print("\n📋 Current table structure:")
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'compounds' 
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            # Apply schema updates
            print("\n🔧 Applying schema updates...")
            for update in schema_updates:
                try:
                    print(f"  - {update['description']}")
                    cur.execute(update['sql'])
                    print(f"    ✅ Success")
                except Exception as e:
                    print(f"    ❌ Error: {e}")
            
            # Commit changes
            conn.commit()
            print("\n✅ Schema updates committed successfully!")
            
            # Check updated table structure
            print("\n📋 Updated table structure:")
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'compounds' 
                ORDER BY ordinal_position;
            """)
            
            columns = cur.fetchall()
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            # Check compound count
            cur.execute("SELECT COUNT(*) FROM compounds")
            count = cur.fetchone()[0]
            print(f"\n📊 Total compounds in database: {count}")
            
            # Show sample data
            if count > 0:
                print("\n🔍 Sample compound data:")
                cur.execute("SELECT chembl_id, pref_name, molecular_formula, bioactivities_count FROM compounds LIMIT 3")
                samples = cur.fetchall()
                for sample in samples:
                    print(f"  - {sample[0]}: {sample[1]} ({sample[2]}) - {sample[3]} bioactivities")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🗃️  Database Schema Update Script")
    print("=" * 50)
    
    success = update_database_schema()
    
    if success:
        print("\n🎉 Database schema updated successfully!")
        print("\nYou can now run your DataAgent without column errors.")
        print("\nTo test, run:")
        print("  python database_manager.py")
    else:
        print("\n❌ Schema update failed!")
        print("\nPlease check the error messages above and try again.")