#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / 'tien-ich-lumi-hanoi/index.html').read_text(encoding='utf-8')

assert '<title>Tiện ích Lumi Hanoi: bể bơi, thể thao, cảnh quan &amp; tiện ích</title>' in html
assert 'hơn 80 tiện ích' not in html
assert 'hơn 80 hạng mục' not in html
assert '15 sân thể thao' not in html
assert 'Vì sao có tài liệu ghi “&gt;100 tiện ích”, trong khi bộ khác đánh số đến 88?' in html
assert '106xs0YINtuQcBADM7J401QzwIaFv-erF' in html
assert '1lHh0HKxvkBdCZ2ojHvlKvStAbpu-s_eg' in html
assert '&gt;100 tiện ích đa dạng độc bản' in html
assert '4,3 ha cảnh quan' in html
assert 'đánh số tới <strong>88</strong>' in html
assert 'Xem đủ 21 phối cảnh 3D Lumi Signature' in html
assert 'tên tiện ích cụ thể + phân khu + nguồn' in html

print('PASS: V8.8 amenity counts are source-scoped instead of flattened into one SEO number')
