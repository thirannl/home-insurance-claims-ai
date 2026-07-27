"""
e2e_pipeline_test.py
====================
End-to-end test for the /upload/submit call.

Verifies (in order):
  STEP 1 - API responds with HTTP 200
  STEP 2 - policy_chunks rows exist for the returned policy_id (NOT FAISS)
  STEP 3 - vector_service.search_index returns non-empty list of strings
  STEP 4 - Groq received real context (no fallback / system-error message)
  STEP 5 - assessment JSON contains a valid decision field

Run from the backend/ directory:
    python e2e_pipeline_test.py
"""

import io
import sys
import json
import textwrap
import requests
from sqlalchemy import text

import os, pathlib
os.chdir(pathlib.Path(__file__).parent)
from dotenv import load_dotenv
load_dotenv(override=True)

from app.db.database import SessionLocal
from app.services.vector_service import vector_service

BASE_URL    = "http://127.0.0.1:8000"
SUBMIT_URL  = f"{BASE_URL}/upload/submit"
RESULTS     = {}

def pass_fail(step, ok, detail=""):
    tag  = "PASS" if ok else "FAIL"
    line = f"[{tag}]  [{step}]"
    if detail:
        line += f"  ->  {detail}"
    print(line)
    RESULTS[step] = ok
    return ok

POLICY_TEXT = """HOME INSURANCE POLICY - TEST DOCUMENT
======================================
Policy Number: TEST-2026-001
Insured: John Doe
Property: 123 Test Street, Chennai

COVERAGE:
- Fire Damage: Covered up to INR 50,00,000
- Flood Damage: Covered up to INR 20,00,000
- Theft: Covered up to INR 5,00,000
- Earthquake: NOT covered

EXCLUSIONS:
- Pre-existing structural defects are excluded.
- Damage due to negligence is excluded.
- Intentional damage is excluded.

CLAIM PROCEDURE:
Claims must be filed within 30 days of the incident.
Supporting documents: FIR (if theft), photographs, repair estimates.
"""

CLAIM_TEXT = (
    "My house at 123 Test Street suffered severe fire damage on 20-Jul-2026. "
    "The kitchen caught fire due to an electrical short circuit. "
    "Estimated repair cost is INR 12,00,000. "
    "I am requesting claim settlement under the fire damage clause."
)

