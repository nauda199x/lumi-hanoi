#!/usr/bin/env python3
"""Strengthen the primary Lumi Hanoi rental hub and its topical cluster.

This is intentionally a post-processing layer after generate_rent_category_seo.py:
- keeps the main /cho-thue-lumi-hanoi/ title aligned with the short query "thuê lumi hanoi";
- adds visible inventory freshness without fake daily timestamps;
- creates crawlable rental landing pages for Signature, Prestige and Elite;
- adds contextual links from the three authoritative phase guides back into the rental cluster;
- keeps the new landing pages in sitemap.xml.

The script is idempotent and safe to run on every marketplace sync.
"""
from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path

import generate_rent_category_seo as rent

ROOT = Path(__file__).resolve().parents[1]
SITE = rent.SITE
HUB = ROOT / "cho-thue-lumi-hanoi" / "index.html"
SITEMAP = ROOT / "sitemap.xml"
PHASE_CLUSTER_START = "<!-- RENT-PHASE-CLUSTER:START -->"
PHASE_CLUSTER_END = "<!-- RENT-PHASE-CLUSTER:END -->"
FRESHNESS_START = "<!-- RENT-HUB-FRESHNESS:START -->"
FRESHNESS_END = "<!-- RENT-HUB-FRESHNESS:END -->"
GUIDE_CTA_START = "<!-- RENT-PHASE-GUIDE-CTA:START -->"
GUIDE_CTA_END = "<!-- RENT-PHASE-GUIDE-CTA:END -->"

PHASES = [
    {
        "phase": "Signature",
        "slug": "cho-thue-lumi-signature",
        "label": "Lumi Signature",
        "short": "Signature",
        "towers": "S1, S2, S3, S5 và S6",
        "guide": "/lumi-signature/",
        "hero": "/assets/media/signature/lumi-signature-landscape.webp",
        "context": "Lumi Signature gồm năm tòa S1, S2, S3, S5 và S6. Khi so sánh căn thuê, nên đối chiếu đúng tòa, tầng, layout, diện tích sử dụng và hiện trạng bàn giao của từng căn thay vì chỉ nhìn số phòng.",
    },
    {
        "phase": "Prestige",
        "slug": "cho-thue-lumi-prestige",
        "label": "Lumi Prestige",
        "short": "Prestige",
        "towers": "P1 và P2",
        "guide": "/lumi-prestige/",
        "hero": "/assets/media/prestige/lumi-prestige-hero.webp",
        "context": "Lumi Prestige gồm hai tòa P1 và P2. Giá thuê trên website là giá rao của từng tin công khai; người thuê nên kiểm tra đúng tòa, tầng, layout, mức hoàn thiện và các chi phí sử dụng trước khi đặt cọc.",
    },
    {
        "phase": "Elite",
        "slug": "cho-thue-lumi-elite",
        "label": "Lumi Elite",
        "short": "Elite",
        "towers": "E1 và E2",
        "guide": "/lumi-elite/",
        "hero": "/assets/media/elite/lumi-elite-facade.webp",
        "context": "Lumi Elite gồm hai tòa Elite 1 và Elite 2, thường được ký hiệu E1 và E2 trong hệ thống giao dịch của website. Trước khi thuê cần đối chiếu chính xác tòa, tầng, loại căn, diện tích và hiện trạng thực tế của căn đăng.",
    },
]


def esc(value) -> str:
    return html.escape(str(value or "").strip(), quote=True)


def phase_rows(listings: list[dict], phase: str) -> list[dict]:
    target = phase.casefold()
    return [row for row in listings if rent.clean(row.get("phase")).casefold() == target]


def replace_block(raw: str, start: str, end: str, block: str, anchor: str | None = None) -> str:
    if start in raw and end in raw:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), block, raw, count=1, flags=re.S)
    if anchor and anchor in raw:
        return raw.replace(anchor, block + "\n" + anchor, 1)
    return raw


