#!/usr/bin/env python3
"""Static acceptance checks for issue #24 / Prestige V8.1B."""
from decimal import Decimal
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets/media/prestige/unit-layouts/manifest.v8.1b.json"
PAGE = ROOT / "layout-can-ho-lumi-prestige/index.html"
SOURCE_FOLDER_ID = "1kRyHJ2hrz7zwC0hTdWgnU6-yheXeA3HH"

EXPECTED = [
    ("1VKqInYQetfQSYCbA7-hLpDOjl6HsLhbE", "Căn Hộ-01.jpg", "01", "4BR LARGE", 4, "Large", "136.0", "146.9", "assets/media/prestige/unit-layouts/prestige-layout-01-4br-large.webp", 3200, 4267, "layout-01"),
    ("1A0gF2IVzLFyLtqKViR1rqCQJz5grqlQ1", "Căn Hộ-02.jpg", "02", "4BR MEDIUM", 4, "Medium", "127.5", "138.0", "assets/media/prestige/unit-layouts/prestige-layout-02-4br-medium.webp", 3200, 4267, "layout-02"),
    ("1BJhbuCebZX81EhAc_2i5qP4BSTUEUFaL", "Căn Hộ-03.jpg", "03", "3BR EXTRA LARGE", 3, "Extra Large", "126.0", "135.5", "assets/media/prestige/unit-layouts/prestige-layout-03-3br-extra-large.webp", 3200, 4267, "layout-03"),
    ("1Z3a8hTn4FPCArX34JPgx_A290JyCR_CM", "Căn Hộ-04.jpg", "04", "3BR EXTRA LARGE", 3, "Extra Large", "118.3", "128.2", "assets/media/prestige/unit-layouts/prestige-layout-04-3br-extra-large.webp", 3200, 4267, "layout-04"),
    ("1_hiWv4gkfkbuiYlkWiNNv5rTFOD-M0z5", "Căn Hộ-05.jpg", "05", "3BR EXTRA LARGE", 3, "Extra Large", "128.6", "138.9", "assets/media/prestige/unit-layouts/prestige-layout-05-3br-extra-large.webp", 3200, 4267, "layout-05"),
    ("1_RITFlrBKBH_0VyLf-enj87__umK99AW", "Căn Hộ-06.jpg", "06", "3BR EXTRA LARGE", 3, "Extra Large", "137.1", "147.7", "assets/media/prestige/unit-layouts/prestige-layout-06-3br-extra-large.webp", 3200, 4267, "layout-06"),
    ("1q08A8QK1SBa_heSj9Nju5Ser_fNYrK6e", "Căn Hộ-07.jpg", "07", "3BR MEDIUM", 3, "Medium", "86.0", "93.1", "assets/media/prestige/unit-layouts/prestige-layout-07-3br-medium.webp", 3200, 4267, "layout-07"),
    ("1NqgP5QrCeLWNTbSRAVXede7soimD68kU", "Căn Hộ-08.jpg", "08", "3BR EXTRA LARGE", 3, "Extra Large", "117.9", "126.8", "assets/media/prestige/unit-layouts/prestige-layout-08-3br-extra-large.webp", 3200, 4267, "layout-08"),
    ("1XtSNfQEzm2cSkvag3wUU1x7Nx6pzgUxN", "Căn Hộ-09.jpg", "09", "3BR EXTRA LARGE", 3, "Extra Large", "117.1", "125.8", "assets/media/prestige/unit-layouts/prestige-layout-09-3br-extra-large.webp", 3200, 4267, "layout-09"),
    ("1g8nWchAZjLYFUKV3ozCi8JlK7xMQh5hE", "Căn Hộ-10.jpg", "10", "3BR LARGE", 3, "Large", "107.8", "116.2", "assets/media/prestige/unit-layouts/prestige-layout-10-3br-large.webp", 3200, 4267, "layout-10"),
    ("18xfeUp94-0p_s9zY8e1kA7xWYfQQz77q", "Căn Hộ-11.jpg", "11", "3BR LARGE", 3, "Large", "106.9", "115.2", "assets/media/prestige/unit-layouts/prestige-layout-11-3br-large.webp", 3200, 4267, "layout-11"),
    ("1U3exnWsMZRIBSbDOJX1xq2euvA73cYO0", "Căn Hộ-12.jpg", "12", "3BR EXTRA LARGE", 3, "Extra Large", "118.2", "129.1", "assets/media/prestige/unit-layouts/prestige-layout-12-3br-extra-large.webp", 3200, 4267, "layout-12"),
    ("13M4zE-hQt7vIZn0tGHkKrsWIli9U76fn", "Căn Hộ-13.jpg", "13", "2BR EXTRA LARGE", 2, "Extra Large", "85.7", "92.9", "assets/media/prestige/unit-layouts/prestige-layout-13-2br-extra-large.webp", 3200, 4267, "layout-13"),
    ("1eGgG9Ogx8vGYfPi7kvIasQMmnEs5uUSY", "Căn Hộ-14.jpg", "14", "2BR LARGE", 2, "Large", "71.4", "77.2", "assets/media/prestige/unit-layouts/prestige-layout-14-2br-large.webp", 3200, 4267, "layout-14"),
    ("1GZAY8iK5UuPpGqUhXsJXiqRQHBXUR78R", "Căn Hộ-15.jpg", "15", "1BR EXTRA LARGE", 1, "Extra Large", "54.9", "60.2", "assets/media/prestige/unit-layouts/prestige-layout-15-1br-extra-large.webp", 3200, 4267, "layout-15"),
    ("1yK3-Il3Q6PTyFmxfygLx3LqjWTPHKEZo", "Căn Hộ-16.jpg", "16", "1BR EXTRA LARGE", 1, "Extra Large", "53.9", "59.1", "assets/media/prestige/unit-layouts/prestige-layout-16-1br-extra-large.webp", 3200, 4267, "layout-16"),
    ("1ifo6ViRtCPB8dtI5f35iiVpB9Z8zuKAq", "Căn Hộ-17.jpg", "17", "3BR MEDIUM", 3, "Medium", "85.8", "92.3", "assets/media/prestige/unit-layouts/prestige-layout-17-3br-medium.webp", 3200, 4267, "layout-17"),
    ("1wCt3VSERbp0_QIwBfUWcwdnF6qNyzhW0", "Căn Hộ-18.jpg", "18", "2BR MEDIUM", 2, "Medium", "62.2", "68.8", "assets/media/prestige/unit-layouts/prestige-layout-18-2br-medium.webp", 3200, 4267, "layout-18"),
    ("19vCkzxeAzmllsKnv7tCuopbTLMZpYa-x", "Căn Hộ-19.jpg", "19", "2BR MEDIUM", 2, "Medium", "62.1", "67.5", "assets/media/prestige/unit-layouts/prestige-layout-19-2br-medium.webp", 3200, 4266, "layout-19"),
    ("12SO6r4L3vVLOO78pdsP4GQ3gEkMhH2RN", "Căn Hộ-20.jpg", "20", "2BR LARGE", 2, "Large", "71.3", "77.2", "assets/media/prestige/unit-layouts/prestige-layout-20-2br-large.webp", 3200, 4267, "layout-20"),
    ("1lun5EVu7gOqvhFg14nt_WWBQ-HF5LjK5", "Căn Hộ-21.jpg", "21", "2BR SMALL", 2, "Small", "54.5", "59.8", "assets/media/prestige/unit-layouts/prestige-layout-21-2br-small.webp", 3200, 4266, "layout-21"),
    ("15WriRHaZNg4CtV2oNTUz86_oilcXAMsy", "Căn Hộ-22.jpg", "22", "1BR MEDIUM", 1, "Medium", "42.2", "46.2", "assets/media/prestige/unit-layouts/prestige-layout-22-1br-medium.webp", 3200, 4267, "layout-22"),
]

