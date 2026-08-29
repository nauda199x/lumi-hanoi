#!/usr/bin/env python3
"""Regression checks for GitHub Pages legacy URL consolidation."""
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://lumi-hanoi.com"
REDIRECTS = {
    "toa-s1-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-signature/s1/",
    "toa-s2-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-signature/s2/",
    "toa-s3-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-signature/s3/",
    "toa-s5-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-signature/s5/",
    "toa-s6-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-signature/s6/",
    "toa-signature-1-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-signature/s1/",
    "toa-signature-2-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-signature/s2/",
    "toa-signature-3-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-signature/s3/",
    "toa-signature-5-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-signature/s5/",
    "toa-signature-6-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-signature/s6/",
    "toa-p1-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-prestige/p1/",
    "toa-p2-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-prestige/p2/",
    "toa-prestige-1-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-prestige/p1/",
    "toa-prestige-2-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-prestige/p2/",
    "toa-e1-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-elite/e1/",
    "toa-e2-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-elite/e2/",
    "toa-elite-1-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-elite/e1/",
    "toa-elite-2-lumi-hanoi/index.html": "/mat-bang-lumi-hanoi/lumi-elite/e2/",
    "vi-tri/index.html": "/vi-tri-lumi-hanoi/",
    "giai-doan-2/index.html": "/lumi-prestige/",
    "tien-do/index.html": "/tien-do-lumi-hanoi/",
    "giai-doan-1/index.html": "/lumi-signature/",
    "giai-doan-3/index.html": "/lumi-elite/",
    "chu-dau-tu/index.html": "/chu-dau-tu-capitaland/",
    "lien-he/index.html": "/giao-dich-lumi-hanoi/"
}

errors = []
for relative, destination in REDIRECTS.items():
    path = ROOT / relative
    if not path.is_file():
        errors.append(f"missing static redirect page: {relative}")
        continue
    html = path.read_text(encoding="utf-8")
    absolute = SITE + destination
    required = (
        'data-legacy-redirect',
        f'<link rel="canonical" href="{absolute}">',
        f'<meta http-equiv="refresh" content="0;url={absolute}">',
        "window.location.replace(",
        f'href="{destination}"',
    )
    for token in required:
        if token not in html:
            errors.append(f"{relative}: missing {token}")
    if re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex', html, re.I):
        errors.append(f"{relative}: redirect page must stay crawlable")

netlify = tomllib.loads((ROOT / "netlify.toml").read_text(encoding="utf-8"))
rules = {(r.get("from"), r.get("to"), r.get("status"), r.get("force")) for r in netlify.get("redirects", [])}
for old, new in {
    "/vi-tri/*": "/vi-tri-lumi-hanoi/:splat",
    "/giai-doan-2/*": "/lumi-prestige/:splat",
    "/tien-do/*": "/tien-do-lumi-hanoi/:splat",
    "/giai-doan-1/*": "/lumi-signature/:splat",
    "/giai-doan-3/*": "/lumi-elite/:splat",
    "/chu-dau-tu/*": "/chu-dau-tu-capitaland/:splat",
    "/lien-he/*": "/giao-dich-lumi-hanoi/:splat",
}.items():
    if (old, new, 301, True) not in rules:
        errors.append(f"netlify.toml missing 301: {old} -> {new}")

sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
for relative in REDIRECTS:
    legacy_url = SITE + "/" + relative.removesuffix("index.html")
    if f"<loc>{legacy_url}</loc>" in sitemap:
        errors.append(f"legacy URL must not be in sitemap: {legacy_url}")

if errors:
    print(f"Legacy redirect QA FAILED ({len(errors)} issue(s))")
    for error in errors:
        print("- " + error)
    sys.exit(1)

print(f"Legacy redirect QA passed for {len(REDIRECTS)} static redirect pages.")