def replace_meta(raw: str, attr_pattern: str, replacement: str) -> str:
    if re.search(attr_pattern, raw, flags=re.S):
        return re.sub(attr_pattern, replacement, raw, count=1, flags=re.S)
    return raw


def inventory_count(raw: str) -> int:
    match = re.search(r'data-listing-count[^>]*>\s*(\d+)\s+tin', raw, flags=re.I)
    return int(match.group(1)) if match else 0


def period(today: date) -> str:
    return f"T{today.month}/{today.year}"


def strengthen_hub(listings: list[dict], today: date) -> str:
    raw = HUB.read_text(encoding="utf-8")
    current_period = period(today)
    title = f"Thuê Lumi Hanoi | Căn Hộ Cho Thuê Mới Nhất {current_period}"
    description = (
        "Thuê Lumi Hanoi: quỹ căn cho thuê cập nhật theo tòa, phân khu và loại căn. "
        "Xem giá rao, diện tích, hình ảnh và liên hệ trực tiếp người đăng."
    )

    raw = replace_meta(raw, r"<title>.*?</title>", f"<title>{esc(title)}</title>")
    raw = replace_meta(raw, r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(description)}">')
    raw = replace_meta(raw, r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(title)}">')
    raw = replace_meta(raw, r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(description)}">')
    raw = replace_meta(raw, r'<meta name="twitter:title" content="[^"]*">', f'<meta name="twitter:title" content="{esc(title)}">')
    raw = replace_meta(raw, r'<meta name="twitter:description" content="[^"]*">', f'<meta name="twitter:description" content="{esc(description)}">')

    if '<meta name="robots"' not in raw:
        raw = raw.replace(
            '<link rel="canonical" href="https://lumi-hanoi.com/cho-thue-lumi-hanoi/">',
            '<link rel="canonical" href="https://lumi-hanoi.com/cho-thue-lumi-hanoi/">\n    <meta name="robots" content="index,follow,max-image-preview:large">',
            1,
        )

    raw = re.sub(r'"headline":"[^"]*"', f'"headline":"{title}"', raw, count=1)
    hub_modified = rent.modified_date(listings, today)
    raw = re.sub(r'"dateModified":"\d{4}-\d{2}-\d{2}"', f'"dateModified":"{hub_modified}"', raw, count=1)

    count = inventory_count(raw)
    freshness = (
        f'{FRESHNESS_START}\n'
        f'<p class="rent-hub-freshness"><strong>Cập nhật {current_period}</strong> · '
        f'{count} tin cho thuê đang công khai · dữ liệu được đồng bộ tự động khi tin được duyệt.</p>\n'
        f'{FRESHNESS_END}'
    )
    hero_anchor = '<p class="lead">Xem quỹ căn Lumi Hanoi đang cho thuê'
    if FRESHNESS_START in raw:
        raw = replace_block(raw, FRESHNESS_START, FRESHNESS_END, freshness)
    elif hero_anchor in raw:
        # Put freshness immediately before the existing lead so the H1 stays uncluttered.
        raw = raw.replace(hero_anchor, freshness + "\n              " + hero_anchor, 1)

    cards = []
    for item in PHASES:
        count_phase = len(phase_rows(listings, item["phase"]))
        cards.append(
            '<div class="fact-card">'
            f'<strong><a href="/{item["slug"]}/">Thuê {esc(item["label"])}</a></strong>'
            f'<span>{count_phase} tin đang công khai · {esc(item["towers"])}</span>'
            '</div>'
        )
    phase_cluster = (
        f'{PHASE_CLUSTER_START}\n'
        '<section class="section section-alt" aria-labelledby="rent-phase-title"><div class="container">'
        '<div class="section-heading"><p class="eyebrow">Tìm theo phân khu</p>'
        '<h2 id="rent-phase-title">Thuê Lumi Hanoi theo phân khu</h2>'
        '<p>Đi thẳng vào quỹ căn Lumi Signature, Lumi Prestige hoặc Lumi Elite. '
        'Mỗi trang chỉ hiển thị tin thuộc đúng phân khu và liên kết ngược về quỹ thuê tổng.</p></div>'
        '<div class="facts-grid">' + "".join(cards) + '</div></div></section>\n'
        f'{PHASE_CLUSTER_END}'
    )
    raw = replace_block(raw, PHASE_CLUSTER_START, PHASE_CLUSTER_END, phase_cluster, rent.CLUSTER_START)

    HUB.write_text(raw, encoding="utf-8")
    return hub_modified


