#!/usr/bin/env python3
"""Generate controlled sale-intent landing pages for Lumi Hanoi phases.

Only three phase pages are maintained: Signature, Prestige and Elite. They use
approved marketplace inventory, render listings as crawlable HTML, and become
indexable only when at least two apartment listings are currently public. This
keeps the commercial architecture useful without opening a faceted crawl trap.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from statistics import mean

import generate_marketplace_seo as gen

SITE = gen.SITE
HUB = gen.ROOT / "mua-ban-lumi-hanoi" / "index.html"
SITEMAP = gen.ROOT / "sitemap.xml"
CLUSTER_START = "<!-- SALE-PHASE-CLUSTER:START -->"
CLUSTER_END = "<!-- SALE-PHASE-CLUSTER:END -->"
INDEX_THRESHOLD = 2

PHASES = (
    {
        "phase": "Signature",
        "slug": "mua-ban-lumi-signature",
        "name": "Lumi Signature",
        "towers": ("S1", "S2", "S3", "S5", "S6"),
        "hero": "/assets/media/signature/lumi-signature-landscape.webp",
        "context": "Lumi Signature gồm S1, S2, S3, S5 và S6. Khi so sánh căn chuyển nhượng, nên đối chiếu đúng tòa, tầng và mặt bằng trước khi so giá chào.",
    },
    {
        "phase": "Prestige",
        "slug": "mua-ban-lumi-prestige",
        "name": "Lumi Prestige",
        "towers": ("P1", "P2"),
        "hero": "/assets/media/prestige/lumi-prestige-hero.webp",
        "context": "Lumi Prestige gồm P1 và P2. Hai căn cùng số phòng có thể khác diện tích, layout và vị trí trên mặt bằng, vì vậy giá chào chỉ nên so sau khi chuẩn hóa đúng sản phẩm.",
    },
    {
        "phase": "Elite",
        "slug": "mua-ban-lumi-elite",
        "name": "Lumi Elite",
        "towers": ("E1", "E2"),
        "hero": "/assets/media/home/lumi-hanoi-streetscape.webp",
        "context": "Lumi Elite gồm E1 và E2. Trang này chỉ mở index khi quỹ căn bán công khai đủ dày; website không tự tạo giá hoặc tồn kho khi chưa có dữ liệu được duyệt.",
    },
)


def phase_rows(listings: list[dict], phase: str) -> list[dict]:
    rows = []
    for listing in listings:
        if listing.get("listing_type") != "sale":
            continue
        if gen.clean(listing.get("phase")) != phase:
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


def current_period(today: date) -> str:
    return f"T{today.month}/{today.year}"


def latest_date(rows: list[dict], today: date) -> str:
    values = [gen.date_only(row.get("approved_at") or row.get("created_at")) for row in rows]
    values = [value for value in values if value]
    return max(values) if values else today.replace(day=1).isoformat()


def average_price(rows: list[dict]) -> str:
    values = [gen.numeric(row.get("price_vnd")) for row in rows]
    values = [value for value in values if value]
    return gen.format_market_price(mean(values), "sale") if values else "Chưa đủ dữ liệu"


def tower_links(towers: tuple[str, ...]) -> str:
    return "".join(
        f'<a href="{gen.esc(gen.tower_link(tower))}">Mặt bằng {gen.esc(tower)}</a>'
        for tower in towers
    )


def other_phase_links(current_slug: str) -> str:
    links = []
    for item in PHASES:
        if item["slug"] == current_slug:
            continue
        links.append(f'<a href="/{item["slug"]}/">{gen.esc(item["name"])}</a>')
    links.append('<a href="/mua-ban-lumi-hanoi/">Toàn bộ quỹ mua bán</a>')
    return "".join(links)


def render_page(item: dict, rows: list[dict], today: date) -> str:
    period = current_period(today)
    canonical = f"{SITE}/{item['slug']}/"
    count = len(rows)
    indexable = count >= INDEX_THRESHOLD
    robots = "index,follow,max-image-preview:large" if indexable else "noindex,follow,max-image-preview:large"
    title = f"Mua Bán {item['name']} | Căn Hộ Chuyển Nhượng {period}"
    description = (
        f"Mua bán {item['name']}: {count} căn hộ đang công khai. Xem giá chào, diện tích, tòa, ảnh, "
        "mặt bằng và liên hệ trực tiếp người đăng trên Lumi Hanoi."
    )
    modified = latest_date(rows, today)
    listing_html = "\n".join(gen.render_static_card(row) for row in rows[:12])
    if not listing_html:
        listing_html = (
            '<div class="marketplace-state" role="status"><strong>Chưa có căn hộ đang bán trong phân khu này.</strong>'
            '<p>Quỹ căn mới sẽ xuất hiện sau khi tin được duyệt. Trang chưa đủ dữ liệu sẽ không được đưa vào chỉ mục Google.</p></div>'
        )
    items = [
        {
            "@type": "ListItem",
            "position": idx + 1,
            "url": SITE + gen.listing_url(row),
            "name": gen.compact_text(row.get("title", "")),
        }
        for idx, row in enumerate(rows[:12])
    ]
    graph = [
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Mua bán Lumi Hanoi", "item": SITE + "/mua-ban-lumi-hanoi/"},
                {"@type": "ListItem", "position": 3, "name": f"Mua bán {item['name']}", "item": canonical},
            ],
        },
        {
            "@type": "CollectionPage",
            "name": f"Mua bán {item['name']}",
            "headline": title,
            "description": description,
            "url": canonical,
            "dateModified": modified,
            "inLanguage": "vi-VN",
            "isPartOf": {"@type": "WebSite", "name": "Lumi Hanoi", "url": SITE + "/"},
        },
    ]
    if items:
        graph.append({"@type": "ItemList", "numberOfItems": len(items), "itemListElement": items})
    schema = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    towers_text = ", ".join(item["towers"])
    status_copy = (
        f"Trang đang index vì có {count} căn hộ bán công khai."
        if indexable
        else f"Hiện có {count} căn; trang tạm noindex cho đến khi có ít nhất {INDEX_THRESHOLD} căn hộ bán công khai."
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
<div class="container breadcrumb"><a href="/">Trang chủ</a><span aria-hidden="true">/</span><a href="/mua-ban-lumi-hanoi/">Mua bán Lumi Hanoi</a><span aria-hidden="true">/</span>{gen.esc(item['name'])}</div>
<header class="article-hero marketplace-hero"><img class="article-hero-media" src="{item['hero']}" alt="Mua bán {gen.esc(item['name'])}" width="1600" height="900" decoding="async"><div class="container"><p class="eyebrow">Quỹ mua bán theo phân khu · {period}</p><h1>Mua bán {gen.esc(item['name'])}</h1><p class="lead">{gen.esc(item['context'])}</p><div class="hero-actions"><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#mua-ban">Đăng tin mua bán</a><a class="btn" href="/gia-can-ho-lumi-hanoi/">Xem Market Index</a></div></div></header>
<section class="marketplace-section" aria-labelledby="phase-sale-listings"><div class="container"><div class="marketplace-heading"><div><p class="eyebrow">Tin đã duyệt đang công khai</p><h2 id="phase-sale-listings">Căn {gen.esc(item['name'])} đang bán</h2></div><div class="marketplace-actions"><span class="marketplace-count">{count} tin đăng</span><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#mua-ban">+ Đăng tin</a></div></div><div class="listing-grid">{listing_html}</div></div></section>
<div class="container article-layout reading-shell article-layout--with-sidebar"><article class="article">
<h2>Quỹ căn và giá chào {gen.esc(item['name'])}</h2><p>Hiện hệ thống ghi nhận <strong>{count} căn hộ</strong> bán/chuyển nhượng đã duyệt trong phân khu. Giá chào trung bình của các tin có giá là <strong>{gen.esc(average_price(rows))}</strong>. Số liệu thay đổi theo quỹ căn và không phải giá giao dịch công chứng.</p>
<div class="facts-grid"><div class="fact-card"><strong>{count} tin</strong><span>Căn hộ bán đang công khai</span></div><div class="fact-card"><strong>{gen.esc(average_price(rows))}</strong><span>Giá chào trung bình từ tin đủ giá</span></div><div class="fact-card"><strong>{gen.esc(towers_text)}</strong><span>Các tòa thuộc phân khu</span></div></div>
<h2>Đối chiếu mặt bằng trước khi so giá</h2><p>Giá chỉ có ý nghĩa khi so đúng loại căn, diện tích, tòa, tầng và vị trí. Mở mặt bằng từng tòa để kiểm tra cấu trúc sản phẩm trước khi liên hệ người đăng.</p><nav class="detail-related" aria-label="Mặt bằng các tòa">{tower_links(item['towers'])}</nav>
<h2>Đi tiếp trong hệ thống Lumi Hanoi</h2><nav class="detail-related" aria-label="Mua bán theo phân khu">{other_phase_links(item['slug'])}</nav>
<h2>Chính sách index dữ liệu</h2><p>{gen.esc(status_copy)} Cách này giúp Google tập trung crawl vào các landing có quỹ hàng thật thay vì tạo hàng loạt trang lọc mỏng.</p>
</article><aside><div class="toc"><strong>Đi nhanh</strong><a href="#phase-sale-listings">Căn đang bán</a><a href="/gia-can-ho-lumi-hanoi/">Market Index</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a><a href="/mua-ban-lumi-hanoi/">Quỹ bán tổng</a><a href="/dang-tin-lumi-hanoi/#mua-ban">Đăng tin</a></div></aside></div>
</main>
<footer class="site-footer"><div class="container footer-grid"><div><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><p>Cổng thông tin dự án &amp; thị trường căn hộ.</p></div><div><nav class="footer-links" aria-label="Điều hướng cuối trang"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a><a href="/tin-tuc/">Tin tức</a></nav><p class="disclaimer">Website thông tin và giao dịch độc lập, không phải website chính thức của CapitaLand Development.</p></div></div></footer>
<script src="/assets/js/site.js?v=20260907-performance1" defer></script>
</body></html>'''


def replace_marked(raw: str, start: str, end: str, body: str) -> str:
    block = start + "\n" + body.strip() + "\n" + end
    if start in raw and end in raw:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, raw, count=1, flags=re.S)
    return raw


def sync_hub(rows_by_phase: dict[str, list[dict]]) -> None:
    raw = HUB.read_text(encoding="utf-8")
    cards = []
    for item in PHASES:
        count = len(rows_by_phase[item["phase"]])
        cards.append(
            f'<a class="fact-card" href="/{item["slug"]}/"><strong>{gen.esc(item["name"])}</strong>'
            f'<span>{count} căn hộ bán đang công khai · {gen.esc(", ".join(item["towers"]))}</span></a>'
        )
    body = (
        '<section class="section sale-phase-cluster" aria-labelledby="sale-phase-title"><div class="container">'
        '<div class="section-heading"><div><p class="eyebrow">Mua bán theo phân khu</p><h2 id="sale-phase-title">Chọn Signature, Prestige hoặc Elite</h2></div>'
        '<p>Đi từ phân khu → tòa → mặt bằng → tin chi tiết để so đúng sản phẩm trước khi so giá.</p></div>'
        f'<div class="facts-grid">{"".join(cards)}</div></div></section>'
    )
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


def sync_sitemap(rows_by_phase: dict[str, list[dict]], today: date) -> None:
    raw = SITEMAP.read_text(encoding="utf-8")
    for item in PHASES:
        url = f"{SITE}/{item['slug']}/"
        raw = re.sub(rf"\s*<url>\s*<loc>{re.escape(url)}</loc>.*?</url>", "", raw, flags=re.S)
    insertions = []
    for item in PHASES:
        rows = rows_by_phase[item["phase"]]
        if len(rows) < INDEX_THRESHOLD:
            continue
        url = f"{SITE}/{item['slug']}/"
        insertions.append(
            f"  <url><loc>{url}</loc><lastmod>{latest_date(rows, today)}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>"
        )
    if insertions:
        raw = raw.replace("</urlset>", "\n" + "\n".join(insertions) + "\n</urlset>", 1)
    SITEMAP.write_text(raw.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    today = date.today()
    listings = gen.fetch_approved()
    rows_by_phase = {item["phase"]: phase_rows(listings, item["phase"]) for item in PHASES}
    for item in PHASES:
        target = gen.ROOT / item["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_page(item, rows_by_phase[item["phase"]], today), encoding="utf-8")
    sync_hub(rows_by_phase)
    sync_sitemap(rows_by_phase, today)
    summary = ", ".join(f"{item['phase']}={len(rows_by_phase[item['phase']])}" for item in PHASES)
    print(f"Sale phase SEO generated: {summary}; index threshold={INDEX_THRESHOLD}")


if __name__ == "__main__":
    main()
