#!/usr/bin/env python3
"""Finalize and validate the Lumi Hanoi marketplace listing sitemap.

The marketplace generator already creates crawlable detail pages. This step makes
sitemap-tin-dang.xml a strict projection of the currently public, indexable
Supabase inventory and uses updated_at as the preferred lastmod value. It also
fails CI if a sitemap URL has no generated detail page or if an eligible listing
is missing from the sitemap.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import generate_marketplace_seo as gen  # noqa: E402

SITEMAP = ROOT / "sitemap-tin-dang.xml"


def clean(value) -> str:
    return str(value or "").strip()


def compact(value) -> str:
    return re.sub(r"\s+", " ", clean(value)).strip()


def is_indexable(listing: dict) -> bool:
    """Mirror the production marketplace indexing policy.

    Descriptions only need to be non-empty; requiring filler text would keep
    otherwise complete approved listings out of Google discovery.
    """
    images = listing.get("listing_images") or []
    return all(
        [
            len(compact(listing.get("title"))) >= 12,
            bool(compact(listing.get("description"))),
            bool(images),
            bool(listing.get("price_vnd")),
            bool(listing.get("area_sqm")),
            bool(listing.get("tower")),
            bool(listing.get("unit_type")),
        ]
    )


def fetch_public_approved() -> list[dict]:
    base, key, _ = gen.read_public_config()
    params = {
        "select": (
            "id,slug,listing_type,title,description,tower,unit_type,area_sqm,price_vnd,"
            "is_featured,approved_at,created_at,updated_at,expires_at,"
            "listing_images(id,storage_path,sort_order,alt_text)"
        ),
        "status": "eq.approved",
        "order": "is_featured.desc,sort_priority.desc,approved_at.desc",
        "limit": "1000",
    }
    url = f"{base}/rest/v1/listings?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(
        url,
        headers={
            "apikey": key,
            "Accept": "application/json",
            "User-Agent": "lumi-hanoi-marketplace-sitemap-finalizer/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected Supabase response while finalizing marketplace sitemap")
    return payload


def lastmod(listing: dict) -> str:
    for field in ("updated_at", "approved_at", "created_at"):
        value = clean(listing.get(field))
        match = re.match(r"(\d{4}-\d{2}-\d{2})", value)
        if match:
            return match.group(1)
    return ""


def write_sitemap(listings: list[dict]) -> list[str]:
    eligible = [listing for listing in listings if is_indexable(listing)]
    urls = [gen.SITE + gen.listing_url(listing) for listing in eligible]
    if len(urls) != len(set(urls)):
        duplicates = sorted({url for url in urls if urls.count(url) > 1})
        raise RuntimeError(f"Duplicate marketplace sitemap URLs: {duplicates[:5]}")

    rows = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for listing, loc in zip(eligible, urls):
        rows.append("  <url>")
        rows.append(f"    <loc>{escape(loc)}</loc>")
        stamp = lastmod(listing)
        if stamp:
            rows.append(f"    <lastmod>{stamp}</lastmod>")
        rows.append("  </url>")
    rows.append("</urlset>")
    SITEMAP.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return urls


def validate_detail_pages(urls: list[str]) -> None:
    missing: list[str] = []
    for url in urls:
        path = urlparse(url).path.strip("/")
        page = ROOT / path / "index.html"
        if not page.exists():
            missing.append(path)
    if missing:
        raise RuntimeError(
            "Marketplace sitemap points to missing generated detail pages: " + ", ".join(missing[:10])
        )


def write_summary(approved_count: int, indexed_count: int) -> None:
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary:
        return
    with open(summary, "a", encoding="utf-8") as handle:
        handle.write("## Marketplace sitemap sync\n")
        handle.write(f"- Public approved listings: **{approved_count}**\n")
        handle.write(f"- Indexable listing URLs in sitemap: **{indexed_count}**\n")
        handle.write("- `lastmod`: prefers `updated_at`, then `approved_at`, then `created_at`\n")
        handle.write("- Sitemap/detail-page parity: **OK**\n")


def main() -> None:
    listings = fetch_public_approved()
    urls = write_sitemap(listings)
    validate_detail_pages(urls)
    write_summary(len(listings), len(urls))
    print(f"Marketplace sitemap finalized: {len(urls)}/{len(listings)} approved listings indexable")


if __name__ == "__main__":
    main()
