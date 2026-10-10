#!/usr/bin/env python3
"""Generate a compact, non-interactive rental price table from approved listings.

Every displayed price is computed from the explicit structured unit type, area,
monthly asking price, and furnishing. No inferred furniture or fabricated prices.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from statistics import mean

import generate_marketplace_seo as gen


FURNISHINGS = (
    ("original", "Nguyên bản"),
    ("basic", "Đồ cơ bản"),
    ("full", "Full nội thất"),
)
RENT_HEAD = (
    '<div class="market-table-head"><div><p class="eyebrow">Cho thuê</p>'
    '<h3>Giá rao thuê theo loại căn</h3></div>'
    '<a href="/cho-thue-lumi-hanoi/">Xem quỹ thuê →</a></div>'
)


def furnishing_group(value) -> str:
    """Accept only the furnishing field, not claims made in titles/descriptions."""
    text = unicodedata.normalize("NFD", gen.clean(value).lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"\s+", " ", text.replace("đ", "d")).strip()
    if "nguyen ban" in text or "ban giao" in text:
        return "original"
    if "co ban" in text:
        return "basic"
    if "full" in text or "day du" in text:
        return "full"
    return "unknown"


def area_bucket(value) -> int:
    """53.8 and 54 m² belong in the same ~54 m² comparison group."""
    area = gen.numeric(value)
    if not area:
        raise ValueError("Positive area required")
    return math.floor(area + 0.5)


def rental_groups(listings: list[dict]) -> dict[str, dict[int, dict[str, list[dict]]]]:
    groups = {unit: defaultdict(lambda: defaultdict(list))
              for unit in gen.APARTMENT_UNIT_TYPES}
    for row in gen.market_rows(listings, "rent"):
        # Keep counts consistent with records generated on the public website.
        if not re.fullmatch(r"[a-z0-9-]{8,120}", gen.clean(row.get("slug"))):
            continue
        groups[gen.clean(row["unit_type"])][area_bucket(row["area_sqm"])][
            furnishing_group(row.get("furnishing"))
        ].append(row)
    return groups


def million(value: float, places: int = 1) -> str:
    """Compact Vietnamese display: 9.67 -> 9,7 and 8.00 -> 8."""
    return f"{value / 1_000_000:.{places}f}".rstrip("0").rstrip(".").replace(".", ",")


def render_cell(rows: list[dict]) -> str:
    """One compact average price per furnishing/area; no ranges or sample counts."""
    if not rows:
        return '<td class="rent-price-empty" aria-label="Chưa có dữ liệu">—</td>'
    average = million(mean(gen.numeric(r["price_vnd"]) for r in rows))
    return f'<td><strong class="rent-table-value">{gen.esc(average)} triệu</strong></td>'

def render_unit(unit: str, sizes: dict[int, dict[str, list[dict]]]) -> str:
    display_rows = []
    for size in sorted(sizes):
        groups = sizes[size]
        if not any(groups.get(key) for key, _ in FURNISHINGS):
            continue
        classified_rows = [
            row for key, _ in FURNISHINGS for row in groups.get(key, [])
        ]
        # Avoid presenting a 53.8m² listing as exactly 54m².
        approximate = any(abs(float(row["area_sqm"]) - size) > 0.049
                          for row in classified_rows)
        area = ("≈" if approximate else "") + f"{size} m²"
        cells = "".join(render_cell(groups.get(key, []))
                        for key, _ in FURNISHINGS)
        display_rows.append(
            f'<tr><th scope="row">{gen.esc(area)}</th>{cells}</tr>'
        )

    if not display_rows:
        return ""
    table = (
        '<div class="rent-simple-table-wrap"><table class="rent-simple-table">'
        f'<caption class="rent-visually-hidden">Giá thuê trung bình căn {gen.esc(unit)}'
        ' theo diện tích và nội thất; đơn vị triệu đồng mỗi tháng.</caption>'
        '<colgroup><col class="rent-col-area"><col span="3" class="rent-col-price"></colgroup>'
        '<thead><tr><th scope="col">Diện tích</th>'
        + "".join(f'<th scope="col">{gen.esc(label)}</th>'
                  for _, label in FURNISHINGS)
        + '</tr></thead><tbody>' + "".join(display_rows)
        + '</tbody></table></div>'
    )
    return (
        f'<section class="rent-simple-unit" aria-label="Giá thuê trung bình {gen.esc(unit)}">'
        f'<div class="rent-simple-unit-title"><h4>{gen.esc(unit)}</h4></div>'
        f'{table}</section>'
    )

def render_breakdown(listings: list[dict]) -> str:
    groups = rental_groups(listings)
    sections = [
        section for unit in gen.APARTMENT_UNIT_TYPES
        if (section := render_unit(unit, groups[unit]))
    ]
    unavailable = [
        unit for unit in gen.APARTMENT_UNIT_TYPES
        if not any(groups[unit][size].get(key)
                   for size in groups[unit] for key, _ in FURNISHINGS)
    ]
    empty_note = (
        '<p class="rent-simple-empty">Chưa có dữ liệu giá cho: '
        + gen.esc(", ".join(unavailable)) + '.</p>'
        if unavailable else ""
    )
    tables = "".join(sections) if sections else (
        '<p class="rent-simple-empty">Chưa đủ dữ liệu để lập bảng giá thuê.</p>'
    )
    return (
        '<div class="market-table-card rent-market-card" id="bang-gia-thue-chi-tiet">'
        '<div class="rent-simple-head"><div><p class="eyebrow">Bảng giá thị trường</p>'
        '<h3>Bảng giá thuê theo diện tích và nội thất</h3></div>'
        '<p>Giá thuê trung bình <span>Đơn vị: triệu đồng/tháng</span></p></div>'
        f'<div class="rent-simple-sections">{tables}</div>'
        f'{empty_note}'
        '<p class="rent-price-note">Giá rao thuê trung bình được tự động tính từ '
        'các tin đã duyệt, có đủ giá, diện tích và tình trạng nội thất; không tính '
        'shop chân đế. Dấu ≈ chỉ diện tích được làm tròn đến m² gần nhất. '
        'Căn chưa rõ nội thất không được tự gán vào nhóm khác. '
        'Đây là giá chào tham khảo, không phải giá chốt giao dịch.</p>'
        '</div>'
    )

def sync_rent_breakdown(listings: list[dict], path: Path | None = None) -> None:
    path = path or gen.PRICE_PAGE
    raw = path.read_text(encoding="utf-8")
    anchor = raw.find(RENT_HEAD)
    if anchor < 0:
        raise RuntimeError("Rental price card not found in freshly generated price page")
    start = raw.rfind('    <div class="market-table-card">', 0, anchor)
    end = raw.find('    <div class="market-table-card">', anchor + len(RENT_HEAD))
    if start < 0 or end < 0:
        raise RuntimeError("Unable to isolate rental price card")
    updated = raw[:start] + "    " + render_breakdown(listings) + "\n\n" + raw[end:]
    updated = re.sub(
        r"/assets/css/market-price\.css\?v=[^\"']+",
        "/assets/css/market-price.css?v=20261010-rent-average3",
        updated,
        count=1,
    )
    path.write_text(updated, encoding="utf-8")
    count = sum(
        len(rows) for unit in rental_groups(listings).values()
        for groups in unit.values() for rows in groups.values()
    )
    print(f"Rental price simple tables: {count} approved listings classified")
