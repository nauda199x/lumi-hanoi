#!/usr/bin/env python3
"""Static acceptance checks for issue #22 / Prestige V8.1A."""
from __future__ import annotations
import hashlib, json, sys
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'assets/media/prestige/manifest.v8.json'
EXPECTED={
'11jadUR3YF3cIZd1MQ5Eg2tm5MQ_45PRF':('P1','Tầng 2–19, 21–22, 24–28','assets/media/prestige/floor-plans/p1-t02-19-21-22-24-28.webp','toa-p1-lumi-hanoi/index.html','p1-tang-2-19-21-22-24-28',2400,3200),
'1ky6AoU-RKfkQQfPggTiTcfD286hP9c1-':('P1','Tầng 20','assets/media/prestige/floor-plans/p1-t20.webp','toa-p1-lumi-hanoi/index.html','p1-tang-20',2400,3200),
'1EriYOtwKs3pD7ETAo_o8BnuNbvZrBaF5':('P1','Tầng 23','assets/media/prestige/floor-plans/p1-t23.webp','toa-p1-lumi-hanoi/index.html','p1-tang-23',2400,3200),
'1vHglsZVk2aqp_t6aKvml1xQo17wQN9WR':('P1','Tầng 29','assets/media/prestige/floor-plans/p1-t29.webp','toa-p1-lumi-hanoi/index.html','p1-tang-29',2400,3200),
'1k_KbeRS92wbVOTF4_XKh18D1kb-CareO':('P2','Tầng 2–12, 14–19, 21–28','assets/media/prestige/floor-plans/p2-t02-12-14-19-21-28.webp','toa-p2-lumi-hanoi/index.html','p2-tang-2-12-14-19-21-28',2400,3201),
'1DGpCt-vZmqeokHQseBvivHTaOKKkWXRI':('P2','Tầng 13','assets/media/prestige/floor-plans/p2-t13.webp','toa-p2-lumi-hanoi/index.html','p2-tang-13',2400,3200),
'11h2HZD-WUqcgPVdMh0gkxK95wjF9_T49':('P2','Tầng 20','assets/media/prestige/floor-plans/p2-t20.webp','toa-p2-lumi-hanoi/index.html','p2-tang-20',2400,3200),
'13cMmDd-E23cakiNCzh68Lr8MmK_wRyRy':('P2','Tầng 29','assets/media/prestige/floor-plans/p2-t29.webp','toa-p2-lumi-hanoi/index.html','p2-tang-29',2400,3200)}
class Parser(HTMLParser):
 def __init__(self): super().__init__(); self.sections={}; self.stack=[]; self.h1=[]; self.canonical=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs); self.stack.append((tag,a))
  if tag=='link' and a.get('rel')=='canonical': self.canonical.append(a.get('href'))
  if tag=='section' and 'floor-plan-section' in a.get('class','').split(): self.sections[a['id']]={'meta':a,'h2':[],'img':[],'link':[],'caption':[]}
  current=next((x for x in reversed(self.stack) if x[0]=='section' and x[1].get('id') in self.sections),None)
  if current and tag=='img': self.sections[current[1]['id']]['img'].append(a)
  if current and tag=='a': self.sections[current[1]['id']]['link'].append(a)
 def handle_data(self,data):
  if not self.stack:return
  if self.stack[-1][0]=='h1':self.h1.append(data.strip())
  current=next((x for x in reversed(self.stack) if x[0]=='section' and x[1].get('id') in self.sections),None)
  if current and self.stack[-1][0] in ('h2','figcaption'):self.sections[current[1]['id']]['h2' if self.stack[-1][0]=='h2' else 'caption'].append(data.strip())
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i][0]==tag:del self.stack[i:];break
def fail(msg):print('FAIL:',msg,file=sys.stderr);raise SystemExit(1)
data=json.loads(MANIFEST.read_text()); assets=data.get('assets',[])
actual={a['source']['drive_file_id']:(a['tower'],a['floor_group'],a['local_file'],a['rendered_page'],a['anchor'],a['width'],a['height']) for a in assets}
if data.get('version')!='8.1A' or len(assets)!=8 or actual!=EXPECTED:fail('manifest must exactly map each authoritative Drive ID to its tower, floor group, local image, page, anchor and dimensions')
if len({hashlib.sha256((ROOT/a['local_file']).read_bytes()).hexdigest() for a in assets})!=8:fail('eight local derivatives must have distinct contents')
parsers={}
for page in {x[3] for x in EXPECTED.values()}:
 parser=Parser();parser.feed((ROOT/page).read_text());parsers[page]=parser
 tower='P1' if 'p1' in page else 'P2'; expected_url=f'https://lumi-hanoi.com/toa-{tower.lower()}-lumi-hanoi/'
 if parser.canonical!=[expected_url] or ''.join(parser.h1)!=f'Tòa {tower} Lumi Hanoi':fail(f'canonical/H1 mismatch on {page}')
 expected_anchors={x[4] for x in EXPECTED.values() if x[0]==tower}
 if set(parser.sections)!=expected_anchors:fail(f'{page} must contain only its four genuine {tower} groups')
for drive_id,(tower,group,local,page,anchor,width,height) in EXPECTED.items():
 section=parsers[page].sections[anchor]; image=section['img']; link=section['link']; url='/'+local
 if section['meta'].get('data-tower')!=tower or section['meta'].get('data-floor-group')!=group:fail(f'rendered metadata mismatch for {drive_id}')
 if len(image)!=1 or len(link)!=1 or image[0].get('src')!=url or link[0].get('href')!=url or 'data-lightbox' not in link[0]:fail(f'exact rendered image/lightbox mismatch for {drive_id}')
 if (image[0].get('width'),image[0].get('height'))!=(str(width),str(height)):fail(f'dimensions mismatch for {drive_id}')
 if image[0].get('loading')!='lazy' or image[0].get('decoding')!='async' or not all(x in image[0].get('alt','') for x in ('mã căn','loại phòng ngủ','NFA','GFA','chú giải')):fail(f'accessibility/performance mismatch for {drive_id}')
 if not ''.join(section['h2']).strip() or not ''.join(section['caption']).strip():fail(f'H2/caption missing for {drive_id}')
overview=(ROOT/'lumi-prestige/index.html').read_text()
if 'floor-plan-section' in overview or 'lumi-prestige-typical-floor.webp' in overview:fail('Prestige overview must not own tower floor-plan sections or render the old generic plan')
if not all(f'/toa-prestige-{x}-lumi-hanoi/' in overview for x in ('1','2')):fail('Prestige overview must link both canonical tower pages')
print('PASS: exact 8 Drive IDs → exact towers/groups/files → exact P1/P2 pages and rendered sections')
