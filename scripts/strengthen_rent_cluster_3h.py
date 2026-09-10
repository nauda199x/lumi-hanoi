#!/usr/bin/env python3
"""3H: gate and interlink the finite Lumi Hanoi rental SEO cluster.

Runs after the existing rental generators, rental-tower generator and 3D entity
loop. It keeps only inventory-backed rental intent pages indexable, enriches
unit/phase landings with live asking-price/tower context, and replaces hash-only
navigation with clean tower/unit landings when the corresponding page is
eligible for indexing.
"""
from __future__ import annotations

import re
from datetime import date
from statistics import mean

import generate_marketplace_seo as gen
import generate_rent_category_seo as rent
import generate_rent_tower_seo as towers
import strengthen_rent_hub_seo as phases

SITE = gen.SITE
ROOT = gen.ROOT
SITEMAP = ROOT / "sitemap.xml"
INDEX_THRESHOLD = 2
BLOCK_START = "<!-- RENT-3H-INTENT:START -->"
BLOCK_END = "<!-- RENT-3H-INTENT:END -->"
BRIDGE_START = "<!-- TOWER-MARKETPLACE-BRIDGE:START -->"
BRIDGE_END = "<!-- TOWER-MARKETPLACE-BRIDGE:END -->"
UNIT_TO_SLUG = {item["unit"]: item["slug"] for item in rent.CATEGORIES}
TOWER_TO_ITEM = {item["tower"]: item for item in towers.TOWERS}


def clean(value) -> str:
    return gen.clean(value)


def rental_apartments(listings: list[dict]) -> list[dict]:
    return [row for row in listings if row.get("listing_type") == "rent" and clean(row.get("unit_type")) in gen.APARTMENT_UNIT_TYPES and clean(row.get("slug"))]


def unit_rows(listings: list[dict], unit: str) -> list[dict]:
    return [row for row in rental_apartments(listings) if clean(row.get("unit_type")) == unit]


def phase_rows(listings: list[dict], phase_name: str) -> list[dict]:
    target=phase_name.casefold()
    return [row for row in rental_apartments(listings) if clean(row.get("phase")).casefold()==target]


def tower_rows(listings: list[dict], tower: str) -> list[dict]:
    return [row for row in rental_apartments(listings) if clean(row.get("tower")).upper()==tower.upper()]


def avg_price(rows: list[dict]) -> str:
    values=[gen.numeric(row.get("price_vnd")) for row in rows]; values=[v for v in values if v]
    return gen.format_market_price(mean(values),"rent") if values else "Chưa đủ dữ liệu"


def latest(rows: list[dict], today: date) -> str:
    values=[gen.date_only(row.get("approved_at") or row.get("created_at")) for row in rows]; values=[v for v in values if v]
    return max(values) if values else today.replace(day=1).isoformat()


def set_robots(raw: str, indexable: bool) -> str:
    value="index,follow,max-image-preview:large" if indexable else "noindex,follow,max-image-preview:large"
    if re.search(r'<meta\s+name="robots"\s+content="[^"]*">',raw,flags=re.I):
        return re.sub(r'<meta\s+name="robots"\s+content="[^"]*">',f'<meta name="robots" content="{value}">',raw,count=1,flags=re.I)
    canonical=re.search(r'(<link\s+rel="canonical"\s+href="[^"]+">)',raw,flags=re.I)
    if not canonical: raise RuntimeError("Cannot locate canonical while setting robots")
    return raw[:canonical.end()]+f'\n<meta name="robots" content="{value}">'+raw[canonical.end():]


def upsert_block(raw: str, block: str) -> str:
    if BLOCK_START in raw and BLOCK_END in raw:
        return re.sub(re.escape(BLOCK_START)+r".*?"+re.escape(BLOCK_END),lambda _:block,raw,count=1,flags=re.S)
    anchor='<div class="container article-layout'
    pos=raw.find(anchor)
    if pos>=0: return raw[:pos]+block+'\n'+raw[pos:]
    return raw.replace("</main>",block+"\n</main>",1)


def tower_distribution(rows: list[dict]) -> str:
    counts={tower:0 for tower in TOWER_TO_ITEM}
    for row in rows:
        tower=clean(row.get("tower")).upper()
        if tower in counts: counts[tower]+=1
    parts=[]
    for tower,count in counts.items():
        if not count: continue
        item=TOWER_TO_ITEM[tower]
        parts.append(
            f'<div class="fact-card"><strong>{tower} · {count} căn</strong><span>'
            f'<a href="/{item["slug"]}/">Quỹ thuê {tower}</a> · '
            f'<a href="{gen.tower_link(tower)}">Mặt bằng {tower}</a> · '
            f'<a href="/gia-can-ho-lumi-hanoi/#market-index-{tower.lower()}">Market Index</a></span></div>'
        )
    return ''.join(parts) or '<p>Chưa có đủ dữ liệu theo tòa.</p>'


