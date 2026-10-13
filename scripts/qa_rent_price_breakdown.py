#!/usr/bin/env python3
"""Check canonical NFA sale/rent price matrices and regression constraints."""
from pathlib import Path
import re
import tempfile

from rent_price_breakdown import (
    RENT_HEAD, area_catalog, furnishing_group, normalized_rental_area,
    rental_groups, render_breakdown, render_sale_breakdown, sync_rent_breakdown,
    million,
)


def listing(slug, unit, area, price, furnishing="", kind="rent"):
    return {
        "slug": slug, "unit_type": unit, "area_sqm": area,
        "price_vnd": price, "furnishing": furnishing,
        "listing_type": kind, "tower": "S2",
        "title": f"Căn {unit} {area} m²",
    }


presets, aliases = area_catalog()
assert presets["1PN"] == [43, 47, 54]
assert presets["2PN"] == [54, 62, 74, 85, 97]
assert presets["3PN"] == [85, 95, 101, 107, 112, 117, 130, 137]
assert presets["4PN"] == [128, 136]
assert presets["Duplex"] == [115, 134, 143, 194, 200, 212]
assert presets["Penthouse"] == [346, 368, 377, 402]
assert normalized_rental_area("1PN", 42.2) == 43
assert normalized_rental_area("1PN", 47) == 47
assert normalized_rental_area("1PN", 54) == 54
assert normalized_rental_area("2PN", 53.8) == 54
assert normalized_rental_area("3PN", 81) == 85
assert normalized_rental_area("3PN", 111.6) == 112
assert normalized_rental_area("1PN", 43.4) is None
assert normalized_rental_area("2PN", 80) is None
assert normalized_rental_area("3PN", 87) is None
assert furnishing_group("Nguyên bản") == "basic"
assert furnishing_group("Nội thất cơ bản") == "basic"
assert furnishing_group("Đồ cơ bản") == "basic"
assert furnishing_group("Full nội thất") == "full"
assert furnishing_group("") == "unknown"
assert million(9_666_666.6) == "9,7"

rows = [
    listing("basic-one43", "1PN", 43, 7_000_000, "Nội thất cơ bản"),
    listing("basic-one422", "1PN", 42.2, 9_000_000, "Nguyên bản"),
    listing("full-one54", "1PN", 54, 12_000_000, "Full nội thất"),
    listing("full-two538", "2PN", 53.8, 11_000_000, "Đầy đủ nội thất"),
    listing("basic-two74", "2PN", 74, 9_000_000, "Đồ cơ bản"),
    listing("unclear-two", "2PN", 54, 20_000_000),
    listing("basic-three81", "3PN", 81, 13_000_000, "Đồ cơ bản"),
    listing("basic-three85", "3PN", 85, 15_000_000, "Đồ cơ bản"),
    listing("outlier-three", "3PN", 87, 30_000_000, "Full nội thất"),
    listing("invalid slug", "2PN", 54, 90_000_000, "Full nội thất"),
    listing("sale-one-43", "1PN", 43, 3_100_000_000, kind="sale"),
    listing("sale-one422", "1PN", 42.2, 3_300_000_000, kind="sale"),
    listing("sale-two80", "2PN", 80, 10_000_000_000, kind="sale"),
    listing("shop-exclude", "Shop chân đế", 54, 100_000_000),
]
groups = rental_groups(rows)
assert len(groups["1PN"][43]["basic"]) == 2
assert groups["2PN"][54]["unknown"]
assert len(groups["3PN"][85]["basic"]) == 2
assert not groups["3PN"].get(87)
rent = render_breakdown(rows)
sale = render_sale_breakdown(rows)
assert rent.count('class="rent-simple-table"') == len(presets)
assert sale.count('class="rent-simple-table"') == len(presets)
for unit, allowed in presets.items():
    rsection = rent.split(f'id="rent-area-{unit.lower()}"', 1)[1].split("</section>", 1)[0]
    ssection = sale.split(f'id="sale-area-{unit.lower()}"', 1)[1].split("</section>", 1)[0]
    for area in allowed:
        assert f"<th scope=\"row\">{area} m²</th>" in rsection
        assert f"<th scope=\"row\">{area} m²</th>" in ssection
assert '<strong class="rent-table-value">8 triệu</strong>' in rent
assert '<strong class="rent-table-value">14 triệu</strong>' in rent
assert "3,2 tỷ" in sale
assert "87 m²" not in rent and "80 m²" not in sale
assert "90 triệu" not in rent and "30 triệu" not in rent
assert "Nguyên bản</th>" not in rent
assert "Full nội thất" in rent and "Đồ cơ bản" in rent
assert "rent-price.js" not in rent and "<details" not in rent
assert not re.search(r"\b\d+\s+tin\b", rent)
assert "Giá/m²/tháng" not in rent
assert 'href="#rent-area-1pn"' in rent

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "index.html"
    path.write_text(
        '<link rel="stylesheet" href="/assets/css/market-price.css?v=old">'
        '<!-- MARKET-PRICE-STATS:START -->'
        '    <div class="market-table-card">' + RENT_HEAD
        + '<div class="market-table-scroll"><table><tbody></tbody></table></div></div>'
        '    <div class="market-table-card"><p>Other stats stay</p></div>'
        '<!-- MARKET-PRICE-STATS:END -->', encoding="utf-8",
    )
    sync_rent_breakdown(rows, path)
    output = path.read_text(encoding="utf-8")
    assert "Bảng giá thuê theo diện tích" in output
    assert "Bảng giá bán theo diện tích" in output
    assert output.count('class="rent-simple-table"') == len(presets) * 2
    assert "Other stats stay" in output
    assert "20261013-area-price-v2" in output
    assert '<h3>Giá rao thuê theo loại căn</h3>' not in output

css = (Path(__file__).resolve().parents[1] / "assets/css/market-price.css").read_text(encoding="utf-8")
assert ".area-price-card" in css
assert ".sale-area-card" in css
assert ".area-price-links" in css
assert "@media(max-width:820px)" in css
print("Canonical NFA pricing QA passed")
