
import os
import subprocess
import json
import sys
import io

# Fix for UnicodeEncodeError on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

scenarios = [
    {
        "name": "Valid Fire Claim",
        "claim": """Claimant Name: Jeevanraj
Incident Date: 2026-04-01
Report Date: 2026-04-03
Incident Type: Fire
Description: Small kitchen fire.
Affected Area: Kitchen
Estimated Claim Value: ₹10,000"""
    },
    {
        "name": "Late Reporting (15 days)",
        "claim": """Claimant Name: Jeevanraj
Incident Date: 2026-04-01
Report Date: 2026-04-16
Incident Type: Fire
Description: Living room damage.
Affected Area: Living Room
Estimated Claim Value: ₹20,000"""
    },
    {
        "name": "Theft without Police Complaint",
        "claim": """Claimant Name: Jeevanraj
Incident Date: 2026-04-01
Report Date: 2026-04-02
Incident Type: Theft
Description: Laptop stolen from home. No police complaint filed yet.
Affected Area: Study
Estimated Claim Value: ₹50,000"""
    },
    {
        "name": "Excluded Peril (Flood)",
        "claim": """Claimant Name: Jeevanraj
Incident Date: 2026-04-01
Report Date: 2026-04-02
Incident Type: Flood
Description: Basement flooded due to heavy rain.
Affected Area: Basement
Estimated Claim Value: ₹30,000"""
    },
    {
        "name": "Valid Theft Claim",
        "claim": """Claimant Name: Jeevanraj
Incident Date: 2026-04-01
Report Date: 2026-04-02
Incident Type: Theft
Description: Jewellery stolen. Police complaint filed within 2 hours.
Affected Area: Bedroom
Estimated Claim Value: ₹80,000"""
    }
]

def run_test(scenario):
    print(f"\n--- Testing Scenario: {scenario['name']} ---")
    with open("claim.txt", "w", encoding="utf-8") as f:
        f.write(scenario["claim"])
    
    result = subprocess.run(["python", "main.py"], capture_output=True, text=True, encoding="utf-8")
    
    print(result.stdout)

for s in scenarios:
    run_test(s)
