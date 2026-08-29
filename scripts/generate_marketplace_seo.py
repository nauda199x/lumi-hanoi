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

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "assets/js/marketplace-config.js"
SITE = "https://lumi-hanoi.com"
MARKER = ".marketplace-generated"
SITEMAP = ROOT / "sitemap-tin-dang.xml"

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
            "id,slug,listing_code,listing_type,title,description,phase,tower,"
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
            len(compact_text(listing.get("title", ""))) >= 20,
            len(compact_text(listing.get("description", ""))) >= 120,
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
            f'<figure><img src="{esc(src)}" alt="{esc(alt)}" loading="{loading}" decoding="async"></figure>'
        )
    return '<div class="detail-gallery">' + "".join(figures) + "</div>"


def render_page(listing: dict) -> str:
    segment, action = CATEGORY[listing["listing_type"]]
    rel_url = listing_url(listing)
    canonical = SITE + rel_url
    title = compact_text(listing.get("title", "Tin căn hộ Lumi Hanoi"))
    description = meta_description(listing)
    robots = "index,follow,max-image-preview:large" if indexable(listing) else "noindex,follow"
    images = sorted(listing.get("listing_images") or [], key=lambda item: int(item.get("sort_order") or 0))
    hero_image = storage_url(images[0]["storage_path"]) if images else SITE + "/assets/media/og/lumi-hanoi-og.webp"
    phone = clean(listing.get("contact_phone"))
    phone_href = re.sub(r"[^+\d]", "", phone)
    zalo_number = re.sub(r"\D", "", phone)
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
    zalo_html = (
        f'<a class="btn" href="https://zalo.me/{esc(zalo_number)}" target="_blank" rel="noopener">Nhắn Zalo</a>'
        if zalo_number else ""
    )
    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
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
  <link rel="stylesheet" href="/assets/css/marketplace.css?v=20260829-seo">
  <script type="application/ld+json">{schema_json}</script>
</head>
<body>
  <a class="skip-link" href="#main">Bỏ qua điều hướng</a>
  <header class="site-header"><div class="container nav"><a class="brand" href="/" aria-label="Lumi Hanoi – Trang chủ"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="primary-nav">Menu</button><nav id="primary-nav" class="nav-links" data-nav-links data-open="false" aria-label="Điều hướng chính"><a href="/tong-quan-lumi-hanoi/">Tổng quan</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a><details class="nav-dropdown"><summary>Phân khu</summary><div class="nav-dropdown-menu"><a href="/lumi-signature/">Lumi Signature</a><a href="/lumi-prestige/">Lumi Prestige</a><a href="/lumi-elite/">Lumi Elite</a></div></details><a href="/tien-do-lumi-hanoi/">Tiến độ</a><a href="/tin-tuc/">Tin tức</a><details class="nav-dropdown"><summary>Giao dịch</summary><div class="nav-dropdown-menu nav-dropdown-menu--right"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a></div></details></nav></div></header>
  <main id="main" data-static-listing data-listing-slug="{esc(listing.get('slug'))}">
    <div class="container breadcrumb"><a href="/">Trang chủ</a><span aria-hidden="true">/</span><a href="/{segment}/">{action} Lumi Hanoi</a><span aria-hidden="true">/</span>{esc(listing.get('listing_code'))}</div>
    <div class="container detail-shell">
      <article>
        {render_gallery(listing)}
        <div class="detail-copy">
          <p class="eyebrow">{esc(listing.get('listing_code'))} · {action}</p>
          <h1>{esc(title)}</h1>
          <div class="marketplace-live-note" data-live-status hidden></div>
          <h2>Thông tin căn hộ</h2>
          <p>{description_html}</p>
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
        <div class="detail-contact">
          <a class="btn btn-primary" href="tel:{esc(phone_href)}">{esc(phone) or 'Gọi người đăng'}</a>
          {zalo_html}
        </div>
        <p class="detail-note">Không chuyển tiền chỉ dựa trên nội dung tin đăng hoặc trao đổi qua điện thoại.</p>
      </div></aside>
    </div>
  </main>
  <footer class="site-footer"><div class="container footer-grid"><div><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><p>Cổng thông tin dự án &amp; thị trường căn hộ.</p></div><div><nav class="footer-links" aria-label="Điều hướng cuối trang"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a><a href="/tin-tuc/">Tin tức</a></nav><p class="disclaimer">Website thông tin và giao dịch độc lập, không phải website chính thức của CapitaLand Development.</p></div></div></footer>
  <script src="/assets/js/site.js" defer></script>
  <script src="/assets/js/marketplace-config.js"></script>
  <script src="/assets/js/marketplace-api.js?v=20260829-seo"></script>
  <script src="/assets/js/marketplace-static-status.js?v=20260829-seo" defer></script>
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


def main() -> None:
    listings = fetch_approved()
    generated = write_pages(listings)
    write_sitemap(generated)
    indexed = sum(1 for listing in generated if indexable(listing))
    print(f"Marketplace SEO: generated={len(generated)}, indexable={indexed}")


if __name__ == "__main__":
    main()
