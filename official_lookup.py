"""Fetch official e-passport fees when possible; use offline SQLite upon failure.

No AI is trusted to calculate money; only fully parsed official tables or cached
official fee fixtures can be used. The portal may serve client-rendered HTML.
"""
from __future__ import annotations
import re
from policy_store import cache_fees, load_seed


def parse_official_fee_text(text: str) -> dict:
    """Extract 12 BDT prices with context (pages, validity, delivery).

    Reject incomplete pages to prevent silently mixing different tariffs.
    """
    normal = re.sub(r"\s+", " ", text.replace("\xa0", " "))
    # Limit search to inside-Bangladesh table (the mission table is in USD).
    start = re.search(r"e[- ]?Passport fees for inside Bangladesh", normal, re.I)
    if not start:
        raise ValueError("Domestic fee section not found")
    section = normal[start.end():]
    end = re.search(r"e[- ]?Passport fees for Bangladesh Mission", section, re.I)
    if end:
        section = section[:end.start()]
    headers = list(re.finditer(r"e[- ]?Passport with\s+(48|64)\s+pages\s+and\s+(5|10)\s+years\s+validity", section, re.I))
    parsed: dict[tuple[int, int, str], int] = {}
    for i, h in enumerate(headers):
        chunk = section[h.end():(headers[i+1].start() if i+1 < len(headers) else len(section))]
        pages, years = int(h.group(1)), int(h.group(2))
        for speed, pattern in (
            ("regular", r"(?<!Super )Regular delivery\s*:?\s*(?:TK|BDT|৳)\s*([\d,]+)"),
            ("express", r"(?<!Super )Express delivery\s*:?\s*(?:TK|BDT|৳)\s*([\d,]+)"),
            ("super_express", r"Super[- ]?Express delivery\s*:?\s*(?:TK|BDT|৳)\s*([\d,]+)"),
        ):
            m = re.search(pattern, chunk, re.I)
            if m:
                parsed[(pages, years, speed)] = int(m.group(1).replace(",", ""))
    if len(parsed) != 12:
        raise ValueError(f"Expected 12 domestic official fee values, found {len(parsed)}")
    if not all(1000 <= x <= 50000 for x in parsed.values()):
        raise ValueError("Unexpected fee values")
    return parsed


def resolve_fees(offline: bool = False) -> tuple[dict, str, str]:
    """Returns fees, provenance, warning; always falls back to SQLite."""
    if not offline:
        try:
            import requests
            from bs4 import BeautifulSoup
            response = requests.get(load_seed()["sources"]["fees"], timeout=8,
                                    headers={"User-Agent": "AmarPassportAI/1.0 educational-project"})
            response.raise_for_status()
            parsed = parse_official_fee_text(BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True))
            return parsed, "Online official portal (parsed domestic fee table)", ""
        except Exception as exc:
            reason = type(exc).__name__
            return cache_fees(), "Offline SQLite cache (official 2026 fee snapshot)", f"Live lookup unavailable ({reason}); cached fees used. Verify before payment."
    return cache_fees(), "Offline SQLite cache (official 2026 fee snapshot)", "Offline mode: cached fees used. Verify before payment."
