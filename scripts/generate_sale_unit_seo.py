#!/usr/bin/env python3
"""Generate controlled sale-intent pages for 1PN, 2PN and 3PN Lumi Hanoi."""
from __future__ import annotations

import json
import re
from datetime import date
from statistics import mean

import generate_marketplace_seo as gen

SITE = gen.SITE
HUB = gen.ROOT / "mua-ban-lumi-hanoi" / "index.html"
SITEMAP = gen.ROOT / "sitemap.xml"
INDEX_THRESHOLD = 2
CLUSTER_START = "<!-- SALE-UNIT-CLUSTER:START -->"
CLUSTER_END = "<!-- SALE-UNIT-CLUSTER:END -->"

UNITS = (
    {
        "unit": "1PN",
        "slug": "mua-ban-can-ho-1-phong-ngu-lumi-hanoi",
        "info_url": "/can-ho-1-phong-ngu-lumi-hanoi/",
        "hero": "/assets/media/signature/lumi-signature-landscape.webp",
        "context": "Căn 1PN phù hợp khi người mua ưu tiên diện tích gọn và tổng giá dễ tiếp cận hơn. Trước khi so giá, cần đối chiếu đúng tòa, tầng, diện tích và layout của từng căn.",
    },
    {
        "unit": "2PN",
        "slug": "mua-ban-can-ho-2-phong-ngu-lumi-hanoi",
        "info_url": "/can-ho-2-phong-ngu-lumi-hanoi/",
        "hero": "/assets/media/prestige/lumi-prestige-hero.webp",
        "context": "Căn 2PN có nhiều cấu hình diện tích và layout. Hai căn cùng nhãn 2PN vẫn có thể khác đáng kể về công năng, vị trí trên mặt bằng tầng và giá chào theo m².",
    },
    {
        "unit": "3PN",
        "slug": "mua-ban-can-ho-3-phong-ngu-lumi-hanoi",
        "info_url": "/can-ho-3-phong-ngu-lumi-hanoi/",
        "hero": "/assets/media/prestige/lumi-prestige-garden.webp",
        "context": "Căn 3PN có biên độ diện tích rộng hơn, nên giá tổng không đủ để so sánh. Cần đọc thêm đơn giá/m², tòa, tầng, mặt bằng và layout trước khi đánh giá mức chào.",
    },
)

TOWERS = ("S1", "S2", "S3", "S5", "S6", "P1", "P2", "E1", "E2")


def unit_rows(listings: list[dict], unit: str) -> list[dict]:
    rows = []
    for listing in listings:
        if listing.get("listing_type") != "sale":
            continue
        if gen.clean(listing.get("unit_type")) != unit:
            continue
        if not gen.clean(listing.get("slug")):
            continue
        rows.append(listing)
    return sorted(rows, key=lambda row: (row.get("approved_at") or "", row.get("created_at") or "", row.get("id") or ""), reverse=True)


def latest_date(rows: list[dict], today: date) -> str:
    values = [gen.date_only(row.get("approved_at") or row.get("created_at")) for row in rows]
    values = [value for value in values if value]
    return max(values) if values else today.replace(day=1).isoformat()


def average_price(rows: list[dict]) -> str:
    values = [gen.numeric(row.get("price_vnd")) for row in rows]
    values = [value for value in values if value]
    return gen.format_market_price(mean(values), "sale") if values else "Chưa đủ dữ liệu"


def average_ppsm(rows: list[dict]) -> str:
    values = []
    for row in rows:
        price = gen.numeric(row.get("price_vnd"))
        area = gen.numeric(row.get("area_sqm"))
        if price and area:
            values.append(price / area)
    return gen.format_market_ppsm(mean(values), "sale") if values else "Chưa đủ dữ liệu"


def tower_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        tower = gen.clean(row.get("tower")).upper()
        if tower in TOWERS:
            counts[tower] = counts.get(tower, 0) + 1
    return counts


def sale_tower_url(tower: str) -> str:
    return f"/mua-ban-toa-{tower.lower()}-lumi-hanoi/"


def tower_distribution(rows: list[dict]) -> str:
    counts = tower_counts(rows)
    if not counts:
        return '<p class="notice">Chưa có đủ quỹ căn công khai để phân bổ theo tòa.</p>'
    cards = []
    for tower in TOWERS:
        count = counts.get(tower, 0)
        if not count:
            continue
        cards.append(
            '<div class="fact-card">'
            f'<strong>{tower} · {count} căn</strong>'
            f'<span><a href="{sale_tower_url(tower)}">Quỹ bán {tower}</a> · '
            f'<a href="{gen.tower_link(tower)}">Mặt bằng {tower}</a> · '
            f'<a href="/gia-can-ho-lumi-hanoi/#market-index-{tower.lower()}">Market Index</a></span>'
            '</div>'
        )
    return '<div class="facts-grid">' + "".join(cards) + '</div>'


