#!/usr/bin/env python3
"""Generate a compact, non-interactive rental price table from approved listings.

Every displayed price is computed from the explicit structured unit type, area,
monthly asking price, and furnishing. No inferred furniture or fabricated prices.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from statistics import mean

import generate_marketplace_seo as gen


FURNISHINGS = (
    ("basic", "Đồ cơ bản"),
    ("full", "Full nội thất"),
)
RENT_HEAD = (
    '<div class="market-table-head"><div><p class="eyebrow">Cho thuê</p>'
    '<h3>Giá rao thuê theo loại căn</h3></div>'
    '<a href="/cho-thue-lumi-hanoi/">Xem quỹ thuê →</a></div>'
)



@lru_cache(maxsize=1)
def area_catalog():
    """Read the precise same NFA selection and legacy aliases as the listing form."""
    source = (gen.ROOT / "assets/js/lumi-area-presets.js").read_text(encoding="utf-8")
    def get(name):
        found = re.search(r"const\s+" + name + r"\s*=\s*Object\.freeze\((\{.*?\})\);", source, re.S)
        if not found:
            raise RuntimeError("Lumi NFA catalogue not found: " + name)
        return json.loads(found.group(1))
    groups, aliases = get("groups"), get("aliases")
    if tuple(groups) != gen.APARTMENT_UNIT_TYPES:
        raise RuntimeError("Lumi NFA catalogue diverges from listing types")
    return groups, aliases


def furnishing_group(value) -> str:
    """Accept only the furnishing field, not claims made in titles/descriptions."""
    text = unicodedata.normalize("NFD", gen.clean(value).lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"\s+", " ", text.replace("đ", "d")).strip()
    if "nguyen ban" in text or "ban giao" in text or "co ban" in text:
        return "basic"
    if "full" in text or "day du" in text:
        return "full"
    return "unknown"


def normalized_rental_area(unit: str, value) -> int | None:
    """Accept only the form's canonical NFA or individually verified legacy NFA."""
    area = gen.numeric(value)
    groups, aliases = area_catalog()
    if not area or unit not in groups:
        return None
    for size in groups[unit]:
        if abs(area - size) < 0.049:
            return size
    for size, actual in aliases.get(unit, {}).items():
        if any(abs(area - float(v)) < 0.049 for v in actual):
            return int(size)
    return None


