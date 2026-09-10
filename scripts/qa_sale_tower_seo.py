#!/usr/bin/env python3
"""Regression checks for controlled sale tower SEO pages."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import generate_sale_tower_seo as sale


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

    rows_by_tower = {}
    for item in sale.TOWERS:
        path = root / item["slug"] / "index.html"
        raw = text(path)
        canonical = f"{sale.SITE}/{item['slug']}/"
        count_match = re.search(r'<span class="marketplace-count">(\d+) tin đăng</span>', raw)
        if not count_match:
            fail(f"missing inventory count: {path}")
        count = int(count_match.group(1))
        rows_by_tower[item["tower"]] = count
        should_index = count >= sale.INDEX_THRESHOLD
        expected_robots = "index,follow,max-image-preview:large" if should_index else "noindex,follow,max-image-preview:large"
        checks = [
            (f'<link rel="canonical" href="{canonical}">' in raw, "canonical"),
            (f'<meta name="robots" content="{expected_robots}">' in raw, "robots"),
            (raw.count("<h1>") == 1, "single H1"),
            (f"<h1>Mua bán tòa {item['tower']} Lumi Hanoi</h1>" in raw, "tower H1"),
            ('"@type":"CollectionPage"' in raw, "CollectionPage schema"),
            ('"@type":"BreadcrumbList"' in raw, "Breadcrumb schema"),
            (f'/{item["phase_slug"]}/' in raw, "phase sale link"),
            (sale.gen.tower_link(item["tower"]) in raw, "tower floor-plan link"),
            ("/gia-can-ho-lumi-hanoi/" in raw, "Market Index link"),
            ("/mua-ban-lumi-hanoi/" in raw, "sale hub link"),
            ("Shop chân đế" not in raw, "shop excluded from apartment tower page"),
            ("?" not in canonical and "#" not in canonical, "clean canonical"),
        ]
        for ok, label in checks:
            if not ok:
                fail(f"{label} check failed: {path}")
        in_sitemap = canonical in sitemap_locs
        if in_sitemap != should_index:
            fail(f"sitemap/index policy mismatch: {path} count={count}")

    phase_groups: dict[str, list[dict]] = {}
    for item in sale.TOWERS:
        phase_groups.setdefault(item["phase_slug"], []).append(item)
    for phase_slug, towers in phase_groups.items():
        raw = text(root / phase_slug / "index.html")
        if sale.CLUSTER_START not in raw or sale.CLUSTER_END not in raw:
            fail(f"sale tower cluster markers missing: {phase_slug}")
        for item in towers:
            if f'/{item["slug"]}/' not in raw:
                fail(f"phase page missing tower link: {item['slug']}")

    indexed = [tower for tower, count in rows_by_tower.items() if count >= sale.INDEX_THRESHOLD]
    noindexed = [tower for tower, count in rows_by_tower.items() if count < sale.INDEX_THRESHOLD]
    print(
        "Sale tower SEO QA: PASS — "
        f"indexable={','.join(indexed) or 'none'}; noindex={','.join(noindexed) or 'none'}"
    )


if __name__ == "__main__":
    main()
