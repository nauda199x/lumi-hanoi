#!/usr/bin/env python3
from __future__ import annotations
import enhance_marketplace_conversion as conv
import generate_marketplace_seo as gen
import generate_sale_tower_seo as sale

def fail(msg): raise SystemExit(msg)
def read(path):
    if not path.is_file(): fail(f'missing {path}')
    return path.read_text(encoding='utf-8')
def main():
    conv.main()
    saved=read(gen.ROOT/'tin-da-luu-lumi-hanoi/index.html')
    if '<meta name="robots" content="noindex,follow">' not in saved: fail('saved listings page must be noindex,follow')
    sitemap=read(gen.ROOT/'sitemap.xml')
    if 'tin-da-luu-lumi-hanoi' in sitemap: fail('saved listings page must not enter sitemap')
    for required in ('data-saved-listings','saved-listings.js','marketplace-conversion.js'):
        if required not in saved: fail(f'saved page missing {required}')
    market=read(gen.ROOT/'gia-can-ho-lumi-hanoi/index.html')
    if market.count(conv.MARKET_START)!=1 or 'data-conversion-surface="market-index"' not in market: fail('Market Index conversion block missing')
    for item in sale.TOWERS:
        raw=read(gen.ROOT/gen.tower_link(item['tower']).lstrip('/')/'index.html')
        if raw.count(conv.FLOOR_START)!=1 or f'Đăng căn {item["tower"]}' not in raw: fail(f'floorplan conversion missing {item["tower"]}')
    checked=0
    for root_name in ('mua-ban-lumi-hanoi','cho-thue-lumi-hanoi'):
        root=gen.ROOT/root_name
        if not root.is_dir(): continue
        for marker in root.rglob(gen.MARKER):
            path=marker.parent/'index.html'; raw=read(path); checked+=1
            if raw.count(conv.DETAIL_START)!=1: fail(f'detail conversion duplicate/missing {path}')
            if '/tin-da-luu-lumi-hanoi/' not in raw or 'data-detail-owner-post' not in raw: fail(f'detail conversion links missing {path}')
            if raw.count(conv.CSS)!=1 or raw.count(conv.JS)!=1: fail(f'conversion assets duplicate/missing {path}')
    if not checked: fail('no listing details checked')
    for slug in ('mua-ban-lumi-hanoi','cho-thue-lumi-hanoi','mua-ban-can-ho-1-phong-ngu-lumi-hanoi','mua-ban-can-ho-2-phong-ngu-lumi-hanoi'):
        raw=read(gen.ROOT/slug/'index.html')
        if raw.count(conv.START)!=1 or 'data-saved-count' not in raw: fail(f'landing conversion missing {slug}')
    js=read(gen.ROOT/'assets/js/marketplace-conversion.js')
    for token in ('marketplace_conversion','data-conversion-action','lumi-saved-listing:','contact_phone'):
        if token=='contact_phone':
            if token in js: fail('saved snapshot must not store phone/contact data')
        elif token not in js: fail(f'conversion js missing {token}')
    if 'fetch(' in js: fail('conversion helper must not send saved data to network')
    saved_js=read(gen.ROOT/'assets/js/saved-listings.js')
    if 'localStorage' not in saved_js or 'fetch(' in saved_js: fail('saved listings must remain local-only')
    print(f'Marketplace conversion QA: PASS — {checked} listing details + 9 floorplans + Market Index + saved-list page')
if __name__=='__main__': main()