def unit_mix(rows: list[dict]) -> str:
    counts={}
    for row in rows:
        unit=clean(row.get("unit_type"))
        if unit: counts[unit]=counts.get(unit,0)+1
    parts=[]
    for unit,count in sorted(counts.items()):
        slug=UNIT_TO_SLUG.get(unit)
        if slug: parts.append(f'<a href="/{slug}/">{gen.esc(unit)} · {count} căn</a>')
    return ''.join(parts) or '<span>Chưa có quỹ căn công khai.</span>'


def unit_block(unit: str, rows: list[dict], indexable: bool) -> str:
    status=(f"Trang đủ điều kiện index với {len(rows)} tin thuê {unit} công khai." if indexable else f"Trang tạm noindex vì mới có {len(rows)} tin; cần tối thiểu {INDEX_THRESHOLD} tin công khai.")
    return (
        f'{BLOCK_START}\n<section class="section" data-rent-3h="unit"><div class="container"><div class="section-heading"><div><p class="eyebrow">Dữ liệu thuê theo loại căn</p><h2>Giá thuê và tòa đang có căn {gen.esc(unit)}</h2></div></div>'
        f'<p>Hiện có <strong>{len(rows)} căn {gen.esc(unit)}</strong> cho thuê đã duyệt; giá chào trung bình từ các tin có giá là <strong>{gen.esc(avg_price(rows))}</strong>. Giá rao có thể thay đổi theo tòa, tầng, nội thất và thời điểm.</p>'
        f'<div class="facts-grid"><div class="fact-card"><strong>{len(rows)} tin</strong><span>Quỹ thuê {gen.esc(unit)} đang công khai</span></div><div class="fact-card"><strong>{gen.esc(avg_price(rows))}</strong><span>Giá thuê chào trung bình</span></div></div>'
        f'<h3>Căn {gen.esc(unit)} hiện nằm ở tòa nào?</h3><div class="facts-grid">{tower_distribution(rows)}</div>'
        f'<p class="notice"><strong>Chính sách index:</strong> {gen.esc(status)} Hệ thống chỉ mở index khi có quỹ thật để tránh tạo landing mỏng.</p></div></section>\n{BLOCK_END}'
    )


def phase_block(item: dict, rows: list[dict], indexable: bool) -> str:
    status=(f"Trang đủ điều kiện index với {len(rows)} tin thuê công khai." if indexable else f"Trang tạm noindex vì mới có {len(rows)} tin; cần tối thiểu {INDEX_THRESHOLD} tin công khai.")
    return (
        f'{BLOCK_START}\n<section class="section" data-rent-3h="phase"><div class="container"><div class="section-heading"><div><p class="eyebrow">Dữ liệu thuê theo phân khu</p><h2>Quỹ thuê {gen.esc(item["label"])}</h2></div></div>'
        f'<p>Hiện có <strong>{len(rows)} căn hộ</strong> cho thuê đã duyệt tại {gen.esc(item["label"])}; giá chào trung bình là <strong>{gen.esc(avg_price(rows))}</strong>.</p>'
        f'<div class="facts-grid"><div class="fact-card"><strong>{len(rows)} tin</strong><span>Nguồn cung đang công khai</span></div><div class="fact-card"><strong>{gen.esc(avg_price(rows))}</strong><span>Giá thuê chào trung bình</span></div></div>'
        f'<h3>Loại căn đang có</h3><nav class="detail-related" aria-label="Loại căn thuê trong {gen.esc(item["label"])}">{unit_mix(rows)}</nav>'
        f'<h3>Phân bổ theo tòa</h3><div class="facts-grid">{tower_distribution(rows)}</div>'
        f'<p class="notice"><strong>Chính sách index:</strong> {gen.esc(status)}</p></div></section>\n{BLOCK_END}'
    )


def remove_sitemap(raw: str, url: str) -> str:
    return re.sub(rf"\s*<url>\s*<loc>{re.escape(url)}</loc>.*?</url>","",raw,flags=re.S)


def add_sitemap(raw: str, url: str, modified: str, priority: str) -> str:
    entry=f'  <url><loc>{url}</loc><lastmod>{modified}</lastmod><changefreq>daily</changefreq><priority>{priority}</priority></url>'
    return raw.replace("</urlset>","\n"+entry+"\n</urlset>",1)


