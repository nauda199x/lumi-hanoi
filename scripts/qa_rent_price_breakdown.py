#!/usr/bin/env python3
"""Fixture-based QA: no fabricated price/furnishing, no shop, linkable source ads."""
from __future__ import annotations

import tempfile
from pathlib import Path

from rent_price_breakdown import (
    RENT_HEAD, furnishing_group, rental_groups, render_breakdown, sync_rent_breakdown,
)


def listing(slug, unit, area, price, furnishing, kind="rent", tower="S2", title=""):
    return {
        "slug": slug,
        "unit_type": unit,
        "area_sqm": area,
        "price_vnd": price,
        "furnishing": furnishing,
        "listing_type": kind,
        "tower": tower,
        "title": title or f"Căn {unit} {area} m²",
    }


rows = [
    listing("basic-one-1234", "1PN", 43, 7_000_000, "Nội thất cơ bản"),
    listing("full-two-12345", "2PN", 53.8, 11_000_000, "Đầy đủ nội thất"),
    listing("basic-two-1234", "2PN", 54, 8_500_000, "Nội thất cơ bản"),
    listing("sixtytwo-1234", "2PN", 62, 12_000_000, "Full nội thất"),
    listing("seventyfour12", "2PN", 74, 9_000_000, "Bàn giao nguyên bản"),
    listing("unknown-three12", "3PN", 87, 13_000_000, "", title="3PN full đồ"),
    listing("invalid-slug", "2PN", 80, 19_000_000, "Đầy đủ nội thất"),
    listing("sale-exclude12", "2PN", 54, 4_000_000_000, "Đầy đủ nội thất", kind="sale"),
    listing("shop-exclude12", "Shop chân đế", 54, 40_000_000, "Full nội thất"),
]
# Exercise a genuinely invalid slug (spaces), not merely an unusual suffix.
rows[6]["slug"] = "invalid slug"
groups = rental_groups(rows)
assert sum(len(rs) for by_area in groups["2PN"].values() for rs in by_area.values()) == 4
assert len(groups["2PN"][54]["full"]) == 1
assert len(groups["2PN"][54]["basic"]) == 1
assert len(groups["2PN"][62]["full"]) == 1
assert len(groups["2PN"][74]["original"]) == 1
assert len(groups["3PN"][87]["unknown"]) == 1  # headline must not imply furnishing
assert furnishing_group("Đầy đủ nội thất") == "full"
assert furnishing_group("Nội thất cơ bản") == "basic"
assert furnishing_group("Bàn giao nguyên bản") == "original"

html = render_breakdown(rows)
assert "≈54 m²" in html
assert "62 m²" in html and "74 m²" in html and "87 m²" in html
assert "8,5 triệu/tháng" in html and "11 triệu/tháng" in html
assert "sale-exclude12" not in html and "shop-exclude12" not in html
assert "invalid slug" not in html
assert "rent-price-matrix" in html and "Xem 1 tin gốc" in html
assert 'id="gia-thue-2pn" class="rent-price-category" open' in html
assert "/cho-thue-lumi-hanoi/basic-two-1234/" in html
assert "Giá/m²/tháng" not in html

with tempfile.TemporaryDirectory() as tmp:
    file = Path(tmp) / "index.html"
    file.write_text(
        '<link rel="stylesheet" href="/assets/css/market-price.css?v=20260830-price1">'
        '<!-- MARKET-PRICE-STATS:START -->'
        '    <div class="market-table-card">' + RENT_HEAD
        + '<div class="market-table-scroll"><table><tbody></tbody></table></div></div>'
        '    <div class="market-table-card"><p>Other stats stay</p></div>'
        '<!-- MARKET-PRICE-STATS:END -->',
        encoding="utf-8",
    )
    sync_rent_breakdown(rows, file)
    output = file.read_text(encoding="utf-8")
    assert "Giá thuê theo diện tích" in output
    assert "Other stats stay" in output
    assert "v=20261010-rent-detail1" in output
    assert "rent-price.js" in output
    assert output.count('id="gia-thue-2pn"') == 1

print("Rental price breakdown QA passed")
