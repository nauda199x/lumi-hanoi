#!/usr/bin/env python3
"""Regression checks for the controlled 1PN/2PN/3PN sale SEO cluster."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import generate_sale_unit_seo as sale


def fail(message: str) -> None:
    raise SystemExit(message)


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing generated page: {path}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    if tuple(item["unit"] for item in sale.UNITS) != ("1PN", "2PN", "3PN"):
        fail("sale unit cluster must stay finite: 1PN, 2PN, 3PN only")

    sale.main()
    root = sale.gen.ROOT
    sitemap_root = ET.parse(root / "sitemap.xml").getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_locs = {node.text for node in sitemap_root.findall(".//sm:loc", ns) if node.text}
    counts: dict[str, int] = {}

    for item in sale.UNITS:
        unit = item["unit"]
        path = root / item["slug"] / "index.html"
        raw = read(path)
        canonical = f"{sale.SITE}/{item['slug']}/"
        count_match = re.search(r'<span class="marketplace-count">(\d+) tin đăng</span>', raw)
        if not count_match:
            fail(f"missing inventory count: {path}")
        count = int(count_match.group(1))
        counts[unit] = count
        should_index = count >= sale.INDEX_THRESHOLD
        robots = "index,follow,max-image-preview:large" if should_index else "noindex,follow,max-image-preview:large"
        checks = [
            (f'<link rel="canonical" href="{canonical}">' in raw, "canonical"),
            (f'<meta name="robots" content="{robots}">' in raw, "robots"),
            (raw.count("<h1>") == 1, "single H1"),
            (f"<h1>Mua bán căn hộ {unit} Lumi Hanoi</h1>" in raw, "unit H1"),
            ('"@type":"CollectionPage"' in raw, "CollectionPage schema"),
            ('"@type":"BreadcrumbList"' in raw, "Breadcrumb schema"),
            (item["info_url"] in raw, "layout/info link"),
            ("/gia-can-ho-lumi-hanoi/" in raw, "Market Index link"),
            ("/mua-ban-lumi-hanoi/" in raw, "sale hub link"),
            ("Shop chân đế" not in raw, "shop excluded"),
            ("?" not in canonical and "#" not in canonical, "clean canonical"),
        ]
        if count:
            checks.append(('"@type":"ItemList"' in raw, "ItemList schema"))
        for ok, label in checks:
            if not ok:
                fail(f"{label} check failed: {path}")
        if (canonical in sitemap_locs) != should_index:
            fail(f"sitemap/index policy mismatch: {path} count={count}")

        rows = sale.unit_rows(sale.gen.fetch_approved(), unit)
        tower_counts = sale.tower_counts(rows)
        for tower, tower_count in tower_counts.items():
            if tower_count < 1:
                continue
            if sale.sale_tower_url(tower) not in raw:
                fail(f"missing sale tower link {tower} on {unit}")
            if sale.gen.tower_link(tower) not in raw:
                fail(f"missing floorplan link {tower} on {unit}")
            if f"/gia-can-ho-lumi-hanoi/#market-index-{tower.lower()}" not in raw:
                fail(f"missing tower Market Index link {tower} on {unit}")

    hub = read(root / "mua-ban-lumi-hanoi" / "index.html")
    if sale.CLUSTER_START not in hub or sale.CLUSTER_END not in hub:
        fail("sale unit cluster markers missing from sale hub")
    for item in sale.UNITS:
        if f'/{item["slug"]}/' not in hub:
            fail(f"sale hub missing unit landing: {item['slug']}")

    unit_urls = {item["unit"]: f"/{item['slug']}/" for item in sale.UNITS}
    detail_root = root / "mua-ban-lumi-hanoi"
    checked_details = 0
    for marker in detail_root.rglob(sale.gen.MARKER):
        page = marker.parent / "index.html"
        if not page.is_file():
            continue
        raw = page.read_text(encoding="utf-8")
        unit = sale.detail_unit(raw)
        target = unit_urls.get(unit)
        if not target:
            continue
        if not re.search(rf'<a\s+data-detail-same-unit\s+href="{re.escape(target)}"', raw, flags=re.I):
            fail(f"detail page missing clean same-unit landing: {page}")
        checked_details += 1

    print(
        "Sale unit SEO QA: PASS — "
        + ", ".join(f"{unit}={count}" for unit, count in counts.items())
        + f"; threshold={sale.INDEX_THRESHOLD}; linked sale details={checked_details}"
    )


if __name__ == "__main__":
    main()
