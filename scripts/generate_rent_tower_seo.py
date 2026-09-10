#!/usr/bin/env python3
"""Generate finite, inventory-backed rental landing pages for Lumi Hanoi towers.

All nine tower URLs exist for navigation. A tower becomes indexable and enters
sitemap.xml only when at least two approved public apartment-rental listings are
available. This mirrors the controlled sale-tower architecture without opening
faceted crawl traps.
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
CLUSTER_START = "<!-- RENT-TOWER-CLUSTER:START -->"
CLUSTER_END = "<!-- RENT-TOWER-CLUSTER:END -->"

TOWERS = (
    {"tower":"S1","phase":"Signature","phase_name":"Lumi Signature","phase_slug":"cho-thue-lumi-signature","slug":"cho-thue-toa-s1-lumi-hanoi","hero":"/assets/media/signature/lumi-signature-landscape.webp"},
    {"tower":"S2","phase":"Signature","phase_name":"Lumi Signature","phase_slug":"cho-thue-lumi-signature","slug":"cho-thue-toa-s2-lumi-hanoi","hero":"/assets/media/signature/lumi-signature-landscape.webp"},
    {"tower":"S3","phase":"Signature","phase_name":"Lumi Signature","phase_slug":"cho-thue-lumi-signature","slug":"cho-thue-toa-s3-lumi-hanoi","hero":"/assets/media/signature/lumi-signature-landscape.webp"},
    {"tower":"S5","phase":"Signature","phase_name":"Lumi Signature","phase_slug":"cho-thue-lumi-signature","slug":"cho-thue-toa-s5-lumi-hanoi","hero":"/assets/media/signature/lumi-signature-landscape.webp"},
    {"tower":"S6","phase":"Signature","phase_name":"Lumi Signature","phase_slug":"cho-thue-lumi-signature","slug":"cho-thue-toa-s6-lumi-hanoi","hero":"/assets/media/signature/lumi-signature-landscape.webp"},
    {"tower":"P1","phase":"Prestige","phase_name":"Lumi Prestige","phase_slug":"cho-thue-lumi-prestige","slug":"cho-thue-toa-p1-lumi-hanoi","hero":"/assets/media/prestige/lumi-prestige-hero.webp"},
    {"tower":"P2","phase":"Prestige","phase_name":"Lumi Prestige","phase_slug":"cho-thue-lumi-prestige","slug":"cho-thue-toa-p2-lumi-hanoi","hero":"/assets/media/prestige/lumi-prestige-hero.webp"},
    {"tower":"E1","phase":"Elite","phase_name":"Lumi Elite","phase_slug":"cho-thue-lumi-elite","slug":"cho-thue-toa-e1-lumi-hanoi","hero":"/assets/media/home/lumi-hanoi-streetscape.webp"},
    {"tower":"E2","phase":"Elite","phase_name":"Lumi Elite","phase_slug":"cho-thue-lumi-elite","slug":"cho-thue-toa-e2-lumi-hanoi","hero":"/assets/media/home/lumi-hanoi-streetscape.webp"},
)

RENT_UNIT_URLS = {
    "1PN":"/cho-thue-can-ho-1-phong-ngu-lumi-hanoi/",
    "2PN":"/cho-thue-can-ho-2-phong-ngu-lumi-hanoi/",
    "3PN":"/cho-thue-can-ho-3-phong-ngu-lumi-hanoi/",
    "4PN":"/cho-thue-can-ho-4-phong-ngu-lumi-hanoi/",
    "Duplex":"/cho-thue-duplex-lumi-hanoi/",
    "Penthouse":"/cho-thue-penthouse-lumi-hanoi/",
}


def period(today: date) -> str:
    return f"T{today.month}/{today.year}"


def tower_rows(listings: list[dict], tower: str) -> list[dict]:
    rows = []
    for row in listings:
        if row.get("listing_type") != "rent":
            continue
        if gen.clean(row.get("tower")).upper() != tower.upper():
            continue
        if gen.clean(row.get("unit_type")) not in gen.APARTMENT_UNIT_TYPES:
            continue
        if not gen.clean(row.get("slug")):
            continue
        rows.append(row)
    return sorted(rows, key=lambda row:(row.get("approved_at") or "", row.get("created_at") or "", row.get("id") or ""), reverse=True)


def latest_date(rows: list[dict], today: date) -> str:
    values = [gen.date_only(row.get("approved_at") or row.get("created_at")) for row in rows]
    values = [value for value in values if value]
    return max(values) if values else today.replace(day=1).isoformat()


def average_price(rows: list[dict]) -> str:
    values = [gen.numeric(row.get("price_vnd")) for row in rows]
    values = [value for value in values if value]
    return gen.format_market_price(mean(values), "rent") if values else "Chưa đủ dữ liệu"


def unit_mix(rows: list[dict]) -> str:
    counts: dict[str,int] = {}
    for row in rows:
        unit = gen.clean(row.get("unit_type"))
        if unit:
            counts[unit] = counts.get(unit, 0) + 1
    return " · ".join(f"{unit}: {count}" for unit,count in sorted(counts.items())) if counts else "Chưa có quỹ căn công khai"


def unit_links(rows: list[dict]) -> str:
    seen=[]
    for row in rows:
        unit=gen.clean(row.get("unit_type"))
        if unit in RENT_UNIT_URLS and unit not in seen:
            seen.append(unit)
    if not seen:
        return '<a href="/mat-bang-lumi-hanoi/">Tra cứu mặt bằng và loại căn</a>'
    return "".join(f'<a href="{RENT_UNIT_URLS[unit]}">Thuê căn {gen.esc(unit)}</a>' for unit in seen)


def sibling_links(item: dict, rows_by_tower: dict[str,list[dict]]) -> str:
    links=[]
    for sibling in TOWERS:
        if sibling["phase"] != item["phase"] or sibling["tower"] == item["tower"]:
            continue
        links.append(f'<a href="/{sibling["slug"]}/">{sibling["tower"]} · {len(rows_by_tower[sibling["tower"]])} căn</a>')
    links.append(f'<a href="/{item["phase_slug"]}/">Toàn bộ {gen.esc(item["phase_name"])}</a>')
    return "".join(links)


def render_page(item: dict, rows: list[dict], rows_by_tower: dict[str,list[dict]], today: date) -> str:
    tower=item["tower"]; count=len(rows); current=period(today)
    canonical=f"{SITE}/{item['slug']}/"; indexable=count>=INDEX_THRESHOLD
    robots="index,follow,max-image-preview:large" if indexable else "noindex,follow,max-image-preview:large"
    title=f"Cho Thuê Tòa {tower} Lumi Hanoi | Căn Hộ Thuê {current}"
    description=f"Cho thuê tòa {tower} Lumi Hanoi: {count} căn hộ đang công khai. Xem giá thuê, diện tích, loại căn, mặt bằng {tower}, hình ảnh và liên hệ người đăng."
    modified=latest_date(rows,today); floorplan=gen.tower_link(tower)
    cards="\n".join(gen.render_static_card(row) for row in rows[:12])
    if not cards:
        cards=f'<div class="marketplace-state" role="status"><strong>Chưa có căn hộ tòa {tower} đang cho thuê.</strong><p>Khi tin mới được duyệt, quỹ căn sẽ tự xuất hiện tại đây. Trang chưa đủ dữ liệu sẽ không vào chỉ mục Google.</p></div>'
    graph=[
        {"@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":"Trang chủ","item":SITE+"/"},
            {"@type":"ListItem","position":2,"name":"Cho thuê Lumi Hanoi","item":SITE+"/cho-thue-lumi-hanoi/"},
            {"@type":"ListItem","position":3,"name":f"Thuê {item['phase_name']}","item":f"{SITE}/{item['phase_slug']}/"},
            {"@type":"ListItem","position":4,"name":f"Cho thuê tòa {tower}","item":canonical},
        ]},
        {"@type":"CollectionPage","name":f"Cho thuê tòa {tower} Lumi Hanoi","headline":title,"description":description,"url":canonical,"dateModified":modified,"inLanguage":"vi-VN","about":[f"Cho thuê tòa {tower} Lumi Hanoi",f"Thuê căn hộ tòa {tower} Lumi Hanoi",item["phase_name"]],"isPartOf":{"@type":"WebSite","name":"Lumi Hanoi","url":SITE+"/"}},
    ]
    if rows:
        graph.append({"@type":"ItemList","numberOfItems":min(count,12),"itemListElement":[{"@type":"ListItem","position":i+1,"url":SITE+gen.listing_url(row),"name":gen.compact_text(row.get("title",""))} for i,row in enumerate(rows[:12])]})
    schema=json.dumps({"@context":"https://schema.org","@graph":graph},ensure_ascii=False,separators=(",",":")).replace("</","<\\/")
    status=(f"Trang đang index vì có {count} căn hộ thuê công khai tại tòa {tower}." if indexable else f"Hiện tòa {tower} có {count} căn; trang tạm noindex cho đến khi có ít nhất {INDEX_THRESHOLD} căn hộ thuê công khai.")
    return f'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{gen.esc(title)}</title><meta name="description" content="{gen.esc(description)}"><meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}"><link rel="icon" href="/favicon.svg?v=20260828" type="image/svg+xml"><meta name="theme-color" content="#f5f1e8">
<meta property="og:type" content="website"><meta property="og:locale" content="vi_VN"><meta property="og:site_name" content="Lumi Hanoi"><meta property="og:title" content="{gen.esc(title)}"><meta property="og:description" content="{gen.esc(description)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{SITE}{item['hero']}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{gen.esc(title)}"><meta name="twitter:description" content="{gen.esc(description)}"><meta name="twitter:image" content="{SITE}{item['hero']}">
<link rel="stylesheet" href="/assets/css/site.css?v=20260907-layoutfix1"><link rel="stylesheet" href="/assets/css/marketplace.css?v=20260902-mobileux2"><script type="application/ld+json">{schema}</script></head>
<body class="marketplace-discovery"><a class="skip-link" href="#main">Bỏ qua điều hướng</a>
<header class="site-header"><div class="container nav"><a class="brand" href="/" aria-label="Lumi Hanoi – Trang chủ"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="primary-nav">Menu</button><nav id="primary-nav" class="nav-links" data-nav-links data-open="false" aria-label="Điều hướng chính"><a href="/tong-quan-lumi-hanoi/">Tổng quan</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a><a href="/tien-do-lumi-hanoi/">Tiến độ</a><a href="/tin-tuc/">Tin tức</a><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/" aria-current="page">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a></nav></div></header>
<main id="main"><div class="container breadcrumb"><a href="/">Trang chủ</a><span aria-hidden="true">/</span><a href="/cho-thue-lumi-hanoi/">Cho thuê Lumi Hanoi</a><span aria-hidden="true">/</span><a href="/{item['phase_slug']}/">{gen.esc(item['phase_name'])}</a><span aria-hidden="true">/</span>Tòa {tower}</div>
<header class="article-hero marketplace-hero"><img class="article-hero-media" src="{item['hero']}" alt="Cho thuê tòa {tower} Lumi Hanoi" width="1600" height="900" decoding="async"><div class="container"><p class="eyebrow">Quỹ thuê theo tòa · {current}</p><h1>Cho thuê tòa {tower} Lumi Hanoi</h1><p class="lead">Xem riêng quỹ căn thuê tại tòa {tower} thuộc {gen.esc(item['phase_name'])}. Trước khi so giá, đối chiếu đúng loại căn, diện tích, tầng và mặt bằng tòa.</p><div class="hero-actions"><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#cho-thue">Đăng tin tòa {tower}</a><a class="btn" href="{floorplan}">Xem mặt bằng {tower}</a></div></div></header>
<section class="marketplace-section" aria-labelledby="tower-rent-listings"><div class="container"><div class="marketplace-heading"><div><p class="eyebrow">Tin đã duyệt đang công khai</p><h2 id="tower-rent-listings">Căn tòa {tower} đang cho thuê</h2></div><div class="marketplace-actions"><span class="marketplace-count">{count} tin đăng</span><a class="btn btn-primary" href="/dang-tin-lumi-hanoi/#cho-thue">+ Đăng tin</a></div></div><div class="listing-grid">{cards}</div></div></section>
<div class="container article-layout reading-shell article-layout--with-sidebar"><article class="article"><h2>Giá thuê và nguồn cung tòa {tower}</h2><p>Hệ thống hiện ghi nhận <strong>{count} căn hộ</strong> cho thuê đã duyệt tại tòa {tower}. Giá thuê chào trung bình từ các tin có giá là <strong>{gen.esc(average_price(rows))}</strong>. Đây là giá rao tham khảo, không phải mức giá giao dịch bắt buộc.</p><div class="facts-grid"><div class="fact-card"><strong>{count} tin</strong><span>Quỹ thuê tòa {tower}</span></div><div class="fact-card"><strong>{gen.esc(average_price(rows))}</strong><span>Giá thuê chào trung bình</span></div></div>
<h2>Loại căn đang có tại tòa {tower}</h2><p>{gen.esc(unit_mix(rows))}. Quỹ thuê thay đổi theo tin được duyệt hoặc gỡ khỏi hệ thống.</p><nav class="detail-related" aria-label="Thuê theo loại căn">{unit_links(rows)}</nav>
<h2>Mặt bằng tòa {tower}</h2><p>Đối chiếu mặt bằng trước khi so hai căn cùng số phòng để kiểm tra đúng vị trí, tầng và cấu hình căn hộ.</p><nav class="detail-related" aria-label="Tra cứu tòa {tower}"><a href="{floorplan}">Mặt bằng {tower}</a><a href="/{item['phase_slug']}/">Thuê {gen.esc(item['phase_name'])}</a><a href="/gia-can-ho-lumi-hanoi/#market-index-{tower.lower()}">Market Index {tower}</a></nav>
<h2>Các tòa khác trong {gen.esc(item['phase_name'])}</h2><nav class="detail-related" aria-label="Các tòa khác">{sibling_links(item,rows_by_tower)}</nav><h2>Chính sách index dữ liệu</h2><p>{gen.esc(status)} Ngưỡng này giúp Google tập trung vào landing có quỹ thuê thật thay vì index hàng loạt trang lọc mỏng.</p></article><aside><div class="toc"><strong>Đi nhanh</strong><a href="#tower-rent-listings">Căn đang thuê</a><a href="{floorplan}">Mặt bằng {tower}</a><a href="/{item['phase_slug']}/">Quỹ {gen.esc(item['phase_name'])}</a><a href="/gia-can-ho-lumi-hanoi/#market-index-{tower.lower()}">Market Index</a><a href="/cho-thue-lumi-hanoi/">Quỹ thuê tổng</a></div></aside></div></main>
<footer class="site-footer"><div class="container footer-grid"><div><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">LH</span><span>LUMI HANOI</span></a><p>Cổng thông tin dự án &amp; thị trường căn hộ.</p></div><div><nav class="footer-links" aria-label="Điều hướng cuối trang"><a href="/mua-ban-lumi-hanoi/">Mua bán</a><a href="/cho-thue-lumi-hanoi/">Cho thuê</a><a href="/dang-tin-lumi-hanoi/">Đăng tin</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a></nav><p class="disclaimer">Website thông tin và giao dịch độc lập, không phải website chính thức của CapitaLand Development.</p></div></div></footer><script src="/assets/js/site.js?v=20260907-performance1" defer></script></body></html>'''


def cluster(rows_by_tower: dict[str,list[dict]]) -> str:
    links="".join(f'<a href="/{item["slug"]}/">Tòa {item["tower"]} · {len(rows_by_tower[item["tower"]])} căn</a>' for item in TOWERS)
    return f'{CLUSTER_START}\n<section class="section section-alt" aria-labelledby="rent-tower-title"><div class="container"><div class="section-heading"><p class="eyebrow">Tìm theo tòa</p><h2 id="rent-tower-title">Cho thuê Lumi Hanoi theo từng tòa</h2><p>Tra cứu S1–S6, P1–P2 và E1–E2 bằng landing hữu hạn. Tòa chưa đủ quỹ vẫn phục vụ điều hướng nhưng không được đưa vào chỉ mục Google.</p></div><nav class="detail-related" aria-label="Cho thuê theo từng tòa">{links}</nav></div></section>\n{CLUSTER_END}'


def update_hub(rows_by_tower: dict[str,list[dict]]) -> None:
    path=gen.ROOT/"cho-thue-lumi-hanoi"/"index.html"; raw=path.read_text(encoding="utf-8"); block=cluster(rows_by_tower)
    if CLUSTER_START in raw and CLUSTER_END in raw:
        raw=re.sub(re.escape(CLUSTER_START)+r".*?"+re.escape(CLUSTER_END),lambda _:block,raw,count=1,flags=re.S)
    elif "<!-- RENT-SEO-CLUSTER:START -->" in raw:
        raw=raw.replace("<!-- RENT-SEO-CLUSTER:START -->",block+"\n<!-- RENT-SEO-CLUSTER:START -->",1)
    else:
        raw=raw.replace("</main>",block+"\n</main>",1)
    path.write_text(raw,encoding="utf-8")


def update_phase_pages(rows_by_tower: dict[str,list[dict]]) -> None:
    phase_first={}
    for item in TOWERS: phase_first.setdefault(item["phase"],item)
    for phase,item in phase_first.items():
        path=gen.ROOT/item["phase_slug"]/"index.html"
        if not path.is_file(): continue
        members=[tower for tower in TOWERS if tower["phase"]==phase]
        links="".join(f'<a href="/{tower["slug"]}/">Tòa {tower["tower"]} · {len(rows_by_tower[tower["tower"]])} căn</a>' for tower in members)
        block=f'{CLUSTER_START}\n<h2>Cho thuê {gen.esc(item["phase_name"])} theo từng tòa</h2><p>Đi từ phân khu đến đúng tòa, mặt bằng và tin chi tiết. Tòa chưa đủ dữ liệu được giữ noindex.</p><nav class="detail-related" aria-label="Cho thuê theo tòa">{links}</nav>\n{CLUSTER_END}'
        raw=path.read_text(encoding="utf-8")
        if CLUSTER_START in raw and CLUSTER_END in raw: raw=re.sub(re.escape(CLUSTER_START)+r".*?"+re.escape(CLUSTER_END),lambda _:block,raw,count=1,flags=re.S)
        else: raw=raw.replace("</article>",block+"\n</article>",1)
        path.write_text(raw,encoding="utf-8")


def update_sitemap(rows_by_tower: dict[str,list[dict]], today: date) -> None:
    raw=SITEMAP.read_text(encoding="utf-8")
    for item in TOWERS:
        canonical=re.escape(f"{SITE}/{item['slug']}/")
        raw=re.sub(rf"\s*<url>\s*<loc>{canonical}</loc>.*?</url>","",raw,flags=re.S)
    entries=[]
    for item in TOWERS:
        rows=rows_by_tower[item["tower"]]
        if len(rows)<INDEX_THRESHOLD: continue
        entries.append(f'  <url><loc>{SITE}/{item["slug"]}/</loc><lastmod>{latest_date(rows,today)}</lastmod><changefreq>daily</changefreq><priority>0.7</priority></url>')
    if entries: raw=raw.replace("</urlset>","\n"+"\n".join(entries)+"\n</urlset>",1)
    SITEMAP.write_text(raw.rstrip()+"\n",encoding="utf-8")


def main() -> None:
    today=date.today(); listings=gen.fetch_approved(); rows_by_tower={item["tower"]:tower_rows(listings,item["tower"]) for item in TOWERS}
    for item in TOWERS:
        target=gen.ROOT/item["slug"]/"index.html"; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(render_page(item,rows_by_tower[item["tower"]],rows_by_tower,today),encoding="utf-8")
    update_hub(rows_by_tower); update_phase_pages(rows_by_tower); update_sitemap(rows_by_tower,today)
    indexed=[item["tower"] for item in TOWERS if len(rows_by_tower[item["tower"]])>=INDEX_THRESHOLD]
    print("Generated rent tower SEO pages. Indexed towers: "+(", ".join(indexed) if indexed else "none"))

if __name__=="__main__": main()
