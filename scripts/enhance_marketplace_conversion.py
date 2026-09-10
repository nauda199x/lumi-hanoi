#!/usr/bin/env python3
"""3F: add a lightweight conversion layer to marketplace SEO surfaces."""
from __future__ import annotations
import re
from datetime import date, timedelta
from pathlib import Path
import generate_marketplace_seo as gen
import generate_sale_tower_seo as sale

CSS='<link rel="stylesheet" href="/assets/css/marketplace-conversion.css?v=20260910-3f">'
JS='<script src="/assets/js/marketplace-conversion.js?v=20260910-3f" defer></script>'
START='<!-- MARKETPLACE-CONVERSION:START -->'; END='<!-- MARKETPLACE-CONVERSION:END -->'
DETAIL_START='<!-- MARKETPLACE-CONVERSION:DETAIL-START -->'; DETAIL_END='<!-- MARKETPLACE-CONVERSION:DETAIL-END -->'
FLOOR_START='<!-- MARKETPLACE-CONVERSION:FLOOR-START -->'; FLOOR_END='<!-- MARKETPLACE-CONVERSION:FLOOR-END -->'
MARKET_START='<!-- MARKETPLACE-CONVERSION:MARKET-START -->'; MARKET_END='<!-- MARKETPLACE-CONVERSION:MARKET-END -->'
LANDINGS=(
'mua-ban-lumi-hanoi','cho-thue-lumi-hanoi','mua-ban-lumi-signature','mua-ban-lumi-prestige','mua-ban-lumi-elite',
'mua-ban-can-ho-1-phong-ngu-lumi-hanoi','mua-ban-can-ho-2-phong-ngu-lumi-hanoi','mua-ban-can-ho-3-phong-ngu-lumi-hanoi',
'cho-thue-lumi-signature','cho-thue-lumi-prestige','cho-thue-lumi-elite','cho-thue-can-ho-1-phong-ngu-lumi-hanoi','cho-thue-can-ho-2-phong-ngu-lumi-hanoi','cho-thue-can-ho-3-phong-ngu-lumi-hanoi','cho-thue-can-ho-4-phong-ngu-lumi-hanoi','cho-thue-duplex-lumi-hanoi','cho-thue-penthouse-lumi-hanoi','cho-thue-shop-chan-de-lumi-hanoi',
)+tuple(x['slug'] for x in sale.TOWERS)

def marked(raw,start,end,body):
    block=start+'\n'+body+'\n'+end
    if start in raw and end in raw:return re.sub(re.escape(start)+r'.*?'+re.escape(end),lambda _:block,raw,count=1,flags=re.S)
    return raw

def assets(raw):
    if CSS not in raw: raw=raw.replace('</head>',CSS+'\n</head>',1)
    if JS not in raw: raw=raw.replace('</body>',JS+'\n</body>',1)
    return raw

def listing_type(raw):
    return 'rent' if ('data-listing-type="rent"' in raw or '<span data-detail-type>Cho thuê</span>' in raw) else 'sale'

def strip(kind):
    post='/dang-tin-lumi-hanoi/#cho-thue' if kind=='rent' else '/dang-tin-lumi-hanoi/#mua-ban'
    return f'<section class="mp-conversion-strip" data-conversion-surface="landing" aria-label="Hành động nhanh"><div class="mp-conversion-copy"><strong>So sánh căn rồi quay lại khi cần</strong><span>Lưu các tin quan tâm trên thiết bị này, hoặc đăng quỹ căn của anh/chị miễn phí.</span></div><div class="mp-conversion-actions"><a class="mp-conversion-link" href="/tin-da-luu-lumi-hanoi/" data-conversion-action="open_saved_list">Tin đã lưu <span class="mp-saved-count" data-saved-count>0</span></a><a class="mp-conversion-link mp-conversion-link--primary" href="{post}" data-conversion-action="owner_post">Đăng tin miễn phí</a></div></section>'

