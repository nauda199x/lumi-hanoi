#!/usr/bin/env python3
"""Regression checks for 3D marketplace ↔ floorplan ↔ Market Index linking."""
from __future__ import annotations

import re
from pathlib import Path

import generate_marketplace_seo as gen
import strengthen_marketplace_entity_loop as loop


def fail(message: str) -> None:
    raise SystemExit(message)


def detail_tower(raw: str) -> str:
    match = re.search(r"<span\s+data-detail-tower>([^<]+)</span>", raw, flags=re.I)
    return loop.normalize_tower(match.group(1)) if match else ""


def href_for(raw: str, attr: str) -> str:
    match = re.search(rf'<a\s+{re.escape(attr)}\s+href="([^"]+)"', raw, flags=re.I)
    return match.group(1) if match else ""


def main() -> None:
    # Apply twice to prove the postprocessor is deterministic/idempotent on generated HTML.
    loop.main()
    tracked: dict[Path, str] = {}
    tracked[loop.PRICE_PAGE] = loop.PRICE_PAGE.read_text(encoding="utf-8")
    for tower in loop.TOWERS:
        sale_page = gen.ROOT / f"mua-ban-toa-{tower.lower()}-lumi-hanoi" / "index.html"
        floor_page = loop.floorplan_page(tower)
        if sale_page.is_file():
            tracked[sale_page] = sale_page.read_text(encoding="utf-8")
        if floor_page.is_file():
            tracked[floor_page] = floor_page.read_text(encoding="utf-8")
    for root_name, _ in loop.DETAIL_ROOTS:
        root = gen.ROOT / root_name
        if root.is_dir():
            for marker in root.rglob(gen.MARKER):
                page = marker.parent / "index.html"
                if page.is_file():
                    tracked[page] = page.read_text(encoding="utf-8")
    if loop.DYNAMIC_SHELL.is_file():
        tracked[loop.DYNAMIC_SHELL] = loop.DYNAMIC_SHELL.read_text(encoding="utf-8")

    loop.main()
    for path, before in tracked.items():
        if path.read_text(encoding="utf-8") != before:
            fail(f"3D postprocessor is not idempotent: {path}")

    price = loop.PRICE_PAGE.read_text(encoding="utf-8")
    for tower in loop.TOWERS:
        anchor = f'id="market-index-{tower.lower()}"'
        if price.count(anchor) != 1:
            fail(f"Market Index must expose exactly one row anchor for {tower}")

        sale_page = gen.ROOT / f"mua-ban-toa-{tower.lower()}-lumi-hanoi" / "index.html"
        if sale_page.is_file():
            raw = sale_page.read_text(encoding="utf-8")
            exact = loop.market_index_url(tower)
            if exact not in raw:
                fail(f"{tower}: sale tower landing is missing exact Market Index link")
            if 'href="/gia-can-ho-lumi-hanoi/"' in raw:
                fail(f"{tower}: sale tower landing still contains generic Market Index href")
            if gen.tower_link(tower) not in raw:
                fail(f"{tower}: sale tower landing lost exact floorplan link")

        floor_page = loop.floorplan_page(tower)
        if floor_page.is_file():
            raw = floor_page.read_text(encoding="utf-8")
            match = re.search(re.escape(loop.BRIDGE_START) + r"(.*?)" + re.escape(loop.BRIDGE_END), raw, flags=re.S)
            if not match:
                fail(f"{tower}: floorplan bridge missing")
            block = match.group(1)
            if loop.market_index_url(tower) not in block:
                fail(f"{tower}: floorplan bridge does not deep-link to its Market Index row")

    checked = 0
    for root_name, listing_type in loop.DETAIL_ROOTS:
        root = gen.ROOT / root_name
        if not root.is_dir():
            continue
        for marker in root.rglob(gen.MARKER):
            page = marker.parent / "index.html"
            if not page.is_file():
                continue
            raw = page.read_text(encoding="utf-8")
            tower = detail_tower(raw)
            if not tower:
                continue
            checked += 1
            if raw.count("data-detail-market-index") != 1:
                fail(f"{page}: expected exactly one Market Index detail link")
            if href_for(raw, "data-detail-floorplan") != gen.tower_link(tower):
                fail(f"{page}: wrong exact floorplan link for {tower}")
            if href_for(raw, "data-detail-market-index") != loop.market_index_url(tower):
                fail(f"{page}: wrong Market Index deep-link for {tower}")
            if loop.SCRIPT_TAG not in raw:
                fail(f"{page}: entity-loop hydration script missing")
            if listing_type == "sale" and href_for(raw, "data-detail-same-tower") != loop.sale_tower_url(tower):
                fail(f"{page}: sale detail does not link to controlled {tower} sale landing")

    if checked == 0:
        fail("No generated listing details with valid tower were checked")

    shell = loop.DYNAMIC_SHELL.read_text(encoding="utf-8")
    if shell.count("data-detail-market-index") != 1 or loop.SCRIPT_TAG not in shell:
        fail("Dynamic listing shell is missing 3D Market Index link/script")

    js = (gen.ROOT / "assets/js/marketplace-entity-loop.js").read_text(encoding="utf-8")
    for required in ("marketIndexUrl", "saleTowerUrl", "MutationObserver", "data-detail-market-index", "data-detail-same-tower"):
        if required not in js:
            fail(f"Entity-loop client helper missing {required}")

    print(f"Marketplace entity loop QA: PASS — {checked} generated detail pages linked to exact tower entities")


if __name__ == "__main__":
    main()
