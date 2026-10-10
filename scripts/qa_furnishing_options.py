#!/usr/bin/env python3
"""Verify all Lumi Hanoi listing forms and price tables have only two furnishing choices."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
FORM_FILES={
    "dang-tin-lumi-hanoi/index.html":'id="furnishing"',
    "quan-ly-tin-lumi-hanoi/index.html":'id="manage-furnishing"',
    "admin/index.html":'id="edit-furnishing"',
}
for filename, id_token in FORM_FILES.items():
    html=(ROOT/filename).read_text(encoding="utf-8")
    select=re.search(r'<select\b[^>]*'+re.escape(id_token)+r'[^>]*>.*?</select>',html,re.S)
    assert select, f"{filename}: missing furnishing select"
    content=select.group(0)
    assert 'required' in content, f"{filename}: choose furnishing is required"
    options=re.findall(r'<option([^>]*)>(.*?)</option>',content,re.S)
    allowed=[v for attrs,v in options if 'value=""' not in attrs]
    assert allowed==["Đồ cơ bản","Full nội thất"], (filename,allowed)
    assert 'Bàn giao nguyên bản' not in content and 'Nội thất cơ bản' not in content

p=(ROOT/"scripts/rent_price_breakdown.py").read_text(encoding="utf-8")
assert '("basic", "Đồ cơ bản"),' in p and '("full", "Full nội thất"),' in p
assert '("original", "Nguyên bản"),' not in p
assert '<col span="2" class="rent-col-price">' in p
assert "nguyen ban" in p and 'return "basic"' in p

for filename in ("assets/js/marketplace-form.js","assets/js/listing-manage.js","assets/js/marketplace-admin.js"):
    js=(ROOT/filename).read_text(encoding="utf-8")
    assert 'normalizeFurnishing' in js or 'furnishing:value("furnishing")' in js
    assert "Đầy đủ nội thất</option>" not in js

css=(ROOT/"assets/css/market-price.css").read_text(encoding="utf-8")
assert ".rent-col-area{width:30%}" in css
assert ".rent-col-price{width:35%}" in css
print("Exactly two furnishing types QA passed")
