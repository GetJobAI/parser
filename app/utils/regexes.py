from __future__ import annotations

import re
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?:(?:\+?\d{1,3})?[\s().-]*)?(?:\d[\s().-]*){7,15}\d"
)
URL_RE = re.compile(
    r"\b(?:https?://)?(?:www\.)?[A-Z0-9][A-Z0-9.-]+\.[A-Z]{2,}(?:/[^\s]*)?\b",
    re.IGNORECASE,
)
DATE_TOKEN = (
    r"(?:"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}"
    r"|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"|\d{1,2}[./-]\d{4}"
    r"|\d{4}"
    r")"
)
DATE_RANGE_RE = re.compile(
    rf"\b({DATE_TOKEN})\s*(?:-|–|—|to)\s*(Present|Current|Now|{DATE_TOKEN})\b",
    re.IGNORECASE,
)


def extract_first_email(text: str) -> str | None:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None


def extract_first_phone(text: str) -> str | None:
    match = PHONE_RE.search(text)
    return match.group(0).strip() if match else None


def extract_urls(text: str) -> list[str]:
    urls: list[str] = []
    for match in URL_RE.finditer(text):
        if match.start() > 0 and text[match.start() - 1] == "@":
            continue
        urls.append(match.group(0).strip(".,;"))
    return list(dict.fromkeys(urls))


def detect_profile_links(urls: list[str]) -> dict[str, str | None]:
    linkedin = None
    github = None
    website = None

    for raw_url in urls:
        normalized = raw_url if raw_url.startswith("http") else f"https://{raw_url}"
        host = urlparse(normalized).netloc.lower()
        if "linkedin.com" in host and linkedin is None:
            linkedin = normalized
        elif "github.com" in host and github is None:
            github = normalized
        elif website is None:
            website = normalized

    return {
        "linkedin": linkedin,
        "github": github,
        "website": website,
    }


def extract_date_range(text: str) -> str | None:
    match = DATE_RANGE_RE.search(text)
    return match.group(0) if match else None


def split_date_range(date_range: str | None) -> tuple[str | None, str | None]:
    if not date_range:
        return None, None
    parts = re.split(r"\s*(?:-|–|—|to)\s*", date_range, maxsplit=1)
    if len(parts) != 2:
        return date_range, None
    return parts[0].strip(), parts[1].strip()
