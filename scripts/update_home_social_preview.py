#!/usr/bin/env python3
"""Keep the homepage Open Graph/Twitter preview pointed at the premium real-photo asset."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "index.html"
OG_URL = "https://lumi-hanoi.com/assets/media/og/lumi-hanoi-og-thuc-te-20260910.webp"
OG_ALT = "Lumi Hanoi – hình ảnh thực tế không gian và các tòa căn hộ"


def remove_meta(raw: str, *, attr: str, key: str) -> str:
    pattern = rf'^[ \t]*<meta\s+{attr}="{re.escape(key)}"\s+content="[^"]*"\s*/?>\s*\n?'
    return re.sub(pattern, "", raw, flags=re.I | re.M)


def main() -> None:
    raw = HOME.read_text(encoding="utf-8")
    original = raw

    # Remove stale optional image tags first so the block is deterministic.
    for key in ("og:image:secure_url", "og:image:type", "og:image:alt", "og:image:width", "og:image:height"):
        raw = remove_meta(raw, attr="property", key=key)
    for key in ("twitter:image", "twitter:image:alt"):
        raw = remove_meta(raw, attr="name", key=key)

    og_block = (
        f'    <meta property="og:image" content="{OG_URL}">\n'
        f'    <meta property="og:image:secure_url" content="{OG_URL}">\n'
        '    <meta property="og:image:type" content="image/webp">\n'
        f'    <meta property="og:image:alt" content="{OG_ALT}">'
    )
    raw, og_count = re.subn(
        r'^[ \t]*<meta\s+property="og:image"\s+content="[^"]*"\s*/?>',
        og_block,
        raw,
        count=1,
        flags=re.I | re.M,
    )
    if og_count != 1:
        raise RuntimeError("Homepage og:image tag was not found")

    twitter_block = (
        '    <meta name="twitter:card" content="summary_large_image">\n'
        f'    <meta name="twitter:image" content="{OG_URL}">\n'
        f'    <meta name="twitter:image:alt" content="{OG_ALT}">'
    )
    raw, twitter_count = re.subn(
        r'^[ \t]*<meta\s+name="twitter:card"\s+content="[^"]*"\s*/?>',
        twitter_block,
        raw,
        count=1,
        flags=re.I | re.M,
    )
    if twitter_count != 1:
        raise RuntimeError("Homepage twitter:card tag was not found")

    # Guard against accidentally touching ranking-critical homepage metadata.
    if '<title>Lumi Hanoi – Thông tin dự án, Mua bán & Cho thuê căn hộ</title>' not in raw:
        raise RuntimeError("Homepage title changed unexpectedly")
    if '<link rel="canonical" href="https://lumi-hanoi.com/">' not in raw:
        raise RuntimeError("Homepage canonical changed unexpectedly")

    if raw != original:
        HOME.write_text(raw, encoding="utf-8")
        print(f"Homepage social preview updated: {OG_URL}")
    else:
        print("Homepage social preview already current")


if __name__ == "__main__":
    main()