FORBIDDEN_CODES = ("D2A", "D1A", "C16G", "C15G", "C14G", "C13G", "C6BG", "C5G", "C3AG", "B9G", "B5G", "A3G", "A2GM")


def fail(message):
    print("FAIL:", message, file=sys.stderr)
    raise SystemExit(1)


manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
assets = manifest.get("assets", [])
if manifest.get("version") != "8.1B":
    fail("manifest version must be 8.1B")
if manifest.get("source_folder_id") != SOURCE_FOLDER_ID:
    fail("wrong authoritative Drive folder ID")
if len(assets) != 22:
    fail("manifest must contain exactly 22 assets")

expected_by_id = {row[0]: row[1:] for row in EXPECTED}
if len(expected_by_id) != 22:
    fail("QA catalog itself must contain 22 unique Drive IDs")

seen_ids, seen_files, checksums = set(), set(), set()
for asset in assets:
    drive_id = asset.get("drive_file_id")
    if not drive_id or drive_id.startswith("ISSUE-24-"):
        fail("placeholder or missing Drive ID")
    if drive_id not in expected_by_id:
        fail("unexpected Drive ID: " + str(drive_id))

    expected = expected_by_id[drive_id]
    fields = (
        asset.get("source_jpg_filename"),
        asset.get("layout_number"),
        asset.get("verified_type"),
        asset.get("bedroom_count"),
        asset.get("size_class"),
        str(asset.get("nfa_sqm")),
        str(asset.get("gfa_sqm")),
        asset.get("local_webp"),
        asset.get("width"),
        asset.get("height"),
        asset.get("rendered_anchor"),
    )
    if (
        fields[:5] != expected[:5]
        or Decimal(fields[5]) != Decimal(expected[5])
        or Decimal(fields[6]) != Decimal(expected[6])
        or fields[7:] != expected[7:]
    ):
        fail("authoritative catalog mismatch for Drive ID " + drive_id)

    if drive_id in seen_ids:
        fail("duplicate Drive ID: " + drive_id)
    seen_ids.add(drive_id)

    local = asset["local_webp"]
    if local in seen_files:
        fail("duplicate local production file: " + local)
    seen_files.add(local)

    path = ROOT / local
    if not path.is_file():
        fail("missing local production file: " + local)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != asset.get("sha256"):
        fail("checksum mismatch: " + local)
    if digest in checksums:
        fail("all 22 drawings must have distinct checksums")
    checksums.add(digest)

