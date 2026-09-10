#!/usr/bin/env python3
"""Bridge tower floor-plan authority into live Lumi Hanoi marketplace inventory.

The nine existing tower floor-plan pages keep their floor-plan title, H1,
canonical and primary visual intent. This generator adds one lightweight,
crawlable module after the floor-plan/editorial content that exposes approved
apartment inventory for the same tower: counts, asking-price benchmarks, up to
two recent sale/rent detail links and controlled marketplace CTAs.

No new faceted/indexable rental URLs are created here. Sale CTAs use the finite
3B tower landing set; rental CTAs reuse the canonical rental hub with the
existing client-side #tower filter.
"""
from __future__ import annotations

import re
from statistics import median

import generate_marketplace_seo as gen
import generate_sale_tower_seo as sale

BRIDGE_START = "<!-- TOWER-MARKETPLACE-BRIDGE:START -->"
BRIDGE_END = "<!-- TOWER-MARKETPLACE-BRIDGE:END -->"
MAX_RECENT_LINKS = 2


def tower_rows(listings: list[dict], tower: str, listing_type: str) -> list[dict]:
    rows: list[dict] = []
    for listing in listings:
        if listing.get("listing_type") != listing_type:
            continue
        if gen.clean(listing.get("tower")).upper() != tower.upper():
            continue
        if gen.clean(listing.get("unit_type")) not in gen.APARTMENT_UNIT_TYPES:
            continue
        if not gen.clean(listing.get("slug")):
            continue
        rows.append(listing)
    return sorted(
        rows,
        key=lambda row: (
            row.get("is_featured") is True,
            row.get("approved_at") or "",
            row.get("created_at") or "",
            row.get("id") or "",
        ),
        reverse=True,
    )


def asking_benchmark(rows: list[dict], listing_type: str) -> str:
    values = [gen.numeric(row.get("price_vnd")) for row in rows]
    values = [value for value in values if value]
    if not values:
        return "Chưa đủ dữ liệu"
    return gen.format_market_price(median(values), listing_type)


def short_title(row: dict, tower: str) -> str:
    value = gen.compact_text(row.get("title", ""))
    # The bridge is an editorial navigation surface, so do not echo phone
    # numbers that a poster may have put into a title.
    value = re.sub(r"(?<!\d)(?:\+?84|0)[\d.\s-]{8,}(?!\d)", "", value).strip(" -–—·|")
    value = re.sub(r"\s{2,}", " ", value).strip()
    if not value:
        value = f"Xem tin {gen.clean(row.get('unit_type')) or 'căn hộ'} tòa {tower}"
    if len(value) > 82:
        value = value[:79].rsplit(" ", 1)[0] + "…"
    return value


def recent_links(rows: list[dict], listing_type: str, tower: str) -> str:
    links = []
    for row in rows[:MAX_RECENT_LINKS]:
        links.append(
            f'<a data-market-listing-link="{listing_type}" href="{gen.esc(gen.listing_url(row))}">'
            f'{gen.esc(short_title(row, tower))}</a>'
        )
    if links:
        label = "Tin mua bán mới" if listing_type == "sale" else "Tin cho thuê mới"
        return f'<nav class="detail-related" aria-label="{label} tòa {tower}">' + "".join(links) + "</nav>"
    action = "bán" if listing_type == "sale" else "cho thuê"
    return f'<p>Chưa có tin {action} tòa {tower} đang công khai.</p>'


