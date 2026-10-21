#!/usr/bin/env python3
"""Generate lightweight, self-hosted WebP heroes for the three marketplace pages.

Run from repo root in GitHub Actions. Never modifies the original source images.
Only changes three hero image references and their dedicated CSS file.
"""
from __future__ import annotations
import io
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "assets/media/handover-2026"
CSS = ROOT / "assets/css/marketplace-real-heroes.css"
SPECS = (
    ("dang-tin-lumi-hanoi/index.html", "lumi-hanoi-toa-thap-duong-dao-thuc-te", 700),
    ("mua-ban-lumi-hanoi/index.html", "lumi-hanoi-canh-quan-mat-nuoc-thuc-te", 640),
    ("cho-thue-lumi-hanoi/index.html", "lumi-hanoi-goc-sofa-sanh-thuc-te", 640),
)
OLD_CSS_LINK = '<link rel="stylesheet" href="/assets/css/marketplace-real-heroes.css?v=20261021-real-heroes1">'
NEW_CSS_LINK = '<link rel="stylesheet" href="/assets/css/marketplace-real-heroes.css?v=20261021-heroes-perf1">'


def optimize(path: Path, limit_width: int, max_bytes: int, original_bytes: int) -> tuple[bytes, int, int]:
    with Image.open(path) as raw:
        original = ImageOps.exif_transpose(raw).convert("RGB")
    target_bytes = min(max_bytes, int(original_bytes * .79))
    smallest = None
    for width in (limit_width, int(limit_width * .90), int(limit_width * .80)):
        resized = original.copy()
        if resized.width > width:
            height = round(resized.height * width / resized.width)
            resized = resized.resize((width, height), Image.Resampling.LANCZOS)
        for quality in (74, 70, 66, 62, 58, 54, 50):
            out = io.BytesIO()
            resized.save(out, "WEBP", quality=quality, method=6)
            data = out.getvalue()
            if smallest is None or len(data) < len(smallest[0]):
                smallest = (data, resized.width, resized.height)
            if len(data) <= target_bytes:
                return data, resized.width, resized.height
    assert smallest is not None
    if len(smallest[0]) >= original_bytes:
        raise RuntimeError(f"No size reduction: {path}")
    return smallest


def swap_one(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        if new in text:   # reruns are idempotent
            return text
        raise RuntimeError(f"Missing expected reference {label}: {old}")
    return text.replace(old, new)


def main() -> None:
    css = CSS.read_text(encoding="utf-8")
    for page, stem, breakpoint in SPECS:
        original = MEDIA / (stem + ".webp")
        original_mobile = MEDIA / (stem + "-640.webp")
        if not original.is_file() or not original_mobile.is_file():
            raise RuntimeError(f"Missing approved on-site source photo: {stem}")
        for source, suffix, limit, ceiling in (
            (original, "-hero-lite.webp", 1440, 195 * 1024),
            (original_mobile, "-hero-lite-640.webp", 640, 72 * 1024),
        ):
            output = MEDIA / (stem + suffix)
            if not output.exists():
                data, width, height = optimize(source, limit, ceiling, source.stat().st_size)
                output.write_bytes(data)
                print(f"{output.relative_to(ROOT)} {source.stat().st_size:,} -> {len(data):,} bytes ({width}x{height})", flush=True)
        base = "/assets/media/handover-2026/" + stem
        lite = base + "-hero-lite"
        # Replacing the mobile variant first prevents accidental double replacements.
        css = swap_one(css, base + "-640.webp", lite + "-640.webp", stem + " CSS mobile")
        css = swap_one(css, base + ".webp", lite + ".webp", stem + " CSS desktop")
        htmlfile = ROOT / page
        html = htmlfile.read_text(encoding="utf-8")
        if page != "dang-tin-lumi-hanoi/index.html":
            html = swap_one(html, base + "-640.webp", lite + "-640.webp", stem + " HTML mobile")
            html = swap_one(html, base + ".webp", lite + ".webp", stem + " HTML desktop")
        if OLD_CSS_LINK in html:
            # Correct breakpoint prevents both images downloading on phones.
            preload = (
                f'<link rel="preload" as="image" href="{lite}-640.webp" media="(max-width: {breakpoint}px)" fetchpriority="high">\n'
                f'<link rel="preload" as="image" href="{lite}.webp" media="(min-width: {breakpoint+1}px)" fetchpriority="high">\n'
            )
            html = html.replace(OLD_CSS_LINK, preload + NEW_CSS_LINK, 1)
        elif NEW_CSS_LINK not in html:
            raise RuntimeError(f"Hero stylesheet link missing in {page}")
        htmlfile.write_text(html, encoding="utf-8")
    # Hero image covers large areas. Avoid GPU filters on lower-end mobile devices.
    marker = "/* MARKETPLACE-HERO-PERF-20261021 */"
    if marker not in css:
        css += (
            "\n" + marker + "\n"
            ".marketplace-discovery .marketplace-hero--sale .article-hero-media,"
            ".marketplace-discovery .marketplace-hero--rent .article-hero-media{filter:none}\n"
            ".submit-landing .submit-hero-card{backdrop-filter:none;-webkit-backdrop-filter:none}\n"
        )
    CSS.write_text(css, encoding="utf-8")
    for page, stem, _ in SPECS:
        html = (ROOT / page).read_text(encoding="utf-8")
        if NEW_CSS_LINK not in html or (stem + "-hero-lite") not in html:
            raise RuntimeError(f"Failed final verification for {page}")
    print("Verified all three pages use locally optimized hero images and versioned CSS.")


if __name__ == "__main__":
    main()
