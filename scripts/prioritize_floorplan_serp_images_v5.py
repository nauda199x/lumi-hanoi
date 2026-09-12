#!/usr/bin/env python3
from __future__ import annotations
import html,json,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import prioritize_floorplan_serp_images_v4 as previous

ROOT=Path(__file__).resolve().parents[1]
SITE="https://lumi-hanoi.com"
PAGE=ROOT/"mat-bang-lumi-hanoi/layout-can-ho-lumi-hanoi/index.html"
URL=SITE+"/mat-bang-lumi-hanoi/layout-can-ho-lumi-hanoi/"
ASSET="/assets/media/layouts/lumi-hanoi-layout-overview-1200x630.webp"
ALT="Layout căn hộ Lumi Hanoi theo Signature, Prestige và Elite"
CSS=ROOT/"assets/css/layout-seo-hub.css"
SITEMAP=ROOT/"sitemap-images.xml"
SOURCES=[("SIGNATURE","/assets/media/signature/unit-layouts/signature-s1-s5-1br-a1.webp"),("PRESTIGE","/assets/media/prestige/unit-layouts/prestige-layout-22-1br-medium.webp"),("ELITE","/assets/media/elite/unit-layouts/elite-layout-page-09.webp")]

def set_meta(doc,selector,key,value):
    p=re.compile(rf'<meta\b(?=[^>]*\b{selector}="{re.escape(key)}")[^>]*>',re.I);m=p.search(doc);v=html.escape(str(value),quote=True)
    if m:
        tag=m.group(0);tag=re.sub(r'\bcontent="[^"]*"',f'content="{v}"',tag,count=1,flags=re.I) if 'content=' in tag else tag[:-1]+f' content="{v}">' 
        return doc[:m.start()]+tag+doc[m.end():]
    return doc.replace('</head>',f'<meta {selector}="{key}" content="{v}"></head>',1)

def get_meta(doc,selector,key):
    m=re.search(rf'<meta\b(?=[^>]*\b{selector}="{re.escape(key)}")[^>]*>',doc,re.I)
    if not m:return None
    c=re.search(r'content="([^"]*)"',m.group(0),re.I);return html.unescape(c.group(1)) if c else None

def make_image():
    out=ROOT/ASSET.lstrip('/');out.parent.mkdir(parents=True,exist_ok=True)
    im=Image.new('RGB',(1200,630),'#f4f0e7');d=ImageDraw.Draw(im);d.rounded_rectangle((28,28,1172,602),22,fill='#fbfaf7',outline='#d8d0c3',width=2)
    d.text((58,48),'LUMI HANOI',fill='#171917');d.text((58,72),'APARTMENT LAYOUT OVERVIEW',fill='#756d60')
    for i,(label,src) in enumerate(SOURCES):
        p=ROOT/src.lstrip('/');
        if not p.is_file():raise RuntimeError(f'missing {src}')
        with Image.open(p) as x: thumb=ImageOps.contain(ImageOps.exif_transpose(x).convert('RGB'),(310,370),Image.Resampling.LANCZOS)
        x0=58+i*369;d.rounded_rectangle((x0,112,x0+345,560),16,fill='white',outline='#ded7cb',width=2);d.text((x0+18,130),label,fill='#171917');im.paste(thumb,(x0+(345-thumb.width)//2,168+(370-thumb.height)//2))
    im.save(out,'WEBP',quality=84,method=6)

def patch_schema(doc):
    absolute=SITE+ASSET
    p=re.compile(r'<script type="application/ld\+json">(.*?)</script>',re.I|re.S)
    def repl(m):
        try:data=json.loads(m.group(1))
        except:return m.group(0)
        changed=False
        for n in data.get('@graph',[]):
            if isinstance(n,dict) and n.get('@type')=='CollectionPage' and n.get('url')==URL:
                n['dateModified']='2026-09-12';n['image']=absolute;n['primaryImageOfPage']={'@type':'ImageObject','contentUrl':absolute,'width':1200,'height':630,'caption':ALT};changed=True
        return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False,separators=(',',':'))+'</script>' if changed else m.group(0)
    return p.sub(repl,doc)

def patch_page():
    doc=PAGE.read_text(encoding='utf-8');absolute=SITE+ASSET
    for selector,key,value in [('property','og:image',absolute),('property','og:image:type','image/webp'),('property','og:image:width','1200'),('property','og:image:height','630'),('property','og:image:alt',ALT),('name','twitter:card','summary_large_image'),('name','twitter:image',absolute),('name','twitter:image:alt',ALT)]:doc=set_meta(doc,selector,key,value)
    doc=patch_schema(doc)
    marker='<!-- LAYOUT-HUB-SERP-VISUAL -->'
    if marker not in doc:
        fig=marker+f'<figure class="layout-library-serp-visual"><img src="{ASSET}" width="1200" height="630" alt="{ALT}" loading="eager" fetchpriority="high" decoding="async"><figcaption>Signature · Prestige · Elite</figcaption></figure>'
        doc=doc.replace('</nav>\n      </div>\n    </header>','</nav>'+fig+'\n      </div>\n    </header>',1)
    PAGE.write_text(doc,encoding='utf-8')

def patch_css():
    css=CSS.read_text(encoding='utf-8');mark='/* LAYOUT-HUB-SERP-VISUAL */'
    if mark not in css:css+='\n'+mark+'\n.layout-library-serp-visual{max-width:980px;margin:1.35rem 0 0;padding:.55rem;border:1px solid rgba(255,255,255,.18);border-radius:18px;background:rgba(255,255,255,.06)}.layout-library-serp-visual img{display:block;width:100%;height:auto;border-radius:12px}.layout-library-serp-visual figcaption{margin:.5rem .15rem 0;font-size:.72rem;color:#d4d2ca}\n'
    CSS.write_text(css,encoding='utf-8')

def patch_sitemap():
    xml=SITEMAP.read_text(encoding='utf-8');image=SITE+ASSET;tag=f'\n    <image:image>\n      <image:loc>{image}</image:loc>\n    </image:image>';p=re.compile(rf'(<url>\s*<loc>{re.escape(URL)}</loc>)(.*?)(</url>)',re.S);m=p.search(xml)
    if m and image not in m.group(2):xml=xml[:m.start()]+m.group(1)+tag+m.group(2)+m.group(3)+xml[m.end():]
    elif not m:xml=xml.replace('</urlset>',f'  <url>\n    <loc>{URL}</loc>{tag}\n  </url>\n</urlset>')
    SITEMAP.write_text(xml,encoding='utf-8')

def verify():
    doc=PAGE.read_text(encoding='utf-8');absolute=SITE+ASSET
    if get_meta(doc,'property','og:image')!=absolute or get_meta(doc,'name','twitter:image')!=absolute:raise RuntimeError('layout hub social image mismatch')
    if f'src="{ASSET}"' not in doc:raise RuntimeError('layout hub overview not visible')
    with Image.open(ROOT/ASSET.lstrip('/')) as im:
        if im.size!=(1200,630):raise RuntimeError('layout hub overview size mismatch')

def main():
    previous.main();make_image();patch_page();patch_css();patch_sitemap();verify();print('layout hub:',ASSET)
if __name__=='__main__':main()
