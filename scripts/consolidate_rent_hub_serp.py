#!/usr/bin/env python3
"""Consolidate broad rental-query SEO signals on the primary Lumi Hanoi rental hub.

Goals:
- make /cho-thue-lumi-hanoi/ the clear target for broad queries such as
  "thuê lumi hanoi" / "cho thuê căn hộ chung cư lumi hanoi";
- keep the requested SERP-style title fresh by month/year;
- prevent the narrower Signature landing page from competing in the sitemap;
- add fallback canonical/noindex signals on that page in case a static host serves it
  without the Netlify 301 redirect.

This script is intentionally idempotent and runs after the rental generators.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://lumi-hanoi.com"
HUB = ROOT / "cho-thue-lumi-hanoi" / "index.html"
SIGNATURE = ROOT / "cho-thue-lumi-signature" / "index.html"
SITEMAP = ROOT / "sitemap.xml"


def period(today: date) -> str:
    return f"T{today.month}/{today.year}"


def replace_once(raw: str, pattern: str, replacement: str) -> str:
    return re.sub(pattern, replacement, raw, count=1, flags=re.S)


def update_hub(today: date) -> None:
    raw = HUB.read_text(encoding="utf-8")
    current_period = period(today)
    title = f"Cho Thuê Căn Hộ Chung Cư Lumi Hanoi Giá Tốt {current_period}"
    description = (
        f"Cho thuê căn hộ chung cư Lumi Hanoi giá tốt {current_period}: quỹ căn đang cho thuê "
        "theo phân khu, tòa và loại căn. Xem giá rao, diện tích, hình ảnh và liên hệ trực tiếp người đăng."
    )

    raw = replace_once(raw, r"<title>.*?</title>", f"<title>{title}</title>")
    raw = replace_once(
        raw,
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{description}">',
    )
    raw = replace_once(
        raw,
        r'<meta property="og:title" content="[^"]*">',
        f'<meta property="og:title" content="{title}">',
    )
    raw = replace_once(
        raw,
        r'<meta property="og:description" content="[^"]*">',
        f'<meta property="og:description" content="{description}">',
    )
    raw = replace_once(
        raw,
        r'<meta name="twitter:title" content="[^"]*">',
        f'<meta name="twitter:title" content="{title}">',
    )
    raw = replace_once(
        raw,
        r'<meta name="twitter:description" content="[^"]*">',
        f'<meta name="twitter:description" content="{description}">',
    )

    # Align visible heading and structured-data headline with the SERP target.
    raw = replace_once(
        raw,
        r"<h1>Cho thuê chung cư Lumi Hanoi</h1>",
        "<h1>Cho thuê căn hộ chung cư Lumi Hanoi giá tốt</h1>",
    )
    raw = replace_once(raw, r'"headline":"[^"]*"', f'"headline":"{title}"')
    raw = re.sub(
        r'data-inventory-home-title="[^"]*"',
        f'data-inventory-home-title="{title}"',
        raw,
        count=1,
    )

    # Keep the primary URL explicit even if an upstream generator changes markup.
    canonical = f'{SITE}/cho-thue-lumi-hanoi/'
    raw = replace_once(
        raw,
        r'<link rel="canonical" href="[^"]*">',
        f'<link rel="canonical" href="{canonical}">',
    )
    raw = replace_once(
        raw,
        r'<meta property="og:url" content="[^"]*">',
        f'<meta property="og:url" content="{canonical}">',
    )

    HUB.write_text(raw, encoding="utf-8")


def deindex_signature_fallback() -> None:
    """Fallback only: production should serve a 301 from Netlify before this HTML."""
    if not SIGNATURE.exists():
        return
    raw = SIGNATURE.read_text(encoding="utf-8")
    canonical = f'{SITE}/cho-thue-lumi-hanoi/'
    raw = replace_once(
        raw,
        r'<meta name="robots" content="[^"]*">',
        '<meta name="robots" content="noindex,follow,max-image-preview:large">',
    )
    raw = replace_once(
        raw,
        r'<link rel="canonical" href="[^"]*">',
        f'<link rel="canonical" href="{canonical}">',
    )
    raw = replace_once(
        raw,
        r'<meta property="og:url" content="[^"]*">',
        f'<meta property="og:url" content="{canonical}">',
    )
    SIGNATURE.write_text(raw, encoding="utf-8")


def remove_signature_from_sitemap() -> None:
    if not SITEMAP.exists():
        return
    raw = SITEMAP.read_text(encoding="utf-8")
    signature_url = re.escape(f"{SITE}/cho-thue-lumi-signature/")
    raw = re.sub(
        rf"\s*<url>\s*<loc>{signature_url}</loc>.*?</url>",
        "",
        raw,
        flags=re.S,
    )
    SITEMAP.write_text(raw.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    today = date.today()
    update_hub(today)
    deindex_signature_fallback()
    remove_signature_from_sitemap()
    print(
        "Consolidated rental SERP target: "
        f"{SITE}/cho-thue-lumi-hanoi/ — "
        f"Cho Thuê Căn Hộ Chung Cư Lumi Hanoi Giá Tốt {period(today)}"
    )


if __name__ == "__main__":
    main()
