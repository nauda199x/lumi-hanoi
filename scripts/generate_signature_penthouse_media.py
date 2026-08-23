#!/usr/bin/env python3
"""Generate optimized web previews from the verified Signature penthouse PDFs."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import fitz
import requests
from PIL import Image

OUT = Path("assets/media/signature/penthouse")
OUT.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "S1": {"id": "1E8bquyIGKfjJmzw1DMFz7QhauYp_M91K", "pages": [(0, "s1-floor-35.webp")]},
    "S2": {"id": "11Jj-zHsk1Tk84aFhuzcUDkZiKSZXYqHn", "pages": [(0, "s2-floor-35.webp")]},
    "S3": {"id": "1vMyv4hj7SYKgTlzge7-2opnkCbHU0FFo", "pages": [(0, "s3-floor-35.webp")]},
    "S5": {"id": "1bTusfxZrbE9ZAuDLUvF4tDIXUWfpbgUJ", "pages": [(0, "s5-floor-34.webp")]},
    "S6": {"id": "1GbYNZe3MJtbe497rrxwmeEv6HfLCHL4i", "pages": [(0, "s6-floor-34.webp"), (1, "s6-floor-35.webp")]},
}


def download(file_id: str) -> bytes:
    urls = [
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t",
        f"https://drive.google.com/uc?export=download&id={file_id}",
    ]
    last = None
    for url in urls:
        r = requests.get(url, timeout=60, allow_redirects=True)
        last = r
        if r.ok and r.content.startswith(b"%PDF"):
            return r.content
    raise RuntimeError(f"Could not download PDF {file_id}: {last.status_code if last else 'no response'}")


def crop_white(im: Image.Image) -> Image.Image:
    gray = im.convert("L")
    mask = gray.point(lambda x: 255 if x < 248 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return im
    l, t, r, b = bbox
    pad = 30
    return im.crop((max(0, l-pad), max(0, t-pad), min(im.width, r+pad), min(im.height, b+pad)))


def render(pdf_bytes: bytes, page_no: int) -> Image.Image:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(page_no)
    # 180 dpi equivalent: 180/72 = 2.5 scale.
    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
    im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    im = im.rotate(-90, expand=True)
    return crop_white(im)


def main() -> None:
    for tower, meta in SOURCES.items():
        pdf = download(meta["id"])
        for page_no, filename in meta["pages"]:
            im = render(pdf, page_no)
            target = OUT / filename
            im.save(target, "WEBP", lossless=True, method=6)
            print(f"{tower}: {filename} -> {im.width}x{im.height}, {target.stat().st_size} bytes")


if __name__ == "__main__":
    main()
