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

"""Structure for 'accessor_table':
  - accessor_id (TEXT)
  - password (TEXT)
  - name (TEXT)

Structure for 'policy':
  - policy_id (BIGINT)
  - uploaded_at (TIMESTAMP)
  - location (TEXT)

Structure for 'claim':
  - claim_id (BIGINT)
  - policy_id (BIGINT)
  - customer_name (TEXT)
  - claim_type (TEXT)
  - claim_time (TIMESTAMP)
  - result (TEXT)

Structure for 'terms_and_conditions':
  - id (BIGINT)
  - updated_at (TIMESTAMP)
  - location (TEXT)"""