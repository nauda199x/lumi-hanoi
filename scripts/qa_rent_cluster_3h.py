#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
import xml.etree.ElementTree as ET

import generate_marketplace_seo as gen
import generate_rent_category_seo as rent
import generate_rent_tower_seo as towers
import strengthen_rent_hub_seo as phases
import strengthen_rent_cluster_3h as h

ROOT=gen.ROOT

def fail(msg): raise SystemExit(msg)
def read(path: Path) -> str:
    if not path.is_file(): fail(f"missing {path}")
    return path.read_text(encoding="utf-8")
def in_sitemap(raw: str, url: str) -> bool: return f"<loc>{url}</loc>" in raw
def robots(raw: str) -> str:
    m=re.search(r'<meta\s+name="robots"\s+content="([^"]+)">',raw,re.I)
    return m.group(1) if m else ""
def h1(raw: str) -> int: return len(re.findall(r"<h1\b",raw,re.I))

def main():
    # Rebuild the rental layer in workflow order so QA covers generators, not stale committed HTML.
    rent.main(); phases.main(); towers.main(); h.main()
    listings=gen.fetch_approved(); today=__import__('datetime').date.today()
    tower_counts={t:len(h.tower_rows(listings,t)) for t in h.TOWER_TO_ITEM}
    unit_counts={item['unit']:len(h.unit_rows(listings,item['unit'])) for item in rent.CATEGORIES}
    phase_counts={item['phase']:len(h.phase_rows(listings,item['phase'])) for item in phases.PHASES}
    sitemap=read(ROOT/'sitemap.xml'); ET.parse(ROOT/'sitemap.xml')

    for item in towers.TOWERS:
        tower=item['tower']; count=tower_counts[tower]; eligible=count>=h.INDEX_THRESHOLD
        path=ROOT/item['slug']/'index.html'; raw=read(path); url=f"{gen.SITE}/{item['slug']}/"
        if h1(raw)!=1: fail(f"{tower}: H1 count")
        if f'<link rel="canonical" href="{url}">' not in raw: fail(f"{tower}: canonical")
        if ('noindex' not in robots(raw)) != eligible: fail(f"{tower}: robots gate count={count}")
        if in_sitemap(sitemap,url) != eligible: fail(f"{tower}: sitemap gate count={count}")
        for needed in (gen.tower_link(tower),f'/gia-can-ho-lumi-hanoi/#market-index-{tower.lower()}',f'/{item["phase_slug"]}/'):
            if needed not in raw: fail(f"{tower}: missing link {needed}")
        if 'Shop chân đế' in raw or 'Shop chân' in raw: fail(f"{tower}: shop leaked into apartment tower page")

    for item in rent.CATEGORIES:
        unit=item['unit']; count=unit_counts[unit]; eligible=count>=h.INDEX_THRESHOLD
        raw=read(ROOT/item['slug']/'index.html'); url=f"{gen.SITE}/{item['slug']}/"
        if ('noindex' not in robots(raw)) != eligible: fail(f"{unit}: robots gate count={count}")
        if in_sitemap(sitemap,url) != eligible: fail(f"{unit}: sitemap gate count={count}")
        if h.BLOCK_START not in raw or 'data-rent-3h="unit"' not in raw: fail(f"{unit}: 3H benchmark missing")

    for item in phases.PHASES:
        phase=item['phase']; count=phase_counts[phase]; eligible=count>=h.INDEX_THRESHOLD
        raw=read(ROOT/item['slug']/'index.html'); url=f"{gen.SITE}/{item['slug']}/"
        if ('noindex' not in robots(raw)) != eligible: fail(f"{phase}: robots gate count={count}")
        if in_sitemap(sitemap,url) != eligible: fail(f"{phase}: sitemap gate count={count}")
        if h.BLOCK_START not in raw or 'data-rent-3h="phase"' not in raw: fail(f"{phase}: 3H benchmark missing")
        if towers.CLUSTER_START not in raw: fail(f"{phase}: tower cluster missing")

    hub=read(ROOT/'cho-thue-lumi-hanoi'/'index.html')
    if towers.CLUSTER_START not in hub: fail('rent hub missing tower cluster')
    for item in towers.TOWERS:
        if f'/{item["slug"]}/' not in hub: fail(f'hub missing {item["tower"]} tower link')

    price=read(ROOT/'gia-can-ho-lumi-hanoi'/'index.html')
    for tower,count in tower_counts.items():
        clean=f'/cho-thue-toa-{tower.lower()}-lumi-hanoi/'
        fallback=f'/cho-thue-lumi-hanoi/#tower={tower}'
        expected=clean if count>=h.INDEX_THRESHOLD else fallback
        if expected not in price: fail(f'Market Index rent target wrong for {tower}')
        floor=read(ROOT/gen.tower_link(tower).lstrip('/')/'index.html')
        bridge=re.search(re.escape(h.BRIDGE_START)+r'(.*?)'+re.escape(h.BRIDGE_END),floor,re.S)
        if not bridge or expected not in bridge.group(1): fail(f'floorplan bridge rent target wrong for {tower}')

    detail_checked=0
    for marker in (ROOT/'cho-thue-lumi-hanoi').rglob(gen.MARKER):
        raw=read(marker.parent/'index.html'); tower=h.detail_value(raw,'tower').upper(); unit=h.detail_value(raw,'unit')
        expected_tower=h.clean_tower_url(tower,tower_counts); expected_unit=h.clean_unit_url(unit,unit_counts)
        if expected_tower not in raw: fail(f'detail same-tower target wrong: {marker.parent.name}')
        if expected_unit not in raw: fail(f'detail same-unit target wrong: {marker.parent.name}')
        detail_checked+=1
    if not detail_checked: fail('no rental detail pages checked')

    # 3H post-processing itself must be idempotent.
    tracked=[ROOT/'sitemap.xml',ROOT/'cho-thue-lumi-hanoi'/'index.html',ROOT/'gia-can-ho-lumi-hanoi'/'index.html']
    tracked += [ROOT/item['slug']/'index.html' for item in towers.TOWERS]
    before={p:read(p) for p in tracked}; h.main(); after={p:read(p) for p in tracked}
    if before!=after: fail('3H postprocessor is not idempotent')
    print(f"3H Rental SEO QA: PASS — units={unit_counts}; phases={phase_counts}; towers={tower_counts}; details={detail_checked}")

if __name__=='__main__': main()
