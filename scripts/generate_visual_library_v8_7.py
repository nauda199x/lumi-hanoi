#!/usr/bin/env python3
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'assets/data/visual-library-v8.7.json'
MAX_WIDTH = 1800
QUALITY = 82


def fetch_image(drive_id: str) -> Image.Image:
    url = f'https://drive.google.com/thumbnail?id={drive_id}&sz=w2400'
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    content_type = response.headers.get('content-type', '')
    if not content_type.startswith('image/'):
        raise RuntimeError(f'{drive_id}: expected image response, got {content_type}')
    image = Image.open(BytesIO(response.content))
    image = ImageOps.exif_transpose(image).convert('RGB')
    return image


def optimize(image: Image.Image) -> Image.Image:
    if image.width > MAX_WIDTH:
        height = round(image.height * MAX_WIDTH / image.width)
        image = image.resize((MAX_WIDTH, height), Image.Resampling.LANCZOS)
    return image


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    for asset in data['assets']:
        target = ROOT / asset['localFile']
        target.parent.mkdir(parents=True, exist_ok=True)
        image = optimize(fetch_image(asset['driveId']))
        image.save(target, 'WEBP', quality=QUALITY, method=6)
        print(f"{asset['key']}: {image.width}x{image.height} -> {target.relative_to(ROOT)} ({target.stat().st_size // 1024} KB)")


if __name__ == '__main__':
    main()
