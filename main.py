
# pip install groq

from groq import Groq
import json
import sys
import io
from datetime import datetime

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fix for UnicodeEncodeError on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# 🔹 API Key
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ----------------------------
# READ INPUT FILES
# ----------------------------

with open("policy.txt", "r", encoding="utf-8") as f:
    policy = f.read()

with open("claim.txt", "r", encoding="utf-8") as f:
    claim_text = f.read()

with open("terms.txt", "r", encoding="utf-8") as f:
    terms = f.read()

# ----------------------------
# EXTRACT DATES & CALCULATE DELAY
# ----------------------------
def extract_date(text, label):
    for line in text.splitlines():
        if label in line:
            return line.split(":")[1].strip()
    return None

incident_date_str = extract_date(claim_text, "Incident Date")
report_date_str = extract_date(claim_text, "Report Date")

delay_days = "Unknown"
if incident_date_str and report_date_str:
    try:
        d1 = datetime.strptime(incident_date_str, "%Y-%m-%d")
        d2 = datetime.strptime(report_date_str, "%Y-%m-%d")
        delay_days = (d2 - d1).days
    except:
        pass

# ----------------------------
# PROMPT
# ----------------------------
prompt = f"""
You are an insurance claim assessment system.

Claim Data:
{claim_text}

Computed Data:
- Days between Incident and Report: {delay_days} days

Policy:
{policy}

General Terms and Conditions:
{terms}

STRICT ASSESSMENT RULES:
1. T&C Rule 1: Claim MUST be reported within 7 days. If 'Days between Incident and Report' is greater than 7, the decision MUST be 'Not Covered'.
2. Incident Type Check: If theft, check police complaint (within 24h).
3. Policy Coverage: Check if incident type is covered and not excluded.

Return ONLY raw JSON in this format:
{{
  "decision": "Covered" | "Not Covered" | "Needs Human Review",
  "justification": "Explain the decision. Mention the {delay_days} days delay if it violates Rule 1.",
  "flags": []
}}
"""
# ----------------------------
# API CALL
# ----------------------------

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0
)

result = response.choices[0].message.content

print("RAW RESPONSE:\n")
print(result)