def sibling_links(current_slug: str) -> str:
    links = []
    for item in UNITS:
        if item["slug"] != current_slug:
            links.append(f'<a href="/{item["slug"]}/">Mua bán căn {item["unit"]}</a>')
    links.append('<a href="/mua-ban-lumi-hanoi/">Toàn bộ quỹ mua bán</a>')
    return "".join(links)


def render_page(item: dict, rows: list[dict], today: date) -> str:
    unit = item["unit"]
    count = len(rows)
    period = f"T{today.month}/{today.year}"
    canonical = f"{SITE}/{item['slug']}/"
    indexable = count >= INDEX_THRESHOLD
    robots = "index,follow,max-image-preview:large" if indexable else "noindex,follow,max-image-preview:large"
    title = f"Mua Bán Căn Hộ {unit} Lumi Hanoi | Giá & Quỹ Căn {period}"
    description = f"Mua bán căn hộ {unit} Lumi Hanoi: {count} căn đang công khai. Xem giá chào, giá/m², tòa, diện tích, mặt bằng, hình ảnh và liên hệ trực tiếp người đăng."
    modified = latest_date(rows, today)
    listing_html = "\n".join(gen.render_static_card(row) for row in rows[:12])
    if not listing_html:
        listing_html = f'<div class="marketplace-state" role="status"><strong>Chưa có căn {unit} đang bán.</strong><p>Khi tin mới được duyệt, quỹ căn sẽ tự xuất hiện. Trang chưa đủ dữ liệu không được đưa vào chỉ mục Google.</p></div>'

    graph = [
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Mua bán Lumi Hanoi", "item": SITE + "/mua-ban-lumi-hanoi/"},
                {"@type": "ListItem", "position": 3, "name": f"Mua bán căn {unit}", "item": canonical},
            ],
        },
        {
            "@type": "CollectionPage",
            "name": f"Mua bán căn hộ {unit} Lumi Hanoi",
            "headline": title,
            "description": description,
            "url": canonical,
            "dateModified": modified,
            "inLanguage": "vi-VN",
            "about": [f"Mua bán căn {unit} Lumi Hanoi", f"Giá căn {unit} Lumi Hanoi", f"Căn hộ {unit} Lumi Hanoi"],
            "isPartOf": {"@type": "WebSite", "name": "Lumi Hanoi", "url": SITE + "/"},
        },
    ]
    if rows:
        graph.append({
            "@type": "ItemList",
            "numberOfItems": min(count, 12),
            "itemListElement": [
                {"@type": "ListItem", "position": idx + 1, "url": SITE + gen.listing_url(row), "name": gen.compact_text(row.get("title", ""))}
                for idx, row in enumerate(rows[:12])
            ],
        })
    schema = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    counts = tower_counts(rows)
    towers_text = " · ".join(f"{tower}: {count}" for tower, count in counts.items()) if counts else "Chưa có quỹ căn"
    status = f"Trang đang index vì có {count} căn {unit} bán công khai." if indexable else f"Hiện có {count} căn {unit}; trang tạm noindex cho đến khi có ít nhất {INDEX_THRESHOLD} căn bán công khai."

    return f'''<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{gen.esc(title)}</title>
<meta name="description" content="{gen.esc(description)}"><meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}"><link rel="icon" href="/favicon.svg?v=20260828" type="image/svg+xml"><meta name="theme-color" content="#f5f1e8">
<meta property="og:type" content="website"><meta property="og:locale" content="vi_VN"><meta property="og:site_name" content="Lumi Hanoi"><meta property="og:title" content="{gen.esc(title)}"><meta property="og:description" content="{gen.esc(description)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{SITE}{item['hero']}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{gen.esc(title)}"><meta name="twitter:description" content="{gen.esc(description)}"><meta name="twitter:image" content="{SITE}{item['hero']}">
<link rel="stylesheet" href="/assets/css/site.css?v=20260907-layoutfix1"><link rel="stylesheet" href="/assets/css/marketplace.css?v=20260902-mobileux2">
<script type="application/ld+json">{schema}</script>
</head>
<body class="marketplace-discovery">
<a class="skip-link" href="#main">Bỏ qua điều hướng</a>
<header class="site-header"><div class="container nav"><a class="brand" href="/" aria-label="Lumi Hanoi – Trang chủ"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="primary-nav">Menu</button><nav id="primary-nav" class="nav-links" data-nav-links data-open="false" aria-label="Điều hướng chính"><a href="/tong-quan-lumi-hanoi/">Tổng quan</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a><details class="nav-dropdown"><summary>Phân khu</summary><div class="nav-dropdown-menu"><a href="/lumi-signature/">Lumi Signature</a><a href="/lumi-prestige/">Lumi Prestige</a><a href="/lumi-elite/">Lumi Elite</a></div></details><a href="/tien-do-lumi-hanoi/">Tiến độ</a><a href="/tin-tuc/">Tin tức</a><details class="nav-dropdown"><summary>Giao dịch</summary><div class="nav-dropdown-menu nav-dropdown-menu--right"><a href="/mua-ban-lumi-hanoi/" aria-current="page">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a></div></details></nav></div></header>
<main id="main">
<div class="container breadcrumb"><a href="/">Trang chủ</a><span aria-hidden="true">/</span><a href="/mua-ban-lumi-hanoi/">Mua bán Lumi Hanoi</a><span aria-hidden="true">/</span>Căn {unit}</div>
<header class="article-hero marketplace-hero"><img class="article-hero-media" src="{item['hero']}" alt="Mua bán căn {unit} Lumi Hanoi" width="1600" height="900" decoding="async"><div class="container"><p class="eyebrow">Quỹ mua bán theo loại căn · {period}</p><h1>Mua bán căn hộ {unit} Lumi Hanoi</h1><p class="lead">{gen.esc(item['context'])}</p><div class="hero-actions"><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#mua-ban">Đăng tin căn {unit}</a><a class="btn" href="{item['info_url']}">Xem layout {unit}</a></div></div></header>
<section class="marketplace-section" aria-labelledby="unit-sale-listings"><div class="container"><div class="marketplace-heading"><div><p class="eyebrow">Tin đã duyệt đang công khai</p><h2 id="unit-sale-listings">Căn {unit} đang bán</h2></div><div class="marketplace-actions"><span class="marketplace-count">{count} tin đăng</span><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#mua-ban">+ Đăng tin</a></div></div><div class="listing-grid">{listing_html}</div></div></section>
<div class="container article-layout reading-shell article-layout--with-sidebar"><article class="article">
<h2>Giá chào căn {unit} Lumi Hanoi</h2><p>Hệ thống hiện ghi nhận <strong>{count} căn {unit}</strong> bán/chuyển nhượng đã duyệt. Giá chào trung bình là <strong>{gen.esc(average_price(rows))}</strong>; đơn giá chào trung bình từ các tin đủ giá và diện tích là <strong>{gen.esc(average_ppsm(rows))}</strong>. Đây là dữ liệu giá rao, không phải giá giao dịch công chứng.</p>
<div class="facts-grid"><div class="fact-card"><strong>{count} tin</strong><span>Quỹ căn {unit} đang công khai</span></div><div class="fact-card"><strong>{gen.esc(average_price(rows))}</strong><span>Giá chào trung bình</span></div><div class="fact-card"><strong>{gen.esc(average_ppsm(rows))}</strong><span>Đơn giá chào trung bình</span></div></div>
<h2>Căn {unit} đang nằm ở tòa nào?</h2><p>{gen.esc(towers_text)}. Mở đúng quỹ bán và mặt bằng từng tòa trước khi so hai căn cùng loại.</p>{tower_distribution(rows)}
<h2>Đối chiếu layout trước khi so giá</h2><p>Cùng nhãn {unit} nhưng diện tích và cách tổ chức không gian có thể khác. Xem thư viện layout để xác định đúng sản phẩm, sau đó đối chiếu Market Index theo tòa.</p><nav class="detail-related" aria-label="Tra cứu căn {unit}"><a href="{item['info_url']}">Layout căn {unit}</a><a href="/gia-can-ho-lumi-hanoi/">Lumi Hanoi Market Index</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng 9 tòa</a></nav>
<h2>Các loại căn mua bán khác</h2><nav class="detail-related" aria-label="Mua bán theo loại căn">{sibling_links(item['slug'])}</nav>
<h2>Chính sách index dữ liệu</h2><p>{gen.esc(status)} Ngưỡng này giúp Google tập trung vào landing có quỹ hàng thật thay vì index các trang lọc mỏng.</p>
</article><aside><div class="toc"><strong>Đi nhanh</strong><a href="#unit-sale-listings">Căn đang bán</a><a href="{item['info_url']}">Layout {unit}</a><a href="/gia-can-ho-lumi-hanoi/">Market Index</a><a href="/mua-ban-lumi-hanoi/">Quỹ bán tổng</a><a href="/dang-tin-lumi-hanoi/#mua-ban">Đăng tin</a></div></aside></div>
</main>
<footer class="site-footer"><div class="container footer-grid"><div><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><p>Cổng thông tin dự án &amp; thị trường căn hộ.</p></div><div><nav class="footer-links" aria-label="Điều hướng cuối trang"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a></nav><p class="disclaimer">Website thông tin và giao dịch độc lập, không phải website chính thức của CapitaLand Development.</p></div></div></footer>
<script src="/assets/js/site.js?v=20260907-performance1" defer></script>
</body></html>'''


