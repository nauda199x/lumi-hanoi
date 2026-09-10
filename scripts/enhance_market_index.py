#!/usr/bin/env python3
"""Enrich the Lumi Hanoi price page with a tower-level market index.

Runs after the marketplace SEO generator. Values come only from approved public
listings with a valid price and area. Apartment and shop statistics stay separate.
"""
from __future__ import annotations

import re
from statistics import mean

import generate_marketplace_seo as gen

TOWER_INDEX_START = "<!-- MARKET-TOWER-INDEX:START -->"
TOWER_INDEX_END = "<!-- MARKET-TOWER-INDEX:END -->"
TOWERS = (
    ("S1", "Signature"),
    ("S2", "Signature"),
    ("S3", "Signature"),
    ("S5", "Signature"),
    ("S6", "Signature"),
    ("P1", "Prestige"),
    ("P2", "Prestige"),
    ("E1", "Elite"),
    ("E2", "Elite"),
)


def tower_rows(listings: list[dict], listing_type: str, tower: str) -> list[dict]:
    rows = []
    for listing in listings:
        if listing.get("listing_type") != listing_type:
            continue
        if gen.clean(listing.get("tower")).upper() != tower:
            continue
        unit = gen.clean(listing.get("unit_type"))
        if unit not in gen.APARTMENT_UNIT_TYPES:
            continue
        price = gen.numeric(listing.get("price_vnd"))
        area = gen.numeric(listing.get("area_sqm"))
        if not price or not area:
            continue
        rows.append(listing)
    return rows


def average_stats(rows: list[dict]) -> dict[str, float | int | None]:
    pairs = [
        (gen.numeric(row.get("price_vnd")), gen.numeric(row.get("area_sqm")))
        for row in rows
    ]
    pairs = [(price, area) for price, area in pairs if price and area]
    if not pairs:
        return {"count": 0, "price": None, "ppsm": None}
    prices = [price for price, _ in pairs]
    return {
        "count": len(pairs),
        "price": mean(prices),
        "ppsm": mean(price / area for price, area in pairs),
    }


def inventory_link(listing_type: str, tower: str) -> str:
    segment = "cho-thue-lumi-hanoi" if listing_type == "rent" else "mua-ban-lumi-hanoi"
    return f"/{segment}/#tower={tower}"


def count_link(listing_type: str, tower: str, count: int) -> str:
    label = f"{count} tin" if count else "0 tin"
    return f'<a href="{gen.esc(inventory_link(listing_type, tower))}">{label}</a>'


def render_row(listings: list[dict], tower: str, phase: str) -> str:
    sale = average_stats(tower_rows(listings, "sale", tower))
    rent = average_stats(tower_rows(listings, "rent", tower))
    sale_price = gen.format_market_price(sale["price"], "sale") if sale["count"] else "—"
    sale_ppsm = gen.format_market_ppsm(sale["ppsm"], "sale") if sale["count"] else "—"
    rent_price = gen.format_market_price(rent["price"], "rent") if rent["count"] else "—"
    floor_url = gen.tower_link(tower)
    return (
        "<tr>"
        f'<th><a href="{gen.esc(floor_url)}">Tòa {gen.esc(tower)}</a></th>'
        f"<td>{gen.esc(phase)}</td>"
        f'<td>{count_link("sale", tower, int(sale["count"]))}</td>'
        f"<td>{gen.esc(sale_price)}</td>"
        f"<td>{gen.esc(sale_ppsm)}</td>"
        f'<td>{count_link("rent", tower, int(rent["count"]))}</td>'
        f"<td>{gen.esc(rent_price)}</td>"
        "</tr>"
    )


def render_tower_index(listings: list[dict]) -> str:
    rows = "\n        ".join(render_row(listings, tower, phase) for tower, phase in TOWERS)
    return f"""{TOWER_INDEX_START}
    <div class="market-table-card market-tower-index">
      <div class="market-table-head">
        <div><p class="eyebrow">Theo từng tòa</p><h3>Market Index S1–S6, P1–P2, E1–E2</h3></div>
        <a href="/mat-bang-lumi-hanoi/">Xem thư viện mặt bằng →</a>
      </div>
      <p class="market-index-note">Đối chiếu nguồn cung và giá chào theo từng tòa. Nhấn tên tòa để xem mặt bằng; nhấn số tin để mở quỹ căn đang bán hoặc cho thuê đã lọc đúng tòa.</p>
      <div class="market-table-scroll"><table>
        <thead><tr><th>Tòa</th><th>Phân khu</th><th>Tin bán</th><th>Giá bán TB</th><th>Giá/m² TB</th><th>Tin thuê</th><th>Giá thuê TB</th></tr></thead>
        <tbody>
        {rows}
        </tbody>
      </table></div>
      <p class="market-index-source">Chỉ tính căn hộ có đủ giá rao và diện tích trong các tin đã duyệt đang công khai. Đây là giá chào tham khảo, không phải giá giao dịch công chứng.</p>
    </div>
{TOWER_INDEX_END}"""


def upsert_tower_index(raw: str, block: str) -> str:
    if TOWER_INDEX_START in raw and TOWER_INDEX_END in raw:
        return re.sub(
            re.escape(TOWER_INDEX_START) + r".*?" + re.escape(TOWER_INDEX_END),
            lambda _: block,
            raw,
            count=1,
            flags=re.S,
        )
    anchor = '<aside class="shop-market-box"'
    position = raw.find(anchor)
    if position < 0:
        raise RuntimeError("Could not locate shop market block on price page")
    return raw[:position] + block + "\n    " + raw[position:]


def main() -> None:
    if not gen.PRICE_PAGE.exists():
        raise RuntimeError(f"Price page does not exist: {gen.PRICE_PAGE}")
    listings = gen.fetch_approved()
    raw = gen.PRICE_PAGE.read_text(encoding="utf-8")
    raw = raw.replace(
        '<p class="eyebrow">Snapshot thị trường</p><h2 id="market-snapshot-title">Dữ liệu căn hộ đang công khai</h2>',
        '<p class="eyebrow">Lumi Hanoi Market Index</p><h2 id="market-snapshot-title">Giá chào và nguồn cung đang công khai</h2>',
        1,
    )
    raw = upsert_tower_index(raw, render_tower_index(listings))
    gen.PRICE_PAGE.write_text(raw, encoding="utf-8")
    print("Market Index: added tower-level sale/rent supply and asking-price statistics")


if __name__ == "__main__":
    main()