def render_phase_page(item: dict, rows: list[dict], today: date) -> str:
    current_period = period(today)
    title = f"Thuê {item['label']} | Căn Hộ Cho Thuê {current_period}"
    description = (
        f"Thuê {item['label']}: quỹ căn đang cho thuê tại {item['towers']}. "
        "Xem giá rao, diện tích, ảnh và liên hệ trực tiếp người đăng."
    )
    canonical = f"{SITE}/{item['slug']}/"
    modified = rent.modified_date(rows, today)
    count = len(rows)
    cards = "\n".join(rent.render_card(row) for row in rows)
    if not cards:
        cards = (
            '<div class="marketplace-state" role="status"><span class="marketplace-state-mark" aria-hidden="true">0</span><div>'
            f'<h3>Chưa có tin {esc(item["label"])} đang công khai</h3>'
            '<p>Trang vẫn được giữ để người thuê tra cứu đúng phân khu. Khi có tin được duyệt, danh sách sẽ tự xuất hiện tại đây.</p>'
            '<div class="hero-actions"><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#cho-thue">Đăng tin cho thuê</a>'
            '<a class="btn" href="/cho-thue-lumi-hanoi/">Xem toàn bộ quỹ thuê</a></div></div></div>'
        )

    phase_nav = "".join(
        f'<a href="/{phase["slug"]}/">Thuê {esc(phase["label"])}</a>'
        for phase in PHASES
        if phase["slug"] != item["slug"]
    )
    unit_nav = "".join(
        f'<a href="/{category["slug"]}/">{esc(category["short"])}</a>'
        for category in rent.CATEGORIES
    ) + '<a href="/cho-thue-shop-chan-de-lumi-hanoi/">Shop</a>'

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Cho thuê Lumi Hanoi", "item": SITE + "/cho-thue-lumi-hanoi/"},
                    {"@type": "ListItem", "position": 3, "name": f"Thuê {item['label']}", "item": canonical},
                ],
            },
            {
                "@type": "CollectionPage",
                "name": f"Thuê {item['label']}",
                "headline": title,
                "description": description,
                "url": canonical,
                "dateModified": modified,
                "inLanguage": "vi-VN",
                "about": [f"Thuê {item['label']}", f"Cho thuê {item['label']}", "Thuê Lumi Hanoi"],
                "isPartOf": {"@type": "WebSite", "name": "Lumi Hanoi", "url": SITE + "/"},
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
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{esc(canonical)}">
  <link rel="icon" href="/favicon.svg?v=20260828" type="image/svg+xml"><link rel="icon" href="/favicon-32x32.png?v=20260828" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="/apple-touch-icon.png?v=20260828"><link rel="manifest" href="/site.webmanifest">
  <meta name="theme-color" content="#f5f1e8">
  <meta property="og:type" content="website"><meta property="og:locale" content="vi_VN"><meta property="og:site_name" content="Lumi Hanoi"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(canonical)}"><meta property="og:image" content="{SITE}{esc(item['hero'])}"><meta property="og:image:alt" content="Thuê {esc(item['label'])}">
  <meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(description)}"><meta name="twitter:image" content="{SITE}{esc(item['hero'])}">
  <link rel="stylesheet" href="/assets/css/site.css?v=20260829-type"><link rel="stylesheet" href="/assets/css/marketplace.css?v=20260902-mobileux2">
  <script type="application/ld+json">{schema_json}</script>
