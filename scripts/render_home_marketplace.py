#!/usr/bin/env python3
"""Put real, crawlable approved marketplace links in homepage HTML.

The JS marketplace still refreshes the three visible cards. This static fallback
ensures the HTML response has links to real, currently eligible listing details.
It is rebuilt by the same scheduled SEO sync that updates marketplace sitemaps.
"""
from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from pathlib import Path

import generate_marketplace_seo as gen
from finalize_marketplace_sitemap import is_indexable

HOME = gen.ROOT / "index.html"
CARD_START = "<!-- HOME-LIVE-SEO:START -->"
CARD_END = "<!-- HOME-LIVE-SEO:END -->"
LINK_START = "<!-- HOME-RECENT-SEO:START -->"
LINK_END = "<!-- HOME-RECENT-SEO:END -->"
VALID_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def is_current(listing: dict, now: datetime) -> bool:
    if listing.get("status") not in (None, "approved"):
        return False
    slug = str(listing.get("slug") or "").strip()
    if not VALID_SLUG.fullmatch(slug):
        return False
    if listing.get("listing_type") not in ("rent", "sale"):
        return False
    if not is_indexable(listing):
        return False
    expiry = listing.get("expires_at")
    if expiry:
        try:
            dt = datetime.fromisoformat(str(expiry).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt <= now:
                return False
        except (ValueError, TypeError):
            return False
    return True


def choose(listings: list[dict], kind: str, now: datetime) -> list[dict]:
    rows = [row for row in listings if row.get("listing_type") == kind and is_current(row, now)]
    # Prioritize recently approved, genuinely available inventory, not old clickbait.
    rows.sort(
        key=lambda row: (
            str(row.get("approved_at") or row.get("created_at") or ""),
            str(row.get("id") or ""),
        ),
        reverse=True,
    )
    seen = set()
    result = []
    for row in rows:
        if row["slug"] not in seen:
            seen.add(row["slug"])
            result.append(row)
    return result


def first_image(row: dict) -> str:
    imgs = sorted(
        (i for i in row.get("listing_images", []) if i.get("storage_path")),
        key=lambda i: int(i.get("sort_order") or 0),
    )
    return gen.storage_url(imgs[0]["storage_path"]) if imgs else ""


def card(row: dict) -> str:
    url = esc(gen.listing_url(row))
    title = esc(row.get("title") or "Căn hộ Lumi Hà Nội")
    tower = esc(row.get("tower"))
    unit = esc(row.get("unit_type"))
    area = gen.clean(row.get("area_sqm"))
    label = "Cho thuê" if row["listing_type"] == "rent" else "Mua bán"
    place = " · ".join(filter(None, [tower, unit, esc(f"{area} m²" if area else "")]))
    image = esc(first_image(row))
    media = f'<img src="{image}" alt="{title}" width="480" height="330" loading="lazy" decoding="async">' if image else ""
    return (
        '<article class="home-live-card">'
        f'<a class="home-live-media" href="{url}" aria-label="Xem {title}">{media}<span class="home-live-pill">{label}</span></a>'
        '<div class="home-live-body">'
        f'<p class="home-live-location">{place}</p><h3><a href="{url}">{title}</a></h3>'
        '<div class="home-live-bottom">'
        f'<strong class="home-live-price">{esc(gen.format_price(row))}</strong>'
        f'<a class="home-live-detail" href="{url}">Xem căn →</a>'
        '</div></div></article>'
    )


def recent_links(rows: list[dict]) -> str:
    if not rows:
        return ""
    links = []
    for row in rows:
        href = esc(gen.listing_url(row))
        title = esc(row.get("title"))
        links.append(f'<a href="{href}">{title}</a>')
    return '<strong>Tin mới đang có:</strong> ' + " ".join(links)


def replace_marked(page: str, start: str, end: str, body: str) -> str:
    pattern = re.escape(start) + r".*?" + re.escape(end)
    if not re.search(pattern, page, flags=re.S):
        raise ValueError(f"Homepage missing marker: {start}")
    return re.sub(pattern, lambda _: start + "\n" + body + "\n" + end, page, count=1, flags=re.S)


def render(page: str, listings: list[dict], *, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    for kind in ("rent", "sale"):
        rows = choose(listings, kind, now)
        cards = "\n".join(card(row) for row in rows[:3])
        recent = recent_links(rows[3:11])
        grid = f'<div class="home-live-grid" data-home-grid="{kind}" aria-live="polite"></div>'
        if CARD_START + "-" + kind not in page:
            if grid not in page:
                raise ValueError(f"Homepage card container {kind} not found")
            page = page.replace(
                grid,
                grid.replace("</div>", f'\n<!-- HOME-LIVE-SEO:START-{kind} -->\n<!-- HOME-LIVE-SEO:END-{kind} -->\n</div>'),
                1,
            )
        page = replace_marked(page, f"<!-- HOME-LIVE-SEO:START-{kind} -->", f"<!-- HOME-LIVE-SEO:END-{kind} -->", cards)

        if f"<!-- HOME-RECENT-SEO:START-{kind} -->" not in page:
            status = re.search(r'<p\s+class="home-live-status"\s+data-home-status="' + kind + r'".*?</p>', page, re.S)
            if not status:
                raise ValueError(f"Homepage status container {kind} not found")
            following = f'\n<nav class="home-recent-links" aria-label="Tin {kind} mới tại Lumi Hà Nội"><!-- HOME-RECENT-SEO:START-{kind} --><!-- HOME-RECENT-SEO:END-{kind} --></nav>'
            page = page[:status.end()] + following + page[status.end():]
        page = replace_marked(page, f"<!-- HOME-RECENT-SEO:START-{kind} -->", f"<!-- HOME-RECENT-SEO:END-{kind} -->", recent)
    return page


def main() -> None:
    rows = gen.fetch_approved()
    before = HOME.read_text(encoding="utf-8")
    after = render(before, rows)
    if after != before:
        HOME.write_text(after, encoding="utf-8")
    print(
        "Homepage crawlable listings:",
        *(f"{kind}={len(choose(rows, kind, datetime.now(timezone.utc)))}" for kind in ("rent", "sale")),
    )


if __name__ == "__main__":
    main()
