#!/usr/bin/env python3
"""Generate crawlable rental-intent landing pages for Lumi Hanoi.

The pages stay useful even when a category has no live listing: they contain
verified product context, internal links and a clear posting CTA. Approved
marketplace listings are rendered server-side so search engines do not depend
on browser JavaScript to discover the current inventory.
"""
from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "assets/js/marketplace-config.js"
SITE = "https://lumi-hanoi.com"
HUB_PATH = ROOT / "cho-thue-lumi-hanoi" / "index.html"
SITEMAP_PATH = ROOT / "sitemap.xml"
CREATED = "2026-09-04"
CLUSTER_START = "<!-- RENT-SEO-CLUSTER:START -->"
CLUSTER_END = "<!-- RENT-SEO-CLUSTER:END -->"

CATEGORIES = [
    {
        "unit": "1PN",
        "slug": "cho-thue-can-ho-1-phong-ngu-lumi-hanoi",
        "label": "1 phòng ngủ (1PN)",
        "short": "1PN",
        "title": "Cho Thuê Căn Hộ 1PN Lumi Hanoi | Tin Mới {period}",
        "description": "Tin cho thuê căn hộ 1PN Lumi Hanoi đang công khai: xem giá rao, diện tích, tòa, ảnh và liên hệ trực tiếp người đăng. Đăng tin miễn phí.",
        "area": "42,2–54,9 m² NFA trong các layout đã xác minh",
        "context": "Dòng 1BR tại Lumi Hanoi có nhiều cỡ từ Medium tới Extra Large. Khi thuê, nên đối chiếu đúng mã layout, tòa và tầng thay vì chỉ nhìn tổng diện tích.",
        "info_url": "/can-ho-1-phong-ngu-lumi-hanoi/",
        "info_label": "Xem layout căn 1PN",
        "hero": "/assets/media/prestige/lumi-prestige-hero.webp",
    },
    {
        "unit": "2PN",
        "slug": "cho-thue-can-ho-2-phong-ngu-lumi-hanoi",
        "label": "2 phòng ngủ (2PN)",
        "short": "2PN",
        "title": "Cho Thuê Căn Hộ 2PN Lumi Hanoi | Tin Mới {period}",
        "description": "Tin cho thuê căn hộ 2PN Lumi Hanoi đang công khai: xem giá rao, diện tích, tòa, ảnh và liên hệ trực tiếp người đăng. Đăng tin miễn phí.",
        "area": "53,8–85,7 m² NFA trong các layout đã xác minh",
        "context": "Căn 2BR có dải Small, Medium, Large và Extra Large. Số phòng giống nhau nhưng công năng, số khu vệ sinh và diện tích sinh hoạt có thể khác đáng kể.",
        "info_url": "/can-ho-2-phong-ngu-lumi-hanoi/",
        "info_label": "Xem layout căn 2PN",
        "hero": "/assets/media/signature/lumi-signature-landscape.webp",
    },
    {
        "unit": "3PN",
        "slug": "cho-thue-can-ho-3-phong-ngu-lumi-hanoi",
        "label": "3 phòng ngủ (3PN)",
        "short": "3PN",
        "title": "Cho Thuê Căn Hộ 3PN Lumi Hanoi | Tin Mới {period}",
        "description": "Tin cho thuê căn hộ 3PN Lumi Hanoi đang công khai: xem giá rao, diện tích, tòa, ảnh và liên hệ trực tiếp người đăng. Đăng tin miễn phí.",
        "area": "81,3–137,1 m² NFA trong các layout đã xác minh",
        "context": "Căn 3BR có biên độ diện tích rộng từ Small tới Extra Large. Nên kiểm tra mặt bằng tầng, mặt thoáng và cách chia phòng trước khi so sánh hai căn cùng nhãn 3PN.",
        "info_url": "/can-ho-3-phong-ngu-lumi-hanoi/",
        "info_label": "Xem layout căn 3PN",
        "hero": "/assets/media/prestige/lumi-prestige-garden.webp",
    },
    {
        "unit": "4PN",
        "slug": "cho-thue-can-ho-4-phong-ngu-lumi-hanoi",
        "label": "4 phòng ngủ (4PN)",
        "short": "4PN",
        "title": "Cho Thuê Căn Hộ 4PN Lumi Hanoi | Tin Mới {period}",
        "description": "Tin cho thuê căn hộ 4PN Lumi Hanoi đang công khai: xem giá rao, diện tích, tòa, ảnh và liên hệ trực tiếp người đăng. Đăng tin miễn phí.",
        "area": "127,5–136,0 m² NFA cho hai layout 4BR một tầng đã xác minh",
        "context": "4BR một tầng khác Duplex. Tại Lumi Prestige đã xác minh hai cấu hình 4BR Medium và Large; người thuê nên đối chiếu đúng layout và tầng trước khi đặt cọc.",
        "info_url": "/can-ho-4-phong-ngu-lumi-hanoi/",
        "info_label": "Xem layout căn 4PN",
        "hero": "/assets/media/prestige/lumi-prestige-aurora-pool.webp",
    },
    {
        "unit": "Duplex",
        "slug": "cho-thue-duplex-lumi-hanoi",
        "label": "Duplex",
        "short": "Duplex",
        "title": "Cho Thuê Duplex Lumi Hanoi | Tin Mới {period}",
        "description": "Tin cho thuê Duplex Lumi Hanoi đang công khai: xem giá rao, diện tích, tòa, ảnh và liên hệ trực tiếp người đăng. Đối chiếu layout trước khi thuê.",
        "area": "193,2–211,7 m² NFA ở các ví dụ 4BR Duplex Elite đã xác minh",
        "context": "Duplex là căn tổ chức trên hai cao độ có cầu thang nội bộ. Không nên dùng từ Duplex thay cho Penthouse; hai dòng sản phẩm cần được kiểm tra theo đúng hồ sơ tòa và mã căn.",
        "info_url": "/duplex-penthouse-lumi-hanoi/",
        "info_label": "Xem cẩm nang Duplex",
        "hero": "/assets/media/home/lumi-hanoi-streetscape.webp",
    },
    {
        "unit": "Penthouse",
        "slug": "cho-thue-penthouse-lumi-hanoi",
        "label": "Penthouse",
        "short": "Penthouse",
        "title": "Cho Thuê Penthouse Lumi Hanoi | Tin Mới {period}",
        "description": "Tin cho thuê Penthouse Lumi Hanoi đang công khai: xem giá rao, diện tích, tòa, ảnh và liên hệ trực tiếp người đăng. Đối chiếu tầng đỉnh từng tòa.",
        "area": "Cấu hình và diện tích thay đổi theo mã Penthouse và tòa",
        "context": "Penthouse là cấu hình đặc biệt ở tầng trên cùng theo hồ sơ từng tòa. Không mặc định mọi Penthouse đều là Duplex hoặc có cùng sân, tầng và diện tích.",
        "info_url": "/duplex-penthouse-lumi-hanoi/",
        "info_label": "Xem cẩm nang Penthouse",
        "hero": "/assets/media/signature/penthouse/s1-floor-35.webp",
    },
]


