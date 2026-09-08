"""Offline contracts for static/dynamic listing detail and future generated listings."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import sys
import json

sys.path.insert(0,str(Path(__file__).resolve().parent))
import generate_marketplace_seo as gen
from generate_marketplace_seo_average import allow_short_descriptions_for_indexing

class Document(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.nodes=[]
        self.feed(raw)
    def handle_starttag(self,tag,attrs):
        self.nodes.append((tag,dict(attrs)))
    def find(self,tag=None,**attrs):
        return [a for t,a in self.nodes if (tag is None or tag==t) and all(a.get(k)==v for k,v in attrs.items())]

allow_short_descriptions_for_indexing()
row=dict(id='test-id',slug='can-ho-lumi-test-lh-test1234',listing_code='LH-TEST1234',listing_type='rent',title='Căn hộ Lumi Hanoi S3',description='Mô tả căn hộ.',poster_name='Ngọc Vân',contact_phone='0779 637 268',tower='S3',phase='Signature',unit_type='2PN',area_sqm=54,price_vnd=10000000,approved_at='2026-09-08T03:00:00Z',listing_images=[dict(storage_path='one.jpg',sort_order=1),dict(storage_path='two.jpg',sort_order=2)])
for listing_type in ['rent','sale']:
    data={**row,'listing_type':listing_type,'price_vnd':10000000 if listing_type=='rent' else 5400000000}
    raw=gen.render_page(data);doc=Document(raw)
    assert '{{' not in raw and len(doc.find('h1'))==1
    assert doc.find('link',rel='canonical')[0]['href']==gen.SITE+gen.listing_url(data)
    assert doc.find('meta',name='robots')[0]['content'].startswith('index,follow')
    assert len([a for _,a in doc.nodes if 'id' in a])==len({a['id'] for _,a in doc.nodes if 'id' in a})
    calls=[a for _,a in doc.nodes if 'data-detail-phone' in a]
    assert len(calls)==2 and all(a['href']=='tel:0779637268' for a in calls)
    assert ('~100,0 tr/m²' in raw)==(listing_type=='sale')
    images=doc.find('img');assert len(images)==2
    assert images[0]['loading']=='eager' and images[0]['fetchpriority']=='high'
    assert images[1]['loading']=='lazy' and 'fetchpriority' not in images[1]
    same_tower=next(a for _,a in doc.nodes if 'data-detail-same-tower' in a)
    assert parse_qs(urlparse(same_tower['href']).fragment)=={'tower':['S3']}
    assert gen.render_page(data)==raw, 'Generating the same record must be stable'

for count in [0,1,12]:
    raw=gen.render_detail_content({**row,'listing_images':[dict(storage_path=f'{i}.jpg') for i in range(count)],'contact_phone':'','floor_label':None})
    doc=Document(raw);assert len(doc.find('img'))==count
    assert all('hidden' in a for _,a in doc.nodes if 'data-detail-phone' in a or 'data-detail-zalo' in a)
    if count==0: assert 'Hình ảnh đang được bổ sung' in raw

unsafe='<script>alert(1)</script><img src=x onerror=alert(1)>'
raw=gen.render_detail_content({**row,'title':unsafe,'description':unsafe,'poster_name':unsafe})
assert not Document(raw).find('script') and '&lt;script&gt;' in raw
shell=(gen.ROOT/'tin-dang-lumi-hanoi/index.html').read_text()
assert gen.render_detail_content().strip() in shell
for marker in gen.ROOT.glob('*lumi-hanoi/*/.marketplace-generated'):
    path=marker.parent/'index.html';raw=path.read_text();doc=Document(raw)
    assert len(doc.find('h1'))==1 and '{{' not in raw, str(path)
    assert doc.find('link',rel='canonical')[0]['href']==gen.SITE+'/'+str(path.parent.relative_to(gen.ROOT))+'/'
    scripts=[a['src'] for a in doc.find('script') if a.get('src')]
    assert next(i for i,s in enumerate(scripts) if 'listing-detail-ui.js' in s)<next(i for i,s in enumerate(scripts) if 'marketplace-static-status.js' in s)
    for _,a in doc.nodes:
        for key in ['href','src']:
            value=a.get(key,'')
            if value.startswith('/') and not value.startswith('//'):
                local=gen.ROOT/urlparse(value).path.lstrip('/')
                assert local.exists(), f'Missing local link or asset: {value}'
print('Listing detail: shared template, rent/sale, missing data, 0/1/12 images, escaped input, canonicals, assets and contact links: PASS')
