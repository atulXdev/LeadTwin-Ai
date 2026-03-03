"""
Tool: AI Insights
Purpose: Generate "Why this is a good lead" explanations via Groq LLM.
Input: enriched company profile + score data
Output: Human-readable insight string
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def generate_insights(enriched_profile: dict, score_data: dict, contacts: dict) -> str:
    """
    Generate explainable insights for why a lead is valuable.
    Uses Groq API (Llama model). Falls back to template-based if API fails.
    """
    try:
        return _generate_with_groq(enriched_profile, score_data, contacts)
    except Exception as e:
        logger.warning(f"Groq API failed, using template fallback: {e}")
        return _generate_template(enriched_profile, score_data, contacts)


def _generate_with_groq(enriched_profile: dict, score_data: dict, contacts: dict) -> str:
    """Generate insights using Groq API."""
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")

    client = Groq(api_key=api_key)

    company_name = enriched_profile.get("company_name", "Unknown")
    score = score_data.get("score", 0)
    grade = score_data.get("grade", "Cold")

    # Build signal summary
    signals = []
    breakdown = score_data.get("breakdown", {})
    for signal_name, info in breakdown.items():
        if info.get("present"):
            signals.append(f"- {info['description']} (+{info['points']} pts)")

    signals_text = "\n".join(signals) if signals else "No strong signals detected."

    prompt = f"""You are an expert B2B sales analyst. Analyze this lead and write a concise 2-3 sentence insight explaining why this company is worth reaching out to (or not).

Company: {company_name}
Website: {enriched_profile.get('website', 'N/A')}
Score: {score}/100 ({grade})
Tech Stack: {', '.join(enriched_profile.get('tech_stack', [])) or 'Not detected'}
Services: {', '.join(enriched_profile.get('services_detected', [])) or 'Not detected'}
Has Email: {'Yes' if contacts.get('emails') else 'No'}

Positive Signals:
{signals_text}

Write the insight in a direct, actionable tone. Start with the most important finding. Do not use markdown formatting."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200,
    )

    insight = response.choices[0].message.content.strip()
    logger.info(f"Generated Groq insight for {company_name}")
    return insight


def _generate_template(enriched_profile: dict, score_data: dict, contacts: dict) -> str:
    """Fallback: Generate template-based insights without AI."""
    parts = []
    company = enriched_profile.get("company_name", "This company")

    if enriched_profile.get("has_hiring_page"):
        parts.append(f"{company} is actively hiring, indicating growth and budget availability.")

    if enriched_profile.get("has_saas_keywords"):
        parts.append("SaaS/tech keywords detected on their site suggest tech-forward operations.")

    if enriched_profile.get("has_pricing_page"):
        parts.append("They have a pricing page, suggesting a monetized product/service.")

    if enriched_profile.get("uses_modern_stack"):
        tech = ", ".join(enriched_profile.get("tech_stack", [])[:3])
        parts.append(f"Uses modern tech stack ({tech}), likely needs ongoing dev resources.")

    if enriched_profile.get("blog_updated_recently"):
        parts.append("Active blog within last 30 days shows content investment.")

    if contacts.get("emails"):
        parts.append(f"Direct contact available: {contacts['emails'][0]}.")

    if not parts:
        grade = score_data.get("grade", "Cold")
        parts.append(f"Limited signals detected. This is a {grade} lead — consider for future outreach.")

    return " ".join(parts)


# --- Direct CLI usage ---
if __name__ == "__main__":
    mock_profile = {
        "company_name": "AcmeTech",
        "website": "https://acmetech.com",
        "has_hiring_page": True,
        "has_saas_keywords": True,
        "has_pricing_page": True,
        "uses_modern_stack": True,
        "blog_updated_recently": False,
        "tech_stack": ["React", "Node.js", "AWS"],
        "services_detected": ["web development"],
    }
    mock_score = {
        "score": 75, "grade": "Hot",
        "breakdown": {
            "has_email": {"present": True, "points": 20, "description": "Contact email found"},
            "has_hiring_page": {"present": True, "points": 15, "description": "Company is actively hiring"},
        }
    }
    mock_contacts = {"emails": ["info@acme.com"], "phones": [], "linkedin": []}

    print(generate_insights(mock_profile, mock_score, mock_contacts))