def clean(value) -> str:
    return str(value or "").strip()


def esc(value) -> str:
    return html.escape(clean(value), quote=True)


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
        "select": "slug,listing_type,title,description,phase,tower,unit_type,area_sqm,floor_label,price_vnd,approved_at,created_at,listing_images(storage_path,sort_order,alt_text)",
        "status": "eq.approved",
        "listing_type": "eq.rent",
        "order": "is_featured.desc,sort_priority.desc,approved_at.desc",
        "limit": "1000",
    }
    url = f"{base}/rest/v1/listings?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"apikey": key, "Accept": "application/json", "User-Agent": "lumi-hanoi-rent-category-seo/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected Supabase response")
    return payload


def storage_url(path: str) -> str:
    base, _, bucket = read_public_config()
    encoded = "/".join(urllib.parse.quote(part, safe="") for part in clean(path).split("/"))
    return f"{base}/storage/v1/object/public/{urllib.parse.quote(bucket, safe='')}/{encoded}"


def listing_url(listing: dict) -> str:
    return f"/cho-thue-lumi-hanoi/{clean(listing.get('slug'))}/"


def format_area(value) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return (str(int(number)) if number.is_integer() else f"{number:.1f}".replace(".", ",")) + " m²"


def format_price(value) -> str:
    try:
        amount = int(float(value or 0))
    except (TypeError, ValueError):
        amount = 0
    if not amount:
        return "Liên hệ"
    text = f"{amount / 1_000_000:g}".replace(".", ",")
    return f"{text} triệu/tháng"