def enhance_landing(path):
    if not path.is_file():return False
    raw=path.read_text(encoding='utf-8'); raw=assets(raw); body=strip(listing_type(raw)); block=START+'\n'+body+'\n'+END
    if START in raw and END in raw: raw=marked(raw,START,END,body)
    else:
        m=re.search(r'<main\b.*?>.*?</header>',raw,flags=re.S)
        if not m: raise RuntimeError(f'hero not found: {path}')
        raw=raw[:m.end()]+block+raw[m.end():]
    path.write_text(raw,encoding='utf-8'); return True

def enhance_details():
    n=0
    for root_name in ('mua-ban-lumi-hanoi','cho-thue-lumi-hanoi'):
        root=gen.ROOT/root_name
        if not root.is_dir():continue
        for marker in root.rglob(gen.MARKER):
            path=marker.parent/'index.html'; raw=assets(path.read_text(encoding='utf-8')); kind=listing_type(raw); post='/dang-tin-lumi-hanoi/#cho-thue' if kind=='rent' else '/dang-tin-lumi-hanoi/#mua-ban'
            tower_match=re.search(r'<span data-detail-tower>([^<]+)</span>',raw); tower=gen.clean(tower_match.group(1)) if tower_match else ''
            label=f'Có căn {tower} tương tự? Đăng tin miễn phí' if tower else 'Có căn tương tự? Đăng tin miễn phí'
            body=f'<div class="mp-conversion-detail" data-conversion-surface="detail"><a class="mp-conversion-link" href="/tin-da-luu-lumi-hanoi/" data-conversion-action="open_saved_list">Tin đã lưu <span class="mp-saved-count" data-saved-count>0</span></a><a class="mp-conversion-link" data-detail-owner-post href="{post}" data-conversion-action="owner_post">{gen.esc(label)}</a></div>'
            block=DETAIL_START+'\n'+body+'\n'+DETAIL_END
            if DETAIL_START in raw and DETAIL_END in raw:raw=marked(raw,DETAIL_START,DETAIL_END,body)
            else:
                anchor='<p class="ld-contact-note">Liên hệ để xác nhận tình trạng căn và hẹn lịch xem.</p>'
                if anchor not in raw:raise RuntimeError(f'contact anchor missing: {path}')
                raw=raw.replace(anchor,anchor+block,1)
            path.write_text(raw,encoding='utf-8'); n+=1
    shell=gen.ROOT/'tin-dang-lumi-hanoi/index.html'
    if shell.is_file():
        raw=assets(shell.read_text(encoding='utf-8')); body='<div class="mp-conversion-detail" data-conversion-surface="detail"><a class="mp-conversion-link" href="/tin-da-luu-lumi-hanoi/" data-conversion-action="open_saved_list">Tin đã lưu <span class="mp-saved-count" data-saved-count>0</span></a><a class="mp-conversion-link" data-detail-owner-post href="/dang-tin-lumi-hanoi/" data-conversion-action="owner_post">Có căn tương tự? Đăng tin miễn phí</a></div>'; block=DETAIL_START+'\n'+body+'\n'+DETAIL_END
        if DETAIL_START in raw and DETAIL_END in raw:raw=marked(raw,DETAIL_START,DETAIL_END,body)
        else:
            anchor='<p class="ld-contact-note">Liên hệ để xác nhận tình trạng căn và hẹn lịch xem.</p>'
            if anchor in raw: raw=raw.replace(anchor,anchor+block,1)
        shell.write_text(raw,encoding='utf-8')
    return n

