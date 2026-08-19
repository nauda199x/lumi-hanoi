from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
import time
import urllib.request

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]

ASSETS = [
    ("1BaS4oH7XAePOnPiWz58fgVeV5i_sWc7a", "assets/media/home/lumi-hanoi-hero.webp", 1800, 82),
    ("1vuvV1e0k5cYAciBKyIybWV3eb5U0cdMp", "assets/media/home/lumi-hanoi-streetscape.webp", 1600, 82),
    ("1gWmm74dKzFtuQpjBJK44rw9YVo05Fv9g", "assets/media/signature/lumi-signature-landscape.webp", 1600, 82),
    ("14LEecNbBII5ahMGnVoq9ldGiFCMdEEk7", "assets/media/signature/lumi-signature-water-garden.webp", 1600, 82),
    ("17_06GIk0BGmRxid4HNFQ6ykXXTkJ8oYq", "assets/media/signature/lumi-signature-pool.webp", 1500, 82),
    ("1kb6IBIcrmwK_nXqKz8ot9VlV1D2CRdYw", "assets/media/masterplan/lumi-hanoi-masterplan.webp", 1986, 90),
    ("19x4OCPC4ek7Lb_zCZIRcQf9Du6Ohlv5d", "assets/media/prestige/lumi-prestige-hero.webp", 1600, 82),
    ("1CmbdhyMtdSqBGZXb0c7xs-wnsScG3YAM", "assets/media/prestige/lumi-prestige-aurora-pool.webp", 1600, 82),
    ("1gJENvv6CSpvJE4rn_eZi4W1XEwSLYHhM", "assets/media/prestige/lumi-prestige-garden.webp", 1600, 82),
    ("1OfZ7AxsOCezGxu7K3kHiUUjt-Au56Nm-", "assets/media/layouts/lumi-prestige-typical-floor.webp", 2200, 92),
    ("1CnD6Bi3gXGbqw61iugntsfBonTr3RTem", "assets/media/elite/lumi-elite-facade.webp", 1800, 82),
    ("1sflufmGS6ZBs1zQ94kwlvWuxzqB90B-n", "assets/media/elite/lumi-elite-aurora-pool.webp", 1600, 82),
    ("1KN4V7DZ6IlO4ZGn-JP4qXuJpmWwpTj8K", "assets/media/elite/lumi-elite-lobby-e1.webp", 1600, 82),
    ("1fnqn_VoG-7csnJFKtFJzNmBCILJ3ielO", "assets/media/layouts/lumi-elite-masterplan.webp", 2200, 92),
]


def drive_url(file_id: str) -> str:
    return f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"


def download(file_id: str, attempts: int = 4) -> bytes:
    error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(
                drive_url(file_id),
                headers={"User-Agent": "Mozilla/5.0 LumiHanoiNetlifyBuild/1.0"},
            )
            with urllib.request.urlopen(req, timeout=90) as response:
                data = response.read()
                content_type = (response.headers.get("Content-Type") or "").lower()
            if len(data) < 20_000 or "text/html" in content_type:
                raise RuntimeError(f"unexpected response {content_type}, {len(data)} bytes")
            return data
        except Exception as exc:  # noqa: BLE001
            error = exc
            if attempt < attempts:
                time.sleep(attempt * 2)
    raise RuntimeError(f"Drive download failed for {file_id}: {error}")


def build_one(item: tuple[str, str, int, int]) -> tuple[str, int]:
    file_id, rel_path, max_width, quality = item
    raw = download(file_id)
    image = Image.open(BytesIO(raw))
    image = ImageOps.exif_transpose(image).convert("RGB")
    if image.width > max_width:
        new_height = round(image.height * max_width / image.width)
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
    output = ROOT / rel_path
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "WEBP", quality=quality, method=6, exif=b"", icc_profile=None)
    return rel_path, output.stat().st_size


def build_og() -> None:
    source = ROOT / "assets/media/home/lumi-hanoi-hero.webp"
    image = Image.open(source).convert("RGB")
    target_ratio = 1200 / 630
    current_ratio = image.width / image.height
    if current_ratio > target_ratio:
        new_width = round(image.height * target_ratio)
        left = (image.width - new_width) // 2
        image = image.crop((left, 0, left + new_width, image.height))
    else:
        new_height = round(image.width / target_ratio)
        top = (image.height - new_height) // 2
        image = image.crop((0, top, image.width, top + new_height))
    image = image.resize((1200, 630), Image.Resampling.LANCZOS)
    output = ROOT / "assets/media/og/lumi-hanoi-og.webp"
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "WEBP", quality=82, method=6, exif=b"", icc_profile=None)


def main() -> None:
    print(f"Building {len(ASSETS)} verified Lumi Hanoi media assets...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(build_one, item) for item in ASSETS]
        for future in as_completed(futures):
            path, size = future.result()
            print(f"  built {path} ({size / 1024:.0f} KB)")
    build_og()
    print("Verified media build complete.")


if __name__ == "__main__":
    main()
