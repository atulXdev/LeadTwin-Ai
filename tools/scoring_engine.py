"""
Tool: Scoring Engine
Purpose: Score leads 0–100 based on signal matrix from PRD.
Input: enriched company profile + contacts
Output: {score: int, grade: "Hot"|"Warm"|"Cold", breakdown: {}}
"""

import logging

logger = logging.getLogger(__name__)

# Scoring matrix from PRD
SCORING_RULES = {
    "has_email": {
        "points": 20,
        "description": "Contact email found",
    },
    "has_hiring_page": {
        "points": 15,
        "description": "Company is actively hiring",
    },
    "has_saas_keywords": {
        "points": 15,
        "description": "SaaS/tech keywords detected",
    },
    "has_pricing_page": {
        "points": 10,
        "description": "Pricing page exists (monetized product)",
    },
    "uses_modern_stack": {
        "points": 10,
        "description": "Uses modern tech stack",
    },
    "blog_updated_recently": {
        "points": 10,
        "description": "Blog updated in the last 30 days",
    },
    "has_phone": {
        "points": 5,
        "description": "Phone number available",
    },
    "has_linkedin": {
        "points": 5,
        "description": "LinkedIn profile found",
    },
    "has_services_page": {
        "points": 5,
        "description": "Services/solutions page exists",
    },
    "has_about_page": {
        "points": 5,
        "description": "About page exists (established company)",
    },
}


def score_lead(enriched_profile: dict, contacts: dict) -> dict:
    """
    Score a lead based on the enrichment and contact signals.
    Returns score (0-100), grade, and breakdown.
    """
    score = 0
    breakdown = {}

    # Check each scoring rule
    signals = {
        "has_email": len(contacts.get("emails", [])) > 0,
        "has_hiring_page": enriched_profile.get("has_hiring_page", False),
        "has_saas_keywords": enriched_profile.get("has_saas_keywords", False),
        "has_pricing_page": enriched_profile.get("has_pricing_page", False),
        "uses_modern_stack": enriched_profile.get("uses_modern_stack", False),
        "blog_updated_recently": enriched_profile.get("blog_updated_recently", False),
        "has_phone": len(contacts.get("phones", [])) > 0,
        "has_linkedin": len(contacts.get("linkedin", [])) > 0,
        "has_services_page": enriched_profile.get("has_services_page", False),
        "has_about_page": enriched_profile.get("has_about_page", False),
    }

    for signal_name, is_present in signals.items():
        rule = SCORING_RULES[signal_name]
        if is_present:
            score += rule["points"]
            breakdown[signal_name] = {
                "points": rule["points"],
                "description": rule["description"],
                "present": True,
            }
        else:
            breakdown[signal_name] = {
                "points": 0,
                "description": rule["description"],
                "present": False,
            }

    # Cap at 100
    score = min(score, 100)

    # Determine grade
    if score >= 60:
        grade = "Hot"
    elif score >= 35:
        grade = "Warm"
    else:
        grade = "Cold"

    logger.info(f"Scored lead: {score}/100 ({grade})")

    return {
        "score": score,
        "grade": grade,
        "breakdown": breakdown,
        "signals_hit": sum(1 for s in signals.values() if s),
        "signals_total": len(signals),
    }


# --- Direct CLI usage ---
if __name__ == "__main__":
    import json

    mock_profile = {
        "has_hiring_page": True,
        "has_pricing_page": True,
        "has_saas_keywords": True,
        "uses_modern_stack": True,
        "blog_updated_recently": False,
        "has_services_page": True,
        "has_about_page": True,
    }
    mock_contacts = {
        "emails": ["info@acme.com"],
        "phones": ["+91-9876543210"],
        "linkedin": ["https://linkedin.com/company/acme"],
    }

    result = score_lead(mock_profile, mock_contacts)
    print(json.dumps(result, indent=2))
