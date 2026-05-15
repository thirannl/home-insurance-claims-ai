from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))
inspector = inspect(engine)

for table in ['accessor_table', 'policy', 'claim', 'terms_and_conditions']:
    print(f"\nStructure for '{table}':")
    columns = inspector.get_columns(table)
    for c in columns:
        print(f"  - {c['name']} ({c['type']})")