if seen_ids != set(expected_by_id):
    fail("not all authoritative Drive IDs are present")

html = PAGE.read_text(encoding="utf-8")
if html.count("data-layout-card") != 22:
    fail("layout page must render exactly 22 cards")
if html.count("data-lightbox data-lightbox-alt") != 22:
    fail("all 22 drawings must use the full-resolution lightbox")

for drive_id, source_name, number, typ, bedrooms, size, nfa, gfa, local, width, height, anchor in EXPECTED:
    block_match = re.search(fr'<section class="layout-card" id="{re.escape(anchor)}"[^>]*>.*?</section>', html, re.S)
    if not block_match:
        fail("missing rendered anchor: " + anchor)
    block = block_match.group(0)
    url = "/" + local
    if block.count(f'href="{url}"') != 1:
        fail("layout action must link once to its own local full-resolution file: " + number)
    preview = re.search(r'<img [^>]*src="' + re.escape(url) + r'"[^>]*>', block)
    if preview and 'loading="lazy"' not in preview.group(0):
        fail("drawing previews must not eagerly load full-resolution files: " + number)
    if ">Xem bản vẽ " not in block:
        fail("on-demand drawing action missing for layout " + number)
    for value in (typ, f"{bedrooms}BR"):
        if value not in block:
            fail("rendered catalog mismatch for layout " + number + ": " + value)

    nfa_match = re.search(r"NFA[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*m²", block)
    gfa_match = re.search(r"GFA[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*m²", block)
    if not nfa_match or Decimal(nfa_match.group(1)) != Decimal(nfa):
        fail("rendered NFA mismatch for layout " + number)
    if not gfa_match or Decimal(gfa_match.group(1)) != Decimal(gfa):
        fail("rendered GFA mismatch for layout " + number)

for term in (
    'rel="canonical" href="https://lumi-hanoi.com/layout-can-ho-lumi-prestige/"',
    "<h1>Layout căn hộ Lumi Prestige</h1>",
    'data-layout-filter="bedrooms"',
    'data-layout-filter="size"',
    "Cách sử dụng thư viện layout",
    "NFA",
    "GFA",
):
    if term not in html:
        fail("page requirement missing: " + term)

public_blob = html + "\n" + json.dumps(assets, ensure_ascii=False)
for code in FORBIDDEN_CODES:
    if code in public_blob:
        fail("unverified unit code published: " + code)

for path in ("lumi-prestige/index.html", "toa-p1-lumi-hanoi/index.html", "toa-p2-lumi-hanoi/index.html"):
    if "/layout-can-ho-lumi-prestige/" not in (ROOT / path).read_text(encoding="utf-8"):
        fail("internal link missing: " + path)

if "https://lumi-hanoi.com/layout-can-ho-lumi-prestige/" not in (ROOT / "sitemap.xml").read_text(encoding="utf-8"):
    fail("sitemap missing layout library")

print("PASS: exact 22-entry Prestige Drive catalog, 22 distinct local drawings, rendered anchors, filters, lightbox and SEO links")
