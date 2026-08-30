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

home = read("index.html")
overview = read("tong-quan-lumi-hanoi/index.html")
sale = read("mua-ban-lumi-hanoi/index.html")
rent = read("cho-thue-lumi-hanoi/index.html")

checks = {
    "home title": (home, "Lumi Hanoi – Thông tin dự án, Mua bán & Cho thuê căn hộ"),
    "overview title": (overview, "Tổng quan Lumi Hanoi: quy mô 5,6 ha, 9 tòa, 3.950 căn"),
    "sale title": (sale, "Mua bán căn hộ Lumi Hanoi – Quỹ căn chuyển nhượng cập nhật"),
    "rent title": (rent, "Cho thuê căn hộ Lumi Hanoi – Tin đăng mới & giá thuê"),
}
for label, (source, token) in checks.items():
    if f"<title>{token}</title>" not in source:
        errors.append(f"{label} is not aligned with the GSC keyword map")

if "<h1>Cho thuê căn hộ Lumi Hanoi</h1>" not in rent:
    errors.append("rental H1 must target 'Cho thuê căn hộ Lumi Hanoi'")
if '"@type":"CollectionPage"' not in sale or '"@type":"CollectionPage"' not in rent:
    errors.append("marketplace hubs must use CollectionPage schema")

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

print("GSC Top-5 SEO core QA passed.")