def replace_marked(raw: str, start: str, end: str, body: str) -> str:
    block = start + "\n" + body.strip() + "\n" + end
    if start in raw and end in raw:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, raw, count=1, flags=re.S)
    return raw


def sync_hub(rows_by_unit: dict[str, list[dict]]) -> None:
    raw = HUB.read_text(encoding="utf-8")
    cards = []
    for item in UNITS:
        count = len(rows_by_unit[item["unit"]])
        cards.append(f'<a class="fact-card" href="/{item["slug"]}/"><strong>Căn {item["unit"]}</strong><span>{count} căn bán đang công khai · xem giá, tòa và layout</span></a>')
    body = '<section class="section sale-unit-cluster" aria-labelledby="sale-unit-title"><div class="container"><div class="section-heading"><div><p class="eyebrow">Mua bán theo loại căn</p><h2 id="sale-unit-title">Chọn 1PN, 2PN hoặc 3PN</h2></div><p>Đi từ loại căn → tòa → mặt bằng → giá chào → tin chi tiết để so đúng sản phẩm.</p></div><div class="facts-grid">' + "".join(cards) + '</div></div></section>'
    block = CLUSTER_START + "\n" + body + "\n" + CLUSTER_END
    if CLUSTER_START in raw and CLUSTER_END in raw:
        raw = replace_marked(raw, CLUSTER_START, CLUSTER_END, body)
    else:
        anchor = '<section id="quy-can"'
        pos = raw.find(anchor)
        if pos < 0:
            raise RuntimeError("Could not locate sale inventory section in hub")
        raw = raw[:pos] + block + "\n" + raw[pos:]
    HUB.write_text(raw, encoding="utf-8")