def bridge_html(item: dict, listings: list[dict]) -> str:
    tower = item["tower"]
    sale_rows = tower_rows(listings, tower, "sale")
    rent_rows = tower_rows(listings, tower, "rent")
    sale_url = f'/{item["slug"]}/'
    rent_url = f'/cho-thue-lumi-hanoi/#tower={tower}'
    heading_id = f'{tower.lower()}-marketplace-bridge'

    return (
        f'{BRIDGE_START}\n'
        f'<section class="tower-marketplace-bridge" data-marketplace-bridge data-tower="{tower}" aria-labelledby="{heading_id}">'
        f'<h2 id="{heading_id}">Giao dịch tại tòa {tower}</h2>'
        f'<p>Sau khi đối chiếu đúng mặt bằng và nhóm tầng, xem quỹ căn {tower} đang được người dùng đăng công khai để so sánh sản phẩm cùng tòa.</p>'
        '<div class="facts-grid">'
        f'<div class="fact-card"><strong>{len(sale_rows)} căn bán</strong><span>Trung vị giá chào: {gen.esc(asking_benchmark(sale_rows, "sale"))}</span></div>'
        f'<div class="fact-card"><strong>{len(rent_rows)} căn cho thuê</strong><span>Trung vị giá chào: {gen.esc(asking_benchmark(rent_rows, "rent"))}</span></div>'
        '</div>'
        f'<h3>Tin mua bán mới tại {tower}</h3>{recent_links(sale_rows, "sale", tower)}'
        f'<p><a class="btn" data-market-cta="sale" href="{sale_url}">Xem căn {tower} đang bán</a></p>'
        f'<h3>Tin cho thuê mới tại {tower}</h3>{recent_links(rent_rows, "rent", tower)}'
        f'<p><a class="btn" data-market-cta="rent" href="{rent_url}">Xem căn {tower} đang cho thuê</a></p>'
        '<nav class="detail-related" aria-label="Công cụ giao dịch Lumi Hanoi">'
        '<a href="/gia-can-ho-lumi-hanoi/">Lumi Hanoi Market Index</a>'
        f'<a href="/dang-tin-lumi-hanoi/#mua-ban">Đăng tin tòa {tower}</a>'
        '</nav>'
        '<p class="notice"><strong>Nguồn dữ liệu:</strong> các tin đã duyệt đang công khai trên Lumi Hanoi. '
        'Mức giá hiển thị là <strong>giá chào</strong> của người đăng, không phải giá giao dịch công chứng.</p>'
        '</section>\n'
        f'{BRIDGE_END}'
    )


def floorplan_path(tower: str):
    return gen.ROOT / gen.tower_link(tower).lstrip("/") / "index.html"


def upsert_bridge(raw: str, tower: str, block: str) -> str:
    if BRIDGE_START in raw and BRIDGE_END in raw:
        return re.sub(
            re.escape(BRIDGE_START) + r".*?" + re.escape(BRIDGE_END),
            lambda _: block,
            raw,
            count=1,
            flags=re.S,
        )

    faq = re.search(
        rf'<h2(?:\s+[^>]*)?>FAQ\s+mặt\s+bằng\s+{re.escape(tower)}\s+Lumi\s+Hanoi</h2>',
        raw,
        flags=re.I,
    )
    if faq:
        return raw[: faq.start()] + block + raw[faq.start() :]

    article_end = raw.find("</article>")
    if article_end < 0:
        raise RuntimeError(f"Cannot find insertion point on floor-plan page for {tower}")
    return raw[:article_end] + block + raw[article_end:]


def update_pages(listings: list[dict]) -> dict[str, tuple[int, int]]:
    counts: dict[str, tuple[int, int]] = {}
    for item in sale.TOWERS:
        tower = item["tower"]
        path = floorplan_path(tower)
        if not path.is_file():
            raise RuntimeError(f"Missing tower floor-plan page: {path}")
        raw = path.read_text(encoding="utf-8")
        updated = upsert_bridge(raw, tower, bridge_html(item, listings))
        path.write_text(updated, encoding="utf-8")
        counts[tower] = (
            len(tower_rows(listings, tower, "sale")),
            len(tower_rows(listings, tower, "rent")),
        )
    return counts


def main() -> None:
    listings = gen.fetch_approved()
    counts = update_pages(listings)
    summary = ", ".join(f"{tower}={sale_count} bán/{rent_count} thuê" for tower, (sale_count, rent_count) in counts.items())
    print("Floor-plan marketplace bridge generated: " + summary)


if __name__ == "__main__":
    main()
