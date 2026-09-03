#!/usr/bin/env python3
from pathlib import Path
from urllib.parse import urlparse
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://lumi-hanoi.com"

tower_pages = {
    "S1": ("mat-bang-lumi-hanoi/lumi-signature/s1/index.html", 8),
    "S2": ("mat-bang-lumi-hanoi/lumi-signature/s2/index.html", 8),
    "S3": ("mat-bang-lumi-hanoi/lumi-signature/s3/index.html", 8),
    "S5": ("mat-bang-lumi-hanoi/lumi-signature/s5/index.html", 8),
    "S6": ("mat-bang-lumi-hanoi/lumi-signature/s6/index.html", 12),
    "P1": ("mat-bang-lumi-hanoi/lumi-prestige/p1/index.html", 5),
    "P2": ("mat-bang-lumi-hanoi/lumi-prestige/p2/index.html", 5),
    "E1": ("mat-bang-lumi-hanoi/lumi-elite/e1/index.html", 5),
    "E2": ("mat-bang-lumi-hanoi/lumi-elite/e2/index.html", 6),
}

errors = []

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def jsonld(raw):
    out = []
    for body in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', raw, re.I | re.S):
        try:
            out.append(json.loads(body))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON-LD: {exc}")
    return out

for tower, (path, group_count) in tower_pages.items():
    raw = read(path)
    slug = path.replace("index.html", "")
    canonical = SITE + "/" + slug
    if f'<link rel="canonical" href="{canonical}">' not in raw:
        errors.append(f"{tower}: canonical mismatch")
    if len(re.findall(r"<h1\b", raw, re.I)) != 1:
        errors.append(f"{tower}: expected exactly one H1")
    if f'id="{tower.lower()}-read-plan"' not in raw:
        errors.append(f"{tower}: missing decision-context section")
    if f'/mua-ban-lumi-hanoi/#tower={tower}' not in raw or f'/cho-thue-lumi-hanoi/#tower={tower}' not in raw:
        errors.append(f"{tower}: missing tower-filter marketplace links")
    graphs = jsonld(raw)
    flat = []
    for data in graphs:
        if isinstance(data, dict):
            flat.extend(data.get("@graph", [data]))
    if not any(item.get("@type") == "FAQPage" for item in flat if isinstance(item, dict)):
        errors.append(f"{tower}: missing FAQPage schema")
    if f"{group_count} nhóm" not in raw and f"{group_count} nhóm mặt bằng" not in raw:
        errors.append(f"{tower}: group-count context missing")

hub = read("mat-bang-lumi-hanoi/index.html")
if 'id="tower-compare-title"' not in hub:
    errors.append("floor-plan hub missing comparison section")
for tower in tower_pages:
    if f">Mặt bằng {tower}<" not in hub:
        errors.append(f"floor-plan hub missing comparison link for {tower}")
if 'property="og:image"' not in hub or 'name="twitter:card"' not in hub:
    errors.append("floor-plan hub missing complete social metadata")

social_pages = [
    "vi-tri-lumi-hanoi/index.html",
    "lumi-signature/index.html",
    "lumi-prestige/index.html",
    "lumi-elite/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/index.html",
    "mat-bang-lumi-hanoi/lumi-prestige/index.html",
    "tin-tuc/index.html",
    "cho-thue-lumi-hanoi/index.html",
]
for path in social_pages:
    raw = read(path)
    if 'property="og:image"' not in raw or 'name="twitter:card"' not in raw:
        errors.append(f"{path}: incomplete OG/Twitter metadata")

market_js = read("assets/js/marketplace-list.js")
if "const applyQueryFilters=()=>{" not in market_js or 'hashParams.get("tower")' not in market_js:
    errors.append("marketplace tower deep-link initialization missing")
for path in ("mua-ban-lumi-hanoi/index.html", "cho-thue-lumi-hanoi/index.html"):
    if "marketplace-list.js?v=20260903-tower-filter" not in read(path):
        errors.append(f"{path}: stale marketplace list cache key")

