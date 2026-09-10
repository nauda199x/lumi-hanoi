#!/usr/bin/env python3
"""Close the internal-link loop between marketplace, tower floorplans and Market Index.

This runs after the normal marketplace/tower/floorplan generators. It deliberately
post-processes their HTML instead of changing the core listing generator so the
existing publish/index pipeline stays isolated and easy to roll back.
"""
from __future__ import annotations

import re
from pathlib import Path

import generate_marketplace_seo as gen

ROOT = gen.ROOT
TOWERS = ("S1", "S2", "S3", "S5", "S6", "P1", "P2", "E1", "E2")
KNOWN_TOWER = re.compile(r"^(?:S[12356]|P[12]|E[12])$", re.I)
DETAIL_ROOTS = (("mua-ban-lumi-hanoi", "sale"), ("cho-thue-lumi-hanoi", "rent"))
DYNAMIC_SHELL = ROOT / "tin-dang-lumi-hanoi" / "index.html"
PRICE_PAGE = ROOT / "gia-can-ho-lumi-hanoi" / "index.html"
BRIDGE_START = "<!-- TOWER-MARKETPLACE-BRIDGE:START -->"
BRIDGE_END = "<!-- TOWER-MARKETPLACE-BRIDGE:END -->"
SCRIPT_TAG = '<script src="/assets/js/marketplace-entity-loop.js?v=20260910-3d" defer></script>'


def normalize_tower(value: str) -> str:
    tower = str(value or "").strip().upper()
    return tower if KNOWN_TOWER.fullmatch(tower) else ""


def market_index_url(tower: str) -> str:
    tower = normalize_tower(tower)
    return f"/gia-can-ho-lumi-hanoi/#market-index-{tower.lower()}" if tower else "/gia-can-ho-lumi-hanoi/"


def sale_tower_url(tower: str) -> str:
    tower = normalize_tower(tower)
    return f"/mua-ban-toa-{tower.lower()}-lumi-hanoi/" if tower else "/mua-ban-lumi-hanoi/"


def detail_tower(raw: str) -> str:
    match = re.search(r"<span\s+data-detail-tower>([^<]+)</span>", raw, flags=re.I)
    return normalize_tower(match.group(1)) if match else ""


def market_link_markup(tower: str) -> str:
    label = tower or "Chưa cập nhật"
    return (
        f'<a data-detail-market-index href="{market_index_url(tower)}">'
        f'<span>Market Index tòa <b data-detail-tower>{label}</b></span>'
        '<span aria-hidden="true">→</span></a>'
    )


def upsert_detail_market_link(raw: str, tower: str, listing_type: str) -> str:
    link = market_link_markup(tower)
    existing = re.compile(r'<a\s+data-detail-market-index\b[^>]*>.*?</a>', flags=re.I | re.S)
    if existing.search(raw):
        raw = existing.sub(link, raw, count=1)
    else:
        floorplan = re.compile(r'(<a\s+data-detail-floorplan\b[^>]*>.*?</a>)', flags=re.I | re.S)
        if not floorplan.search(raw):
            raise RuntimeError("Could not locate detail floorplan link")
        raw = floorplan.sub(lambda match: match.group(1) + link, raw, count=1)

    if listing_type == "sale" and tower:
        raw = re.sub(
            r'(<a\s+data-detail-same-tower\s+href=")[^"]+("[^>]*>)',
            lambda match: match.group(1) + sale_tower_url(tower) + match.group(2),
            raw,
            count=1,
            flags=re.I,
        )

    if SCRIPT_TAG not in raw:
        if "</body>" not in raw:
            raise RuntimeError("Could not locate </body> in listing detail page")
        raw = raw.replace("</body>", f"  {SCRIPT_TAG}\n</body>", 1)
    return raw


def update_detail_pages() -> tuple[int, int]:
    updated = 0
    exact = 0
    for root_name, listing_type in DETAIL_ROOTS:
        root = ROOT / root_name
        if not root.is_dir():
            continue
        for marker in root.rglob(gen.MARKER):
            page = marker.parent / "index.html"
            if not page.is_file():
                continue
            raw = page.read_text(encoding="utf-8")
            tower = detail_tower(raw)
            new = upsert_detail_market_link(raw, tower, listing_type)
            if tower:
                exact += 1
            if new != raw:
                page.write_text(new, encoding="utf-8")
                updated += 1

    if DYNAMIC_SHELL.is_file():
        raw = DYNAMIC_SHELL.read_text(encoding="utf-8")
        new = upsert_detail_market_link(raw, "", "dynamic")
        if new != raw:
            DYNAMIC_SHELL.write_text(new, encoding="utf-8")
            updated += 1
    return updated, exact


def update_market_index_rows() -> int:
    if not PRICE_PAGE.is_file():
        return 0
    raw = PRICE_PAGE.read_text(encoding="utf-8")
    changed = 0
    for tower in TOWERS:
        floor = gen.tower_link(tower)
        old = f'<tr><th><a href="{floor}">Tòa {tower}</a></th>'
        new = f'<tr id="market-index-{tower.lower()}"><th><a href="{floor}">Tòa {tower}</a></th>'
        if old in raw:
            raw = raw.replace(old, new, 1)
            changed += 1
        elif new not in raw:
            raise RuntimeError(f"Could not locate Market Index row for {tower}")
    PRICE_PAGE.write_text(raw, encoding="utf-8")
    return changed


def update_sale_tower_landings() -> int:
    updated = 0
    for tower in TOWERS:
        page = ROOT / f"mua-ban-toa-{tower.lower()}-lumi-hanoi" / "index.html"
        if not page.is_file():
            continue
        raw = page.read_text(encoding="utf-8")
        exact = market_index_url(tower)
        new = raw.replace('href="/gia-can-ho-lumi-hanoi/"', f'href="{exact}"')
        if new != raw:
            page.write_text(new, encoding="utf-8")
            updated += 1
    return updated


def floorplan_page(tower: str) -> Path:
    t = tower.lower()
    phase = "lumi-signature" if t.startswith("s") else "lumi-prestige" if t.startswith("p") else "lumi-elite"
    return ROOT / "mat-bang-lumi-hanoi" / phase / t / "index.html"


def update_floorplan_bridges() -> int:
    updated = 0
    for tower in TOWERS:
        page = floorplan_page(tower)
        if not page.is_file():
            continue
        raw = page.read_text(encoding="utf-8")
        match = re.search(re.escape(BRIDGE_START) + r"(.*?)" + re.escape(BRIDGE_END), raw, flags=re.S)
        if not match:
            continue
        block = match.group(1)
        new_block = block.replace('href="/gia-can-ho-lumi-hanoi/"', f'href="{market_index_url(tower)}"')
        if new_block != block:
            raw = raw[: match.start(1)] + new_block + raw[match.end(1) :]
            page.write_text(raw, encoding="utf-8")
            updated += 1
    return updated


def main() -> None:
    row_changes = update_market_index_rows()
    tower_pages = update_sale_tower_landings()
    floorplans = update_floorplan_bridges()
    detail_pages, exact_details = update_detail_pages()
    print(
        "Marketplace entity loop: "
        f"Market Index rows={row_changes}, sale tower pages={tower_pages}, "
        f"floorplan bridges={floorplans}, detail pages updated={detail_pages}, "
        f"detail pages with exact tower={exact_details}"
    )


if __name__ == "__main__":
    main()
