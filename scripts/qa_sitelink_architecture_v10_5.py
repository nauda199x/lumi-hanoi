#!/usr/bin/env python3
"""Regression checks for core navigation and P1/P2 sitelink architecture."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

def read(path):
    p = ROOT / path
    if not p.is_file():
        errors.append(f"missing {path}")
        return ""
    return p.read_text(encoding="utf-8")

home = read("index.html")
hub = read("mat-bang-lumi-hanoi/index.html")
prestige_hub = read("mat-bang-lumi-hanoi/lumi-prestige/index.html")
p1 = read("mat-bang-lumi-hanoi/lumi-prestige/p1/index.html")
p2 = read("mat-bang-lumi-hanoi/lumi-prestige/p2/index.html")
prestige = read("lumi-prestige/index.html")
sitemap = read("sitemap.xml")

core_urls = [
    "/tong-quan-lumi-hanoi/",
    "/mat-bang-lumi-hanoi/",
    "/gia-can-ho-lumi-hanoi/",
    "/mua-ban-lumi-hanoi/",
    "/cho-thue-lumi-hanoi/",
    "/tien-do-lumi-hanoi/",
]
for url in core_urls:
    if url not in home:
        errors.append(f"homepage missing core link {url}")

for url in (
    "/mat-bang-lumi-hanoi/lumi-prestige/p1/",
    "/mat-bang-lumi-hanoi/lumi-prestige/p2/",
):
    for name, raw in (("home", home), ("floor hub", hub), ("prestige floor hub", prestige_hub), ("prestige page", prestige)):
        if url not in raw:
            errors.append(f"{name} missing {url}")

p1_tokens = [
    "<title>Mặt bằng P1 Lumi Hanoi – Tầng điển hình & layout Prestige</title>",
    "<h1>Mặt bằng P1 Lumi Hanoi</h1>",
    'id="mat-bang-tang-p1"',
    'id="layout-can-p1"',
    "So sánh P1 &amp; P2",
]
p2_tokens = [
    "<title>Mặt bằng P2 Lumi Hanoi – Tầng điển hình & layout Prestige</title>",
    "<h1>Mặt bằng P2 Lumi Hanoi</h1>",
    'id="mat-bang-tang-p2"',
    'id="layout-can-p2"',
    "So sánh P1 &amp; P2",
]
for token in p1_tokens:
    if token not in p1:
        errors.append(f"P1 missing {token}")
for token in p2_tokens:
    if token not in p2:
        errors.append(f"P2 missing {token}")

for url in (
    "https://lumi-hanoi.com/",
    "https://lumi-hanoi.com/lumi-prestige/",
    "https://lumi-hanoi.com/mat-bang-lumi-hanoi/",
    "https://lumi-hanoi.com/mat-bang-lumi-hanoi/lumi-prestige/",
    "https://lumi-hanoi.com/mat-bang-lumi-hanoi/lumi-prestige/p1/",
    "https://lumi-hanoi.com/mat-bang-lumi-hanoi/lumi-prestige/p2/",
):
    prefix = f"<loc>{url}</loc><lastmod>"
    start = sitemap.find(prefix)
    if start < 0:
        errors.append(f"sitemap lastmod missing for {url}")
        continue
    date_start = start + len(prefix)
    lastmod = sitemap[date_start:date_start + 10]
    if len(lastmod) != 10 or lastmod < "2026-08-31":
        errors.append(f"sitemap lastmod stale for {url}")

if errors:
    print("SEO sitelink architecture QA: FAIL")
    for error in errors:
        print("-", error)
    sys.exit(1)

print("SEO sitelink architecture QA: PASS")
