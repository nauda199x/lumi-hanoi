#!/usr/bin/env python3
"""V5.2 floor-plan manifest, tower pages, SEO, source and UX checks."""
import json,re,sys
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
SLUGS=['signature-1','signature-2','signature-3','signature-5','signature-6','prestige-1','prestige-2','elite-1','elite-2']
CODES=['S1','S2','S3','S5','S6','P1','P2','E1','E2']
class P(HTMLParser):
 def __init__(self): super().__init__();self.h1=0;self.c=[];self.schema=[];self.links=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='h1':self.h1+=1
  if t=='link' and d.get('rel')=='canonical':self.c.append(d.get('href'))
  if t=='a':self.links.append(d.get('href',''))
def main():
 e=[]; m=json.loads((ROOT/'assets/data/floor-plans.json').read_text())
 if [x['code'] for x in m['towers']]!=CODES:e.append('manifest tower codes/order changed')
 for x in m['floorPlans']:
  if not x.get('sourceFile') or not x.get('sourceFolderId'):e.append(f'missing source audit: {x}')
  if x.get('localAsset') and not (ROOT/x['localAsset'].lstrip('/')).is_file():e.append('missing manifest asset '+x['localAsset'])
 for slug in SLUGS:
  path=ROOT/'mat-bang-lumi-hanoi'/slug/'index.html';
  if not path.is_file():e.append('missing page '+slug);continue
  text=path.read_text(); p=P();p.feed(text)
  expected=f'https://lumi-hanoi.com/mat-bang-lumi-hanoi/{slug}/'
  if p.h1!=1:e.append(f'{slug}: H1 count {p.h1}')
  if p.c!=[expected]:e.append(f'{slug}: canonical {p.c}')
  if 'application/ld+json' not in text or 'BreadcrumbList' not in text or 'CollectionPage' not in text:e.append(slug+': schema missing')
  if '/mat-bang-lumi-hanoi/' not in p.links:e.append(slug+': hub link missing')
 hub=(ROOT/'mat-bang-lumi-hanoi/index.html').read_text()
 for slug in SLUGS:
  if f'/mat-bang-lumi-hanoi/{slug}/' not in hub:e.append('hub link missing '+slug)
 if 'data-tower-filter' not in hub:e.append('tower filtering absent')
 site=(ROOT/'assets/js/site.js').read_text()
 if 'data-lightbox' not in site or 'showModal' not in site:e.append('full-resolution lightbox absent')
 sm=(ROOT/'sitemap.xml').read_text()
 for slug in SLUGS:
  if f'https://lumi-hanoi.com/mat-bang-lumi-hanoi/{slug}/' not in sm:e.append('sitemap missing '+slug)
 alltext='\n'.join(p.read_text(errors='ignore').lower() for p in ROOT.rglob('*.html'))
 for domain in ('batdongsan.com.vn','onehousing.vn','vinhomes.vn'):
  if domain in alltext:e.append('competitor reference '+domain)
 if e: print(f'V5.2 floor-plan QA FAILED ({len(e)})\n- '+'\n- '.join(e));return 1
 print(f'V5.2 floor-plan QA passed: 9 tower pages, {len(m["floorPlans"])} audited mappings, hub filters, lightbox, schema and sitemap.')
 return 0
if __name__=='__main__':raise SystemExit(main())
