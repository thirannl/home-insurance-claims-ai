import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def insert_dummy_assessor():
    engine = create_engine(DATABASE_URL)
    
    query = text("""
        INSERT INTO accessor_table (accessor_id, name, password)
        VALUES (:id, :name, :password)
        ON CONFLICT (accessor_id) DO UPDATE SET
            name = EXCLUDED.name,
            password = EXCLUDED.password;
    """)
    
    try:
        with engine.connect() as connection:
            connection.execute(query, {"id": "1", "name": "Krishna", "password": "kris123"})
            connection.commit()
            print("✅ Successfully inserted/updated assessor: Krishna")
    except Exception as e:
        print(f"❌ Error inserting data: {e}")

if __name__ == "__main__":
    insert_dummy_assessor()
