#!/usr/bin/env python3
"""Regression checks: average-only rental tables without visible sample statistics."""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

from rent_price_breakdown import (
    RENT_HEAD, furnishing_group, rental_groups, render_breakdown,
    sync_rent_breakdown, normalized_rental_area, million,
)


def listing(slug, unit, area, price, furnishing, kind="rent", title=""):
    return {
        "slug": slug, "unit_type": unit, "area_sqm": area,
        "price_vnd": price, "furnishing": furnishing,
        "listing_type": kind, "tower": "S2",
        "title": title or f"Căn {unit} {area} m²",
    }


rows = [
    listing("basic-one-1234", "1PN", 43, 7_000_000, "Nội thất cơ bản"),
    listing("basic-one-42x", "1PN", 42, 9_000_000, "Nội thất cơ bản"),
    listing("original-one42", "1PN", 42, 8_000_000, "Bàn giao nguyên bản"),
    listing("original-one43", "1PN", 43, 10_000_000, "Bàn giao nguyên bản"),
    listing("invalid-one54x", "1PN", 54, 40_000_000, "Đầy đủ nội thất"),
    listing("full-two-12345", "2PN", 53.8, 11_000_000, "Đầy đủ nội thất"),
    listing("basic-two-1234", "2PN", 54, 8_500_000, "Nội thất cơ bản"),
    listing("sixtytwo-1234", "2PN", 62, 12_000_000, "Full nội thất"),
    listing("seventyfour12", "2PN", 74, 9_000_000, "Bàn giao nguyên bản"),
    listing("unclear-two-1234", "2PN", 54, 15_000_000, ""),
    listing("basic-three123", "3PN", 81, 13_000_000, "Nội thất cơ bản"),
    listing("unknown-three12", "3PN", 87, 13_000_000, "", title="3PN full đồ"),
    listing("invalid slug", "2PN", 80, 19_000_000, "Đầy đủ nội thất"),
    listing("sale-exclude12", "2PN", 54, 4_000_000_000, "Đầy đủ nội thất", kind="sale"),
    listing("shop-exclude12", "Shop chân đế", 54, 40_000_000, "Full nội thất"),
]
groups = rental_groups(rows)
assert list(groups["1PN"].keys()) == [43], "42m² and 43m² must be one 1PN size"
assert len(groups["1PN"][43]["basic"]) == 4
assert "original" not in groups["1PN"][43]
assert not groups["1PN"].get(54), "Out-of-layout 1PN 54m² must not affect the price"
assert normalized_rental_area("1PN", 42) == 43
assert normalized_rental_area("1PN", 43.4) == 43
assert normalized_rental_area("1PN", 54) is None
assert normalized_rental_area("2PN", 54) == 54
assert sum(len(rs) for by_area in groups["2PN"].values() for rs in by_area.values()) == 5
assert len(groups["2PN"][54]["full"]) == 1
assert len(groups["2PN"][54]["basic"]) == 1
assert len(groups["2PN"][54]["unknown"]) == 1
assert len(groups["2PN"][62]["full"]) == 1
assert len(groups["2PN"][74]["basic"]) == 1
assert len(groups["3PN"][87]["unknown"]) == 1
assert furnishing_group("Đầy đủ nội thất") == "full"
assert furnishing_group("Nội thất cơ bản") == "basic"
assert furnishing_group("Bàn giao nguyên bản") == "basic"
assert furnishing_group("Đồ cơ bản") == "basic"
assert furnishing_group("Full nội thất") == "full"
assert furnishing_group("") == "unknown"
assert million(9_666_666.666) == "9,7"
assert million(8_000_000) == "8"

html = render_breakdown(rows)
# One canonical 1PN area with means recalculated across 42m² + 43m² source ads.
one_pn = html.split('aria-label="Giá thuê trung bình 1PN">', 1)[1].split("</section>", 1)[0]
assert one_pn.count('<tr><th scope="row">43 m²</th>') == 1
assert '<th scope="row">42 m²</th>' not in one_pn
assert '<th scope="row">54 m²</th>' not in one_pn
assert '<strong class="rent-table-value">8,5 triệu</strong>' in one_pn  # (7+9+8+10)/4
assert "40 triệu" not in html
assert "tin khai 42–43m²" in html
assert "≈54 m²" in html
assert "62 m²" in html and "74 m²" in html and "81 m²" in html
assert 'class="rent-simple-table"' in html
assert html.count('<th scope="col">') == 3 * 3
assert '<strong class="rent-table-value">8,5 triệu</strong>' in html
assert '<strong class="rent-table-value">11 triệu</strong>' in html
assert '<strong class="rent-table-value">8 triệu</strong>' in one_pn
assert "15 triệu" not in html  # Unknown furniture must not enter averages
assert "87 m²" not in html  # Unknown-only area must not become a priced row
assert "sale-exclude12" not in html and "shop-exclude12" not in html
assert "invalid slug" not in html
assert "<details" not in html and "<a " not in html
assert "<small" not in html and "tin đủ" not in html
assert "Xem tin gốc" not in html and "Xem quỹ thuê" not in html
assert "rent-price.js" not in html
assert not re.search(r"\b\d+\s+tin\b", html)
assert "Giá/m²/tháng" not in html
assert '<colgroup><col class="rent-col-area">' in html

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
    assert "Bảng giá thuê theo diện tích" in output
    assert "Other stats stay" in output
    assert "v=20261010-two-furnishings" in output
    assert output.count('class="rent-simple-table"') == 3
    assert output.count('<th scope="col">') == 9
    assert ">Nguyên bản</th>" not in output
    assert ">Đồ cơ bản</th>" in output
    assert ">Full nội thất</th>" in output
    assert "Xem tin gốc" not in output
    assert "rent-price.js" not in output

css = (Path(__file__).resolve().parents[1] / "assets/css/market-price.css").read_text(encoding="utf-8")
assert ".rent-col-area" in css and ".rent-col-price" in css
assert "table-layout:fixed" in css
assert ".rent-market-card" in css and "overflow:hidden" in css
print("Rental average-only price tables QA passed")
