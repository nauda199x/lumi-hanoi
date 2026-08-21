#!/usr/bin/env python3
"""Static acceptance checks for issue #24 / Prestige V8.1B."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def fail(x): print('FAIL:',x,file=sys.stderr); raise SystemExit(1)
EXPECTED={'ISSUE-24-DRIVE-ID-01': ('Căn Hộ-01.jpg', '01', '4BR LARGE', 4, 'Large', '136.0', '146.9', 'assets/media/prestige/unit-layouts/prestige-layout-01-4br-large.webp', 'layout-01'),
 'ISSUE-24-DRIVE-ID-02': ('Căn Hộ-02.jpg', '02', '4BR MEDIUM', 4, 'Medium', '127.5', '138.0', 'assets/media/prestige/unit-layouts/prestige-layout-02-4br-medium.webp', 'layout-02'),
 'ISSUE-24-DRIVE-ID-03': ('Căn Hộ-03.jpg',
                          '03',
                          '3BR EXTRA LARGE',
                          3,
                          'Extra Large',
                          '126.00',
                          '135.50',
                          'assets/media/prestige/unit-layouts/prestige-layout-03-3br-extra-large.webp',
                          'layout-03'),
 'ISSUE-24-DRIVE-ID-04': ('Căn Hộ-04.jpg',
                          '04',
                          '3BR EXTRA LARGE',
                          3,
                          'Extra Large',
                          '118.30',
                          '128.20',
                          'assets/media/prestige/unit-layouts/prestige-layout-04-3br-extra-large.webp',
                          'layout-04'),
 'ISSUE-24-DRIVE-ID-05': ('Căn Hộ-05.jpg',
                          '05',
                          '3BR EXTRA LARGE',
                          3,
                          'Extra Large',
                          '128.60',
                          '138.90',
                          'assets/media/prestige/unit-layouts/prestige-layout-05-3br-extra-large.webp',
                          'layout-05'),
 'ISSUE-24-DRIVE-ID-06': ('Căn Hộ-06.jpg',
                          '06',
                          '3BR EXTRA LARGE',
                          3,
                          'Extra Large',
                          '137.10',
                          '147.70',
                          'assets/media/prestige/unit-layouts/prestige-layout-06-3br-extra-large.webp',
                          'layout-06'),
 'ISSUE-24-DRIVE-ID-07': ('Căn Hộ-07.jpg', '07', '3BR MEDIUM', 3, 'Medium', '86.00', '93.10', 'assets/media/prestige/unit-layouts/prestige-layout-07-3br-medium.webp', 'layout-07'),
 'ISSUE-24-DRIVE-ID-08': ('Căn Hộ-08.jpg',
                          '08',
                          '3BR EXTRA LARGE',
                          3,
                          'Extra Large',
                          '117.90',
                          '126.80',
                          'assets/media/prestige/unit-layouts/prestige-layout-08-3br-extra-large.webp',
                          'layout-08'),
 'ISSUE-24-DRIVE-ID-09': ('Căn Hộ-09.jpg',
                          '09',
                          '3BR EXTRA LARGE',
                          3,
                          'Extra Large',
                          '117.1',
                          '125.8',
                          'assets/media/prestige/unit-layouts/prestige-layout-09-3br-extra-large.webp',
                          'layout-09'),
 'ISSUE-24-DRIVE-ID-10': ('Căn Hộ-10.jpg', '10', '3BR LARGE', 3, 'Large', '107.80', '116.20', 'assets/media/prestige/unit-layouts/prestige-layout-10-3br-large.webp', 'layout-10'),
 'ISSUE-24-DRIVE-ID-11': ('Căn Hộ-11.jpg', '11', '3BR LARGE', 3, 'Large', '106.9', '115.2', 'assets/media/prestige/unit-layouts/prestige-layout-11-3br-large.webp', 'layout-11'),
 'ISSUE-24-DRIVE-ID-12': ('Căn Hộ-12.jpg',
                          '12',
                          '3BR EXTRA LARGE',
                          3,
                          'Extra Large',
                          '118.20',
                          '129.10',
                          'assets/media/prestige/unit-layouts/prestige-layout-12-3br-extra-large.webp',
                          'layout-12'),
 'ISSUE-24-DRIVE-ID-13': ('Căn Hộ-13.jpg',
                          '13',
                          '2BR EXTRA LARGE',
                          2,
                          'Extra Large',
                          '85.7',
                          '92.9',
                          'assets/media/prestige/unit-layouts/prestige-layout-13-2br-extra-large.webp',
                          'layout-13'),
 'ISSUE-24-DRIVE-ID-14': ('Căn Hộ-14.jpg', '14', '2BR LARGE', 2, 'Large', '71.4', '77.2', 'assets/media/prestige/unit-layouts/prestige-layout-14-2br-large.webp', 'layout-14'),
 'ISSUE-24-DRIVE-ID-15': ('Căn Hộ-15.jpg',
                          '15',
                          '1BR EXTRA LARGE',
                          1,
                          'Extra Large',
                          '54.9',
                          '60.2',
                          'assets/media/prestige/unit-layouts/prestige-layout-15-1br-extra-large.webp',
                          'layout-15'),
 'ISSUE-24-DRIVE-ID-16': ('Căn Hộ-16.jpg',
                          '16',
                          '1BR EXTRA LARGE',
                          1,
                          'Extra Large',
                          '53.9',
                          '59.1',
                          'assets/media/prestige/unit-layouts/prestige-layout-16-1br-extra-large.webp',
                          'layout-16'),
 'ISSUE-24-DRIVE-ID-17': ('Căn Hộ-17.jpg', '17', '3BR MEDIUM', 3, 'Medium', '85.8', '92.3', 'assets/media/prestige/unit-layouts/prestige-layout-17-3br-medium.webp', 'layout-17'),
 'ISSUE-24-DRIVE-ID-18': ('Căn Hộ-18.jpg', '18', '2BR MEDIUM', 2, 'Medium', '62.2', '68.8', 'assets/media/prestige/unit-layouts/prestige-layout-18-2br-medium.webp', 'layout-18'),
 'ISSUE-24-DRIVE-ID-19': ('Căn Hộ-19.jpg', '19', '2BR MEDIUM', 2, 'Medium', '62.1', '67.5', 'assets/media/prestige/unit-layouts/prestige-layout-19-2br-medium.webp', 'layout-19'),
 'ISSUE-24-DRIVE-ID-20': ('Căn Hộ-20.jpg', '20', '2BR LARGE', 2, 'Large', '71.3', '77.2', 'assets/media/prestige/unit-layouts/prestige-layout-20-2br-large.webp', 'layout-20'),
 'ISSUE-24-DRIVE-ID-21': ('Căn Hộ-21.jpg', '21', '2BR SMALL', 2, 'Small', '54.5', '59.8', 'assets/media/prestige/unit-layouts/prestige-layout-21-2br-small.webp', 'layout-21'),
 'ISSUE-24-DRIVE-ID-22': ('Căn Hộ-22.jpg', '22', '1BR MEDIUM', 1, 'Medium', '42.2', '46.2', 'assets/media/prestige/unit-layouts/prestige-layout-22-1br-medium.webp', 'layout-22')}
m=json.loads((ROOT/'assets/media/prestige/unit-layouts/manifest.v8.1b.json').read_text()); assets=m.get('assets',[])
if any(a.get('drive_file_id','').startswith('ISSUE-24-') for a in assets): fail('placeholder Drive ID is forbidden; copy the exact issue #24 catalog')
actual={a['drive_file_id']:(a['source_jpg_filename'],a['layout_number'],a['verified_type'],a['bedroom_count'],a['size_class'],a['nfa_sqm'],a['gfa_sqm'],a['local_webp'],a['rendered_anchor']) for a in assets}
if m.get('version')!='8.1B' or len(assets)!=22 or actual!=EXPECTED: fail('manifest must exactly equal the authoritative issue #24 catalog')
checks=[]
for a in assets:
 p=ROOT/a['local_webp']; digest=hashlib.sha256(p.read_bytes()).hexdigest(); checks.append(digest)
 if digest!=a['sha256']: fail('checksum mismatch '+str(p))
if len(set(checks))!=22: fail('all drawings must have distinct checksums')
h=(ROOT/'layout-can-ho-lumi-prestige/index.html').read_text()
if h.count('data-layout-card')!=22 or h.count('data-lightbox data-lightbox-alt')!=22: fail('22 rendered cards/images required')
for drive_id,(_,n,typ,bed,size,nfa,gfa,local,anchor) in EXPECTED.items():
 block=re.search(fr'<section class="layout-card" id="{anchor}".*?</section>',h,re.S)
 if not block or block.group().count('/'+local)!=2: fail('exact genuine image missing for '+drive_id)
 for value in (typ,f'{bed}BR',f'{nfa} m²',f'{gfa} m²'):
  if value not in block.group(): fail(f'rendered catalog mismatch for {drive_id}: {value}')
for term in ['rel="canonical" href="https://lumi-hanoi.com/layout-can-ho-lumi-prestige/"','<h1>Layout căn hộ Lumi Prestige</h1>','data-layout-filter="bedrooms"','data-layout-filter="size"','Cách sử dụng thư viện layout']:
 if term not in h: fail('page requirement missing: '+term)
for code in ('D2A','D1A','C16G','C15G','C14G','C13G','C6BG','C5G','C3AG','B9G','B5G','A3G','A2GM'):
 if code in h or code in json.dumps(assets): fail('unverified unit code published: '+code)
for p in ['lumi-prestige/index.html','toa-p1-lumi-hanoi/index.html','toa-p2-lumi-hanoi/index.html']:
 if '/layout-can-ho-lumi-prestige/' not in (ROOT/p).read_text(): fail('internal link missing: '+p)
if 'https://lumi-hanoi.com/layout-can-ho-lumi-prestige/' not in (ROOT/'sitemap.xml').read_text(): fail('sitemap missing')
print('PASS: exact 22-entry Prestige catalog, genuine drawings, filters and SEO links')
