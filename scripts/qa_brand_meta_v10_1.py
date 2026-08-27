#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

TOWER_PAGES = [
    ROOT / "mat-bang-lumi-hanoi/lumi-signature/s1/index.html",
    ROOT / "mat-bang-lumi-hanoi/lumi-signature/s2/index.html",
    ROOT / "mat-bang-lumi-hanoi/lumi-signature/s3/index.html",
    ROOT / "mat-bang-lumi-hanoi/lumi-signature/s5/index.html",
    ROOT / "mat-bang-lumi-hanoi/lumi-signature/s6/index.html",
    ROOT / "mat-bang-lumi-hanoi/lumi-prestige/p1/index.html",
    ROOT / "mat-bang-lumi-hanoi/lumi-prestige/p2/index.html",
    ROOT / "mat-bang-lumi-hanoi/lumi-elite/e1/index.html",
    ROOT / "mat-bang-lumi-hanoi/lumi-elite/e2/index.html",
]

errors = []

favicon = ROOT / "favicon.svg"
if not favicon.exists():
    errors.append("missing favicon.svg")
else:
    svg = favicon.read_text(encoding="utf-8")
    for token in ('viewBox="0 0 64 64"', '#171a18', '#9c7951'):
        if token not in svg:
            errors.append(f"favicon.svg missing expected token: {token}")

site_css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
if "/* V10.1 unified favicon brand mark */" not in site_css:
    errors.append("missing V10.1 brand mark CSS")
if 'background:url("/favicon.svg")' not in site_css:
    errors.append("header brand mark is not sourced from /favicon.svg")

required_meta = [
    '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
    '<meta name="theme-color" content="#171a18">',
    'property="og:description"',
    'property="og:image"',
    'property="og:image:alt"',
    '<meta name="twitter:card" content="summary_large_image">',
    'name="twitter:image"',
]

for path in TOWER_PAGES:
    if not path.exists():
        errors.append(f"missing tower page: {path.relative_to(ROOT)}")
        continue
    html = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    for token in required_meta:
        if token not in html:
            errors.append(f"{rel}: missing {token}")
    if "https://lumi-hanoi.com/mat-bang-lumi-hanoi/" not in html:
        errors.append(f"{rel}: canonical/OG URL is not in nested floor-plan silo")

if errors:
    print(f"Brand/meta V10.1 QA FAILED ({len(errors)} issue(s))")
    for error in errors:
        print("- " + error)
    sys.exit(1)

print(f"Brand/meta V10.1 QA passed for {len(TOWER_PAGES)} tower pages.")
