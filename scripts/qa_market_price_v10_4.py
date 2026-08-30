#!/usr/bin/env python3
"""Regression checks for the data-driven Lumi Hanoi market price page."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        errors.append(f"missing {relative}")
        return ""
    return path.read_text(encoding="utf-8")

page = read("gia-can-ho-lumi-hanoi/index.html")
css = read("assets/css/market-price.css")
generator = read("scripts/generate_marketplace_seo.py")
home = read("index.html")
sale = read("mua-ban-lumi-hanoi/index.html")
rent = read("cho-thue-lumi-hanoi/index.html")
hub = read("giao-dich-lumi-hanoi/index.html")
sitemap = read("sitemap.xml")
workflow = read(".github/workflows/sync-marketplace-seo.yml")

required_page_tokens = [
    "<title>Giá căn hộ Lumi Hanoi – Bảng giá & giá/m² cập nhật 2026</title>",
    '<link rel="canonical" href="https://lumi-hanoi.com/gia-can-ho-lumi-hanoi/">',
    "<h1>Giá căn hộ Lumi Hanoi</h1>",
    "MARKET-PRICE-STATS:START",
    "MARKET-PRICE-STATS:END",
    '"@type":"Dataset"',
    "giá rao",
    "không phải giá giao dịch",
    "/mua-ban-lumi-hanoi/",
    "/cho-thue-lumi-hanoi/",
    "/dang-tin-lumi-hanoi/",
]
for token in required_page_tokens:
    if token not in page:
        errors.append(f"price page missing token: {token}")

for token in ("market-kpis", "market-table-card", "price-factor-grid", "@media(max-width:700px)"):
    if token not in css:
        errors.append(f"price CSS missing: {token}")

for token in (
    'PRICE_PAGE = ROOT / "gia-can-ho-lumi-hanoi" / "index.html"',
    "MARKET_PRICE_START",
    "sync_market_price_page(generated)",
    "APARTMENT_UNIT_TYPES",
    "median(",
    'current_unit.lower() == "shop chân đế"',
    "render_market_table_rows",
    "render_phase_rows",
):
    if token not in generator:
        errors.append(f"generator missing price-data behavior: {token}")

for relative, source in (
    ("index.html", home),
    ("mua-ban-lumi-hanoi/index.html", sale),
    ("cho-thue-lumi-hanoi/index.html", rent),
    ("giao-dich-lumi-hanoi/index.html", hub),
):
    if 'href="/gia-can-ho-lumi-hanoi/"' not in source:
        errors.append(f"{relative}: missing internal link to price page")

if "<loc>https://lumi-hanoi.com/gia-can-ho-lumi-hanoi/</loc>" not in sitemap:
    errors.append("sitemap missing price page")
if "gia-can-ho-lumi-hanoi" not in workflow:
    errors.append("marketplace sync workflow does not commit price page")

if errors:
    print(f"Market price V10.4 QA FAILED ({len(errors)} issue(s))")
    for error in errors:
        print("- " + error)
    sys.exit(1)

print("Market price V10.4 QA passed: SEO page, live aggregation and internal links verified.")
