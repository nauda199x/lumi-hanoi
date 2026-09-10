#!/usr/bin/env python3
"""Generate controlled sale-intent landing pages for individual Lumi Hanoi towers.

All nine tower URLs are maintained for navigation, but a tower page becomes
indexable and enters the sitemap only when at least two approved apartment sale
listings are public. This creates a finite, inventory-backed commercial layer
between phase pages, floor plans and individual marketplace listings without
opening faceted/filter crawl traps.
"""
from __future__ import annotations

import json
import re
from datetime import date
from statistics import mean

import generate_marketplace_seo as gen

SITE = gen.SITE
SITEMAP = gen.ROOT / "sitemap.xml"
INDEX_THRESHOLD = 2
CLUSTER_START = "<!-- SALE-TOWER-CLUSTER:START -->"
CLUSTER_END = "<!-- SALE-TOWER-CLUSTER:END -->"

TOWERS = (
    {"tower": "S1", "phase": "Signature", "phase_name": "Lumi Signature", "phase_slug": "mua-ban-lumi-signature", "slug": "mua-ban-toa-s1-lumi-hanoi", "hero": "/assets/media/signature/lumi-signature-landscape.webp"},
    {"tower": "S2", "phase": "Signature", "phase_name": "Lumi Signature", "phase_slug": "mua-ban-lumi-signature", "slug": "mua-ban-toa-s2-lumi-hanoi", "hero": "/assets/media/signature/lumi-signature-landscape.webp"},
    {"tower": "S3", "phase": "Signature", "phase_name": "Lumi Signature", "phase_slug": "mua-ban-lumi-signature", "slug": "mua-ban-toa-s3-lumi-hanoi", "hero": "/assets/media/signature/lumi-signature-landscape.webp"},
    {"tower": "S5", "phase": "Signature", "phase_name": "Lumi Signature", "phase_slug": "mua-ban-lumi-signature", "slug": "mua-ban-toa-s5-lumi-hanoi", "hero": "/assets/media/signature/lumi-signature-landscape.webp"},
    {"tower": "S6", "phase": "Signature", "phase_name": "Lumi Signature", "phase_slug": "mua-ban-lumi-signature", "slug": "mua-ban-toa-s6-lumi-hanoi", "hero": "/assets/media/signature/lumi-signature-landscape.webp"},
    {"tower": "P1", "phase": "Prestige", "phase_name": "Lumi Prestige", "phase_slug": "mua-ban-lumi-prestige", "slug": "mua-ban-toa-p1-lumi-hanoi", "hero": "/assets/media/prestige/lumi-prestige-hero.webp"},
    {"tower": "P2", "phase": "Prestige", "phase_name": "Lumi Prestige", "phase_slug": "mua-ban-lumi-prestige", "slug": "mua-ban-toa-p2-lumi-hanoi", "hero": "/assets/media/prestige/lumi-prestige-hero.webp"},
    {"tower": "E1", "phase": "Elite", "phase_name": "Lumi Elite", "phase_slug": "mua-ban-lumi-elite", "slug": "mua-ban-toa-e1-lumi-hanoi", "hero": "/assets/media/home/lumi-hanoi-streetscape.webp"},
    {"tower": "E2", "phase": "Elite", "phase_name": "Lumi Elite", "phase_slug": "mua-ban-lumi-elite", "slug": "mua-ban-toa-e2-lumi-hanoi", "hero": "/assets/media/home/lumi-hanoi-streetscape.webp"},
)


def current_period(today: date) -> str:
    return f"T{today.month}/{today.year}"


def tower_rows(listings: list[dict], tower: str) -> list[dict]:
    rows = []
    for listing in listings:
        if listing.get("listing_type") != "sale":
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
        key=lambda row: (row.get("approved_at") or "", row.get("created_at") or "", row.get("id") or ""),
        reverse=True,
    )


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


