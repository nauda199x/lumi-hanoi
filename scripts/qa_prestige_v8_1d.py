#!/usr/bin/env python3
"""Static acceptance checks for issue #28 / Prestige V8.1D."""
import json, re, sys
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'layout-can-ho-lumi-prestige/index.html').read_text()
css=(ROOT/'assets/css/site.css').read_text()
js=(ROOT/'assets/js/site.js').read_text()
assets=json.loads((ROOT/'assets/media/prestige/unit-layouts/manifest.v8.1b.json').read_text())['assets']
def fail(s): print('FAIL:',s,file=sys.stderr); raise SystemExit(1)
blocks=re.findall(r'<section class="layout-card".*?</section>',html,re.S)
if len(blocks)!=22: fail('exactly 22 server-rendered cards required')
previews=[]
for asset,block in zip(assets,blocks):
    url='/'+asset['local_webp']; number=asset['layout_number']
    values=(f'id="{asset["rendered_anchor"]}"',asset['verified_type'],f'{asset["bedroom_count"]}BR',asset['size_class'],asset['nfa_sqm'],asset['gfa_sqm'])
    if any(v not in block for v in values): fail(f'Issue #24 mapping changed for layout {number}')
    img=re.search(r'<figure class="layout-preview"><img ([^>]+)>',block)
    if not img or f'src="{url}"' not in img.group(1): fail(f'layout {number} lacks its genuine exact drawing preview')
    if 'loading="lazy"' not in img.group(1): fail(f'layout {number} preview is eagerly loaded')
    dimensions=(re.search(r'width="(\d+)"',img.group(1)),re.search(r'height="(\d+)"',img.group(1)))
    if not all(dimensions) or tuple(int(value.group(1)) for value in dimensions)!=(asset['width'],asset['height']):
        fail(f'layout {number} preview has fabricated intrinsic dimensions')
    previews.append(re.search(r'src="([^"]+)"',img.group(1)).group(1))
    if block.count('class="layout-view-action"')!=1 or f'href="{url}"' not in block: fail(f'layout {number} full-resolution CTA changed')
if len(set(previews))!=22: fail('every card must use its own genuine preview')
if 'grid-template-columns:repeat(2,minmax(0,1fr))' not in css or '@media(max-width:760px){.layout-card-grid{grid-template-columns:1fr}' not in css: fail('responsive premium 2/1-column presentation missing')
if re.search(r'natural(?:Width|Height)\s*\*\s*zoom',js): fail('interactive zoom must use fitted dimensions, not natural image dimensions')
for token in ('Zoom −','Zoom +','Fit / Reset','Close ×',"image.addEventListener('load'",'fittedWidth*zoom','fittedHeight*zoom','zoom+.25','zoom-.25','const fit=()=>{zoom=1',"stage.classList.toggle('is-zoomed',zoomed)",'max-width:100%;max-height:100%;object-fit:contain','min-width:0'):
    if token not in js+css: fail('fit-based lightbox requirement missing: '+token)
if '.lightbox-stage.is-zoomed{display:block}' not in css or '.lightbox-stage{display:flex' not in css or 'overflow:auto' not in css:
    fail('zoomed lightbox stage must switch from centered fit mode to pan-safe overflow layout')
if html.count('data-layout-filter="bedrooms"')!=5 or html.count('data-layout-filter="size"')!=5 or 'data-layout-count' not in html: fail('filters/count changed')
if 'rel="canonical" href="https://lumi-hanoi.com/layout-can-ho-lumi-prestige/"' not in html: fail('canonical changed')
if re.search(r'href="/[^"]*[?&](?:utm_|[^" ]*chatgpt)',html,re.I): fail('tracked internal link found')
for path in ('lumi-prestige/index.html','mat-bang-lumi-hanoi/lumi-prestige/p1/index.html','mat-bang-lumi-hanoi/lumi-prestige/p2/index.html'):
    if '/layout-can-ho-lumi-prestige/' not in (ROOT/path).read_text(): fail('library internal link missing from '+path)
if 'https://lumi-hanoi.com/layout-can-ho-lumi-prestige/' not in (ROOT/'sitemap.xml').read_text(): fail('sitemap entry missing')
print('PASS: V8.1D premium 22-card catalogue, lazy genuine previews, filters and fit-first zoomable lightbox')
