#!/usr/bin/env python3
"""Make marketplace fact text read naturally in search snippets.

Google can drop middle-dot separators when it builds snippets from listing cards,
which turns text such as "8 triệu/tháng · 54 m²" into
"8 triệu/tháng54 m²". This post-process keeps the visual copy compact while
using literal comma/period separators that survive plain-text extraction better.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENT_HUB = ROOT / "cho-thue-lumi-hanoi" / "index.html"
LIST_JS = ROOT / "assets" / "js" / "marketplace-list.js"
STATIC_START = "<!-- MARKETPLACE-STATIC-LISTINGS:START -->"
STATIC_END = "<!-- MARKETPLACE-STATIC-LISTINGS:END -->"


def normalize_static_rent_cards() -> bool:
    raw = RENT_HUB.read_text(encoding="utf-8")
    if STATIC_START not in raw or STATIC_END not in raw:
        raise RuntimeError("Rental static-listing markers are missing")

    start = raw.index(STATIC_START)
    end = raw.index(STATIC_END, start)
    block = raw[start:end]

    pattern = re.compile(
        r'(<strong class="listing-card-fact-price">)(.*?)(</strong>)',
        flags=re.S,
    )

    def rewrite(match: re.Match[str]) -> str:
        text = match.group(2).strip()
        # Only rental facts on this hub are normalized. Keep content unchanged,
        # only use snippet-safe punctuation instead of middle dots.
        text = re.sub(r"\s*·\s*", ", ", text)
        text = re.sub(r"\s*,\s*", ", ", text).strip(" ,")
        if text and not text.endswith((".", "!", "?")):
            text += "."
        return match.group(1) + text + match.group(3)

    updated_block = pattern.sub(rewrite, block)
    updated = raw[:start] + updated_block + raw[end:]
    if updated == raw:
        return False
    RENT_HUB.write_text(updated, encoding="utf-8")
    return True


def normalize_dynamic_card_facts() -> bool:
    raw = LIST_JS.read_text(encoding="utf-8")

    old = '''    const facts=el("div","listing-card-facts");
    facts.append(el("strong","listing-card-fact-price",api.formatCurrency(listing.price_vnd,listing.listing_type)));
    [
      formatArea(listing.area_sqm),
      pricePerSqm(listing),
      listing.unit_type,
      listing.floor_label?("Tầng "+listing.floor_label):""
    ].filter(Boolean).forEach(value=>facts.append(el("span","",value)));
'''

    new = '''    const facts=el("div","listing-card-facts");
    facts.append(el("strong","listing-card-fact-price",api.formatCurrency(listing.price_vnd,listing.listing_type)));
    const factValues=[
      formatArea(listing.area_sqm),
      pricePerSqm(listing),
      listing.unit_type,
      listing.floor_label?("Tầng "+listing.floor_label):""
    ].filter(Boolean);
    factValues.forEach(value=>{
      facts.append(document.createTextNode(", "));
      facts.append(el("span","",value));
    });
    facts.append(document.createTextNode("."));
'''

    if old in raw:
        updated = raw.replace(old, new, 1)
    elif new in raw:
        return False
    else:
        raise RuntimeError("marketplace-list.js fact-render block has changed; review patch")

    LIST_JS.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    static_changed = normalize_static_rent_cards()
    js_changed = normalize_dynamic_card_facts()
    print(
        "Snippet punctuation normalized: "
        f"rent_hub={'changed' if static_changed else 'current'}, "
        f"marketplace_js={'changed' if js_changed else 'current'}"
    )


if __name__ == "__main__":
    main()
