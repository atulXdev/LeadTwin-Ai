"""
Tool: Sheets Export
Purpose: Export scored leads to CSV file and optionally Google Sheets.
Input: list of lead dicts
Output: filepath of exported CSV
"""

import os
import csv
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Ensure .tmp directory exists
TMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp")


def export_to_csv(leads: list[dict], project_name: str = "leads") -> str:
    """
    Export leads to a CSV file in .tmp/ directory.
    Returns the absolute path of the exported file.
    """
    os.makedirs(TMP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{project_name}_{timestamp}.csv"
    filepath = os.path.join(TMP_DIR, filename)

    # Define CSV columns
    columns = [
        "company_name", "website", "email", "phone", "linkedin",
        "score", "grade", "insights",
        "has_hiring_page", "has_pricing_page", "tech_stack", "services",
    ]

    rows = []
    for lead in leads:
        row = {
            "company_name": lead.get("company_name", ""),
            "website": lead.get("website", ""),
            "email": "; ".join(lead.get("emails", [])) if isinstance(lead.get("emails"), list) else lead.get("email", ""),
            "phone": "; ".join(lead.get("phones", [])) if isinstance(lead.get("phones"), list) else lead.get("phone", ""),
            "linkedin": "; ".join(lead.get("linkedin", [])) if isinstance(lead.get("linkedin"), list) else lead.get("linkedin_url", ""),
            "score": lead.get("score", 0),
            "grade": lead.get("grade", "Cold"),
            "insights": lead.get("insights", ""),
            "has_hiring_page": lead.get("has_hiring_page", False),
            "has_pricing_page": lead.get("has_pricing_page", False),
            "tech_stack": ", ".join(lead.get("tech_stack", [])) if isinstance(lead.get("tech_stack"), list) else "",
            "services": ", ".join(lead.get("services_detected", [])) if isinstance(lead.get("services_detected"), list) else "",
        }
        rows.append(row)

    # Sort by score descending
    rows.sort(key=lambda x: x.get("score", 0), reverse=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Exported {len(rows)} leads to {filepath}")
    return filepath


def format_leads_for_export(
    enriched_profiles: list[dict],
    contacts_list: list[dict],
    scores: list[dict],
    insights_list: list[str],
) -> list[dict]:
    """
    Merge enrichment, contacts, scores, and insights into flat lead dicts for export.
    """
    merged = []
    for i in range(len(enriched_profiles)):
        profile = enriched_profiles[i] if i < len(enriched_profiles) else {}
        contact = contacts_list[i] if i < len(contacts_list) else {}
        score = scores[i] if i < len(scores) else {}
        insight = insights_list[i] if i < len(insights_list) else ""

        lead = {
            **profile,
            "emails": contact.get("emails", []),
            "phones": contact.get("phones", []),
            "linkedin": contact.get("linkedin", []),
            "email": contact.get("emails", [""])[0] if contact.get("emails") else "",
            "score": score.get("score", 0),
            "grade": score.get("grade", "Cold"),
            "insights": insight,
        }
        merged.append(lead)

    return merged


# --- Direct CLI usage ---
if __name__ == "__main__":
    mock_leads = [
        {
            "company_name": "AcmeTech",
            "website": "https://acmetech.com",
            "emails": ["info@acme.com"],
            "phones": ["+91-9876543210"],
            "linkedin": ["https://linkedin.com/company/acme"],
            "score": 75,
            "grade": "Hot",
            "insights": "Actively hiring, SaaS signals detected.",
            "has_hiring_page": True,
            "has_pricing_page": True,
            "tech_stack": ["React", "AWS"],
            "services_detected": ["web development"],
        }
    ]
    path = export_to_csv(mock_leads, "test_project")
    print(f"Exported to: {path}")