def enhance_floorplans():
    n=0
    for item in sale.TOWERS:
        tower=item['tower']; path=gen.ROOT/gen.tower_link(tower).lstrip('/')/'index.html'; raw=assets(path.read_text(encoding='utf-8'))
        body=f'<div class="mp-conversion-inline" data-conversion-surface="floorplan"><div><strong>Chủ căn tòa {tower}?</strong><span>Đăng quỹ bán hoặc cho thuê để tiếp cận người đang tra cứu đúng mặt bằng tòa.</span></div><div class="mp-conversion-actions"><a class="mp-conversion-link" href="/tin-da-luu-lumi-hanoi/" data-conversion-action="open_saved_list">Tin đã lưu <span class="mp-saved-count" data-saved-count>0</span></a><a class="mp-conversion-link mp-conversion-link--primary" href="/dang-tin-lumi-hanoi/" data-conversion-action="floorplan_owner_post">Đăng căn {tower}</a></div></div>'
        block=FLOOR_START+'\n'+body+'\n'+FLOOR_END
        if FLOOR_START in raw and FLOOR_END in raw: raw=marked(raw,FLOOR_START,FLOOR_END,body)
        else:
            pos=raw.find('<!-- TOWER-MARKETPLACE-BRIDGE:END -->')
            if pos<0:raise RuntimeError(f'bridge missing: {path}')
            raw=raw[:pos]+block+raw[pos:]
        path.write_text(raw,encoding='utf-8'); n+=1
    return n

def enhance_market():
    path=gen.ROOT/'gia-can-ho-lumi-hanoi/index.html'; raw=assets(path.read_text(encoding='utf-8'))
    body='<div class="mp-conversion-market" data-conversion-surface="market-index"><div class="mp-conversion-copy"><strong>Đang cân giá một căn Lumi Hanoi?</strong><span>Đối chiếu Market Index với quỹ đang rao, lưu các căn đáng chú ý hoặc đăng căn của anh/chị để thị trường so sánh trực tiếp.</span></div><div class="mp-conversion-actions"><a class="mp-conversion-link" href="/tin-da-luu-lumi-hanoi/" data-conversion-action="market_saved">Tin đã lưu <span class="mp-saved-count" data-saved-count>0</span></a><a class="mp-conversion-link" href="/mua-ban-lumi-hanoi/#quy-can" data-conversion-action="market_sale">Quỹ đang bán</a><a class="mp-conversion-link mp-conversion-link--primary" href="/dang-tin-lumi-hanoi/" data-conversion-action="market_owner_post">Đăng căn của tôi</a></div></div>'
    block=MARKET_START+'\n'+body+'\n'+MARKET_END
    if MARKET_START in raw and MARKET_END in raw:raw=marked(raw,MARKET_START,MARKET_END,body)
    else:
        anchor='<!-- MARKET-TOWER-INDEX:END -->'
        if anchor not in raw:raise RuntimeError('Market Index block missing')
        raw=raw.replace(anchor,anchor+'\n'+block,1)
    path.write_text(raw,encoding='utf-8')

def fresh_badges(listings):
    threshold=(date.today()-timedelta(days=3)).isoformat(); recent={gen.clean(x.get('slug')) for x in listings if gen.clean(x.get('slug')) and gen.date_only(x.get('approved_at') or x.get('created_at'))>=threshold}
    if not recent:return 0
    changed=0
    for slug in LANDINGS:
        path=gen.ROOT/slug/'index.html'
        if not path.is_file():continue
        raw=path.read_text(encoding='utf-8')
        def repl(m):
            nonlocal changed
            block=m.group(0); hit=any(f'/{s}/' in block for s in recent)
            if hit and 'mp-fresh-badge' not in block and '<h3>' in block:
                changed+=1; return block.replace('<h3>','<span class="mp-fresh-badge">Mới cập nhật</span><h3>',1)
            return block
        raw=re.sub(r'<article\b[^>]*data-static-listing-card[^>]*>.*?</article>',repl,raw,flags=re.S); path.write_text(raw,encoding='utf-8')
    return changed

def main():
    listings=gen.fetch_approved(); pages=sum(enhance_landing(gen.ROOT/x/'index.html') for x in LANDINGS); details=enhance_details(); floors=enhance_floorplans(); enhance_market(); badges=fresh_badges(listings)
    print(f'3F conversion layer: landings={pages}, details={details}, floorplans={floors}, fresh badges={badges}')
if __name__=='__main__': main()