def compact(value, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", clean(value)).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "…"


def render_card(listing: dict) -> str:
    images = sorted(listing.get("listing_images") or [], key=lambda item: int(item.get("sort_order") or 0))
    href = listing_url(listing)
    if images:
        src = storage_url(images[0].get("storage_path", ""))
        alt = images[0].get("alt_text") or listing.get("title") or "Tin cho thuê Lumi Hanoi"
        media = f'<a class="listing-card-slide" href="{esc(href)}"><img src="{esc(src)}" alt="{esc(alt)}" width="1200" height="900" loading="lazy" decoding="async"></a>'
    else:
        media = f'<a class="listing-card-slide listing-card-placeholder" href="{esc(href)}">{esc(listing.get("unit_type"))} · {esc(listing.get("tower"))}</a>'
    facts = " · ".join(part for part in [format_price(listing.get("price_vnd")), format_area(listing.get("area_sqm")), clean(listing.get("unit_type")), f'Tầng {clean(listing.get("floor_label"))}' if listing.get("floor_label") else ""] if part)
    location = " · ".join(part for part in ["Lumi Hanoi", clean(listing.get("phase")), clean(listing.get("tower"))] if part)
    return (
        '<article class="listing-card listing-card--marketplace" data-static-listing-card>'
        f'<div class="listing-card-media"><div class="listing-card-gallery-track">{media}</div></div>'
        '<div class="listing-card-body"><div class="listing-card-content">'
        f'<h3><a href="{esc(href)}">{esc(listing.get("title"))}</a></h3>'
        f'<div class="listing-card-facts"><strong class="listing-card-fact-price">{esc(facts)}</strong></div>'
        f'<div class="listing-card-location"><span>{esc(location)}</span></div>'
        f'<p class="listing-card-description">{esc(compact(listing.get("description")) or "Xem giá, hình ảnh và thông tin chi tiết của căn đang cho thuê.")}</p>'
        '</div></div></article>'
    )


def iso_date(value) -> str:
    match = re.match(r"(\d{4}-\d{2}-\d{2})", clean(value))
    return match.group(1) if match else ""


def latest_date(rows: list[dict]) -> str:
    values = [iso_date(row.get("approved_at") or row.get("created_at")) for row in rows]
    values = [value for value in values if value]
    return max(values) if values else ""


def modified_date(rows: list[dict], today: date) -> str:
    month_start = today.replace(day=1).isoformat()
    return max([CREATED, month_start, latest_date(rows) or CREATED])


def category_links(current: str) -> str:
    links = []
    for item in CATEGORIES:
        label = item["short"]
        if item["slug"] == current:
            links.append(f'<strong>{esc(label)}</strong>')
        else:
            links.append(f'<a href="/{item["slug"]}/">{esc(label)}</a>')
    links.append('<a href="/cho-thue-shop-chan-de-lumi-hanoi/">Shop chân đế</a>')
    return "".join(links)


def render_page(item: dict, rows: list[dict], today: date) -> str:
    period = f"T{today.month}/{today.year}"
    title = item["title"].format(period=period)
    canonical = f"{SITE}/{item['slug']}/"
    modified = modified_date(rows, today)
    count = len(rows)
    listing_html = "\n".join(render_card(row) for row in rows)
    if not listing_html:
        listing_html = (
            '<div class="marketplace-state" role="status"><span class="marketplace-state-mark" aria-hidden="true">0</span><div>'
            f'<h3>Chưa có tin {esc(item["short"])} đang công khai</h3>'
            '<p>Trang vẫn được giữ để người thuê tra cứu đúng loại căn. Khi có tin được duyệt, danh sách sẽ tự xuất hiện tại đây.</p>'
            '<div class="hero-actions"><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#cho-thue">Đăng tin cho thuê</a><a class="btn" href="/cho-thue-lumi-hanoi/">Xem toàn bộ quỹ thuê</a></div>'
            '</div></div>'
        )
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Cho thuê Lumi Hanoi", "item": SITE + "/cho-thue-lumi-hanoi/"},
                    {"@type": "ListItem", "position": 3, "name": f"Cho thuê {item['short']} Lumi Hanoi", "item": canonical},
                ],
            },
            {
                "@type": "CollectionPage",
                "name": f"Cho thuê {item['label']} Lumi Hanoi",
                "headline": title,
                "description": item["description"],
                "url": canonical,
                "dateModified": modified,
                "inLanguage": "vi-VN",
                "about": [f"Cho thuê {item['short']} Lumi Hanoi", f"Thuê {item['label']} Lumi Hanoi"],
                "isPartOf": {"@type": "WebSite", "name": "Lumi Hanoi", "url": SITE + "/"},
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": f"Hiện có bao nhiêu tin cho thuê {item['short']} Lumi Hanoi?", "acceptedAnswer": {"@type": "Answer", "text": f"Trang đang hiển thị {count} tin {item['short']} đã được duyệt công khai. Số lượng có thể thay đổi khi có tin mới hoặc tin hết hạn."}},
                    {"@type": "Question", "name": f"Nên kiểm tra gì trước khi thuê {item['short']} Lumi Hanoi?", "acceptedAnswer": {"@type": "Answer", "text": "Nên đối chiếu đúng tòa, tầng, layout, diện tích, hiện trạng nội thất, thông tin người cho thuê và điều khoản hợp đồng trước khi đặt cọc."}},
                    {"@type": "Question", "name": "Giá thuê trên trang có phải bảng giá chính thức không?", "acceptedAnswer": {"@type": "Answer", "text": "Không. Giá hiển thị là giá rao từ từng tin đang công khai. Website không tự điền giá ước đoán khi chưa có dữ liệu tin đăng đủ tin cậy."}},
                ],
            },
        ],
    }
    schema_json = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(item['description'])}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="icon" href="/favicon.svg?v=20260828" type="image/svg+xml"><link rel="icon" href="/favicon-32x32.png?v=20260828" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="/apple-touch-icon.png?v=20260828"><link rel="manifest" href="/site.webmanifest">
  <meta name="theme-color" content="#f5f1e8">
  <meta property="og:type" content="website"><meta property="og:locale" content="vi_VN"><meta property="og:site_name" content="Lumi Hanoi"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(item['description'])}"><meta property="og:url" content="{esc(canonical)}"><meta property="og:image" content="{SITE}{esc(item['hero'])}"><meta property="og:image:alt" content="Cho thuê {esc(item['short'])} Lumi Hanoi">
  <meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(item['description'])}"><meta name="twitter:image" content="{SITE}{esc(item['hero'])}">
  <link rel="stylesheet" href="/assets/css/site.css?v=20260829-type"><link rel="stylesheet" href="/assets/css/marketplace.css?v=20260902-mobileux2">
  <script type="application/ld+json">{schema_json}</script>
