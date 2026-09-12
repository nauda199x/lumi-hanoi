#!/usr/bin/env python3
from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'mat-bang-lumi-hanoi/layout-can-ho-lumi-hanoi/index.html'
CSS=ROOT/'assets/css/layout-seo-hub.css'
IMG='/assets/media/layouts/lumi-hanoi-layout-overview-1200x630.webp'
ABS='https://lumi-hanoi.com'+IMG

def meta(doc,selector,key):
    m=re.search(rf'<meta\b(?=[^>]*\b{selector}="{re.escape(key)}")[^>]*>',doc,re.I)
    if not m:return None
    c=re.search(r'content="([^"]*)"',m.group(0),re.I);return c.group(1) if c else None

def main():
    errors=[];doc=PAGE.read_text(encoding='utf-8')
    if not (ROOT/IMG.lstrip('/')).is_file():errors.append('overview image missing')
    if meta(doc,'property','og:image')!=ABS:errors.append('og:image mismatch')
    if meta(doc,'name','twitter:image')!=ABS:errors.append('twitter:image mismatch')
    if meta(doc,'property','og:image:width')!='1200' or meta(doc,'property','og:image:height')!='630':errors.append('social dimensions mismatch')
    if f'src="{IMG}"' not in doc:errors.append('overview image not visible in hero')
    if 'fetchpriority="high"' not in doc:errors.append('overview image not prioritized')
    if ABS not in doc or 'primaryImageOfPage' not in doc:errors.append('schema image signal missing')
    if 'max-image-preview:large' not in (meta(doc,'name','robots') or ''):errors.append('large image preview missing')
    if 'LAYOUT-HUB-SERP-VISUAL' not in CSS.read_text(encoding='utf-8'):errors.append('layout hub visual CSS missing')
    print({'layout_hub_serp_errors':errors})
    if errors:sys.exit(1)
if __name__=='__main__':main()
