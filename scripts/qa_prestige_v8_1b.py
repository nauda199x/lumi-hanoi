#!/usr/bin/env python3
"""Static acceptance checks for issue #24 / Prestige V8.1B."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def fail(x): print('FAIL:',x,file=sys.stderr); raise SystemExit(1)
m=json.loads((ROOT/'assets/media/prestige/unit-layouts/manifest.v8.1b.json').read_text()); a=m['assets']
if m.get('version')!='8.1B' or len(a)!=22: fail('manifest must contain exactly 22 assets')
keys=['drive_file_id','source_jpg_filename','layout_number','verified_type','bedroom_count','size_class','nfa_sqm','gfa_sqm','local_webp','width','height','sha256','rendered_anchor']
if any(any(k not in x for k in keys) for x in a): fail('incomplete manifest mapping')
if len({x['drive_file_id'] for x in a})!=22 or len({x['local_webp'] for x in a})!=22: fail('Drive IDs and files must be distinct')
checks=[]
for x in a:
 p=ROOT/x['local_webp']; digest=hashlib.sha256(p.read_bytes()).hexdigest(); checks.append(digest)
 if digest!=x['sha256']: fail('checksum mismatch '+str(p))
if len(set(checks))!=22: fail('all drawings must have distinct checksums')
h=(ROOT/'layout-can-ho-lumi-prestige/index.html').read_text()
if h.count('data-layout-card')!=22 or h.count('data-lightbox data-lightbox-alt')!=22: fail('22 rendered cards/images required')
for x in a:
 n=x['layout_number']; url='/'+x['local_webp']
 block=re.search(fr'<section class="layout-card" id="layout-{n}".*?</section>',h,re.S)
 if not block or block.group().count(url)!=2: fail('genuine image missing for layout '+n)
for term in ['rel="canonical" href="https://lumi-hanoi.com/layout-can-ho-lumi-prestige/"','<h1>Layout căn hộ Lumi Prestige</h1>','data-layout-filter="bedrooms"','data-layout-filter="size"','How to use the layout library']:
 if term not in h: fail('page requirement missing: '+term)
for p in ['lumi-prestige/index.html','toa-p1-lumi-hanoi/index.html','toa-p2-lumi-hanoi/index.html']:
 if '/layout-can-ho-lumi-prestige/' not in (ROOT/p).read_text(): fail('internal link missing: '+p)
if 'https://lumi-hanoi.com/layout-can-ho-lumi-prestige/' not in (ROOT/'sitemap.xml').read_text(): fail('sitemap missing')
print('PASS: 22 distinct Prestige layouts, rendered mappings, filters and SEO links')
