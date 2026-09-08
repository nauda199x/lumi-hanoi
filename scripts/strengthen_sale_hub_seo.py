#!/usr/bin/env python3
"""Keep broad Lumi Hanoi sale intent consolidated on /mua-ban-lumi-hanoi/.

Run this after the marketplace generators so the primary sale hub keeps a
stable, SERP-oriented title, canonical and visible freshness signal instead of
being overwritten by generated defaults.
"""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "mua-ban-lumi-hanoi" / "index.html"
CANONICAL = "https://lumi-hanoi.com/mua-ban-lumi-hanoi/"
FRESHNESS_START = "<!-- SALE-HUB-FRESHNESS:START -->"
FRESHNESS_END = "<!-- SALE-HUB-FRESHNESS:END -->"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def period(today: date) -> str:
    return f"T{today.month}/{today.year}"


def replace_once(raw: str, pattern: str, replacement: str) -> str:
    if re.search(pattern, raw, flags=re.S):
        return re.sub(pattern, replacement, raw, count=1, flags=re.S)
    return raw


def inventory_count(raw: str) -> int:
    match = re.search(r'data-listing-count[^>]*>\s*(\d+)\s+tin', raw, flags=re.I)
    return int(match.group(1)) if match else 0


def main() -> None:
    raw = HUB.read_text(encoding="utf-8")
    current_period = period(date.today())
    title = f"Mua Bán Căn Hộ Chung Cư Lumi Hanoi Giá Tốt {current_period}"
    description = (
        f"Mua bán căn hộ chung cư Lumi Hanoi giá tốt {current_period}: quỹ căn đang bán và chuyển nhượng "
        "theo phân khu, tòa và loại căn. Xem giá, diện tích, hình ảnh và liên hệ trực tiếp người đăng."
    )

    raw = replace_once(raw, r"<title>.*?</title>", f"<title>{esc(title)}</title>")
    raw = replace_once(
        raw,
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{esc(description)}">',
    )
    raw = replace_once(
        raw,
        r'<meta property="og:title" content="[^"]*">',
        f'<meta property="og:title" content="{esc(title)}">',
    )
    raw = replace_once(
        raw,
        r'<meta property="og:description" content="[^"]*">',
        f'<meta property="og:description" content="{esc(description)}">',
    )
    raw = replace_once(
        raw,
        r'<meta name="twitter:title" content="[^"]*">',
        f'<meta name="twitter:title" content="{esc(title)}">',
    )
    raw = replace_once(
        raw,
        r'<meta name="twitter:description" content="[^"]*">',
        f'<meta name="twitter:description" content="{esc(description)}">',
    )

    canonical_tag = f'<link rel="canonical" href="{CANONICAL}">'
    raw = replace_once(raw, r'<link rel="canonical" href="[^"]*">', canonical_tag)
    if '<meta name="robots"' not in raw:
        raw = raw.replace(
            canonical_tag,
            canonical_tag + '\n<meta name="robots" content="index,follow,max-image-preview:large">',
            1,
        )
    else:
        raw = replace_once(
            raw,
            r'<meta name="robots" content="[^"]*">',
            '<meta name="robots" content="index,follow,max-image-preview:large">',
        )

    # Keep structured data and JS pagination title aligned with the HTML title.
    raw = re.sub(r'"headline":"[^"]*"', f'"headline":"{title}"', raw, count=1)
    raw = re.sub(
        r'data-inventory-home-title="[^"]*"',
        f'data-inventory-home-title="{esc(title)}"',
        raw,
        count=1,
    )

    count = inventory_count(raw)
    freshness = (
        f'{FRESHNESS_START}\n'
        f'<p class="rent-hub-freshness"><strong>Cập nhật {current_period}</strong> · '
        f'{count} tin mua bán đang công khai · dữ liệu được đồng bộ tự động khi tin được duyệt.</p>\n'
        f'{FRESHNESS_END}'
    )
    if FRESHNESS_START in raw and FRESHNESS_END in raw:
        raw = re.sub(
            re.escape(FRESHNESS_START) + r".*?" + re.escape(FRESHNESS_END),
            freshness,
            raw,
            count=1,
            flags=re.S,
        )
    else:
        hero_lead = '<p class="lead">Xem quỹ căn Lumi Hanoi đang bán'
        if hero_lead in raw:
            raw = raw.replace(hero_lead, freshness + "\n" + hero_lead, 1)

    HUB.write_text(raw, encoding="utf-8")


if __name__ == "__main__":
    main()
