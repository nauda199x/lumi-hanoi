#!/usr/bin/env python3
"""Render honest rental price comparisons by bedroom, approximate area and furnishing.

Uses the same approved public listings captured by the marketplace SEO generator.
Never estimates prices for empty groups or infers furnishing from free-text titles.
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
    ("unknown", "Chưa rõ nội thất"),
)
RENT_HEAD = (
    '<div class="market-table-head"><div><p class="eyebrow">Cho thuê</p>'
    '<h3>Giá rao thuê theo loại căn</h3></div>'
    '<a href="/cho-thue-lumi-hanoi/">Xem quỹ thuê →</a></div>'
)


def furnishing_group(value) -> str:
    """Map only explicit structured-field values, never descriptions/headlines."""
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
    """Group neighbouring declared dimensions at the nearest whole square metre."""
    area = gen.numeric(value)
    if not area:
        raise ValueError("A listing without positive area cannot be bucketed")
    return math.floor(area + 0.5)


def rental_groups(listings: list[dict]) -> dict[str, dict[int, dict[str, list[dict]]]]:
    grouped = {
        unit: defaultdict(lambda: defaultdict(list))
        for unit in gen.APARTMENT_UNIT_TYPES
    }
    for listing in gen.market_rows(listings, "rent"):
        unit = gen.clean(listing.get("unit_type"))
        grouped[unit][area_bucket(listing["area_sqm"])][
            furnishing_group(listing.get("furnishing"))
        ].append(listing)
    return grouped


def millions(value: float) -> str:
    return (f"{value / 1_000_000:.2f}".rstrip("0").rstrip(".")
            .replace(".", ","))


def price_range(rows: list[dict]) -> str:
    if not rows:
        return "—"
    amounts = [gen.numeric(item.get("price_vnd")) for item in rows]
    low, high = min(amounts), max(amounts)
    if low == high:
        return f"{millions(low)} triệu/tháng"
    return f"{millions(low)}–{millions(high)} triệu/tháng"


def price_average(rows: list[dict]) -> str:
    return f"TB {millions(mean(gen.numeric(r['price_vnd']) for r in rows))} triệu" if rows else ""


def source_links(rows: list[dict]) -> str:
    links = []
    for row in sorted(rows, key=lambda x: (gen.numeric(x.get("price_vnd")), gen.clean(x.get("tower")))):
        slug = gen.clean(row.get("slug"))
        if not re.fullmatch(r"[a-z0-9-]{8,120}", slug):
            continue
        url = gen.listing_url(row)
        tower = gen.clean(row.get("tower")) or "Chưa rõ tòa"
        area = gen.format_area(row.get("area_sqm"))
        title = gen.clean(row.get("title")) or "Xem thông tin căn hộ"
        label = f"Tòa {tower} · {area} m² · {gen.format_price(row)}"
        links.append(
            f'<a href="{gen.esc(url)}" title="{gen.esc(title)}">'
            f'{gen.esc(label)} <span aria-hidden="true">↗</span></a>'
        )
    return "".join(links)


def render_cell(rows: list[dict], label: str) -> str:
    if not rows:
        return f'<td class="rent-price-cell rent-price-empty" data-label="{gen.esc(label)}">—</td>'
    count = len(rows)
    sources = source_links(rows)
    details = (
        f'<details class="rent-price-sources"><summary>Xem {count} tin gốc</summary>'
        f'<div class="rent-price-source-links">{sources}</div></details>'
        if sources else ""
    )
    return (
        f'<td class="rent-price-cell" data-label="{gen.esc(label)}">'
        f'<strong class="rent-price-amount">{gen.esc(price_range(rows))}</strong>'
        f'<span class="rent-price-meta">{gen.esc(price_average(rows))} · {count} tin</span>'
        f'{details}</td>'
    )


def render_unit(unit: str, sizes: dict[int, dict[str, list[dict]]], default_open: bool) -> str:
    all_rows = [r for groups in sizes.values() for rows in groups.values() for r in rows]
    count = len(all_rows)
    id_value = f"gia-thue-{unit.lower()}"
    status = f"{count} tin · {price_range(all_rows)}" if count else "Chưa có tin"
    rows = []
    for size in sorted(sizes):
        groups = sizes[size]
        size_rows = [r for records in groups.values() for r in records]
        # A rounded display group is explicitly marked approximate if any listing
        # actually declares a different area, e.g. 53.8 m² shown under ≈54 m².
        approximate = any(abs(float(r["area_sqm"]) - size) > 0.049 for r in size_rows)
        area_label = ("≈" if approximate else "") + str(size) + " m²"
        cells = "".join(render_cell(groups.get(key, []), label) for key, label in FURNISHINGS)
        rows.append(
            f'<tr><th scope="row"><strong>{gen.esc(area_label)}</strong>'
            f'<small>{len(size_rows)} tin</small></th>{cells}</tr>'
        )
    if rows:
        table = (
            f'<div class="rent-price-matrix-wrap"><table class="rent-price-matrix">'
            f'<caption class="sr-only">Giá thuê {gen.esc(unit)} theo diện tích và nội thất</caption>'
            '<thead><tr><th scope="col">Diện tích</th>'
            + "".join(f'<th scope="col">{gen.esc(label)}</th>' for _, label in FURNISHINGS)
            + '</tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>"
        )
    else:
        table = (
            '<p class="rent-price-no-data">Chưa có tin thuê đã duyệt đủ giá và diện tích '
            'cho loại căn này. Website sẽ tự bổ sung khi có tin hợp lệ.</p>'
        )
    return (
        f'<details id="{gen.esc(id_value)}" class="rent-price-category"'
        + (" open" if default_open else "")
        + f'><summary><span class="rent-price-category-name">{gen.esc(unit)}</span>'
        f'<span class="rent-price-category-info">{gen.esc(status)}</span>'
        '<span class="rent-price-category-chevron" aria-hidden="true">⌄</span></summary>'
        + table + "</details>"
    )


def render_breakdown(listings: list[dict]) -> str:
    groups = rental_groups(listings)
    available = [u for u in gen.APARTMENT_UNIT_TYPES if groups[u]]
    default_unit = "2PN" if groups["2PN"] else (available[0] if available else "")
    chips = "".join(
        f'<a href="#gia-thue-{gen.esc(u.lower())}">{gen.esc(u)}'
        f'<span>{sum(len(rows) for g in groups[u].values() for rows in g.values())} tin</span></a>'
        for u in gen.APARTMENT_UNIT_TYPES
    )
    sections = "".join(
        render_unit(unit, groups[unit], default_open=unit == default_unit)
        for unit in gen.APARTMENT_UNIT_TYPES
    )
    return (
        '<div class="market-table-card rent-market-card" id="bang-gia-thue-chi-tiet">'
        '<div class="market-table-head"><div><p class="eyebrow">Cho thuê · dữ liệu tin đăng</p>'
        '<h3>Giá thuê theo diện tích &amp; nội thất</h3></div>'
        '<a href="/cho-thue-lumi-hanoi/">Xem quỹ thuê →</a></div>'
        '<p class="rent-price-intro">So đúng cỡ căn, so đúng nội thất. '
        'Chọn loại căn để xem khoảng giá thuê, giá trung bình và từng tin gốc.</p>'
        f'<nav class="rent-price-pills" aria-label="Chọn loại căn cần so giá">{chips}</nav>'
        f'<div class="rent-price-groups">{sections}</div>'
        '<p class="rent-price-note"><strong>Nguồn:</strong> Tin đang công khai, đã duyệt, '
        'có giá thuê và diện tích hợp lệ; không tính shop chân đế. '
        'Diện tích được nhóm theo m² gần nhất để dễ so sánh (dấu ≈ là diện tích xấp xỉ); '
        'nhấn “Xem tin gốc” để biết số m² chính xác. '
        'Nội thất chỉ phân loại theo thông tin người đăng chọn, không tự suy đoán. '
        'Đây là giá rao tham khảo, không phải giá giao dịch chốt.</p>'
        '</div>'
    )


def sync_rent_breakdown(listings: list[dict], path: Path | None = None) -> None:
    path = path or gen.PRICE_PAGE
    raw = path.read_text(encoding="utf-8")
    anchor = raw.find(RENT_HEAD)
    if anchor < 0:
        raise RuntimeError("Rental price card not found; the SEO price template may have changed")
    start = raw.rfind('    <div class="market-table-card">', 0, anchor)
    end = raw.find('    <div class="market-table-card">', anchor + len(RENT_HEAD))
    if start < 0 or end < 0:
        raise RuntimeError("Could not isolate the rental price card")
    updated = raw[:start] + "    " + render_breakdown(listings) + "\n\n" + raw[end:]
    path.write_text(updated, encoding="utf-8")
    count = sum(len(group) for sizes in rental_groups(listings).values()
                for fields in sizes.values() for group in fields.values())
    print(f"Rental price breakdown: {count} valid listings grouped by size and furnishing")
