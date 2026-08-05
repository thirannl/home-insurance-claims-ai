import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv('.env')
from sqlalchemy import create_engine, text

engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'claim' AND column_name IN ('final_decision','reviewed_by','reviewed_at')"
    ))
    cols = [r[0] for r in result]
    print('Columns found:', cols)
    if len(cols) == 3:
        print('SUCCESS: All 3 override columns are present.')
    else:
        missing = set(['final_decision','reviewed_by','reviewed_at']) - set(cols)
        print('MISSING:', missing)
