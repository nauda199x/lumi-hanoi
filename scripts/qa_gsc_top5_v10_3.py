#!/usr/bin/env python3
"""GSC-driven SEO regression checks for the Top-5 push."""
from pathlib import Path
import re
import sys
import tomllib
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://lumi-hanoi.com"
errors = []

def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        errors.append(f"missing {relative}")
        return ""
    return path.read_text(encoding="utf-8")

def title_of(source: str) -> str:
    match = re.search(r"<title>(.*?)</title>", source, re.I | re.S)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""

home = read("index.html")
overview = read("tong-quan-lumi-hanoi/index.html")
sale = read("mua-ban-lumi-hanoi/index.html")
rent = read("cho-thue-lumi-hanoi/index.html")

exact_checks = {
    "home title": (home, "Lumi Hanoi – Thông tin dự án, Mua bán & Cho thuê căn hộ"),
    "overview title": (overview, "Tổng quan Lumi Hanoi: quy mô 5,6 ha, 9 tòa, 3.950 căn"),
}
for label, (source, token) in exact_checks.items():
    if title_of(source) != token:
        errors.append(f"{label} is not aligned with the GSC keyword map")

sale_title = title_of(sale)
if not sale_title.startswith("Mua bán căn hộ Lumi Hanoi"):
    errors.append("sale title must preserve the 'Mua bán căn hộ Lumi Hanoi' search intent")

rent_title = title_of(rent)
if not re.fullmatch(r"Cho Thuê Chung Cư Lumi Hanoi Mới Nhất T(?:[1-9]|1[0-2])/\d{4}", rent_title):
    errors.append("rent title must preserve the monthly 'Cho Thuê Chung Cư Lumi Hanoi' search intent")

if "<h1>Cho thuê chung cư Lumi Hanoi</h1>" not in rent:
    errors.append("rental H1 must target 'Cho thuê chung cư Lumi Hanoi'")
if '"@type":"CollectionPage"' not in sale or '"@type":"CollectionPage"' not in rent:
    errors.append("marketplace hubs must use CollectionPage schema")

cluster_pages = [
    "lumi-signature/index.html",
    "lumi-prestige/index.html",
    "lumi-elite/index.html",
    "vi-tri-lumi-hanoi/index.html",
    "phap-ly-lumi-hanoi/index.html",
    "tien-do-lumi-hanoi/index.html",
    "can-ho-1-phong-ngu-lumi-hanoi/index.html",
    "can-ho-2-phong-ngu-lumi-hanoi/index.html",
    "can-ho-3-phong-ngu-lumi-hanoi/index.html",
    "can-ho-4-phong-ngu-lumi-hanoi/index.html",
    "duplex-penthouse-lumi-hanoi/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s1/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s2/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s3/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s5/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s6/index.html",
    "mat-bang-lumi-hanoi/lumi-prestige/p1/index.html",
    "mat-bang-lumi-hanoi/lumi-prestige/p2/index.html",
    "mat-bang-lumi-hanoi/lumi-elite/e1/index.html",
    "mat-bang-lumi-hanoi/lumi-elite/e2/index.html",
]
for relative in cluster_pages:
    html = read(relative)
    if 'href="/mua-ban-lumi-hanoi/"' not in html:
        errors.append(f"{relative}: missing sale marketplace link")
    if 'href="/cho-thue-lumi-hanoi/"' not in html:
        errors.append(f"{relative}: missing rental marketplace link")

floor_hub = read("mat-bang-lumi-hanoi/index.html")
for anchor in ("Mua bán căn hộ Lumi Hanoi", "Cho thuê căn hộ Lumi Hanoi"):
    if anchor not in floor_hub:
        errors.append(f"floor-plan hub missing transaction anchor: {anchor}")

for path in ROOT.rglob("index.html"):
    if "admin" in path.parts:
        continue
    html = path.read_text(encoding="utf-8")
    for canonical in re.findall(r'<link\s+rel="canonical"\s+href="([^"]+)"', html, re.I):
        if canonical.startswith("http://"):
            errors.append(f"{path.relative_to(ROOT)} has HTTP canonical: {canonical}")

sitemap = ET.parse(ROOT / "sitemap.xml")
for node in sitemap.findall(".//{*}loc"):
    url = (node.text or "").strip()
    if not url.startswith(SITE + "/") and url != SITE + "/":
        errors.append(f"sitemap has non-canonical URL: {url}")

netlify = tomllib.loads(read("netlify.toml"))
rules = {(r.get("from"), r.get("to"), r.get("status"), r.get("force")) for r in netlify.get("redirects", [])}
for source in ("http://lumi-hanoi.com/*", "http://www.lumi-hanoi.com/*", "https://www.lumi-hanoi.com/*"):
    if (source, "https://lumi-hanoi.com/:splat", 301, True) not in rules:
        errors.append(f"missing canonical-host 301: {source}")

if errors:
    print(f"GSC Top-5 SEO QA FAILED ({len(errors)} issue(s))")
    for error in errors:
        print("- " + error)
    sys.exit(1)

print(f"GSC Top-5 SEO QA passed for {len(cluster_pages)} authority pages.")
