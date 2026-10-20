#!/usr/bin/env python3
"""Import user-supplied public Drive photos as optimized self-hosted WebP assets.

Runs in GitHub Actions with repository-scoped write permissions.
Only rewrites the newly introduced Drive photo IDs, leaving legacy media intact.
"""
from __future__ import annotations

import io
import re
import time
from pathlib import Path

import requests
from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "assets" / "media" / "real-2026"
SOURCE = {
    "1jpHyiWSiiWvPSyfYVFREzX-j13Z2-FHU": "lumi-ho-boi-canh-quan",
    "1Yvgu6_TYYqUOw1ZtdEqKXwtAMrglrf76": "lumi-ho-boi-ghe-nghi",
    "1Htjkg_QJNHCOTDWFGdRp86Dv15WPGcwu": "lumi-duong-dao-canh-quan",
    "11KKI3M7zLN7IkJE5_tNjFiyAe6XAmLj3": "lumi-thap-can-ho-ngoai-that",
    "1XhRFeKbX2PbzwsltIEBrOEU7Em7cjN09": "lumi-signature-buoi-toi",
    "1R_J8RPe4S8mcpbg1c5R06hiD_NV8WoU2": "lumi-san-the-thao",
    "12L8mGNu2YSqbaJH9U7o7GLJ8mZppRbb7": "lumi-phong-sinh-hoat-sofa",
    "1U0gTBj3xVKxTUt70pbrtXSYmI6ilWeOB": "lumi-ban-an-cong-dong",
    "1AyzYkwfMkd3ZxpGNpQmBOIwpmplSOee6": "lumi-phong-sinh-hoat-chung",
    "1zq_xqlr92sVcO0NDZ_dNeZ2MNhZn2npo": "lumi-phong-khach-sinh-hoat",
    "1pTFCdmJ1TJioBZp_cHUtxRyDnm2rEjQS": "lumi-khu-vui-choi-tre-em",
    "1th-H74vN1SqQzjMgjgUowlQJURWNuPhO": "lumi-phong-gym",
    "1D0zSnUUQjqyk7hZ35j3AHmEoRd3LrwSx": "lumi-phong-billiards",
    "1vKqb37_9yXsKavgcwLzd2MmCi-FgzmtQ": "lumi-phong-billiards-toan-canh",
    "1AcdOIaUkoGDBBMT9HFqwbV1lDNOVLEFG": "lumi-ban-billiards",
    "13xQEPg0aIyyAlOcOmsjE367ZJjrAvT0u": "lumi-billiards-thuc-te",
}
HTMLS = (
    ROOT / "index.html",
    ROOT / "tien-ich-lumi-hanoi" / "index.html",
    ROOT / "tong-quan-lumi-hanoi" / "index.html",
    ROOT / "hinh-anh-thuc-te-lumi-hanoi" / "index.html",
)
PHOTO_URL_RE = re.compile(
    r"https://drive\\.google\\.com/thumbnail\\?id=([A-Za-z0-9_-]+)(?:&amp;|&)sz=w(\\d+)"
)


def fetch_image(session: requests.Session, file_id: str) -> Image.Image:
    urls = [
        f"https://drive.google.com/thumbnail?id={file_id}&sz=w1600",
        f"https://drive.google.com/uc?export=download&id={file_id}",
    ]
    last_error = None
    for url in urls:
        for attempt in range(3):
            try:
                resp = session.get(url, timeout=40, allow_redirects=True)
                resp.raise_for_status()
                if not resp.headers.get("Content-Type", "").lower().startswith("image/"):
                    raise ValueError(f"Non-image response {resp.headers.get('Content-Type')}")
                img = Image.open(io.BytesIO(resp.content))
                img.load()
                img = ImageOps.exif_transpose(img)
                return img.convert("RGB")
            except (requests.RequestException, OSError, ValueError, UnidentifiedImageError) as exc:
                last_error = exc
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Could not retrieve {file_id}: {last_error}")


def save_variants(image: Image.Image, stem: str) -> None:
    for width in (640, 1200, 1600):
        resized = image.copy()
        if resized.width > width:
            height = round(resized.height * (width / resized.width))
            resized = resized.resize((width, height), Image.Resampling.LANCZOS)
        out = DEST / f"{stem}-{width}.webp"
        resized.save(out, "WEBP", quality=80, method=5)
        print(f"Saved {out.relative_to(ROOT)} {out.stat().st_size:,} bytes", flush=True)


def local_path(match: re.Match[str]) -> str:
    file_id, requested_width = match.group(1), int(match.group(2))
    stem = SOURCE.get(file_id)
    if not stem:
        return match.group(0)
    if requested_width <= 640:
        w = 640
    elif requested_width <= 1200:
        w = 1200
    else:
        w = 1600
    return f"/assets/media/real-2026/{stem}-{w}.webp"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; LumiPhotoImporter/1.0)"})
        for file_id, stem in SOURCE.items():
            print(f"Downloading {stem}", flush=True)
            save_variants(fetch_image(session, file_id), stem)
    for page in HTMLS:
        source = page.read_text(encoding="utf-8")
        updated = PHOTO_URL_RE.sub(local_path, source)
        if updated == source:
            raise RuntimeError(f"No photo URL replacements found in {page}")
        page.write_text(updated, encoding="utf-8")
        print(f"Rewrote optimized image URLs: {page.relative_to(ROOT)}", flush=True)
    unresolved = []
    for page in HTMLS:
        text = page.read_text(encoding="utf-8")
        for file_id in SOURCE:
            if f"drive.google.com/thumbnail?id={file_id}" in text:
                unresolved.append(f"{page}: {file_id}")
    if unresolved:
        raise RuntimeError("Unresolved original photo URL references: " + ", ".join(unresolved))
    print(f"Imported {len(SOURCE)} unique public photos (3 optimized widths each).", flush=True)


if __name__ == "__main__":
    main()