netlify = read("netlify.toml")
for route in ("/mua-ban-lumi-hanoi/*", "/cho-thue-lumi-hanoi/*"):
    pattern = re.compile(r'\[\[redirects\]\]\s+from\s*=\s*"' + re.escape(route) + r'"\s+to\s*=\s*"/tin-dang-khong-con-hien-thi/"\s+status\s*=\s*404', re.S)
    if not pattern.search(netlify):
        errors.append(f"missing removed-listing 404 rule for {route}")

gone = read("tin-dang-khong-con-hien-thi/index.html")
if 'name="robots" content="noindex,follow"' not in gone:
    errors.append("removed-listing helper must be noindex,follow")
if "location.replace" in read("404.html"):
    errors.append("generic 404 must not JS-redirect removed listings")

legacy_prefixes = (
    "/toa-s1-lumi-hanoi/", "/toa-s2-lumi-hanoi/", "/toa-s3-lumi-hanoi/",
    "/toa-s5-lumi-hanoi/", "/toa-s6-lumi-hanoi/", "/toa-p1-lumi-hanoi/",
    "/toa-p2-lumi-hanoi/", "/toa-e1-lumi-hanoi/", "/toa-e2-lumi-hanoi/",
    "/toa-signature-", "/toa-prestige-", "/toa-elite-",
    "/vi-tri/", "/giai-doan-1/", "/giai-doan-2/", "/giai-doan-3/",
    "/tien-do/", "/chu-dau-tu/",
)
legacy_redirect_files = {
    "toa-s1-lumi-hanoi/index.html", "toa-s2-lumi-hanoi/index.html", "toa-s3-lumi-hanoi/index.html",
    "toa-s5-lumi-hanoi/index.html", "toa-s6-lumi-hanoi/index.html", "toa-p1-lumi-hanoi/index.html",
    "toa-p2-lumi-hanoi/index.html", "toa-e1-lumi-hanoi/index.html", "toa-e2-lumi-hanoi/index.html",
    "toa-signature-1-lumi-hanoi/index.html", "toa-signature-2-lumi-hanoi/index.html",
    "toa-signature-3-lumi-hanoi/index.html", "toa-signature-5-lumi-hanoi/index.html",
    "toa-signature-6-lumi-hanoi/index.html", "toa-prestige-1-lumi-hanoi/index.html",
    "toa-prestige-2-lumi-hanoi/index.html", "toa-elite-1-lumi-hanoi/index.html",
    "toa-elite-2-lumi-hanoi/index.html", "vi-tri/index.html", "giai-doan-1/index.html",
    "giai-doan-2/index.html", "giai-doan-3/index.html", "tien-do/index.html", "chu-dau-tu/index.html",
}
for file in ROOT.rglob("*.html"):
    rel = file.relative_to(ROOT).as_posix()
    if rel.startswith("admin/") or rel in legacy_redirect_files:
        continue
    raw = file.read_text(encoding="utf-8")
    for href in re.findall(r'href=["\']([^"\']+)["\']', raw, re.I):
        if not href.startswith("/"):
            continue
        path = urlparse(href).path
        if any(path.startswith(prefix) for prefix in legacy_prefixes):
            errors.append(f"legacy internal link: {rel} -> {href}")

root = ET.parse(ROOT / "sitemap.xml").getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
locs = [node.text or "" for node in root.findall(".//sm:loc", ns)]
if any("tin-dang-khong-con-hien-thi" in loc for loc in locs):
    errors.append("removed-listing helper must not enter sitemap")
if any(any(urlparse(loc).path.startswith(prefix) for prefix in legacy_prefixes) for loc in locs):
    errors.append("legacy URL found in sitemap")

if errors:
    print("SEO content hub QA: FAIL")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("SEO content hub QA: PASS")
print(f"Checked {len(tower_pages)} tower pages, social metadata, marketplace deep links, removed-listing handling and legacy hrefs.")