</head>
<body>
  <a class="skip-link" href="#main">Bỏ qua điều hướng</a>
  <header class="site-header"><div class="container nav"><a class="brand" href="/" aria-label="Lumi Hanoi – Trang chủ"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="primary-nav">Menu</button><nav id="primary-nav" class="nav-links" data-nav-links data-open="false" aria-label="Điều hướng chính"><a href="/tong-quan-lumi-hanoi/">Tổng quan</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a><details class="nav-dropdown"><summary>Phân khu</summary><div class="nav-dropdown-menu"><a href="/lumi-signature/">Lumi Signature</a><a href="/lumi-prestige/">Lumi Prestige</a><a href="/lumi-elite/">Lumi Elite</a></div></details><a href="/tien-do-lumi-hanoi/">Tiến độ</a><a href="/tin-tuc/">Tin tức</a><details class="nav-dropdown"><summary>Giao dịch</summary><div class="nav-dropdown-menu nav-dropdown-menu--right"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/" aria-current="page">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a></div></details></nav></div></header>
  <main id="main">
    <div class="container breadcrumb"><a href="/">Trang chủ</a><span aria-hidden="true">/</span><a href="/cho-thue-lumi-hanoi/">Cho thuê Lumi Hanoi</a><span aria-hidden="true">/</span>{esc(item['label'])}</div>
    <header class="article-hero marketplace-hero"><img class="article-hero-media" src="{esc(item['hero'])}" width="1200" height="800" alt="Thuê {esc(item['label'])}" decoding="async"><div class="container"><p class="eyebrow">Quỹ thuê theo phân khu · {current_period}</p><h1>Thuê {esc(item['label'])}</h1><p class="lead">Xem riêng căn hộ đang cho thuê tại {esc(item['label'])}, gồm {esc(item['towers'])}. Mỗi tin dẫn tới URL chi tiết riêng với giá rao, ảnh và thông tin liên hệ người đăng.</p><div class="hero-actions"><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#cho-thue">Đăng tin cho thuê</a><a class="btn" href="/cho-thue-lumi-hanoi/">Tất cả căn cho thuê</a></div></div></header>

    <section class="marketplace-section" aria-labelledby="phase-listings"><div class="container"><div class="marketplace-heading"><div><p class="eyebrow">Tin đang công khai</p><h2 id="phase-listings">Căn {esc(item['label'])} đang cho thuê</h2></div><div class="marketplace-actions"><span class="marketplace-count">{count} tin đăng</span><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#cho-thue">+ Đăng tin</a></div></div><div class="listing-grid">{cards}</div></div></section>

    <div class="container article-layout reading-shell article-layout--with-sidebar">
      <article class="article">
        <h2>Thuê {esc(item['label'])}: kiểm tra đúng tòa trước khi so giá</h2>
        <p>{esc(item['context'])}</p>
        <div class="facts-grid"><div class="fact-card"><strong>{esc(item['towers'])}</strong><span>Các tòa thuộc {esc(item['label'])}</span></div><div class="fact-card"><strong>{count} tin</strong><span>Số tin đã duyệt đang công khai tại thời điểm đồng bộ</span></div><div class="fact-card"><strong>Giá rao thực tế</strong><span>Không tự điền giá ước đoán khi thiếu dữ liệu</span></div></div>

        <h2>Tra cứu thông tin phân khu trước khi hẹn xem căn</h2>
        <p>Trang giao dịch chỉ giúp sàng lọc quỹ căn đang đăng. Để hiểu mặt bằng, loại căn và cấu trúc tòa, nên mở cẩm nang phân khu trước khi so sánh hai tin có cùng số phòng.</p>
        <div class="hero-actions"><a class="btn" href="{esc(item['guide'])}">Cẩm nang {esc(item['label'])}</a><a class="btn" href="/mat-bang-lumi-hanoi/">Tra cứu mặt bằng</a></div>

        <h2>Thuê Lumi Hanoi theo loại căn</h2>
        <nav class="detail-related" aria-label="Thuê Lumi Hanoi theo loại căn">{unit_nav}</nav>
        <h2>Phân khu khác</h2>
        <nav class="detail-related" aria-label="Thuê Lumi Hanoi theo phân khu">{phase_nav}<a href="/cho-thue-lumi-hanoi/">Toàn bộ quỹ thuê Lumi Hanoi</a></nav>

        <h2>Lưu ý trước khi đặt cọc</h2>
        <p>Không nên đặt cọc chỉ dựa trên nội dung tin đăng. Cần xác minh người có quyền cho thuê, hiện trạng căn, danh mục nội thất, chi phí sử dụng, thời hạn hợp đồng và điều kiện hoàn cọc trước khi chuyển tiền.</p>
      </article>
      <aside><div class="toc"><strong>Đi nhanh</strong><a href="#phase-listings">Tin đang cho thuê</a><a href="{esc(item['guide'])}">Cẩm nang phân khu</a><a href="/cho-thue-lumi-hanoi/">Quỹ thuê tổng</a><a href="/dang-tin-lumi-hanoi/#cho-thue">Đăng tin miễn phí</a></div></aside>
    </div>
  </main>
  <footer class="site-footer"><div class="container footer-grid"><div><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><p>Cổng thông tin dự án &amp; thị trường căn hộ.</p></div><div><nav class="footer-links" aria-label="Điều hướng cuối trang"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a><a href="/tin-tuc/">Tin tức</a></nav><p class="disclaimer">Website thông tin và giao dịch độc lập, không phải website chính thức của CapitaLand Development.</p></div></div></footer>
  <script src="/assets/js/site.js" defer></script>
