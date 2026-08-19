#!/usr/bin/env python3
"""Extract the reviewer-provided V4 contact sheets with Pillow.

The script accepts the four source sheets in their documented order. It adapts
coordinates proportionally if the attachment transport has reduced a sheet,
and never enlarges extracted production panels. Metadata is discarded when the
new WebP files are encoded.
"""
from pathlib import Path
from PIL import Image
import argparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/media"

def panel(source: Path, box, expected, destination: str, quality: int) -> Image.Image:
    with Image.open(source) as image:
        sx, sy = image.width / expected[0], image.height / expected[1]
        scaled = tuple(round(value * (sx if index % 2 == 0 else sy)) for index, value in enumerate(box))
        result = image.crop(scaled)
        target = OUT / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        result.save(target, "WEBP", quality=quality, method=6, exif=b"", icc_profile=None)
        return result.copy()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("home_signature", type=Path)
    parser.add_argument("prestige", type=Path)
    parser.add_argument("elite", type=Path)
    parser.add_argument("technical", type=Path)
    args = parser.parse_args()
    home = [(0,0,"home/lumi-hanoi-hero.webp"),(1400,0,"home/lumi-hanoi-streetscape.webp"),(0,970,"signature/lumi-signature-landscape.webp"),(1400,970,"signature/lumi-signature-water-garden.webp"),(0,1940,"signature/lumi-signature-pool.webp")]
    hero = None
    for x,y,name in home:
        image = panel(args.home_signature,(x,y,x+1400,y+900),(2800,2910),name,80)
        if x == y == 0: hero = image
    for source, folder, names in [(args.prestige,"prestige",["lumi-prestige-hero.webp","lumi-prestige-aurora-pool.webp","lumi-prestige-garden.webp"]),(args.elite,"elite",["lumi-elite-facade.webp","lumi-elite-aurora-pool.webp","lumi-elite-lobby-e1.webp"])]:
        for (x,y), name in zip([(0,0),(1400,0),(0,970)],names): panel(source,(x,y,x+1400,y+900),(2800,1940),f"{folder}/{name}",80)
    for y,name in [(0,"masterplan/lumi-hanoi-masterplan.webp"),(1680,"layouts/lumi-prestige-typical-floor.webp"),(3360,"layouts/lumi-elite-masterplan.webp")]: panel(args.technical,(0,y,2200,y+1600),(2200,5040),name,92)
    # Social previews have a fixed protocol canvas; derive it only from the real hero.
    ratio = 1200 / 630
    crop_height = round(hero.width / ratio)
    top = max(0, (hero.height - crop_height) // 2)
    og = hero.crop((0, top, hero.width, top + crop_height)).resize((1200,630), Image.Resampling.LANCZOS)
    og.save(OUT / "og/lumi-hanoi-og.webp", "WEBP", quality=82, method=6, exif=b"", icc_profile=None)

if __name__ == "__main__": main()
