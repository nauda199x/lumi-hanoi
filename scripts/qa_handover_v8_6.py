#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

handover = (ROOT / 'noi-that-ban-giao-lumi-hanoi/index.html').read_text(encoding='utf-8')
signature = (ROOT / 'lumi-signature/index.html').read_text(encoding='utf-8')
prestige = (ROOT / 'lumi-prestige/index.html').read_text(encoding='utf-8')
elite = (ROOT / 'lumi-elite/index.html').read_text(encoding='utf-8')
source_notes = (ROOT / 'docs/handover-v8.6-source-notes.md').read_text(encoding='utf-8')

assert '<title>Nội thất bàn giao Lumi Hanoi: Signature, Prestige, Elite</title>' in handover
assert 'https://lumi-hanoi.com/noi-that-ban-giao-lumi-hanoi/' in handover
assert '"@type":"FAQPage"' in handover

for anchor in ('id="signature"', 'id="prestige"', 'id="elite"'):
    assert anchor in handover, f'missing handover anchor {anchor}'

for source_id in (
    '1L8nYH2bAKVJhAq3ZtE71gjAiCC9_K0hC',
    '1qSe2ESYZ4H1w-7Du_I3pj7_8BVtVZBwA',
    '1EXPsmL4GTil8lix-z6HTOo5Vhf_X5EzB',
    '1pZaB7z8J8UGwNlKQuSLvVTPpadpd5CoK',
    '1YG5nxe8H3t2c4xWmZp6TFzMjmEK4Apph',
    '16HRdnxCRM0d4n_aL6cEB34NOqri4-c7O',
    '1EoDDTFSabQopO_v1NRsOXeJH-F5ubQya',
):
    assert source_id in source_notes, f'missing internal verification record {source_id}'
    assert source_id not in handover, f'public handover page exposes source ID {source_id}'

for required in (
    'Signature Duplex',
    'Signature Penthouse',
    'Prestige 1–4PN',
    'Elite 1–3PN',
    'dishwasher TEKA hoặc tương đương',
    'kính full-height',
    'hoặc tương đương',
):
    assert required in handover, f'missing handover detail: {required}'

for name, html, marker, modified in (
    ('Signature', signature, 'signature-handover-source', '2026-08-23'),
    ('Prestige', prestige, 'prestige-handover-source', '2026-08-27'),
    ('Elite', elite, 'elite-handover-source', '2026-08-23'),
):
    assert marker in html, f'{name}: missing source-backed handover section'
    assert '/noi-that-ban-giao-lumi-hanoi/' in html, f'{name}: missing handover internal link'
    dates = re.findall(r'"dateModified":"(\\d{4}-\\d{2}-\\d{2})"', html)
    assert dates and max(dates) >= modified, f'{name}: dateModified older than {modified}'
assert '/toa-p1-lumi-hanoi/' not in prestige, 'Prestige still links legacy P1 URL'
assert '/toa-p2-lumi-hanoi/' not in prestige, 'Prestige still links legacy P2 URL'
assert '/mat-bang-lumi-hanoi/lumi-prestige/p1/' in prestige
assert '/mat-bang-lumi-hanoi/lumi-prestige/p2/' in prestige
assert '/toa-prestige-' not in prestige, 'Prestige still links legacy tower aliases'

print('PASS: V8.6 handover coverage, private verification records and phase enrichment')