</head>
<body>
  <a class="skip-link" href="#main">Bỏ qua điều hướng</a>
  <header class="site-header"><div class="container nav"><a class="brand" href="/" aria-label="Lumi Hanoi – Trang chủ"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="primary-nav">Menu</button><nav id="primary-nav" class="nav-links" data-nav-links data-open="false" aria-label="Điều hướng chính"><a href="/tong-quan-lumi-hanoi/">Tổng quan</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a><details class="nav-dropdown"><summary>Phân khu</summary><div class="nav-dropdown-menu"><a href="/lumi-signature/">Lumi Signature</a><a href="/lumi-prestige/">Lumi Prestige</a><a href="/lumi-elite/">Lumi Elite</a></div></details><a href="/tien-do-lumi-hanoi/">Tiến độ</a><a href="/tin-tuc/">Tin tức</a><details class="nav-dropdown"><summary>Giao dịch</summary><div class="nav-dropdown-menu nav-dropdown-menu--right"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/" aria-current="page">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a></div></details></nav></div></header>
  <main id="main">
    <div class="container breadcrumb"><a href="/">Trang chủ</a><span aria-hidden="true">/</span><a href="/cho-thue-lumi-hanoi/">Cho thuê Lumi Hanoi</a><span aria-hidden="true">/</span>{esc(item['short'])}</div>
    <header class="article-hero marketplace-hero"><img class="article-hero-media" src="{esc(item['hero'])}" width="1200" height="800" alt="Cho thuê {esc(item['label'])} Lumi Hanoi" decoding="async"><div class="container"><p class="eyebrow">Quỹ thuê theo loại căn · {period}</p><h1>Cho thuê {esc(item['label'])} Lumi Hanoi</h1><p class="lead">Xem riêng tin {esc(item['short'])} đang cho thuê tại Lumi Hanoi. Giá hiển thị là giá rao của từng tin công khai; mỗi căn dẫn tới URL chi tiết riêng với ảnh và thông tin liên hệ người đăng.</p><div class="hero-actions"><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#cho-thue">Đăng tin cho thuê</a><a class="btn" href="/cho-thue-lumi-hanoi/">Tất cả căn cho thuê</a></div></div></header>

    <section class="marketplace-section" aria-labelledby="category-listings"><div class="container"><div class="marketplace-heading"><div><p class="eyebrow">Tin đang công khai</p><h2 id="category-listings">Căn {esc(item['short'])} Lumi Hanoi đang cho thuê</h2></div><div class="marketplace-actions"><span class="marketplace-count">{count} tin đăng</span><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#cho-thue">+ Đăng tin</a></div></div><div class="listing-grid">{listing_html}</div></div></section>

    <div class="container article-layout reading-shell article-layout--with-sidebar">
      <article class="article">
        <h2>Thuê {esc(item['short'])} Lumi Hanoi: đọc đúng loại căn trước khi xem giá</h2>
        <p>{esc(item['context'])}</p>
        <div class="facts-grid"><div class="fact-card"><strong>{esc(item['short'])}</strong><span>Trang chỉ gom đúng loại căn đang cho thuê</span></div><div class="fact-card"><strong>{esc(item['area'])}</strong><span>Dữ liệu layout tham khảo, không phải quỹ căn đang trống</span></div><div class="fact-card"><strong>{count} tin</strong><span>Số tin đã duyệt đang công khai tại thời điểm đồng bộ</span></div><div class="fact-card"><strong>Giá rao thực tế</strong><span>Không tự điền giá ước đoán khi thiếu dữ liệu</span></div></div>

        <h2>Kiểm tra mặt bằng trước khi thuê</h2>
        <p>Hai căn cùng số phòng có thể khác diện tích, vị trí trên tòa và cách tổ chức công năng. Vì vậy, sau khi thấy một tin phù hợp, nên mở trang layout và mặt bằng tòa để kiểm tra đúng cấu hình trước khi hẹn xem căn.</p>
        <div class="hero-actions"><a class="btn" href="{esc(item['info_url'])}">{esc(item['info_label'])}</a><a class="btn" href="/mat-bang-lumi-hanoi/">Tra cứu mặt bằng tòa</a></div>

        <h2>Giá thuê trên website được hiểu thế nào?</h2>
        <p>Website hiển thị giá rao từ từng tin được duyệt. Đây không phải bảng giá chính thức của chủ đầu tư và không phải cam kết giao dịch. Khi số lượng dữ liệu đủ lớn, trang dữ liệu giá sẽ tổng hợp thống kê từ các tin công khai thay vì tự suy đoán.</p>
        <p><a class="btn" href="/gia-can-ho-lumi-hanoi/">Xem dữ liệu giá Lumi Hanoi</a></p>

        <h2>Các loại căn cho thuê khác</h2>
        <nav class="detail-related" aria-label="Cho thuê Lumi Hanoi theo loại căn">{category_links(item['slug'])}</nav>

        <h2>Câu hỏi thường gặp</h2>
        <h3>Hiện có bao nhiêu tin cho thuê {esc(item['short'])} Lumi Hanoi?</h3><p>Trang đang hiển thị <strong>{count} tin</strong> đã được duyệt công khai. Số lượng thay đổi khi có tin mới hoặc tin hết hạn.</p>
        <h3>Có nên đặt cọc chỉ dựa trên tin đăng?</h3><p>Không. Trước khi đặt cọc cần kiểm tra người có quyền cho thuê, hiện trạng căn, điều khoản hợp đồng và các chi phí liên quan. Tin đăng là nguồn thông tin ban đầu để liên hệ và sàng lọc.</p>
      </article>
      <aside><div class="toc"><strong>Đi nhanh</strong><a href="#category-listings">Tin {esc(item['short'])} đang cho thuê</a><a href="{esc(item['info_url'])}">Layout {esc(item['short'])}</a><a href="/gia-can-ho-lumi-hanoi/">Dữ liệu giá</a><a href="/dang-tin-lumi-hanoi/#cho-thue">Đăng tin miễn phí</a></div></aside>
    </div>
  </main>
  <footer class="site-footer"><div class="container footer-grid"><div><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><p>Cổng thông tin dự án &amp; thị trường căn hộ.</p></div><div><nav class="footer-links" aria-label="Điều hướng cuối trang"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a><a href="/tin-tuc/">Tin tức</a></nav><p class="disclaimer">Website thông tin và giao dịch độc lập, không phải website chính thức của CapitaLand Development.</p></div></div></footer>
  <script src="/assets/js/site.js" defer></script>
