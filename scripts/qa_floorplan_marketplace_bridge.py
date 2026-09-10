#!/usr/bin/env python3
"""Regression checks for the 3C floor-plan → marketplace bridge."""
from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import generate_floorplan_marketplace_bridge as bridge


def fail(message: str) -> None:
    raise SystemExit(message)


def capture(pattern: str, raw: str, label: str) -> str:
    match = re.search(pattern, raw, flags=re.I | re.S)
    if not match:
        fail(f"missing {label}")
    return html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()


def local_file(href: str) -> Path:
    parsed = urlparse(href)
    path = unquote(parsed.path).lstrip("/")
    target = bridge.gen.ROOT / path
    if parsed.path.endswith("/"):
        target /= "index.html"
    return target


def module(raw: str, tower: str) -> str:
    match = re.search(
        re.escape(bridge.BRIDGE_START) + r"(.*?)" + re.escape(bridge.BRIDGE_END),
        raw,
        flags=re.S,
    )
    if not match:
        fail(f"{tower}: marketplace bridge markers missing")
    return match.group(1)


def main() -> None:
    before: dict[str, tuple[str, str, str, str]] = {}
    for item in bridge.sale.TOWERS:
        tower = item["tower"]
        path = bridge.floorplan_path(tower)
        if not path.is_file():
            fail(f"{tower}: missing floor-plan page {path}")
        raw = path.read_text(encoding="utf-8")
        title = capture(r"<title>(.*?)</title>", raw, f"{tower} title")
        h1 = capture(r"<h1[^>]*>(.*?)</h1>", raw, f"{tower} H1")
        canonical = capture(r'<link\s+rel="canonical"\s+href="([^"]+)"', raw, f"{tower} canonical")
        robots = capture(r'<meta\s+name="robots"\s+content="([^"]+)"', raw, f"{tower} robots")
        before[tower] = (title, h1, canonical, robots)

    listings = bridge.gen.fetch_approved()
    bridge.update_pages(listings)
    first_pass = {item["tower"]: bridge.floorplan_path(item["tower"]).read_text(encoding="utf-8") for item in bridge.sale.TOWERS}
    bridge.update_pages(listings)

    counts: list[str] = []
    for item in bridge.sale.TOWERS:
        tower = item["tower"]
        path = bridge.floorplan_path(tower)
        raw = path.read_text(encoding="utf-8")
        if raw != first_pass[tower]:
            fail(f"{tower}: generator is not idempotent")

        title = capture(r"<title>(.*?)</title>", raw, f"{tower} title after generation")
        h1 = capture(r"<h1[^>]*>(.*?)</h1>", raw, f"{tower} H1 after generation")
        canonical = capture(r'<link\s+rel="canonical"\s+href="([^"]+)"', raw, f"{tower} canonical after generation")
        robots = capture(r'<meta\s+name="robots"\s+content="([^"]+)"', raw, f"{tower} robots after generation")
        if (title, h1, canonical, robots) != before[tower]:
            fail(f"{tower}: 3C changed title/H1/canonical/robots")
        if "mặt bằng" not in title.lower() or "mặt bằng" not in h1.lower():
            fail(f"{tower}: primary floor-plan intent was lost")
        if raw.count(bridge.BRIDGE_START) != 1 or raw.count(bridge.BRIDGE_END) != 1:
            fail(f"{tower}: duplicate marketplace bridge markers")
        if raw.count("<h1") != 1:
            fail(f"{tower}: expected exactly one H1")

        section = module(raw, tower)
        expected_sale = f'/{item["slug"]}/'
        expected_rent = f'/cho-thue-lumi-hanoi/#tower={tower}'
        checks = [
            (f'data-tower="{tower}"' in section, "tower binding"),
            (f'>Giao dịch tại tòa {tower}</h2>' in section, "bridge H2"),
            (expected_sale in section, "controlled sale-tower CTA"),
            (expected_rent in section, "canonical rent-hub filter CTA"),
            ("/gia-can-ho-lumi-hanoi/" in section, "Market Index link"),
            ("/dang-tin-lumi-hanoi/#mua-ban" in section, "post-listing CTA"),
            ("giá chào" in section.lower(), "asking-price disclosure"),
            ("không phải giá giao dịch công chứng" in section.lower(), "transaction-price disclaimer"),
            ("shop chân đế" not in section.lower(), "shop exclusion"),
            ("<img" not in section.lower(), "image-free lightweight bridge"),
            ("application/ld+json" not in section.lower() and "ItemList" not in section, "no competing schema"),
        ]
        for ok, label in checks:
            if not ok:
                fail(f"{tower}: {label} check failed")

        primary_pos = raw.find("data-primary-floor-plan")
        if primary_pos < 0:
            # Elite pages render all authoritative floor groups directly rather
            # than designating one group as the primary plan. The semantic
            # floor-plan section itself is therefore the correct content marker.
            primary_pos = raw.find("floor-plan-section")
        bridge_pos = raw.find(bridge.BRIDGE_START)
        article_end = raw.find("</article>")
        if primary_pos < 0 or not (primary_pos < bridge_pos < article_end):
            fail(f"{tower}: bridge must sit after primary floor-plan content and before article end")

        sale_links = re.findall(r'<a[^>]+data-market-listing-link="sale"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', section, flags=re.S)
        rent_links = re.findall(r'<a[^>]+data-market-listing-link="rent"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', section, flags=re.S)
        if len(sale_links) > bridge.MAX_RECENT_LINKS or len(rent_links) > bridge.MAX_RECENT_LINKS:
            fail(f"{tower}: too many recent listing links")

        for kind, links in (("sale", sale_links), ("rent", rent_links)):
            for href, anchor_html in links:
                expected_prefix = "/mua-ban-lumi-hanoi/" if kind == "sale" else "/cho-thue-lumi-hanoi/"
                if not href.startswith(expected_prefix):
                    fail(f"{tower}: {kind} detail link escaped its canonical marketplace namespace: {href}")
                if not local_file(href).is_file():
                    fail(f"{tower}: generated detail link does not resolve locally: {href}")
                anchor = html.unescape(re.sub(r"<[^>]+>", "", anchor_html)).strip()
                if re.search(r"(?<!\d)(?:\+?84|0)[\d.\s-]{8,}(?!\d)", anchor):
                    fail(f"{tower}: phone number leaked into bridge anchor text")

        expected_sale_count = len(bridge.tower_rows(listings, tower, "sale"))
        expected_rent_count = len(bridge.tower_rows(listings, tower, "rent"))
        if f"<strong>{expected_sale_count} căn bán</strong>" not in section:
            fail(f"{tower}: sale count mismatch")
        if f"<strong>{expected_rent_count} căn cho thuê</strong>" not in section:
            fail(f"{tower}: rent count mismatch")
        if len(sale_links) != min(expected_sale_count, bridge.MAX_RECENT_LINKS):
            fail(f"{tower}: recent sale link count mismatch")
        if len(rent_links) != min(expected_rent_count, bridge.MAX_RECENT_LINKS):
            fail(f"{tower}: recent rent link count mismatch")

        counts.append(f"{tower}={expected_sale_count}/{expected_rent_count}")

    print("Floor-plan marketplace bridge QA: PASS — sale/rent counts " + ", ".join(counts))


if __name__ == "__main__":
    main()
