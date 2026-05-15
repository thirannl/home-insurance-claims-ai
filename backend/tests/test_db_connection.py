import os
import sys
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

# Add the parent directory to sys.path so we can import app modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def test_connection():
    if "[YOUR-PASSWORD]" in DATABASE_URL:
        print("❌ ERROR: Please update your database password in the .env file!")
        return

    print(f"Connecting to: {DATABASE_URL.split('@')[1]}...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # 1. Test Connection & List Tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("\n✅ Connection Successful!")
        print(f"Total tables found: {len(tables)}")
        print("Tables list:", ", ".join(tables))
        
        # 2. Check Assessors Table
        if 'assessors' in tables:
            print("\n--- Rows in 'assessors' table ---")
            with engine.connect() as connection:
                result = connection.execute(text("SELECT id, email, full_name, role FROM assessors LIMIT 5"))
                rows = result.fetchall()
                
                if not rows:
                    print("No rows found in 'assessors' table.")
                for row in rows:
                    print(f"ID: {row.id} | Email: {row.email} | Name: {row.full_name} | Role: {row.role}")
        else:
            print("\n⚠️ 'assessors' table not found. Have you run the schema.sql yet?")
            
    except Exception as e:
        print(f"\n❌ Connection Failed!")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
