
from groq import Groq
import json

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 🔹 API Key
api_key = os.getenv("GROQ_API_KEY")

# 🔹 Initialize client
client = Groq(api_key=api_key)


# --- Define Policy and Claim ---
policy = """
Water damage from plumbing is covered.
Flood damage is NOT covered.
Jewellery covered up to ₹500 per item.
"""

claim = """
Incident: Pipe burst in kitchen
Damage: Water damaged walls and floor
Value: ₹20000
"""

# --- Create Prompt ---
prompt = f"""
You are an insurance claim assessment system.
Return ONLY valid JSON with no extra text.

Claim:
{claim}

Policy:
{policy}

Instructions:
1. Decide one of:
   - Covered
   - Not Covered
   - Needs Human Review

2. Justification must include:
   - What the claim says
   - What the policy says
   - Why it is covered or not

Return format:
{{
  "decision": "",
  "justification": "",
  "flags": []
}}
"""

# --- Call API ---
try:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # or mixtral-8x7b-32768
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    result = response.choices[0].message.content

    print("=== RAW RESPONSE ===")
    print(result)

    # 🔹 Parse JSON
    try:
        parsed = json.loads(result)
        print("\n=== PARSED JSON ===")
        print(parsed)
    except:
        print("\nResponse is not valid JSON")


except Exception as e:
    print("Error:", e)