def rental_groups(listings: list[dict]) -> dict[str, dict[int, dict[str, list[dict]]]]:
    groups = {unit: defaultdict(lambda: defaultdict(list))
              for unit in gen.APARTMENT_UNIT_TYPES}
    for row in gen.market_rows(listings, "rent"):
        # Keep counts consistent with records generated on the public website.
        if not re.fullmatch(r"[a-z0-9-]{8,120}", gen.clean(row.get("slug"))):
            continue
        unit = gen.clean(row["unit_type"])
        normalized_area = normalized_rental_area(unit, row["area_sqm"])
        if normalized_area is None:
            continue
        groups[unit][normalized_area][
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
    """Show ALL form-approved NFA groups, including those with no approved price."""
    display_rows = []
    for size in area_catalog()[0][unit]:
        groups = sizes.get(size, {})
        cells = "".join(render_cell(groups.get(key, [])) for key, _ in FURNISHINGS)
        display_rows.append(f'<tr><th scope="row">{size} m²</th>{cells}</tr>')
    table = (
        '<div class="rent-simple-table-wrap"><table class="rent-simple-table">'
        f'<caption class="rent-visually-hidden">Giá thuê {gen.esc(unit)} theo diện tích thông thủy</caption>'
        '<colgroup><col class="rent-col-area"><col span="2" class="rent-col-price"></colgroup>'
        '<thead><tr><th scope="col">Diện tích</th>'
        + "".join(f'<th scope="col">{gen.esc(label)}</th>' for _, label in FURNISHINGS)
        + '</tr></thead><tbody>' + "".join(display_rows) + '</tbody></table></div>'
    )
    return (
        f'<section class="rent-simple-unit" id="rent-area-{gen.esc(unit.lower())}" '
        f'aria-label="Giá thuê {gen.esc(unit)} theo diện tích thông thủy">'
        f'<div class="rent-simple-unit-title"><h4>{gen.esc(unit)}</h4>'
        f'<span>{len(area_catalog()[0][unit])} nhóm diện tích</span></div>'
        f'{table}</section>'
    )


def render_area_nav(prefix: str) -> str:
    links = "".join(
        f'<a href="#{prefix}-area-{gen.esc(unit.lower())}">{gen.esc(unit)}</a>'
        for unit in gen.APARTMENT_UNIT_TYPES
    )
    return f'<nav class="area-price-links" aria-label="Chọn loại căn">{links}</nav>'


def render_sale_breakdown(listings: list[dict]) -> str:
    """Sale matrix is normalized by the same canonical NFA, not bedroom count alone."""
    groups = {unit: defaultdict(list) for unit in gen.APARTMENT_UNIT_TYPES}
    for row in gen.market_rows(listings, "sale"):
        if not re.fullmatch(r"[a-z0-9-]{8,120}", gen.clean(row.get("slug"))):
            continue
        unit = gen.clean(row.get("unit_type"))
        area = normalized_rental_area(unit, row.get("area_sqm"))
        if area is not None:
            groups[unit][area].append(row)
    sections = []
    for unit, by_area in groups.items():
        rows = []
        for size in area_catalog()[0][unit]:
            matches = by_area.get(size, [])
            if matches:
                avg = mean(gen.numeric(r["price_vnd"]) for r in matches)
                ppsm = mean(gen.numeric(r["price_vnd"]) / gen.numeric(r["area_sqm"]) for r in matches)
                cells = (f'<td><strong class="rent-table-value">{str(round(avg / 1_000_000_000, 2)).replace(".", ",")} tỷ</strong></td>'
                         f'<td><strong class="rent-table-value">{million(ppsm)} tr/m²</strong></td>')
            else:
                cells = '<td class="rent-price-empty">—</td><td class="rent-price-empty">—</td>'
            rows.append(f'<tr><th scope="row">{size} m²</th>{cells}</tr>')
        sections.append(
            f'<section class="rent-simple-unit" id="sale-area-{gen.esc(unit.lower())}">'
            f'<div class="rent-simple-unit-title"><h4>{gen.esc(unit)}</h4>'
            f'<span>{len(area_catalog()[0][unit])} nhóm diện tích</span></div>'
            '<div class="rent-simple-table-wrap"><table class="rent-simple-table">'
            '<colgroup><col class="rent-col-area"><col span="2" class="rent-col-price"></colgroup>'
            '<thead><tr><th scope="col">Diện tích</th><th scope="col">Giá bán TB</th><th scope="col">Giá/m² TB</th></tr></thead>'
            + '<tbody>' + "".join(rows) + '</tbody></table></div></section>'
        )
    return (
        '<div class="market-table-card rent-market-card area-price-card sale-area-card" id="bang-gia-ban-theo-dien-tich">'
        '<div class="rent-simple-head"><div><p class="eyebrow">Mua bán · tra cứu chi tiết</p>'
        '<h3>Bảng giá bán theo diện tích thông thủy</h3>'
        '<p class="area-price-lead">Giá trung bình theo từng nhóm diện tích chuẩn, '
        'không gộp căn nhỏ và căn lớn cùng số phòng ngủ.</p></div>'
        '<p>Giá rao trung bình <span>tỷ đồng · triệu đồng/m²</span></p></div>'
        + render_area_nav("sale")
        + '<div class="rent-simple-sections">' + "".join(sections) + '</div>'
        '<p class="rent-price-note">Dữ liệu từ tin bán đã duyệt, có đủ giá và diện tích thông thủy '
        'đối chiếu được với danh mục chuẩn. Giá/m² dùng diện tích thực tế trong tin, '
        'không thay bằng diện tích làm tròn của nhóm. Dấu — là chưa có dữ liệu, '
        'không phải giá bằng 0; giá rao không phải giá giao dịch.</p></div>'
    )


def render_breakdown(listings: list[dict]) -> str:
    groups = rental_groups(listings)
    tables = "".join(render_unit(unit, groups[unit]) for unit in gen.APARTMENT_UNIT_TYPES)
    return (
        '<div class="market-table-card rent-market-card area-price-card" id="bang-gia-thue-chi-tiet">'
        '<div class="rent-simple-head"><div><p class="eyebrow">Cho thuê · tra cứu chi tiết</p>'
        '<h3>Bảng giá thuê theo diện tích thông thủy</h3>'
        '<p class="area-price-lead">So sánh từng nhóm căn theo hai trạng thái nội thất. '
        'Diện tích chuẩn đồng bộ với form đăng tin.</p></div>'
        '<p>Giá thuê trung bình <span>triệu đồng/tháng</span></p></div>'
        + render_area_nav("rent")
        + f'<div class="rent-simple-sections">{tables}</div>'
        '<p class="rent-price-note"><strong>Lưu ý:</strong> Mỗi dòng là nhóm diện tích '
        'thông thủy chuẩn (không phải tim tường hay số đo chính xác của mọi layout). '
        'Chỉ lấy tin thuê đã duyệt, có đủ giá và nội thất. Dữ liệu cũ “Nguyên bản” '
        'được gộp vào “Đồ cơ bản”; nội thất chưa khai không bị tự gán. '
        'Chỉ đối chiếu các diện tích cũ đã được xác minh trong form, '
        'không làm tròn tùy ý. Dấu — là chưa có dữ liệu, không phải giá bằng 0. '
        'Giá rao tham khảo, không phải giá chốt.</p></div>'
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
    updated = raw[:start] + "    " + render_sale_breakdown(listings) + "\n\n    " + render_breakdown(listings) + "\n\n" + raw[end:]
    updated = re.sub(
        r"/assets/css/market-price\.css\?v=[^\"']+",
        "/assets/css/market-price.css?v=20261013-area-price-v2",
        updated,
        count=1,
    )
    path.write_text(updated, encoding="utf-8")
    count = sum(
        len(rows) for unit in rental_groups(listings).values()
        for groups in unit.values() for rows in groups.values()
    )
    print(f"Rental price simple tables: {count} approved listings classified")
