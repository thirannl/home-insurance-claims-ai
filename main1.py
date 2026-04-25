
import requests
import json
from docx import Document

# ----------------------------
# READ DOCX FILE
# ----------------------------
def read_docx(path):
    doc = Document(path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


# ----------------------------
# LOAD INPUT FILES
# ----------------------------
def load_claim(path):
    with open(path, "r") as f:
        return json.load(f)


# ----------------------------
# CLEAN JSON FROM MODEL OUTPUT
# ----------------------------
def extract_json(text):
    start = text.find("{")
    end = text.rfind("}") + 1

    if start != -1 and end != -1:
        return text[start:end]
    return text


# ----------------------------
# MAIN EXECUTION
# ----------------------------
def main():

    # 🔹 Load files
    claim = load_claim("data\\claim.json")
    policy = read_docx("data\\sample-policy using llm.docx")
    terms = read_docx("data\\sample-t&c.docx")

    # 🔹 Limit text (IMPORTANT)
    policy = policy[:3000]
    terms = terms[:3000]

    # 🔹 Convert claim to string
    claim_text = json.dumps(claim, indent=2)

    # 🔹 Prompt (FINAL VERSION)
    prompt = f"""
You are an expert insurance claims assessor.

Your task is to evaluate a claim using ONLY the provided policy and terms.

----------------------------
STRICT RULES (MANDATORY)
----------------------------
1. Use ONLY the given claim, policy, and terms.
2. Do NOT invent or assume anything.
3. Do NOT reinterpret or modify the claim.
4. Do NOT use unrelated policy sections.
5. Check numerical calculation correctly.
6. check date in correctly if needed for date of incident and date of reporting
----------------------------
CRITICAL DECISION RULES
----------------------------
1. Exclusions override everything.
2. Limits override coverage.
3. You MUST check limits BEFORE giving final decision.
4. If claim amount exceeds policy limit AND endorsement is NOT provided:
   ->"Check limits carefully " and perform numerical calculation correctly 
   → FINAL DECISION MUST BE "Needs Human Review"
5. You are NOT allowed to return "Covered" if limits are violated.
6. If a required condition for coverage is explicitly NOT satisfied in the claim → decision MUST be "Not Covered".
7. Do NOT return "Needs Human Review" when the claim clearly violates a condition.
----------------------------
MANDATORY DECISION FLOW
----------------------------
Follow ALL steps in order:

Step 1: Identify incident type  
Step 2: Check if covered  (if not follow any one point ->RETURN "Not covered" , STOP here)
Step 3: Check exclusions  
Step 4: Check limits (CRITICAL)
    - If claim amount > limit:
        → Check endorsement
        → If endorsement NOT mentioned:
            → RETURN "Needs Human Review" (STOP here)
Step 5: Check conditions
- If condition is clearly satisfied → continue
- If condition is missing → Needs Human Review
- If condition is clearly NOT satisfied → Not Covered (STOP)
Step 6: Check terms and conditions (important)
       -check terms and condition on each point whether it suit for this claim and considered this .
       -if(not follow any point-> RETURN "Needs Human Review" (STOP here) )
Step 7: Final decision  

----------------------------
IMPORTANT
----------------------------
- DO NOT stop after checking coverage
- Step 4 (limits) is mandatory
- If Step 4 fails → DO NOT return "Covered"

----------------------------
INPUT
----------------------------
Claim:
{claim}

Policy:
{policy}

Terms:
{terms}

----------------------------
OUTPUT (STRICT JSON ONLY)
----------------------------
Return ONLY valid JSON.

Rules for flags:
- flags MUST NOT be empty  
- Any conditions that must be met for the claim to proceed
- If claim exceeds limit → include flag: "Claim exceeds policy limit"
- If endorsement missing → include flag: "Endorsement not available"
- If information missing → include flag describing missing data

{{
  "decision": "Covered | Not Covered | Needs Human Review",
  "justification": "Short explanation based on policy",
  "flags": ["at least one meaningful flag if applicable"]
}}
"""

    # 🔹 Call Ollama
    url = "http://localhost:11434/api/generate"

    data = {
        "model": "llama3.1:8b",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=data)

    # 🔹 Extract output
    raw_output = response.json()["response"]

    print("\n===== RAW OUTPUT =====\n")
    print(raw_output)

    # 🔹 Clean JSON
    cleaned = extract_json(raw_output)

    try:
        parsed = json.loads(cleaned)
        print("\n===== CLEAN OUTPUT =====\n")
        print(json.dumps(parsed, indent=2))
    except:
        print("\n⚠️ JSON parsing failed. Showing raw output.")


# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    main()