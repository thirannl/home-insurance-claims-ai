import gradio as gr
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
# CLEAN JSON FROM MODEL OUTPUT
# ----------------------------
def extract_json(text):
    start = text.find("{")
    end = text.rfind("}") + 1

    if start != -1 and end != -1:
        return text[start:end]
    return text


# ----------------------------
# LOAD POLICY & TERMS (ONCE)
# ----------------------------
policy = read_docx("data/sample-policy using llm.docx")[:3000]
terms = read_docx("data/sample-t&c.docx")[:3000]


# ----------------------------
# MAIN FUNCTION (UI → LLM)
# ----------------------------
def evaluate_claim(claimant_name, date, incident_type, description, area, amount):

    claim = {
        "claimant_name": claimant_name,
        "date_of_incident": date,
        "incident_type": incident_type,
        "description": description,
        "affected_area": area,
        "estimated_value": amount
    }

    claim_text = json.dumps(claim, indent=2)

    prompt = f"""
You are an expert insurance claims assessor.

Your task is to evaluate a claim using ONLY the given policy and terms.

----------------------------
STRICT RULES
----------------------------
1. Use ONLY the given claim, policy, and terms.
2. Do NOT assume anything not written.
3. Do NOT modify the claim.
4. Use ONLY relevant sections of policy.
5. Check numerical calculations carefully.

----------------------------
CRITICAL DECISION RULES
----------------------------
1. Exclusions override everything.
2. Limits override coverage.
3. You MUST check limits before final decision.
4. If claim exceeds limit AND endorsement is not provided:
   → decision MUST be "Needs Human Review"
5. Do NOT return "Covered" if limits are violated.

----------------------------
DECISION FLOW
----------------------------
Step 1: Identify incident type  
Step 2: Check coverage (check all relevant points in policy is matched or not if type is matched but remaining points are not matched → RETURN "Needs Human Review" , STOP here)
Step 3: Check exclusions  
Step 4: Check limits (CRITICAL)
    - If exceeded:
        → Check endorsement
        → If not mentioned:
            → Needs Human Review (STOP)

Step 5: Check conditions  
Step 6: Final decision  

----------------------------
INPUT
----------------------------
Claim:
{claim_text}

Policy:
{policy}

Terms:
{terms}

----------------------------
OUTPUT (STRICT JSON ONLY)
----------------------------
Return ONLY valid JSON.

Rules for flags:
- flags should ALWAYS contain meaningful information
- If claim is Covered:
    → include conditions to proceed (e.g., deductible, documents required)
- If claim is Not Covered:
    → include the exact reason (e.g., exclusion triggered)
- If claim is Needs Human Review:
    → include missing or unclear information

- Do NOT leave flags empty
- Do NOT add irrelevant flags

{{
  "decision": "Covered | Not Covered | Needs Human Review",
  "justification": "Short explanation based on policy",
  "flags": ["meaningful conditions or issues"]
}}
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False
            }
        )

        raw_output = response.json()["response"]

        # Extract JSON
        cleaned = extract_json(raw_output)
        parsed = json.loads(cleaned)

        decision = parsed.get("decision", "")
        justification = parsed.get("justification", "")
        flags = "\n".join(parsed.get("flags", []))

        return decision, justification, flags

    except Exception as e:
        return "Error", str(e), ""


# ----------------------------
# UI DESIGN
# ----------------------------
with gr.Blocks() as app:

    gr.Markdown("# 🏠 Home Insurance Claim Evaluator")
    gr.Markdown("### 👤 Assessor Input")

    claimant_name = gr.Textbox(label="Claimant Name")
    date = gr.Textbox(label="Date of Incident (YYYY-MM-DD)")

    with gr.Row():
        incident_type = gr.Textbox(label="Incident Type")
        amount = gr.Number(label="Estimated Value (₹)")

    description = gr.Textbox(label="Description", lines=3)
    area = gr.Textbox(label="Affected Area")

    btn = gr.Button("🚀 Evaluate Claim")

    gr.Markdown("### 📊 Result")

    decision = gr.Textbox(label="Decision")
    justification = gr.Textbox(label="Justification", lines=3)
    flags = gr.Textbox(label="Flags")

    btn.click(
        evaluate_claim,
        inputs=[claimant_name, date, incident_type, description, area, amount],
        outputs=[decision, justification, flags]
    )


# ----------------------------
# RUN APP
# ----------------------------
app.launch()