#!/usr/bin/env python3
"""Generate crawlable static SEO pages for approved Lumi Hanoi marketplace listings.

The public Supabase publishable key is intentionally read from the browser config.
Only rows already exposed by the anonymous RLS policy are fetched.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "assets/js/marketplace-config.js"
SITE = "https://lumi-hanoi.com"
MARKER = ".marketplace-generated"
SITEMAP = ROOT / "sitemap-tin-dang.xml"
MAIN_SITEMAP = ROOT / "sitemap.xml"
SHOP_LANDING = ROOT / "cho-thue-shop-chan-de-lumi-hanoi" / "index.html"
PRICE_PAGE = ROOT / "gia-can-ho-lumi-hanoi" / "index.html"
STATIC_LISTING_START = "<!-- MARKETPLACE-STATIC-LISTINGS:START -->"
STATIC_LISTING_END = "<!-- MARKETPLACE-STATIC-LISTINGS:END -->"
SHOP_LISTING_START = "<!-- MARKETPLACE-SHOP-LISTINGS:START -->"
SHOP_LISTING_END = "<!-- MARKETPLACE-SHOP-LISTINGS:END -->"
MAIN_SITEMAP_START = "<!-- MARKETPLACE-LISTINGS:START -->"
MAIN_SITEMAP_END = "<!-- MARKETPLACE-LISTINGS:END -->"
MARKET_PRICE_START = "<!-- MARKET-PRICE-STATS:START -->"
MARKET_PRICE_END = "<!-- MARKET-PRICE-STATS:END -->"
APARTMENT_UNIT_TYPES = ("1PN", "2PN", "3PN", "4PN", "Duplex", "Penthouse")
MARKET_PHASES = ("Signature", "Prestige", "Elite")

CATEGORY = {
    "sale": ("mua-ban-lumi-hanoi", "Mua bán"),
    "rent": ("cho-thue-lumi-hanoi", "Cho thuê"),
}
UNIT_LINKS = {
    "1PN": "/can-ho-1-phong-ngu-lumi-hanoi/",
    "2PN": "/can-ho-2-phong-ngu-lumi-hanoi/",
    "3PN": "/can-ho-3-phong-ngu-lumi-hanoi/",
    "4PN": "/can-ho-4-phong-ngu-lumi-hanoi/",
    "Duplex": "/duplex-penthouse-lumi-hanoi/",
    "Penthouse": "/duplex-penthouse-lumi-hanoi/",
    "Shop chân đế": "/cho-thue-shop-chan-de-lumi-hanoi/",
}


def read_public_config() -> tuple[str, str, str]:
    raw = CONFIG_PATH.read_text(encoding="utf-8")
    def grab(name: str) -> str:
        match = re.search(rf'{re.escape(name)}\s*:\s*"([^"]+)"', raw)
        if not match:
            raise RuntimeError(f"Missing {name} in {CONFIG_PATH}")
        return match.group(1)
    return grab("supabaseUrl").rstrip("/"), grab("supabasePublishableKey"), grab("storageBucket")


def fetch_approved() -> list[dict]:
    base, key, _ = read_public_config()
    params = {
        "select": (
            "id,slug,listing_code,listing_type,title,description,poster_name,phase,tower,"
            "bedroom_count,unit_type,area_sqm,floor_label,price_vnd,furnishing,"
            "available_from,contact_phone,is_featured,approved_at,expires_at,created_at,"
            "listing_images(id,storage_path,sort_order,alt_text)"
        ),
        "status": "eq.approved",
        "order": "is_featured.desc,sort_priority.desc,approved_at.desc",
        "limit": "1000",
    }
    url = f"{base}/rest/v1/listings?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={
            "apikey": key,
            "Accept": "application/json",
            "User-Agent": "lumi-hanoi-marketplace-seo-generator/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected Supabase response")
    return payload


def clean(value) -> str:
    return str(value or "").strip()


def esc(value) -> str:
    return html.escape(clean(value), quote=True)


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", clean(value)).strip()


def meta_description(listing: dict) -> str:
    action = "Cho thuê" if listing.get("listing_type") == "rent" else "Mua bán"
    specs = " · ".join(
        part
        for part in [
            clean(listing.get("tower")),
            clean(listing.get("unit_type")),
            f"{format_area(listing.get('area_sqm'))} m²" if listing.get("area_sqm") else "",
            format_price(listing),
        ]
        if part
    )
    desc = compact_text(listing.get("description", ""))
    base = f"{action} căn {specs} tại Lumi Hanoi. {desc}".strip()
    if len(base) <= 158:
        return base
    return base[:155].rsplit(" ", 1)[0] + "…"


def format_area(value) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}".replace(".", ",")


def format_price(listing: dict) -> str:
    try:
        amount = int(float(listing.get("price_vnd") or 0))
    except (TypeError, ValueError):
        amount = 0
    if not amount:
        return "Liên hệ"
    if listing.get("listing_type") == "rent":
        return f"{amount / 1_000_000:g}".replace(".", ",") + " triệu/tháng"
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " tỷ"
    return f"{amount:,}".replace(",", ".") + " đ"


def storage_url(path: str) -> str:
    base, _, bucket = read_public_config()
    encoded = "/".join(urllib.parse.quote(part, safe="") for part in clean(path).split("/"))
    return f"{base}/storage/v1/object/public/{urllib.parse.quote(bucket, safe='')}/{encoded}"


def listing_url(listing: dict) -> str:
    segment = CATEGORY[listing["listing_type"]][0]
    return f"/{segment}/{listing['slug']}/"


def tower_link(tower: str) -> str:
    tower = clean(tower).lower()
    if not tower:
        return "/mat-bang-lumi-hanoi/"
    phase = "lumi-signature" if tower.startswith("s") else "lumi-prestige" if tower.startswith("p") else "lumi-elite"
    return f"/mat-bang-lumi-hanoi/{phase}/{tower}/"


def indexable(listing: dict) -> bool:
    images = listing.get("listing_images") or []
    return all(
        [
            len(compact_text(listing.get("title", ""))) >= 12,
            len(compact_text(listing.get("description", ""))) >= 40,
            bool(images),
            bool(listing.get("price_vnd")),
            bool(listing.get("area_sqm")),
            bool(listing.get("tower")),
            bool(listing.get("unit_type")),
        ]
    )


def date_only(value) -> str:
    value = clean(value)
    if not value:
        return ""
    match = re.match(r"(\d{4}-\d{2}-\d{2})", value)
    return match.group(1) if match else ""


def render_gallery(listing: dict) -> str:
    images = sorted(listing.get("listing_images") or [], key=lambda item: int(item.get("sort_order") or 0))
    if not images:
        return '<div class="marketplace-state"><span class="marketplace-state-mark">LH</span><div><h3>Tin chưa có ảnh</h3><p>Liên hệ người đăng để kiểm tra hiện trạng căn.</p></div></div>'
    figures = []
    for index, item in enumerate(images):
        src = storage_url(item.get("storage_path", ""))
        alt = item.get("alt_text") or f"{listing.get('title')} — ảnh {index + 1}"
        loading = "eager" if index == 0 else "lazy"
        figures.append(
            f'<figure><img src="{esc(src)}" alt="{esc(alt)}" width="1200" height="900" loading="{loading}" decoding="async"></figure>'
        )
    return (
        '<div class="detail-gallery">'
        '<div class="detail-gallery-track">'
        + "".join(figures)
        + '</div><span class="detail-gallery-counter" data-static-gallery-counter>1/'
        + str(len(images))
        + "</span></div>"
    )


def render_static_card(listing: dict) -> str:
    images = sorted(listing.get("listing_images") or [], key=lambda item: int(item.get("sort_order") or 0))
    image_html = ""
    if images:
        src = storage_url(images[0].get("storage_path", ""))
        alt = images[0].get("alt_text") or listing.get("title") or "Tin đăng Lumi Hanoi"
        image_html = (
            f'<a class="listing-card-slide" href="{esc(listing_url(listing))}" aria-label="Xem {esc(listing.get("title"))}">'
            f'<img src="{esc(src)}" alt="{esc(alt)}" width="1200" height="900" loading="lazy" decoding="async"></a>'
        )
    else:
        image_html = (
            f'<a class="listing-card-slide listing-card-placeholder" href="{esc(listing_url(listing))}">'
            f'{esc(listing.get("unit_type") or "Căn hộ")} · {esc(listing.get("tower") or "Lumi Hanoi")}</a>'
        )
    description = compact_text(listing.get("description", ""))
    if len(description) > 180:
        description = description[:177].rsplit(" ", 1)[0] + "…"
    facts = " · ".join(
        part for part in [
            format_price(listing),
            f'{format_area(listing.get("area_sqm"))} m²' if listing.get("area_sqm") else "",
            clean(listing.get("unit_type")),
            f'Tầng {clean(listing.get("floor_label"))}' if listing.get("floor_label") else "",
        ] if part
    )
    location = " · ".join(part for part in ["Lumi Hanoi", clean(listing.get("phase")), clean(listing.get("tower"))] if part)
    return (
        '<article class="listing-card listing-card--marketplace" data-static-listing-card>'
        '<div class="listing-card-media"><div class="listing-card-gallery-track">' + image_html + '</div></div>'
        '<div class="listing-card-body"><div class="listing-card-content">'
        f'<h3><a href="{esc(listing_url(listing))}">{esc(listing.get("title"))}</a></h3>'
        f'<div class="listing-card-facts"><strong class="listing-card-fact-price">{esc(facts)}</strong></div>'
        f'<div class="listing-card-location"><span>{esc(location)}</span></div>'
        f'<p class="listing-card-description">{esc(description or "Xem hình ảnh, giá và thông tin chi tiết của tin đăng.")}</p>'
        '</div></div></article>'
    )


def replace_marked_block(raw: str, start: str, end: str, body: str) -> str:
    block = start + "\n" + body.strip() + "\n" + end
    if start in raw and end in raw:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), block, raw, count=1, flags=re.S)
    return raw

def numeric(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def market_rows(listings: list[dict], listing_type: str, unit_type: str | None = None, phase: str | None = None) -> list[dict]:
    rows = []
    for listing in listings:
        if listing.get("listing_type") != listing_type:
            continue
        current_unit = clean(listing.get("unit_type"))
        if current_unit.lower() == "shop chân đế":
            continue
        if current_unit not in APARTMENT_UNIT_TYPES:
            continue
        if unit_type and current_unit != unit_type:
            continue
        if phase and clean(listing.get("phase")) != phase:
            continue
        if numeric(listing.get("price_vnd")) is None or numeric(listing.get("area_sqm")) is None:
            continue
        rows.append(listing)
    return rows


def market_stats(rows: list[dict]) -> dict:
    prices = [numeric(row.get("price_vnd")) for row in rows]
    areas = [numeric(row.get("area_sqm")) for row in rows]
    pairs = [(price, area) for price, area in zip(prices, areas) if price and area]
    valid_prices = [price for price, _ in pairs]
    per_sqm = [price / area for price, area in pairs]
    if not valid_prices:
        return {"count": 0, "min": None, "max": None, "median": None, "ppsm": None}
    return {
        "count": len(valid_prices),
        "min": min(valid_prices),
        "max": max(valid_prices),
        "median": median(valid_prices),
        "ppsm": median(per_sqm) if per_sqm else None,
    }


def format_market_price(value: float | None, listing_type: str) -> str:
    if value is None:
        return "—"
    if listing_type == "rent":
        amount = value / 1_000_000
        text = f"{amount:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".").rstrip("0").rstrip(",")
        return text + " triệu/tháng"
    amount = value / 1_000_000_000
    text = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".").rstrip("0").rstrip(",")
    return text + " tỷ"


def format_market_range(stats: dict, listing_type: str) -> str:
    if not stats.get("count"):
        return "—"
    low = format_market_price(stats.get("min"), listing_type)
    high = format_market_price(stats.get("max"), listing_type)
    return low if low == high else f"{low} – {high}"


def format_market_ppsm(value: float | None, listing_type: str) -> str:
    if value is None:
        return "—"
    amount = value / 1_000_000
    text = f"{amount:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".").rstrip("0").rstrip(",")
    return text + (" tr/m²/tháng" if listing_type == "rent" else " tr/m²")


def latest_market_date(listings: list[dict]) -> str:
    dates = [date_only(item.get("approved_at") or item.get("created_at")) for item in listings]
    dates = [value for value in dates if value]
    return max(dates) if dates else datetime.now().date().isoformat()


def vi_date(iso_date: str) -> str:
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", iso_date or "")
    return f"{match.group(3)}/{match.group(2)}/{match.group(1)}" if match else iso_date


def render_market_table_rows(listings: list[dict], listing_type: str) -> str:
    rendered = []
    for unit in APARTMENT_UNIT_TYPES:
        stats = market_stats(market_rows(listings, listing_type, unit_type=unit))
        rendered.append(
            "<tr>"
            f"<th>{esc(unit)}</th>"
            f"<td>{stats['count']}</td>"
            f"<td>{esc(format_market_range(stats, listing_type))}</td>"
            f"<td>{esc(format_market_price(stats.get('median'), listing_type))}</td>"
            f"<td>{esc(format_market_ppsm(stats.get('ppsm'), listing_type))}</td>"
            "</tr>"
        )
    return "\n".join(rendered)


def render_phase_rows(listings: list[dict]) -> str:
    rendered = []
    for phase in MARKET_PHASES:
        sale = market_stats(market_rows(listings, "sale", phase=phase))
        rent = market_stats(market_rows(listings, "rent", phase=phase))
        rendered.append(
            "<tr>"
            f"<th>{esc(phase)}</th>"
            f"<td>{sale['count']}</td>"
            f"<td>{esc(format_market_price(sale.get('median'), 'sale'))}</td>"
            f"<td>{esc(format_market_ppsm(sale.get('ppsm'), 'sale'))}</td>"
            f"<td>{rent['count']}</td>"
            f"<td>{esc(format_market_price(rent.get('median'), 'rent'))}</td>"
            "</tr>"
        )
    return "\n".join(rendered)


def render_shop_market(listings: list[dict]) -> str:
    sale_rows = [row for row in listings if row.get("listing_type") == "sale" and clean(row.get("unit_type")).lower() == "shop chân đế" and numeric(row.get("price_vnd")) and numeric(row.get("area_sqm"))]
    rent_rows = [row for row in listings if row.get("listing_type") == "rent" and clean(row.get("unit_type")).lower() == "shop chân đế" and numeric(row.get("price_vnd")) and numeric(row.get("area_sqm"))]
    sale_stats = market_stats_any(sale_rows)
    rent_stats = market_stats_any(rent_rows)
    sale_value = "Chưa có dữ liệu"
    rent_value = "Chưa có dữ liệu"
    if sale_stats["count"]:
        sale_value = f"{format_market_price(sale_stats.get('median'), 'sale')} · khoảng {format_market_ppsm(sale_stats.get('ppsm'), 'sale')}"
    if rent_stats["count"]:
        rent_value = f"{format_market_price(rent_stats.get('median'), 'rent')} · khoảng {format_market_ppsm(rent_stats.get('ppsm'), 'rent')}"
    return (
        '<aside class="shop-market-box" aria-labelledby="shop-market-title"><div><p class="eyebrow">Dữ liệu tách riêng</p>'
        '<h3 id="shop-market-title">Shop chân đế Lumi Hanoi</h3>'
        f'<p>Shop không được gộp vào thống kê căn hộ ở. Hiện có {sale_stats["count"]} tin bán và {rent_stats["count"]} tin thuê shop đủ dữ liệu.</p></div>'
        f'<dl><div><dt>Shop đang bán</dt><dd>{esc(sale_value)}</dd></div><div><dt>Shop đang thuê</dt><dd>{esc(rent_value)}</dd></div></dl></aside>'
    )


def market_stats_any(rows: list[dict]) -> dict:
    pairs = []
    for row in rows:
        price = numeric(row.get("price_vnd"))
        area = numeric(row.get("area_sqm"))
        if price and area:
            pairs.append((price, area))
    if not pairs:
        return {"count": 0, "min": None, "max": None, "median": None, "ppsm": None}
    prices = [price for price, _ in pairs]
    return {
        "count": len(prices),
        "min": min(prices),
        "max": max(prices),
        "median": median(prices),
        "ppsm": median([price / area for price, area in pairs]),
    }


def render_market_price_block(listings: list[dict]) -> str:
    sale = market_stats(market_rows(listings, "sale"))
    rent = market_stats(market_rows(listings, "rent"))
    updated = latest_market_date(listings)
    warning = ""
    if sale["count"] < 3 or rent["count"] < 3:
        warning = (
            '<div class="market-data-warning"><strong>Mẫu dữ liệu căn hộ hiện chưa đủ để công bố mức giá đại diện.</strong>'
            '<span>Website không điền giá ước đoán. Khi có thêm tin 1PN, 2PN, 3PN… được duyệt, các bảng dưới sẽ tự cập nhật.</span></div>'
        )
    sale_median = format_market_price(sale.get("median"), "sale") if sale["count"] else "Chưa đủ dữ liệu"
    sale_ppsm = format_market_ppsm(sale.get("ppsm"), "sale") if sale["count"] else "Chưa đủ dữ liệu"
    rent_median = format_market_price(rent.get("median"), "rent") if rent["count"] else "Chưa đủ dữ liệu"
    return f"""<section class="section market-price-snapshot" aria-labelledby="market-snapshot-title">
  <div class="container">
    <div class="market-price-heading">
      <div><p class="eyebrow">Snapshot thị trường</p><h2 id="market-snapshot-title">Dữ liệu căn hộ đang công khai</h2></div>
      <p class="market-price-updated">Tin đăng được đồng bộ tự động. Cập nhật dữ liệu gần nhất: <strong>{esc(vi_date(updated))}</strong>.</p>
    </div>
    <div class="market-kpis">
      <article><span>Tin căn hộ đang bán</span><strong>{sale["count"]}</strong><small>Không tính shop chân đế</small></article>
      <article><span>Giá bán trung vị</span><strong>{esc(sale_median)}</strong><small>Chỉ tính tin đủ giá và diện tích</small></article>
      <article><span>Giá/m² trung vị</span><strong>{esc(sale_ppsm)}</strong><small>Dùng trung vị, không dùng trung bình</small></article>
      <article><span>Giá thuê trung vị</span><strong>{esc(rent_median)}</strong><small>{rent["count"]} tin căn hộ đang cho thuê</small></article>
    </div>
    {warning}

    <div class="market-table-card">
      <div class="market-table-head"><div><p class="eyebrow">Mua bán</p><h3>Giá rao bán theo loại căn</h3></div><a href="/mua-ban-lumi-hanoi/">Xem quỹ căn →</a></div>
      <div class="market-table-scroll"><table><thead><tr><th>Loại căn</th><th>Số tin</th><th>Khoảng giá rao</th><th>Trung vị</th><th>Giá/m² trung vị</th></tr></thead><tbody>
        {render_market_table_rows(listings, "sale")}
      </tbody></table></div>
    </div>

    <div class="market-table-card">
      <div class="market-table-head"><div><p class="eyebrow">Cho thuê</p><h3>Giá rao thuê theo loại căn</h3></div><a href="/cho-thue-lumi-hanoi/">Xem quỹ thuê →</a></div>
      <div class="market-table-scroll"><table><thead><tr><th>Loại căn</th><th>Số tin</th><th>Khoảng giá rao</th><th>Trung vị</th><th>Giá/m²/tháng</th></tr></thead><tbody>
        {render_market_table_rows(listings, "rent")}
      </tbody></table></div>
    </div>

    <div class="market-table-card">
      <div class="market-table-head"><div><p class="eyebrow">Phân khu</p><h3>So sánh Signature, Prestige và Elite</h3></div><a href="/mat-bang-lumi-hanoi/">Đối chiếu mặt bằng →</a></div>
      <div class="market-table-scroll"><table><thead><tr><th>Phân khu</th><th>Tin bán</th><th>Giá bán trung vị</th><th>Giá/m²</th><th>Tin thuê</th><th>Giá thuê trung vị</th></tr></thead><tbody>
        {render_phase_rows(listings)}
      </tbody></table></div>
    </div>

    {render_shop_market(listings)}
  </div>
