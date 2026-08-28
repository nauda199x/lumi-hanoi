#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / 'tien-ich-lumi-hanoi/index.html').read_text(encoding='utf-8')
source_notes = (ROOT / 'docs/source-package-v1.md').read_text(encoding='utf-8')

assert '<title>Tiện ích Lumi Hanoi: bể bơi, thể thao, cảnh quan &amp; tiện ích</title>' in html
assert 'hơn 80 tiện ích' not in html
assert 'hơn 80 hạng mục' not in html
assert '15 sân thể thao' not in html
assert 'Vì sao có tài liệu ghi “&gt;100 tiện ích”, trong khi bộ khác đánh số đến 88?' in html
for source_id in ('106xs0YINtuQcBADM7J401QzwIaFv-erF', '1lHh0HKxvkBdCZ2ojHvlKvStAbpu-s_eg'):
    assert source_id in source_notes
    assert source_id not in html
assert '&gt;100 tiện ích đa dạng độc bản' in html
assert '4,3 ha cảnh quan' in html
assert 'đánh số tới <strong>88</strong>' in html
assert 'Xem đủ 21 phối cảnh 3D Lumi Signature' in html
assert 'tên tiện ích cụ thể + phân khu + phạm vi áp dụng' in html

print('PASS: V8.8 amenity counts remain scoped without public source IDs')