def sync_sitemap(rows_by_unit: dict[str, list[dict]], today: date) -> None:
    raw = SITEMAP.read_text(encoding="utf-8")
    for item in UNITS:
        url = f"{SITE}/{item['slug']}/"
        raw = re.sub(rf"\s*<url>\s*<loc>{re.escape(url)}</loc>.*?</url>", "", raw, flags=re.S)
    insertions = []
    for item in UNITS:
        rows = rows_by_unit[item["unit"]]
        if len(rows) < INDEX_THRESHOLD:
            continue
        url = f"{SITE}/{item['slug']}/"
        insertions.append(f"  <url><loc>{url}</loc><lastmod>{latest_date(rows, today)}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>")
    if insertions:
        raw = raw.replace("</urlset>", "\n" + "\n".join(insertions) + "\n</urlset>", 1)
    SITEMAP.write_text(raw.rstrip() + "\n", encoding="utf-8")


def detail_unit(raw: str) -> str:
    match = re.search(r"<(?:dd|b)\s+data-detail-unit>([^<]+)</(?:dd|b)>", raw, flags=re.I)
    return gen.clean(match.group(1)) if match else ""


def update_sale_detail_links() -> int:
    unit_urls = {item["unit"]: f"/{item['slug']}/" for item in UNITS}
    root = gen.ROOT / "mua-ban-lumi-hanoi"
    updated = 0
    if not root.is_dir():
        return 0
    for marker in root.rglob(gen.MARKER):
        page = marker.parent / "index.html"
        if not page.is_file():
            continue
        raw = page.read_text(encoding="utf-8")
        target = unit_urls.get(detail_unit(raw))
        if not target:
            continue
        new = re.sub(r'(<a\s+data-detail-same-unit\s+href=")[^"]+("[^>]*>)', lambda match: match.group(1) + target + match.group(2), raw, count=1, flags=re.I)
        if new != raw:
            page.write_text(new, encoding="utf-8")
            updated += 1
    return updated


def main() -> None:
    today = date.today()
    listings = gen.fetch_approved()
    rows_by_unit = {item["unit"]: unit_rows(listings, item["unit"]) for item in UNITS}
    for item in UNITS:
        target = gen.ROOT / item["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_page(item, rows_by_unit[item["unit"]], today), encoding="utf-8")
    sync_hub(rows_by_unit)
    sync_sitemap(rows_by_unit, today)
    details = update_sale_detail_links()
    summary = ", ".join(f"{item['unit']}={len(rows_by_unit[item['unit']])}" for item in UNITS)
    print(f"Sale unit SEO generated: {summary}; index threshold={INDEX_THRESHOLD}; detail links updated={details}")


if __name__ == "__main__":
    main()
