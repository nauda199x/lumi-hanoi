from __future__ import annotations

import io
import time
import urllib.request
from pathlib import Path
from typing import Final

from PIL import Image, ImageOps

ROOT: Final = Path(__file__).resolve().parents[1]

ASSETS: Final = [
    # Homepage / project-wide renderings
    ("1BaS4oH7XAePOnPiWz58fgVeV5i_sWc7a", "assets/media/home/lumi-hanoi-hero.webp", "rendering"),
    ("1vuvV1e0k5cYAciBKyIybWV3eb5U0cdMp", "assets/media/home/lumi-hanoi-streetscape.webp", "rendering"),
    # Signature
    ("1gWmm74dKzFtuQpjBJK44rw9YVo05Fv9g", "assets/media/signature/lumi-signature-landscape.webp", "rendering"),
    ("14LEecNbBII5ahMGnVoq9ldGiFCMdEEk7", "assets/media/signature/lumi-signature-water-garden.webp", "rendering"),
    ("17_06GIk0BGmRxid4HNFQ6ykXXTkJ8oYq", "assets/media/signature/lumi-signature-pool.webp", "rendering"),
    # Prestige
    ("19x4OCPC4ek7Lb_zCZIRcQf9Du6Ohlv5d", "assets/media/prestige/lumi-prestige-hero.webp", "rendering"),
    ("1CmbdhyMtdSqBGZXb0c7xs-wnsScG3YAM", "assets/media/prestige/lumi-prestige-aurora-pool.webp", "rendering"),
    ("1gJENvv6CSpvJE4rn_eZi4W1XEwSLYHhM", "assets/media/prestige/lumi-prestige-garden.webp", "rendering"),
    ("1OfZ7AxsOCezGxu7K3kHiUUjt-Au56Nm-", "assets/media/layouts/lumi-prestige-typical-floor.webp", "technical"),
    # Elite
    ("1CnD6Bi3gXGbqw61iugntsfBonTr3RTem", "assets/media/elite/lumi-elite-facade.webp", "rendering"),
    ("1sflufmGS6ZBs1zQ94kwlvWuxzqB90B-n", "assets/media/elite/lumi-elite-aurora-pool.webp", "rendering"),
    ("1KN4V7DZ6IlO4ZGn-JP4qXuJpmWwpTj8K", "assets/media/elite/lumi-elite-lobby-e1.webp", "rendering"),
    ("1fnqn_VoG-7csnJFKtFJzNmBCILJ3ielO", "assets/media/layouts/lumi-elite-masterplan.webp", "technical"),
    # Project masterplan
    ("1kb6IBIcrmwK_nXqKz8ot9VlV1D2CRdYw", "assets/media/masterplan/lumi-hanoi-masterplan.webp", "technical"),
]


def download_drive(file_id: str, attempts: int = 4) -> bytes:
    # These are reviewer-verified project files. Download at build/import time;
    # the deployed site never hotlinks Google Drive.
    url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
    headers = {"User-Agent": "Mozilla/5.0 LumiHanoiMediaImporter/1.0"}
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as response:
                data = response.read()
            if len(data) < 10_000:
                raise RuntimeError(f"Downloaded payload unexpectedly small ({len(data)} bytes)")
            return data
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < attempts:
                time.sleep(attempt * 3)
    raise RuntimeError(f"Unable to download Drive file {file_id}: {last_error}")


def normalize_image(data: bytes, kind: str) -> Image.Image:
    image = Image.open(io.BytesIO(data))
    image.load()
    image = ImageOps.exif_transpose(image).convert("RGB")
    max_width = 2000 if kind == "technical" else 1600
    if image.width > max_width:
        new_height = round(image.height * max_width / image.width)
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
    return image


def save_webp(image: Image.Image, target: Path, kind: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    quality = 90 if kind == "technical" else 78
    image.save(target, "WEBP", quality=quality, method=6)


def create_og(hero_path: Path) -> None:
    image = Image.open(hero_path).convert("RGB")
    # 1200 x 630 Open Graph crop from the verified real project rendering.
    image = ImageOps.fit(
        image,
        (1200, 630),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    target = ROOT / "assets/media/og/lumi-hanoi-og.webp"
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, "WEBP", quality=78, method=6)


def main() -> None:
    for file_id, relative_path, kind in ASSETS:
        target = ROOT / relative_path
        print(f"Importing {relative_path} from verified Drive file {file_id}")
        data = download_drive(file_id)
        image = normalize_image(data, kind)
        save_webp(image, target, kind)
        print(f"  -> {image.width}x{image.height}, {target.stat().st_size:,} bytes")

    create_og(ROOT / "assets/media/home/lumi-hanoi-hero.webp")
    og = ROOT / "assets/media/og/lumi-hanoi-og.webp"
    print(f"Created {og.relative_to(ROOT)}: {og.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
