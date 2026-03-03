"""
Tool: Contact Extractor
Purpose: Extract emails, phone numbers, and LinkedIn URLs from page content.
Input: html (str), text (str)
Output: {emails: [], phones: [], linkedin: []}
"""

import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Regex patterns
EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE
)

PHONE_PATTERN = re.compile(
    r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
)

LINKEDIN_PATTERN = re.compile(
    r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9\-_/]+',
    re.IGNORECASE
)

# Common false-positive emails to filter out
BLACKLISTED_EMAILS = {
    "example@example.com", "email@example.com", "test@test.com",
    "your@email.com", "name@domain.com", "user@example.com",
}

BLACKLISTED_EMAIL_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "w3.org",
    "schema.org", "googleapis.com", "cloudflare.com",
    "webpack.js.org", "github.com", "npmjs.com",
}


def extract_contacts(html: str = "", text: str = "") -> dict:
    """
    Extract contact information from HTML and text content.
    Returns deduplicated and validated contacts.
    """
    content = text
    if html:
        try:
            soup = BeautifulSoup(html, "lxml")
            # Also check mailto: links
            mailto_emails = []
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if href.startswith("mailto:"):
                    email = href.replace("mailto:", "").split("?")[0].strip()
                    mailto_emails.append(email)

            content = text + " " + soup.get_text(separator=" ", strip=True)
        except Exception:
            content = text

    # Extract emails
    raw_emails = EMAIL_PATTERN.findall(content)
    if html:
        raw_emails.extend(mailto_emails if 'mailto_emails' in dir() else [])

    emails = _validate_emails(list(set(raw_emails)))

    # Extract phones
    raw_phones = PHONE_PATTERN.findall(content)
    phones = _validate_phones(raw_phones)

    # Extract LinkedIn URLs
    linkedin = list(set(LINKEDIN_PATTERN.findall(content)))

    logger.info(f"Extracted: {len(emails)} emails, {len(phones)} phones, {len(linkedin)} LinkedIn")

    return {
        "emails": emails,
        "phones": phones,
        "linkedin": linkedin,
    }


def _validate_emails(emails: list[str]) -> list[str]:
    """Filter out false-positive and blacklisted emails."""
    valid = []
    for email in emails:
        email = email.lower().strip().rstrip(".")
        domain = email.split("@")[-1]

        if email in BLACKLISTED_EMAILS:
            continue
        if domain in BLACKLISTED_EMAIL_DOMAINS:
            continue
        if len(email) > 100:
            continue
        # Skip image file references picked up by regex
        if any(email.endswith(ext) for ext in [".png", ".jpg", ".gif", ".svg", ".css", ".js"]):
            continue

        valid.append(email)

    return list(set(valid))


def _validate_phones(phones: list[str]) -> list[str]:
    """Filter phone numbers — keep only plausible ones."""
    valid = []
    for phone in phones:
        digits = re.sub(r'\D', '', phone)
        # Valid phone: 7–15 digits
        if 7 <= len(digits) <= 15:
            valid.append(phone.strip())
    return list(set(valid))[:5]  # Max 5 phones per company


# --- Direct CLI usage ---
if __name__ == "__main__":
    import json
    test_text = """
    Contact us at info@acme.com or sales@acme.com
    Phone: +91-9876543210
    LinkedIn: https://www.linkedin.com/company/acme-corp
    """
    result = extract_contacts(text=test_text)
    print(json.dumps(result, indent=2))