</body>
</html>
"""


def sync_categories(listings: list[dict], today: date) -> dict[str, str]:
    modified: dict[str, str] = {}
    for item in CATEGORIES:
        rows = [row for row in listings if clean(row.get("unit_type")) == item["unit"]]
        target = ROOT / item["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        new = render_page(item, rows, today)
        old = target.read_text(encoding="utf-8") if target.exists() else ""
        if old != new:
            target.write_text(new, encoding="utf-8")
        modified[item["slug"]] = modified_date(rows, today)
    return modified


def cluster_html(listings: list[dict]) -> str:
    cards = []
    for item in CATEGORIES:
        count = sum(1 for row in listings if clean(row.get("unit_type")) == item["unit"])
        cards.append(f'<div class="fact-card"><strong><a href="/{item["slug"]}/">Cho thuê {esc(item["short"])} Lumi Hanoi</a></strong><span>{count} tin đang công khai · xem riêng đúng loại căn</span></div>')
    shop_count = sum(1 for row in listings if clean(row.get("unit_type")).lower() == "shop chân đế")
    cards.append(f'<div class="fact-card"><strong><a href="/cho-thue-shop-chan-de-lumi-hanoi/">Cho thuê Shop chân đế</a></strong><span>{shop_count} tin shop đang công khai</span></div>')
    return (
        f'{CLUSTER_START}\n<section class="section" aria-labelledby="rent-type-title"><div class="container"><div class="section-heading"><p class="eyebrow">Tìm đúng nhu cầu</p><h2 id="rent-type-title">Cho thuê Lumi Hanoi theo loại căn</h2><p>Đi thẳng vào trang 1PN, 2PN, 3PN, 4PN, Duplex, Penthouse hoặc Shop. Mỗi trang vẫn có nội dung tra cứu hữu ích ngay cả khi chưa có tin mới.</p></div><div class="facts-grid">'
        + "".join(cards)
        + f'</div></div></section>\n{CLUSTER_END}'
    )


def replace_meta(raw: str, pattern: str, replacement: str) -> str:
    return re.sub(pattern, replacement, raw, count=1, flags=re.S)


def sync_hub(listings: list[dict], today: date) -> str:
    if not HUB_PATH.exists():
        return CREATED
    raw = HUB_PATH.read_text(encoding="utf-8")
    period = f"T{today.month}/{today.year}"
    title = f"Cho Thuê Căn Hộ Lumi Hanoi | Tin Mới {period}"
    description = "Cho thuê căn hộ Lumi Hanoi: quỹ căn 1PN, 2PN, 3PN, 4PN, Duplex, Penthouse và shop chân đế. Xem giá rao, ảnh và liên hệ trực tiếp người đăng."
    raw = replace_meta(raw, r"<title>.*?</title>", f"<title>{title}</title>")
    raw = replace_meta(raw, r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{description}">')
    raw = replace_meta(raw, r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{title}">')
    raw = replace_meta(raw, r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{description}">')
    raw = replace_meta(raw, r'<meta name="twitter:title" content="[^"]*">', f'<meta name="twitter:title" content="{title}">')
    raw = replace_meta(raw, r'<meta name="twitter:description" content="[^"]*">', f'<meta name="twitter:description" content="{description}">')
    raw = re.sub(r'"headline":"[^"]*"', f'"headline":"{title}"', raw, count=1)
    hub_modified = modified_date(listings, today)
    raw = re.sub(r'"dateModified":"\d{4}-\d{2}-\d{2}"', f'"dateModified":"{hub_modified}"', raw, count=1)
    block = cluster_html(listings)
    if CLUSTER_START in raw and CLUSTER_END in raw:
        raw = re.sub(re.escape(CLUSTER_START) + r".*?" + re.escape(CLUSTER_END), block, raw, count=1, flags=re.S)
    else:
        anchor = '<div class="container article-layout reading-shell article-layout--with-sidebar">'
        if anchor not in raw:
            raise RuntimeError("Could not locate rental hub content anchor")
        raw = raw.replace(anchor, block + "\n" + anchor, 1)
    HUB_PATH.write_text(raw, encoding="utf-8")
    return hub_modified


def sitemap_lastmod(raw: str, loc: str) -> str:
    match = re.search(rf'<loc>{re.escape(loc)}</loc><lastmod>(\d{{4}}-\d{{2}}-\d{{2}})</lastmod>', raw)
    return match.group(1) if match else ""


def upsert_sitemap_row(raw: str, loc: str, lastmod: str, priority: str = "0.9") -> str:
    row = f'  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod><changefreq>daily</changefreq><priority>{priority}</priority></url>'
    pattern = rf'\s*<url><loc>{re.escape(loc)}</loc>.*?</url>'
    if re.search(pattern, raw, flags=re.S):
        return re.sub(pattern, "\n" + row, raw, count=1, flags=re.S)
    return raw.replace("</urlset>", row + "\n</urlset>")


def sync_sitemap(category_modified: dict[str, str], hub_modified: str) -> None:
    if not SITEMAP_PATH.exists():
        return
    raw = SITEMAP_PATH.read_text(encoding="utf-8")
    raw = upsert_sitemap_row(raw, SITE + "/cho-thue-lumi-hanoi/", hub_modified, "0.9")
    for item in CATEGORIES:
        loc = f"{SITE}/{item['slug']}/"
        lastmod = category_modified[item["slug"]] or sitemap_lastmod(raw, loc) or CREATED
        raw = upsert_sitemap_row(raw, loc, lastmod, "0.9")
    SITEMAP_PATH.write_text(raw, encoding="utf-8")


def main() -> None:
    today = date.today()
    listings = fetch_approved()
    category_modified = sync_categories(listings, today)
    hub_modified = sync_hub(listings, today)
    sync_sitemap(category_modified, hub_modified)
    counts = {item["unit"]: sum(1 for row in listings if clean(row.get("unit_type")) == item["unit"]) for item in CATEGORIES}
    print("Rental SEO cluster synced:", counts)


if __name__ == "__main__":
    main()
