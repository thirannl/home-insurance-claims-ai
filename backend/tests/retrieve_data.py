import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def retrieve_all_data():
    engine = create_engine(DATABASE_URL)
    tables = ['accessor_table', 'policy', 'claim', 'terms_and_conditions']
    
    with engine.connect() as connection:
        for table in tables:
            print(f"\n--- Data from '{table}' ---")
            try:
                result = connection.execute(text(f"SELECT * FROM {table} LIMIT 5"))
                rows = result.fetchall()
                
                if not rows:
                    print(f"No rows found in {table}.")
                else:
                    # Print column names
                    print(f"Columns: {result.keys()}")
                    for row in rows:
                        print(row)
            except Exception as e:
                print(f"Error retrieving from {table}: {e}")

if __name__ == "__main__":
    retrieve_all_data()