</body>
</html>
"""


def sync_phase_pages(listings: list[dict], today: date) -> dict[str, str]:
    modified: dict[str, str] = {}
    for item in PHASES:
        rows = phase_rows(listings, item["phase"])
        target = ROOT / item["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        content = render_phase_page(item, rows, today)
        old = target.read_text(encoding="utf-8") if target.exists() else ""
        if old != content:
            target.write_text(content, encoding="utf-8")
        modified[item["slug"]] = rent.modified_date(rows, today)
    return modified


def sync_phase_guide_ctas() -> None:
    for item in PHASES:
        path = ROOT / item["guide"].strip("/") / "index.html"
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        block = (
            f'{GUIDE_CTA_START}\n'
            '<div class="hero-actions">'
            f'<a class="btn btn-primary" href="/{item["slug"]}/">Xem căn {esc(item["label"])} đang cho thuê</a>'
            '<a class="btn" href="/cho-thue-lumi-hanoi/">Quỹ thuê Lumi Hanoi</a>'
            '</div>\n'
            f'{GUIDE_CTA_END}'
        )
        if GUIDE_CTA_START in raw:
            raw = replace_block(raw, GUIDE_CTA_START, GUIDE_CTA_END, block)
        else:
            pattern = rf'(<h1>{re.escape(item["label"])}</h1>\s*<p class="lead">.*?</p>)'
            if re.search(pattern, raw, flags=re.S):
                raw = re.sub(pattern, lambda m: m.group(1) + "\n              " + block, raw, count=1, flags=re.S)
        path.write_text(raw, encoding="utf-8")


def sync_sitemap(modified: dict[str, str], hub_modified: str) -> None:
    if not SITEMAP.exists():
        return
    raw = SITEMAP.read_text(encoding="utf-8")
    raw = rent.upsert_sitemap_row(raw, SITE + "/cho-thue-lumi-hanoi/", hub_modified, "0.9")
    for item in PHASES:
        raw = rent.upsert_sitemap_row(raw, f"{SITE}/{item['slug']}/", modified[item["slug"]], "0.9")
    SITEMAP.write_text(raw, encoding="utf-8")


def main() -> None:
    today = date.today()
    listings = rent.fetch_approved()
    hub_modified = strengthen_hub(listings, today)
    phase_modified = sync_phase_pages(listings, today)
    sync_phase_guide_ctas()
    sync_sitemap(phase_modified, hub_modified)
    counts = {item["phase"]: len(phase_rows(listings, item["phase"])) for item in PHASES}
    print("Rental hub authority cluster synced:", counts)


if __name__ == "__main__":
    main()