def make_pdf_bytes(body_text):
    safe = body_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    lines = safe.split("\n")
    stream_lines = ["BT", "/F1 12 Tf", "50 750 Td", "14 TL"]
    for ln in lines:
        stream_lines.append(f"({ln}) Tj T*")
    stream_lines.append("ET")
    stream_content = "\n".join(stream_lines)
    stream_bytes   = stream_content.encode("latin-1")
    stream_length  = len(stream_bytes)

    objects = {}
    objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[2] = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
    objects[3] = (
        b"<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 612 792] "
        b"/Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>"
    )
    objects[4] = (
        f"<< /Length {stream_length} >>\nstream\n".encode() +
        stream_bytes +
        b"\nendstream"
    )
    objects[5] = (
        b"<< /Type /Font /Subtype /Type1 "
        b"/BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    )

    buf   = io.BytesIO()
    xrefs = {}
    buf.write(b"%PDF-1.4\n")
    for obj_id in sorted(objects):
        xrefs[obj_id] = buf.tell()
        buf.write(f"{obj_id} 0 obj\n".encode())
        buf.write(objects[obj_id])
        buf.write(b"\nendobj\n")

    xref_pos = buf.tell()
    num_objs = max(objects) + 1
    buf.write(f"xref\n0 {num_objs}\n".encode())
    buf.write(b"0000000000 65535 f \n")
    for i in range(1, num_objs):
        pos = xrefs.get(i, 0)
        buf.write(f"{pos:010d} 00000 n \n".encode())

    buf.write(
        f"trailer\n<< /Size {num_objs} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n".encode()
    )
    return buf.getvalue()


def run_tests():
    print("\n" + "=" * 60)
    print("  END-TO-END PIPELINE TEST  -  /upload/submit")
    print("=" * 60)

    print("\n[STEP 1] Calling POST /upload/submit ...")
    pdf_bytes = make_pdf_bytes(POLICY_TEXT)
    try:
        resp = requests.post(
            SUBMIT_URL,
            data={
                "customer_name": "E2E TestUser",
                "claim_type":    "fire",
                "claim_text":    CLAIM_TEXT,
            },
            files={
                "policy_file": ("test_policy.pdf", pdf_bytes, "application/pdf"),
            },
            timeout=120,
        )
    except requests.exceptions.ConnectionError:
        print("  WARNING: Could not reach the server at", BASE_URL)
        print("  Run 'uvicorn main:app --reload' in another terminal first.")
        sys.exit(1)

    ok1 = resp.status_code == 200
    pass_fail("STEP 1 - HTTP 200", ok1, f"status={resp.status_code}")
    if not ok1:
        print("  Response body:", resp.text[:500])
        sys.exit(1)

    body       = resp.json()
    policy_id  = body.get("policy_id")
    claim_id   = body.get("claim_id")
    assessment = body.get("assessment", {})
    print(f"  policy_id={policy_id}  claim_id={claim_id}")

    print("\n[STEP 2] Checking policy_chunks table for policy_id =", policy_id)
    db = SessionLocal()
    try:
        rows = db.execute(
            text("SELECT id, left(content,60) AS snippet FROM policy_chunks WHERE policy_id = :pid"),
            {"pid": str(policy_id)},
        ).fetchall()
        chunk_count = len(rows)
        ok2 = chunk_count > 0
        pass_fail(
            "STEP 2 - Chunks in policy_chunks (pgvector, not FAISS)",
            ok2,
            f"{chunk_count} chunks found",
        )
        if rows:
            print(f"  Sample chunk: \"{rows[0].snippet}...\"")
    finally:
        db.close()

    print("\n[STEP 3] Calling vector_service.search_index for policy_id =", policy_id)
    try:
        hits = vector_service.search_index(CLAIM_TEXT, str(policy_id), top_k=3)
        ok3  = isinstance(hits, list) and len(hits) > 0 and isinstance(hits[0], str)
        pass_fail(
            "STEP 3 - search_index returns non-empty list of strings",
            ok3,
            f"{len(hits)} hit(s) returned",
        )
        if hits:
            print(f"  Top hit preview: \"{hits[0][:100]}...\"")
    except Exception as exc:
        pass_fail("STEP 3 - search_index returns non-empty list of strings", False, str(exc))
        ok3 = False

    print("\n[STEP 4] Checking Groq received real context (no error fallback) ...")
    if isinstance(assessment, dict):
        justification = assessment.get("justification", "")
        flags         = assessment.get("flags", [])
        groq_errored  = (
            "Error connecting to Groq" in justification
            or "System Error" in str(flags)
        )
        ok4 = not groq_errored
        pass_fail(
            "STEP 4 - Groq received real context (no fallback)",
            ok4,
            "Groq call succeeded" if ok4 else f"Groq error: {justification[:80]}",
        )
    else:
        ok4 = isinstance(assessment, str) and len(assessment) > 10
        pass_fail(
            "STEP 4 - Groq received real context (no fallback)",
            ok4,
            "Assessment is raw string (non-JSON Groq response)",
        )

    print("\n[STEP 5] Checking assessment.decision field ...")
    if isinstance(assessment, dict):
        decision = assessment.get("decision", "")
        ok5 = bool(decision)
        detail = f"decision='{decision}'"
    else:
        try:
            parsed  = json.loads(assessment)
            decision = parsed.get("decision", "")
            ok5     = bool(decision)
            detail  = f"decision='{decision}'"
        except Exception:
            ok5    = False
            detail = "Could not parse decision from assessment"
    pass_fail("STEP 5 - Valid decision field returned", ok5, detail)

    print("\n" + "=" * 60)
    total   = len(RESULTS)
    passed  = sum(1 for v in RESULTS.values() if v)
    print(f"  RESULT: {passed}/{total} steps passed")
    print("=" * 60)

    if passed == total:
        print("\nAll checks PASSED - pipeline is fully functional.\n")
    else:
        failed_steps = [k for k, v in RESULTS.items() if not v]
        print(f"\nFailed steps: {', '.join(failed_steps)}\n")

    print("\nFull assessment response:")
    print(json.dumps(assessment, indent=2) if isinstance(assessment, dict) else assessment)
    print()


if __name__ == "__main__":
    run_tests()
