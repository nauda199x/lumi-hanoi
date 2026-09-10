#!/usr/bin/env python3
"""Regression checks for controlled sale phase SEO pages."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import generate_sale_phase_seo as sale


def fail(message: str) -> None:
    raise SystemExit(message)


def text(path: Path) -> str:
    if not path.is_file():
        fail(f"missing generated page: {path}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    sale.main()
    root = sale.gen.ROOT
    sitemap_root = ET.parse(root / "sitemap.xml").getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_locs = {node.text for node in sitemap_root.findall(".//sm:loc", ns) if node.text}

    for item in sale.PHASES:
        path = root / item["slug"] / "index.html"
        raw = text(path)
        canonical = f"{sale.SITE}/{item['slug']}/"
        count_match = re.search(r'<span class="marketplace-count">(\d+) tin đăng</span>', raw)
        if not count_match:
            fail(f"missing inventory count: {path}")
        count = int(count_match.group(1))
        should_index = count >= sale.INDEX_THRESHOLD
        expected_robots = "index,follow,max-image-preview:large" if should_index else "noindex,follow,max-image-preview:large"
        checks = [
            (f'<link rel="canonical" href="{canonical}">' in raw, "canonical"),
            (f'<meta name="robots" content="{expected_robots}">' in raw, "robots"),
            (raw.count("<h1>") == 1, "single H1"),
            ('"@type":"CollectionPage"' in raw, "CollectionPage schema"),
            ('"@type":"BreadcrumbList"' in raw, "Breadcrumb schema"),
            ("/mua-ban-lumi-hanoi/" in raw, "sale hub link"),
            ("/gia-can-ho-lumi-hanoi/" in raw, "Market Index link"),
            (all(sale.gen.tower_link(tower) in raw for tower in item["towers"]), "tower floor-plan links"),
            ("Shop chân đế" not in raw, "shop excluded from apartment phase page"),
        ]
        for ok, label in checks:
            if not ok:
                fail(f"{label} check failed: {path}")
        in_sitemap = canonical in sitemap_locs
        if in_sitemap != should_index:
            fail(f"sitemap/index policy mismatch: {path} count={count}")

    hub = text(root / "mua-ban-lumi-hanoi" / "index.html")
    if sale.CLUSTER_START not in hub or sale.CLUSTER_END not in hub:
        fail("sale phase cluster markers missing from sale hub")
    for item in sale.PHASES:
        if f'/{item["slug"]}/' not in hub:
            fail(f"sale hub missing phase link: {item['slug']}")

    if "#tower=" in "\n".join(str(p) for p in []):
        fail("unexpected")
    print("Sale phase SEO QA: PASS — controlled phase landings, index policy and sitemap are valid")


if __name__ == "__main__":
    main()
