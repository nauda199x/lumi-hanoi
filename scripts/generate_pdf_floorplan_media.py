#!/usr/bin/env python3
"""Generate web previews for floor-plan PDFs that were not previously published as images."""
from __future__ import annotations

from pathlib import Path

import fitz
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

SOURCES = [
    {
        "name": "P1 tầng 30",
        "id": "19-uso6U9FWLVs-uN68nqMzKWq6Joxcny",
        "page": 1,
        "target": ROOT / "assets/media/prestige/floor-plans/p1-t30.webp",
    },
    {
        "name": "P2 tầng 30",
        "id": "13XRjgsJbuvXJrymVCBUfucYI4ZM251Qu",
        "page": 1,
        "target": ROOT / "assets/media/prestige/floor-plans/p2-t30.webp",
    },
    {
        "name": "E1 tầng 29",
        "id": "1yfcTt8xlQ7_yVABnKUuqnS1JY0Ty7ZbM",
        "page": 0,
        "target": ROOT / "assets/media/elite/floor-plans/e1-t29.webp",
    },
    {
        "name": "E2 tầng 24",
        "id": "1zqhh1L1f4Nbo4I-ecD1YbgO3y26_fdgU",
        "page": 0,
        "target": ROOT / "assets/media/elite/floor-plans/e2-t24.webp",
    },
    {
        "name": "E2 tầng 29",
        "id": "1zNXaIpnwT5wCTrxl8Q7bG7Cg5n7NJ1Gz",
        "page": 0,
        "target": ROOT / "assets/media/elite/floor-plans/e2-t29.webp",
    },
]


def download(file_id: str) -> bytes:
    urls = [
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t",
        f"https://drive.google.com/uc?export=download&id={file_id}",
    ]
    last = None
    for url in urls:
        response = requests.get(url, timeout=90, allow_redirects=True)
        last = response
        if response.ok and response.content.startswith(b"%PDF"):
            return response.content
    status = last.status_code if last is not None else "no response"
    raise RuntimeError(f"Could not download PDF {file_id}: {status}")


def crop_white(image: Image.Image) -> Image.Image:
    gray = image.convert("L")
    mask = gray.point(lambda x: 255 if x < 248 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return image
    left, top, right, bottom = bbox
    pad = 30
    return image.crop(
        (
            max(0, left - pad),
            max(0, top - pad),
            min(image.width, right + pad),
            min(image.height, bottom + pad),
        )
    )


def render(pdf_bytes: bytes, page_no: int) -> Image.Image:
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = document.load_page(page_no)
    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    image = image.rotate(-90, expand=True)
    return crop_white(image)


def main() -> None:
    for item in SOURCES:
        target: Path = item["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        pdf = download(item["id"])
        image = render(pdf, item["page"])
        image.save(target, "WEBP", lossless=True, method=6)
        print(
            f"{item['name']}: {target.relative_to(ROOT)} -> "
            f"{image.width}x{image.height}, {target.stat().st_size} bytes"
        )


if __name__ == "__main__":
    main()
