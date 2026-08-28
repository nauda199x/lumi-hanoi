#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'assets/data/visual-library-v8.7.json').read_text(encoding='utf-8'))
ASSETS = DATA['assets']

assert DATA['version'] == '8.7'
assert len(ASSETS) == 16, len(ASSETS)
assert len({a['driveId'] for a in ASSETS}) == 16
assert len({a['localFile'] for a in ASSETS}) == 16

for asset in ASSETS:
    path = ROOT / asset['localFile']
    assert path.exists(), f"missing {asset['localFile']}"
    assert path.suffix == '.webp'
    size = path.stat().st_size
    assert 20_000 < size < 650_000, f"unexpected optimized size {size} for {asset['key']}"

pages = {
    'signature-gallery': (ROOT / 'phoi-canh-lumi-signature/index.html').read_text(encoding='utf-8'),
    'signature': (ROOT / 'lumi-signature/index.html').read_text(encoding='utf-8'),
    's1': (ROOT / 'mat-bang-lumi-hanoi/lumi-signature/s1/index.html').read_text(encoding='utf-8'),
    's2': (ROOT / 'mat-bang-lumi-hanoi/lumi-signature/s2/index.html').read_text(encoding='utf-8'),
    's3': (ROOT / 'mat-bang-lumi-hanoi/lumi-signature/s3/index.html').read_text(encoding='utf-8'),
    'elite': (ROOT / 'lumi-elite/index.html').read_text(encoding='utf-8'),
    'e1': (ROOT / 'mat-bang-lumi-hanoi/lumi-elite/e1/index.html').read_text(encoding='utf-8'),
    'e2': (ROOT / 'mat-bang-lumi-hanoi/lumi-elite/e2/index.html').read_text(encoding='utf-8'),
}

assert 'Phối cảnh 3D Lumi Signature: 21 hình' in pages['signature-gallery']
assert 'signature-indoor-v8-7' in pages['signature-gallery']
assert 'signature-indoor-preview-v8-7' in pages['signature']
assert 's1-lobby-v8-7' in pages['s1']
assert 's2-lobby-v8-7' in pages['s2']
assert 's3-lobby-v8-7' in pages['s3']
assert 'elite-visual-library-v8-7' in pages['elite']
assert 'elite-e1-visual-v8-7' in pages['e1']
assert 'elite-e2-visual-v8-7' in pages['e2']

signature_assets = [a for a in ASSETS if a['phase'] == 'signature']
elite_assets = [a for a in ASSETS if a['phase'] == 'elite']

for asset in signature_assets:
    local = '/' + asset['localFile']
    assert local in pages['signature-gallery'], f"Signature gallery missing {local}"

for asset in [a for a in signature_assets if a['scope'] == 'indoor']:
    assert '/' + asset['localFile'] in pages['signature']

for tower, page_key in [('S1','s1'),('S2','s2'),('S3','s3')]:
    asset = next(a for a in signature_assets if a.get('tower') == tower)
    assert '/' + asset['localFile'] in pages[page_key]

for asset in elite_assets:
    local = '/' + asset['localFile']
    assert local in pages['elite'], f"Elite overview missing {local}"

for asset in [a for a in elite_assets if a.get('tower') == 'E1']:
    assert '/' + asset['localFile'] in pages['e1']
for asset in [a for a in elite_assets if a.get('tower') == 'E2']:
    assert '/' + asset['localFile'] in pages['e2']

for asset in ASSETS:
    for page_name, html in pages.items():
        assert asset['driveId'] not in html, f"{page_name}: public page exposes Drive ID"

# Every newly localized image reference must carry intrinsic dimensions and lazy/async loading.
for key, html in pages.items():
    for match in re.finditer(r'<img[^>]+src="(/assets/media/(?:signature/indoor|elite/visual-library)/[^"]+\.webp)"[^>]*>', html):
        tag = match.group(0)
        assert re.search(r'width="\d+"', tag), f'{key}: missing width on {match.group(1)}'
        assert re.search(r'height="\d+"', tag), f'{key}: missing height on {match.group(1)}'
        assert 'loading="lazy"' in tag and 'decoding="async"' in tag, f'{key}: loading attrs missing on {match.group(1)}'
        assert re.search(r'alt="[^"]{8,}"', tag), f'{key}: weak/missing alt on {match.group(1)}'

print('PASS: V8.7 visual library — 16 verified local WebPs with private source IDs')