def unit_mix(rows: list[dict]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        unit = gen.clean(row.get("unit_type"))
        if unit:
            counts[unit] = counts.get(unit, 0) + 1
    if not counts:
        return "Chưa có quỹ căn công khai"
    return " · ".join(f"{unit}: {count}" for unit, count in sorted(counts.items()))


def unit_links(rows: list[dict]) -> str:
    seen = []
    for row in rows:
        unit = gen.clean(row.get("unit_type"))
        if unit and unit not in seen and unit in gen.UNIT_LINKS:
            seen.append(unit)
    if not seen:
        return '<a href="/mat-bang-lumi-hanoi/">Tra cứu loại căn và mặt bằng</a>'
    return "".join(f'<a href="{gen.esc(gen.UNIT_LINKS[unit])}">Cẩm nang {gen.esc(unit)}</a>' for unit in seen)


def sibling_links(item: dict, rows_by_tower: dict[str, list[dict]]) -> str:
    links = []
    for sibling in TOWERS:
        if sibling["phase"] != item["phase"] or sibling["tower"] == item["tower"]:
            continue
        count = len(rows_by_tower[sibling["tower"]])
        links.append(f'<a href="/{sibling["slug"]}/">{sibling["tower"]} · {count} căn</a>')
    links.append(f'<a href="/{item["phase_slug"]}/">Toàn bộ {gen.esc(item["phase_name"])}</a>')
    return "".join(links)


def render_page(item: dict, rows: list[dict], rows_by_tower: dict[str, list[dict]], today: date) -> str:
    tower = item["tower"]
    count = len(rows)
    period = current_period(today)
    canonical = f"{SITE}/{item['slug']}/"
    indexable = count >= INDEX_THRESHOLD
    robots = "index,follow,max-image-preview:large" if indexable else "noindex,follow,max-image-preview:large"
    title = f"Mua Bán Tòa {tower} Lumi Hanoi | Căn Chuyển Nhượng {period}"
    description = (
        f"Mua bán tòa {tower} Lumi Hanoi: {count} căn hộ đang công khai. Xem giá chào, diện tích, loại căn, "
        f"mặt bằng {tower}, hình ảnh và liên hệ trực tiếp người đăng."
    )
    modified = latest_date(rows, today)
    listing_html = "\n".join(gen.render_static_card(row) for row in rows[:12])
    if not listing_html:
        listing_html = (
            f'<div class="marketplace-state" role="status"><strong>Chưa có căn hộ tòa {tower} đang bán.</strong>'
            '<p>Khi tin mới được duyệt, quỹ căn sẽ tự xuất hiện tại đây. Trang chưa đủ dữ liệu sẽ không vào chỉ mục Google.</p></div>'
        )

    graph = [
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Mua bán Lumi Hanoi", "item": SITE + "/mua-ban-lumi-hanoi/"},
                {"@type": "ListItem", "position": 3, "name": f"Mua bán {item['phase_name']}", "item": f"{SITE}/{item['phase_slug']}/"},
                {"@type": "ListItem", "position": 4, "name": f"Mua bán tòa {tower}", "item": canonical},
            ],
        },
        {
            "@type": "CollectionPage",
            "name": f"Mua bán tòa {tower} Lumi Hanoi",
            "headline": title,
            "description": description,
            "url": canonical,
            "dateModified": modified,
            "inLanguage": "vi-VN",
            "about": [f"Mua bán tòa {tower} Lumi Hanoi", f"Chuyển nhượng tòa {tower} Lumi Hanoi", item["phase_name"]],
            "isPartOf": {"@type": "WebSite", "name": "Lumi Hanoi", "url": SITE + "/"},
        },
    ]
    if rows:
        graph.append(
            {
                "@type": "ItemList",
                "numberOfItems": min(count, 12),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": idx + 1,
                        "url": SITE + gen.listing_url(row),
                        "name": gen.compact_text(row.get("title", "")),
                    }
                    for idx, row in enumerate(rows[:12])
                ],
            }
        )
    schema = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    floorplan = gen.tower_link(tower)
    status = (
        f"Trang đang index vì có {count} căn hộ bán công khai tại tòa {tower}."
        if indexable
        else f"Hiện tòa {tower} có {count} căn; trang tạm noindex cho đến khi có ít nhất {INDEX_THRESHOLD} căn hộ bán công khai."
    )

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
<div class="container breadcrumb"><a href="/">Trang chủ</a><span aria-hidden="true">/</span><a href="/mua-ban-lumi-hanoi/">Mua bán Lumi Hanoi</a><span aria-hidden="true">/</span><a href="/{item['phase_slug']}/">{gen.esc(item['phase_name'])}</a><span aria-hidden="true">/</span>Tòa {tower}</div>
<header class="article-hero marketplace-hero"><img class="article-hero-media" src="{item['hero']}" alt="Mua bán tòa {tower} Lumi Hanoi" width="1600" height="900" decoding="async"><div class="container"><p class="eyebrow">Quỹ mua bán theo tòa · {period}</p><h1>Mua bán tòa {tower} Lumi Hanoi</h1><p class="lead">Xem riêng quỹ căn bán/chuyển nhượng tại tòa {tower} thuộc {gen.esc(item['phase_name'])}. Mỗi tin dẫn đến URL chi tiết riêng; trước khi so giá nên đối chiếu đúng loại căn, diện tích và vị trí trên mặt bằng tòa.</p><div class="hero-actions"><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#mua-ban">Đăng tin tòa {tower}</a><a class="btn" href="{floorplan}">Xem mặt bằng {tower}</a></div></div></header>
<section class="marketplace-section" aria-labelledby="tower-sale-listings"><div class="container"><div class="marketplace-heading"><div><p class="eyebrow">Tin đã duyệt đang công khai</p><h2 id="tower-sale-listings">Căn tòa {tower} đang bán</h2></div><div class="marketplace-actions"><span class="marketplace-count">{count} tin đăng</span><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#mua-ban">+ Đăng tin</a></div></div><div class="listing-grid">{listing_html}</div></div></section>
<div class="container article-layout reading-shell article-layout--with-sidebar"><article class="article">
<h2>Giá chào và nguồn cung tòa {tower}</h2><p>Hệ thống hiện ghi nhận <strong>{count} căn hộ</strong> bán/chuyển nhượng đã duyệt tại tòa {tower}. Giá chào trung bình từ các tin có giá là <strong>{gen.esc(average_price(rows))}</strong>; đơn giá trung bình từ các tin đủ cả giá và diện tích là <strong>{gen.esc(average_ppsm(rows))}</strong>. Đây là dữ liệu giá rao, không phải giá giao dịch công chứng.</p>
<div class="facts-grid"><div class="fact-card"><strong>{count} tin</strong><span>Quỹ căn tòa {tower} đang công khai</span></div><div class="fact-card"><strong>{gen.esc(average_price(rows))}</strong><span>Giá chào trung bình</span></div><div class="fact-card"><strong>{gen.esc(average_ppsm(rows))}</strong><span>Đơn giá chào trung bình</span></div></div>
<h2>Loại căn đang có tại tòa {tower}</h2><p>{gen.esc(unit_mix(rows))}. Quỹ căn thay đổi theo các tin được duyệt hoặc gỡ khỏi hệ thống.</p><nav class="detail-related" aria-label="Cẩm nang loại căn">{unit_links(rows)}</nav>
<h2>Mặt bằng tòa {tower} và {gen.esc(item['phase_name'])}</h2><p>Trước khi so hai căn cùng số phòng, nên mở mặt bằng tòa {tower} để kiểm tra vị trí căn, cách bố trí, mặt thoáng và mối liên hệ với tầng điển hình. Sau đó mới so sánh giá chào giữa các căn tương đương.</p><nav class="detail-related" aria-label="Tra cứu tòa {tower}"><a href="{floorplan}">Mặt bằng {tower}</a><a href="/{item['phase_slug']}/">Mua bán {gen.esc(item['phase_name'])}</a><a href="/gia-can-ho-lumi-hanoi/">Lumi Hanoi Market Index</a></nav>
<h2>Các tòa khác trong {gen.esc(item['phase_name'])}</h2><nav class="detail-related" aria-label="Các tòa khác trong phân khu">{sibling_links(item, rows_by_tower)}</nav>
<h2>Chính sách index dữ liệu</h2><p>{gen.esc(status)} Ngưỡng này giúp Google tập trung vào các landing có quỹ hàng thật thay vì index hàng loạt trang tòa mỏng hoặc trống.</p>
</article><aside><div class="toc"><strong>Đi nhanh</strong><a href="#tower-sale-listings">Căn đang bán</a><a href="{floorplan}">Mặt bằng {tower}</a><a href="/{item['phase_slug']}/">Quỹ {gen.esc(item['phase_name'])}</a><a href="/gia-can-ho-lumi-hanoi/">Market Index</a><a href="/mua-ban-lumi-hanoi/">Quỹ bán tổng</a></div></aside></div>
</main>
<footer class="site-footer"><div class="container footer-grid"><div><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><p>Cổng thông tin dự án &amp; thị trường căn hộ.</p></div><div><nav class="footer-links" aria-label="Điều hướng cuối trang"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a></nav><p class="disclaimer">Website thông tin và giao dịch độc lập, không phải website chính thức của CapitaLand Development.</p></div></div></footer>
<script src="/assets/js/site.js?v=20260907-performance1" defer></script>
</body></html>
'''


def phase_cluster(item: dict, rows_by_tower: dict[str, list[dict]]) -> str:
    members = [tower for tower in TOWERS if tower["phase"] == item["phase"]]
    links = "".join(
        f'<a href="/{tower["slug"]}/">Tòa {tower["tower"]} · {len(rows_by_tower[tower["tower"]])} căn</a>'
        for tower in members
    )
    return (
        f'{CLUSTER_START}\n'
        f'<h2>Mua bán {gen.esc(item["phase_name"])} theo từng tòa</h2>'
        '<p>Tra cứu quỹ căn theo đúng tòa để so sánh nguồn cung, giá chào và mở mặt bằng tương ứng. Các tòa chưa đủ dữ liệu vẫn phục vụ điều hướng nhưng không được đưa vào chỉ mục Google.</p>'
        f'<nav class="detail-related" aria-label="Mua bán theo từng tòa">{links}</nav>\n'
        f'{CLUSTER_END}'
    )


def update_phase_pages(rows_by_tower: dict[str, list[dict]]) -> None:
    by_phase: dict[str, dict] = {}
    for item in TOWERS:
        by_phase.setdefault(item["phase"], item)
    for phase, item in by_phase.items():
        path = gen.ROOT / item["phase_slug"] / "index.html"
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8")
        block = phase_cluster(item, rows_by_tower)
        if CLUSTER_START in raw and CLUSTER_END in raw:
            raw = re.sub(re.escape(CLUSTER_START) + r".*?" + re.escape(CLUSTER_END), lambda _: block, raw, count=1, flags=re.S)
        else:
            anchor = "<h2>Đi tiếp trong hệ thống Lumi Hanoi</h2>"
            if anchor in raw:
                raw = raw.replace(anchor, block + "\n" + anchor, 1)
            else:
                raw = raw.replace("</article>", block + "\n</article>", 1)
        path.write_text(raw, encoding="utf-8")


def update_sitemap(rows_by_tower: dict[str, list[dict]], today: date) -> None:
    raw = SITEMAP.read_text(encoding="utf-8")
    for item in TOWERS:
        canonical = re.escape(f"{SITE}/{item['slug']}/")
        raw = re.sub(rf"\s*<url>\s*<loc>{canonical}</loc>.*?</url>", "", raw, flags=re.S)
    entries = []
    for item in TOWERS:
        rows = rows_by_tower[item["tower"]]
        if len(rows) < INDEX_THRESHOLD:
            continue
        modified = latest_date(rows, today)
        entries.append(
            f'  <url><loc>{SITE}/{item["slug"]}/</loc><lastmod>{modified}</lastmod><changefreq>daily</changefreq><priority>0.7</priority></url>'
        )
    if entries:
        raw = raw.replace("</urlset>", "\n" + "\n".join(entries) + "\n</urlset>", 1)
    SITEMAP.write_text(raw.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    today = date.today()
    listings = gen.fetch_approved()
    rows_by_tower = {item["tower"]: tower_rows(listings, item["tower"]) for item in TOWERS}
    for item in TOWERS:
        target = gen.ROOT / item["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_page(item, rows_by_tower[item["tower"]], rows_by_tower, today), encoding="utf-8")
    update_phase_pages(rows_by_tower)
    update_sitemap(rows_by_tower, today)
    indexed = [item["tower"] for item in TOWERS if len(rows_by_tower[item["tower"]]) >= INDEX_THRESHOLD]
    print("Generated sale tower SEO pages. Indexed towers: " + (", ".join(indexed) if indexed else "none"))


if __name__ == "__main__":
    main()