</section>"""


def sync_market_price_page(listings: list[dict]) -> None:
    if not PRICE_PAGE.exists():
        return
    raw = PRICE_PAGE.read_text(encoding="utf-8")
    raw = replace_marked_block(raw, MARKET_PRICE_START, MARKET_PRICE_END, render_market_price_block(listings))
    PRICE_PAGE.write_text(raw, encoding="utf-8")



def sync_category_indexes(listings: list[dict]) -> None:
    for listing_type, (segment, _) in CATEGORY.items():
        path = ROOT / segment / "index.html"
        if not path.exists():
            continue
        rows = [listing for listing in listings if listing.get("listing_type") == listing_type]
        cards = "\n".join(render_static_card(listing) for listing in rows)
        raw = path.read_text(encoding="utf-8")
        if STATIC_LISTING_START in raw and STATIC_LISTING_END in raw:
            raw = replace_marked_block(raw, STATIC_LISTING_START, STATIC_LISTING_END, cards)
        else:
            empty_grid = re.compile(r'(<div class="listing-grid" data-listing-grid)(?: hidden)?(>)\s*</div>')
            replacement = (
                r'\1\2\n' + STATIC_LISTING_START + "\n" + cards + "\n" + STATIC_LISTING_END + "\n</div>"
            )
            raw, count = empty_grid.subn(replacement, raw, count=1)
            if count != 1:
                raise RuntimeError(f"Could not locate listing grid in {path}")
        if rows:
            raw = raw.replace('<div class="listing-grid" data-listing-grid hidden>', '<div class="listing-grid" data-listing-grid>')
            raw = re.sub(
                r'<div class="marketplace-state" data-listing-state(?: hidden)? role="status">',
                '<div class="marketplace-state" data-listing-state hidden role="status">',
                raw,
                count=1,
            )
        else:
            raw = raw.replace('<div class="listing-grid" data-listing-grid>', '<div class="listing-grid" data-listing-grid hidden>')
            raw = re.sub(
                r'<div class="marketplace-state" data-listing-state(?: hidden)? role="status">',
                '<div class="marketplace-state" data-listing-state role="status">',
                raw,
                count=1,
            )
        count_text = f"{len(rows)} tin đăng" if rows else "0 tin đăng"
        raw = re.sub(
            r'(<span class="marketplace-count" data-listing-count aria-label="Số tin đang hiển thị">).*?(</span>)',
            rf'\g<1>{count_text}\2',
            raw,
            count=1,
            flags=re.S,
        )
        path.write_text(raw, encoding="utf-8")


def sync_shop_landing(listings: list[dict]) -> None:
    if not SHOP_LANDING.exists():
        return
    shops = [
        listing for listing in listings
        if listing.get("listing_type") == "rent" and clean(listing.get("unit_type")).lower() == "shop chân đế"
    ]
    cards = "\n".join(render_static_card(listing) for listing in shops)
    if not cards:
        cards = '<div class="marketplace-state"><span class="marketplace-state-mark">LH</span><div><h3>Chưa có shop đang công khai</h3><p>Quay lại trang cho thuê để xem các loại căn khác tại Lumi Hanoi.</p></div></div>'
    raw = SHOP_LANDING.read_text(encoding="utf-8")
    raw = replace_marked_block(raw, SHOP_LISTING_START, SHOP_LISTING_END, cards)
    raw = re.sub(r'(<span data-static-shop-count>).*?(</span>)', rf'\g<1>{len(shops)} tin shop đang hiển thị\2', raw, count=1, flags=re.S)
    SHOP_LANDING.write_text(raw, encoding="utf-8")


def render_page(listing: dict) -> str:
    segment, action = CATEGORY[listing["listing_type"]]
    rel_url = listing_url(listing)
    canonical = SITE + rel_url
    title = compact_text(listing.get("title", "Tin căn hộ Lumi Hanoi"))
    description = meta_description(listing)
    robots = "index,follow,max-image-preview:large" if indexable(listing) else "noindex,follow"
    images = sorted(listing.get("listing_images") or [], key=lambda item: int(item.get("sort_order") or 0))
    hero_image = storage_url(images[0]["storage_path"]) if images else SITE + "/assets/media/og/lumi-hanoi-og.webp"
    area = format_area(listing.get("area_sqm"))
    price = format_price(listing)
    posted = date_only(listing.get("approved_at") or listing.get("created_at"))
    unit_link = UNIT_LINKS.get(clean(listing.get("unit_type")))
    related = [
        f'<a href="{esc(tower_link(listing.get("tower", "")))}">Mặt bằng tòa {esc(listing.get("tower"))}</a>',
        f'<a href="/{segment}/">{action} Lumi Hanoi</a>',
    ]
    if unit_link:
        related.append(f'<a href="{unit_link}">Tìm hiểu căn {esc(listing.get("unit_type"))} Lumi Hanoi</a>')

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": f"{action} Lumi Hanoi", "item": SITE + f"/{segment}/"},
                    {"@type": "ListItem", "position": 3, "name": title, "item": canonical},
                ],
            },
            {
                "@type": "WebPage",
                "name": title,
                "description": description,
                "url": canonical,
                "datePublished": posted or None,
                "inLanguage": "vi-VN",
                "primaryImageOfPage": hero_image,
                "mainEntity": {
                    "@type": "Offer",
                    "price": str(int(float(listing.get("price_vnd") or 0))) if listing.get("price_vnd") else None,
                    "priceCurrency": "VND",
                    "url": canonical,
                    "availability": "https://schema.org/InStock",
                    "itemOffered": {
                        "@type": "Apartment" if clean(listing.get("unit_type")) != "Shop chân đế" else "Place",
                        "name": title,
                        "floorSize": {
                            "@type": "QuantitativeValue",
                            "value": float(listing.get("area_sqm")) if listing.get("area_sqm") else None,
                            "unitCode": "MTK",
                        },
                        "address": {
                            "@type": "PostalAddress",
                            "addressLocality": "Hà Nội",
                            "addressCountry": "VN",
                        },
                    },
                },
            },
        ],
    }

    # Strip null values from compact JSON-LD.
    def prune(value):
        if isinstance(value, dict):
            return {k: prune(v) for k, v in value.items() if v is not None}
        if isinstance(value, list):
            return [prune(v) for v in value if v is not None]
        return value

    legal_note = (
        "Tin đăng được người đăng cung cấp và đã qua bước duyệt hiển thị. "
        "Người xem cần tự kiểm tra danh tính, quyền giao dịch, hiện trạng căn và hồ sơ trước khi đặt cọc."
    )
    schema_json = json.dumps(prune(schema), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    related_html = "".join(related)
    description_html = esc(listing.get("description")).replace("\n", "<br>")
    poster_name = clean(listing.get("poster_name")) or "Người đăng"
    phone = clean(listing.get("contact_phone"))
    phone_href = re.sub(r"[^+\\d]", "", phone)
    zalo_number = re.sub(r"\\D", "", phone)
    zalo_href = f"https://zalo.me/{zalo_number}" if zalo_number else "#"
    zalo_hidden = "" if zalo_number else " hidden"
    price_per_sqm = ""
    if listing.get("listing_type") == "sale" and listing.get("price_vnd") and listing.get("area_sqm"):
        try:
            ppm = float(listing.get("price_vnd")) / float(listing.get("area_sqm")) / 1_000_000
            price_per_sqm = f"~{ppm:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + " tr/m²"
        except (TypeError, ValueError, ZeroDivisionError):
            price_per_sqm = ""
    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>{esc(title)} | Lumi Hanoi</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="{robots}">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="icon" href="/favicon.svg?v=20260828" type="image/svg+xml">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="vi_VN">
  <meta property="og:site_name" content="Lumi Hanoi">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:image" content="{esc(hero_image)}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="/assets/css/site.css?v=20260829-type">
  <link rel="stylesheet" href="/assets/css/marketplace.css?v=20260829-detail5">
  <script type="application/ld+json">{schema_json}</script>
</head>
<body class="listing-detail-page">
  <a class="skip-link" href="#main">Bỏ qua điều hướng</a>
  <header class="site-header"><div class="container nav"><a class="brand" href="/" aria-label="Lumi Hanoi – Trang chủ"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="primary-nav">Menu</button><nav id="primary-nav" class="nav-links" data-nav-links data-open="false" aria-label="Điều hướng chính"><a href="/tong-quan-lumi-hanoi/">Tổng quan</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a><details class="nav-dropdown"><summary>Phân khu</summary><div class="nav-dropdown-menu"><a href="/lumi-signature/">Lumi Signature</a><a href="/lumi-prestige/">Lumi Prestige</a><a href="/lumi-elite/">Lumi Elite</a></div></details><a href="/tien-do-lumi-hanoi/">Tiến độ</a><a href="/tin-tuc/">Tin tức</a><details class="nav-dropdown"><summary>Giao dịch</summary><div class="nav-dropdown-menu nav-dropdown-menu--right"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a></div></details></nav></div></header>
  <main id="main" data-static-listing data-listing-slug="{esc(listing.get('slug'))}">
    <div class="container breadcrumb"><a href="/">Trang chủ</a><span aria-hidden="true">/</span><a href="/{segment}/">{action} Lumi Hanoi</a><span aria-hidden="true">/</span>{esc(listing.get('listing_code'))}</div>
    <div class="container detail-shell detail-shell--portal">
      <article class="detail-main">
        <div class="detail-gallery-wrap">{render_gallery(listing)}</div>
        <div class="detail-mobile-summary">
          <div class="detail-mobile-price"><strong>{esc(price)}</strong><span>{esc(price_per_sqm)}</span></div>
          <div class="detail-quickfacts"><span><b>{esc(listing.get('unit_type'))}</b></span><span><b>{esc(area)} m²</b></span><span>Tầng <b>{esc(listing.get('floor_label') or 'Liên hệ')}</b></span></div>
        </div>
        <div class="detail-copy">
          <p class="eyebrow">{esc(listing.get('listing_code'))} · {action}</p>
          <h1>{esc(title)}</h1>
          <div class="detail-location"><strong>Lumi Hanoi</strong><span>Đại lộ Thăng Long, Tây Mỗ, Hà Nội</span></div>
          <div class="marketplace-live-note" data-live-status hidden></div>
          <h2>Mô tả</h2>
          <p class="detail-description">{description_html}</p>
          <h2>Đặc điểm bất động sản</h2>
          <dl class="detail-feature-list">
            <div><dt>Mức giá</dt><dd>{esc(price)}</dd></div>
            <div><dt>Diện tích</dt><dd>{esc(area)} m²</dd></div>
            <div><dt>Loại căn</dt><dd>{esc(listing.get('unit_type'))}</dd></div>
            <div><dt>Tầng</dt><dd>{esc(listing.get('floor_label') or 'Liên hệ')}</dd></div>
            <div><dt>Phân khu</dt><dd>{esc(listing.get('phase'))}</dd></div>
            <div><dt>Tòa</dt><dd>{esc(listing.get('tower'))}</dd></div>
            <div><dt>Nội thất</dt><dd>{esc(listing.get('furnishing') or 'Liên hệ')}</dd></div>
          </dl>
          <h2>Tham khảo thêm</h2>
          <nav class="detail-related" aria-label="Liên kết liên quan">{related_html}</nav>
          <p class="notice"><strong>Lưu ý:</strong> {esc(legal_note)}</p>
        </div>
      </article>
      <aside><div class="detail-panel">
        <p class="eyebrow">{action} Lumi Hanoi</p>
        <strong class="detail-price">{esc(price)}</strong>
        <dl class="detail-specs">
          <div><dt>Phân khu</dt><dd>{esc(listing.get('phase'))}</dd></div>
          <div><dt>Tòa</dt><dd>{esc(listing.get('tower'))}</dd></div>
          <div><dt>Loại căn</dt><dd>{esc(listing.get('unit_type'))}</dd></div>
          <div><dt>Diện tích</dt><dd>{esc(area)} m²</dd></div>
          <div><dt>Tầng</dt><dd>{esc(listing.get('floor_label') or 'Liên hệ')}</dd></div>
          <div><dt>Nội thất</dt><dd>{esc(listing.get('furnishing') or 'Liên hệ')}</dd></div>
        </dl>
        <div class="detail-poster" data-static-poster><span>Người đăng</span><strong>{esc(poster_name)}</strong></div>
        <div class="detail-contact">
          <a class="btn btn-primary" data-static-phone href="tel:{esc(phone_href)}">{esc(phone) or "Gọi người đăng"}</a>
          <a class="btn" data-static-zalo href="{esc(zalo_href)}" target="_blank" rel="noopener"{zalo_hidden}>Nhắn Zalo</a>
        </div>
        <p class="detail-note">Không chuyển tiền chỉ dựa trên nội dung tin đăng hoặc trao đổi qua điện thoại.</p>
      </div></aside>
    </div>
    <div class="detail-mobile-contact">
      <a class="detail-zalo-fab" data-static-zalo href="{esc(zalo_href)}" target="_blank" rel="noopener"{zalo_hidden} aria-label="Nhắn Zalo">Zalo</a>
      <a class="detail-call-bar" data-static-phone href="tel:{esc(phone_href)}">{esc(phone) or "Gọi người đăng"}</a>
    </div>
  </main>
  <footer class="site-footer"><div class="container footer-grid"><div><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><p>Cổng thông tin dự án &amp; thị trường căn hộ.</p></div><div><nav class="footer-links" aria-label="Điều hướng cuối trang"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a><a href="/tin-tuc/">Tin tức</a></nav><p class="disclaimer">Website thông tin và giao dịch độc lập, không phải website chính thức của CapitaLand Development.</p></div></div></footer>
  <script src="/assets/js/site.js" defer></script>
  <script src="/assets/js/marketplace-config.js"></script>
  <script src="/assets/js/marketplace-api.js?v=20260829-poster"></script>
  <script src="/assets/js/marketplace-lightbox.js?v=20260902-fullimage" defer></script>
  <script src="/assets/js/marketplace-static-status.js?v=20260829-detail4" defer></script>
</body>
</html>
"""