def gate_pages(listings: list[dict], today: date) -> tuple[dict[str,int],dict[str,int]]:
    sitemap=SITEMAP.read_text(encoding="utf-8")
    unit_counts={}; phase_counts={}
    for item in rent.CATEGORIES:
        rows=unit_rows(listings,item["unit"]); unit_counts[item["unit"]]=len(rows); indexable=len(rows)>=INDEX_THRESHOLD
        path=ROOT/item["slug"]/"index.html"; raw=path.read_text(encoding="utf-8"); raw=set_robots(raw,indexable); raw=upsert_block(raw,unit_block(item["unit"],rows,indexable)); path.write_text(raw,encoding="utf-8")
        url=f'{SITE}/{item["slug"]}/'; sitemap=remove_sitemap(sitemap,url)
        if indexable: sitemap=add_sitemap(sitemap,url,latest(rows,today),"0.8")
    for item in phases.PHASES:
        rows=phase_rows(listings,item["phase"]); phase_counts[item["phase"]]=len(rows); indexable=len(rows)>=INDEX_THRESHOLD
        path=ROOT/item["slug"]/"index.html"; raw=path.read_text(encoding="utf-8"); raw=set_robots(raw,indexable); raw=upsert_block(raw,phase_block(item,rows,indexable)); path.write_text(raw,encoding="utf-8")
        url=f'{SITE}/{item["slug"]}/'; sitemap=remove_sitemap(sitemap,url)
        if indexable: sitemap=add_sitemap(sitemap,url,latest(rows,today),"0.85")
    SITEMAP.write_text(sitemap.rstrip()+"\n",encoding="utf-8")
    return unit_counts,phase_counts


def clean_tower_url(tower: str, tower_counts: dict[str,int]) -> str:
    item=TOWER_TO_ITEM.get(tower)
    if item and tower_counts.get(tower,0)>=INDEX_THRESHOLD: return f'/{item["slug"]}/'
    return f'/cho-thue-lumi-hanoi/#tower={tower}' if tower else '/cho-thue-lumi-hanoi/'


def clean_unit_url(unit: str, unit_counts: dict[str,int]) -> str:
    slug=UNIT_TO_SLUG.get(unit)
    if slug and unit_counts.get(unit,0)>=INDEX_THRESHOLD: return f'/{slug}/'
    return f'/cho-thue-lumi-hanoi/#bedroom={unit}' if unit else '/cho-thue-lumi-hanoi/'


def update_floorplans(tower_counts: dict[str,int]) -> int:
    changed=0
    for tower,item in TOWER_TO_ITEM.items():
        path=ROOT/gen.tower_link(tower).lstrip('/')/'index.html'; raw=path.read_text(encoding='utf-8')
        match=re.search(re.escape(BRIDGE_START)+r'(.*?)'+re.escape(BRIDGE_END),raw,flags=re.S)
        if not match: continue
        block=match.group(1); new=re.sub(r'(<a\s+class="btn"\s+data-market-cta="rent"\s+href=")[^"]+("[^>]*>)',lambda m:m.group(1)+clean_tower_url(tower,tower_counts)+m.group(2),block,count=1)
        if new!=block:
            raw=raw[:match.start(1)]+new+raw[match.end(1):]; path.write_text(raw,encoding='utf-8'); changed+=1
    return changed


def update_market_index(tower_counts: dict[str,int]) -> int:
    path=ROOT/'gia-can-ho-lumi-hanoi'/'index.html'; raw=path.read_text(encoding='utf-8'); changed=0
    for tower in TOWER_TO_ITEM:
        old=f'/cho-thue-lumi-hanoi/#tower={tower}'; new=clean_tower_url(tower,tower_counts)
        if old in raw and new!=old: raw=raw.replace(old,new); changed+=1
    path.write_text(raw,encoding='utf-8'); return changed


def detail_value(raw: str, attr: str) -> str:
    match=re.search(rf'<(?:span|b)\s+data-detail-{re.escape(attr)}>([^<]+)</(?:span|b)>',raw,flags=re.I)
    return clean(match.group(1)) if match else ''


def update_details(tower_counts: dict[str,int], unit_counts: dict[str,int]) -> int:
    changed=0; root=ROOT/'cho-thue-lumi-hanoi'
    for marker in root.rglob(gen.MARKER):
        path=marker.parent/'index.html'; raw=path.read_text(encoding='utf-8'); tower=detail_value(raw,'tower').upper(); unit=detail_value(raw,'unit')
        new=re.sub(r'(<a\s+data-detail-same-tower\s+href=")[^"]+("[^>]*>)',lambda m:m.group(1)+clean_tower_url(tower,tower_counts)+m.group(2),raw,count=1,flags=re.I)
        new=re.sub(r'(<a\s+data-detail-same-unit\s+href=")[^"]+("[^>]*>)',lambda m:m.group(1)+clean_unit_url(unit,unit_counts)+m.group(2),new,count=1,flags=re.I)
        if new!=raw: path.write_text(new,encoding='utf-8'); changed+=1
    return changed


def main() -> None:
    today=date.today(); listings=gen.fetch_approved(); unit_counts,phase_counts=gate_pages(listings,today); tower_counts={tower:len(tower_rows(listings,tower)) for tower in TOWER_TO_ITEM}
    floorplans=update_floorplans(tower_counts); market=update_market_index(tower_counts); details=update_details(tower_counts,unit_counts)
    print(f'3H rent cluster: units={unit_counts}; phases={phase_counts}; towers={tower_counts}; floorplans={floorplans}; market={market}; details={details}')

if __name__=='__main__': main()
