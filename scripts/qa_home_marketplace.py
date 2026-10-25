#!/usr/bin/env python3
"""Offline regression checks for crawlable, safe homepage marketplace links."""
from datetime import datetime, timezone
from pathlib import Path

import render_home_marketplace as seo


def listing(slug: str, kind: str, *, expires: str = "2099-01-01T00:00:00Z", title: str = "Cho thuê căn hộ Lumi Hà Nội 2PN") -> dict:
    return {
        "status": "approved",
        "slug": slug,
        "listing_type": kind,
        "title": title,
        "description": "Căn thật đầy đủ thông tin và ảnh được kiểm duyệt trước khi đăng.",
        "tower": "S3",
        "unit_type": "2PN",
        "area_sqm": 62,
        "price_vnd": 12000000 if kind == "rent" else 4200000000,
        "approved_at": "2026-10-23T00:00:00Z",
        "expires_at": expires,
        "listing_images": [{"storage_path": "pending/test/01.jpg", "sort_order": 0}],
    }


def main() -> None:
    page = Path("index.html").read_text(encoding="utf-8")
    rows = [
        listing("tin-thue-moi", "rent", title="Căn 2PN full nội thất Lumi Hanoi"),
        listing("tin-ban-moi", "sale", title="Bán căn 2PN đẹp tại Lumi Hà Nội"),
        listing("tin-thue-het-han", "rent", expires="2000-01-01T00:00:00Z"),
        listing("tin-sai", "rent", title="<script>alert('bad')</script>"),
    ]
    now = datetime(2026, 10, 25, tzinfo=timezone.utc)
    result = seo.render(page, rows, now=now)
    assert '<a class="home-live-media" href="/cho-thue-lumi-hanoi/tin-thue-moi/"' in result
    assert '<a class="home-live-media" href="/mua-ban-lumi-hanoi/tin-ban-moi/"' in result
    assert "/tin-thue-het-han/" not in result, "Expired listings cannot receive homepage links"
    assert "<script>alert('bad')</script>" not in result, "Untrusted titles must be escaped"
    assert "&lt;script&gt;" in result, "Escaped content should remain visible"
    assert seo.render(result, rows, now=now) == result, "Sync must be idempotent"
    assert result.count('<article class="home-live-card">') >= 2
    assert '<link rel="canonical" href="https://lumi-hanoi.com/">' in result
    assert "data-home-grid=\"rent\"" in result and "data-home-grid=\"sale\"" in result
    print("PASS: homepage prerendered crawlable listing links, safety, expiry and idempotency")


if __name__ == "__main__":
    main()