def clear_generated() -> None:
    for listing_type in CATEGORY:
        root = ROOT / CATEGORY[listing_type][0]
        if not root.exists():
            continue
        for child in root.iterdir():
            if child.is_dir() and (child / MARKER).is_file():
                shutil.rmtree(child)


def write_pages(listings: list[dict]) -> list[dict]:
    clear_generated()
    generated = []
    for listing in listings:
        listing_type = listing.get("listing_type")
        slug = clean(listing.get("slug"))
        if listing_type not in CATEGORY or not re.fullmatch(r"[a-z0-9-]{8,120}", slug):
            continue
        segment = CATEGORY[listing_type][0]
        target = ROOT / segment / slug
        target.mkdir(parents=True, exist_ok=True)
        (target / MARKER).write_text("Generated by scripts/generate_marketplace_seo.py\n", encoding="utf-8")
        (target / "index.html").write_text(render_page(listing), encoding="utf-8")
        generated.append(listing)
    return generated


def write_sitemap(listings: list[dict]) -> None:
    rows = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for listing in listings:
        if not indexable(listing):
            continue
        loc = SITE + listing_url(listing)
        lastmod = date_only(listing.get("approved_at") or listing.get("created_at"))
        rows.append("  <url>")
        rows.append(f"    <loc>{esc(loc)}</loc>")
        if lastmod:
            rows.append(f"    <lastmod>{lastmod}</lastmod>")
        rows.append("    <changefreq>daily</changefreq>")
        rows.append("    <priority>0.7</priority>")
        rows.append("  </url>")
    rows.append("</urlset>")
    SITEMAP.write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_main_sitemap(listings: list[dict]) -> None:
    if not MAIN_SITEMAP.exists():
        return
    raw = MAIN_SITEMAP.read_text(encoding="utf-8")
    price_loc = SITE + "/gia-can-ho-lumi-hanoi/"
    market_lastmod = latest_market_date(listings)
    if price_loc not in raw:
        price_row = f'  <url><loc>{price_loc}</loc><lastmod>{market_lastmod}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>\n'
        raw = raw.replace("</urlset>", price_row + "</urlset>")
    else:
        raw = re.sub(r'(<loc>https://lumi-hanoi\\.com/gia-can-ho-lumi-hanoi/</loc><lastmod>)\\d{4}-\\d{2}-\\d{2}(</lastmod>)', rf'\\g<1>{market_lastmod}\\2', raw, count=1)
    landing_loc = SITE + "/cho-thue-shop-chan-de-lumi-hanoi/"
    if landing_loc not in raw:
        landing = (
            "  <url><loc>" + landing_loc + "</loc><lastmod>2026-08-30</lastmod>"
            "<changefreq>daily</changefreq><priority>0.9</priority></url>\n"
        )
        raw = raw.replace("</urlset>", landing + "</urlset>")
    dynamic_rows = []
    for listing in listings:
        if not indexable(listing):
            continue
        loc = SITE + listing_url(listing)
        lastmod = date_only(listing.get("approved_at") or listing.get("created_at"))
        dynamic_rows.append("  <url>")
        dynamic_rows.append(f"    <loc>{esc(loc)}</loc>")
        if lastmod:
            dynamic_rows.append(f"    <lastmod>{lastmod}</lastmod>")
        dynamic_rows.append("    <changefreq>daily</changefreq>")
        dynamic_rows.append("    <priority>0.7</priority>")
        dynamic_rows.append("  </url>")
    block = MAIN_SITEMAP_START + "\n" + "\n".join(dynamic_rows) + "\n" + MAIN_SITEMAP_END
    if MAIN_SITEMAP_START in raw and MAIN_SITEMAP_END in raw:
        raw = replace_marked_block(raw, MAIN_SITEMAP_START, MAIN_SITEMAP_END, "\n".join(dynamic_rows))
    else:
        raw = raw.replace("</urlset>", block + "\n</urlset>")
    MAIN_SITEMAP.write_text(raw, encoding="utf-8")


def main() -> None:
    listings = fetch_approved()
    generated = write_pages(listings)
    sync_category_indexes(generated)
    sync_shop_landing(generated)
    sync_market_price_page(generated)
    write_sitemap(generated)
    write_main_sitemap(generated)
    indexed = sum(1 for listing in generated if indexable(listing))
    print(f"Marketplace SEO: generated={len(generated)}, indexable={indexed}")


if __name__ == "__main__":
    main()
