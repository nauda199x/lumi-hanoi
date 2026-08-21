#!/usr/bin/env python3
"""Static acceptance checks for issue #26 / Prestige V8.1C."""
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "layout-can-ho-lumi-prestige/index.html"
MANIFEST = ROOT / "assets/media/prestige/unit-layouts/manifest.v8.1b.json"
CSS = ROOT / "assets/css/site.css"

def fail(message):
    print("FAIL:", message, file=sys.stderr)
    raise SystemExit(1)

html = PAGE.read_text(encoding="utf-8")
css = CSS.read_text(encoding="utf-8")
assets = json.loads(MANIFEST.read_text(encoding="utf-8"))["assets"]
blocks = re.findall(r'<section class="layout-card".*?</section>', html, re.S)
if len(blocks) != 22 or html.count('class="layout-view-action"') != 22:
    fail("all 22 server-rendered cards need one on-demand action")
if '<div class="layout-card-grid">' not in html:
    fail("compact card grid is missing")
for asset, block in zip(assets, blocks):
    number = asset["layout_number"]
    expected = {
        f'id="{asset["rendered_anchor"]}"',
        asset["verified_type"],
        f'{asset["bedroom_count"]}BR',
        asset["size_class"],
        f'href="/{asset["local_webp"]}"',
        "Xem bản vẽ",
    }
    missing = [value for value in expected if value not in block]
    if missing:
        fail(f"layout {number} missing exact server-rendered data: {missing}")
    nfa = re.search(r"NFA[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*m²", block)
    gfa = re.search(r"GFA[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*m²", block)
    if not nfa or not gfa or Decimal(nfa.group(1)) != Decimal(asset["nfa_sqm"]) or Decimal(gfa.group(1)) != Decimal(asset["gfa_sqm"]):
        fail(f"layout {number} has incorrect NFA/GFA")
    preview = re.search(r'<figure class="layout-preview"><img ([^>]+)>', block)
    if not preview or 'loading="lazy"' not in preview.group(1):
        fail(f"layout {number} needs a lazy genuine drawing preview")
    if block.count("data-lightbox") != 3:
        fail(f"layout {number} action must use the existing lightbox metadata")
if html.count('data-layout-filter="bedrooms"') != 5 or html.count('data-layout-filter="size"') != 5:
    fail("bedroom and size filters must be preserved")
if 'rel="canonical" href="https://lumi-hanoi.com/layout-can-ho-lumi-prestige/"' not in html:
    fail("canonical URL changed")
if re.search(r'href="/[^"]*[?&](?:utm_|[^" ]*chatgpt)', html, re.I):
    fail("tracking parameters found on internal links")
for rule in (
    ".layout-card-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))",
    "@media(max-width:760px){.layout-card-grid{grid-template-columns:1fr}",
):
    if rule not in css:
        fail("responsive grid rule missing: " + rule)
for path in ("lumi-prestige/index.html", "toa-p1-lumi-hanoi/index.html", "toa-p2-lumi-hanoi/index.html"):
    if '/layout-can-ho-lumi-prestige/' not in (ROOT / path).read_text(encoding="utf-8"):
        fail("clean library link missing from " + path)
if 'https://lumi-hanoi.com/layout-can-ho-lumi-prestige/' not in (ROOT / "sitemap.xml").read_text(encoding="utf-8"):
    fail("canonical library URL missing from sitemap")
print("PASS: V8.1C compact responsive grid, 22 exact SSR records and on-demand local lightbox drawings")
