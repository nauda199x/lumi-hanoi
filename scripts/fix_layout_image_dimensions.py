#!/usr/bin/env python3
"""Add intrinsic width/height to floor-plan images used by apartment guide pages.

This is intentionally narrow: it repairs the four apartment/floor-plan guide pages
that use large local WebP plans. Intrinsic dimensions prevent layout shift without
changing rendered CSS sizing.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "can-ho-1-phong-ngu-lumi-hanoi/index.html",
    ROOT / "can-ho-2-phong-ngu-lumi-hanoi/index.html",
    ROOT / "can-ho-3-phong-ngu-lumi-hanoi/index.html",
    ROOT / "duplex-penthouse-lumi-hanoi/index.html",
]
IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
SRC_RE = re.compile(r"\bsrc=(['\"])(.*?)\1", re.IGNORECASE)
WIDTH_RE = re.compile(r"\bwidth=(['\"])[^'\"]*\1", re.IGNORECASE)
HEIGHT_RE = re.compile(r"\bheight=(['\"])[^'\"]*\1", re.IGNORECASE)


def source_file(src: str) -> Path | None:
    parsed = urlparse(src)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
        return None
    path = ROOT / unquote(parsed.path).lstrip("/")
    return path if path.is_file() else None


def repair_tag(tag: str) -> tuple[str, bool]:
    has_width = bool(WIDTH_RE.search(tag))
    has_height = bool(HEIGHT_RE.search(tag))
    if has_width and has_height:
        return tag, False
    src_match = SRC_RE.search(tag)
    if not src_match:
        return tag, False
    image_path = source_file(src_match.group(2))
    if not image_path:
        return tag, False
    try:
        with Image.open(image_path) as image:
            width, height = image.size
    except Exception as exc:  # pragma: no cover - diagnostics for CI
        print(f"skip unreadable image {image_path.relative_to(ROOT)}: {exc}")
        return tag, False

    attrs = ""
    if not has_width:
        attrs += f' width="{width}"'
    if not has_height:
        attrs += f' height="{height}"'
    if tag.endswith("/>"):
        return tag[:-2] + attrs + "/>", True
    return tag[:-1] + attrs + ">", True


def repair_page(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    changed = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        new_tag, did_change = repair_tag(match.group(0))
        changed += int(did_change)
        return new_tag

    updated = IMG_RE.sub(repl, text)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
    return changed


def main() -> None:
    total = 0
    for page in TARGETS:
        count = repair_page(page)
        total += count
        print(f"{page.relative_to(ROOT)}: added intrinsic dimensions to {count} image(s)")
    print(f"total repaired image tags: {total}")


if __name__ == "__main__":
    main()
