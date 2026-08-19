from __future__ import annotations

from io import BytesIO
from pathlib import Path
import time
import urllib.request

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]

ASSETS = [
    {
        "drive_id": "1BaS4oH7XAePOnPiWz58fgVeV5i_sWc7a",
        "original": "5. Ảnh 3D.jpg",
        "output": "assets/media/home/lumi-hanoi-hero.webp",
        "phase": "Project / Signature source set",
        "kind": "Phối cảnh",
        "use": "Homepage hero",
        "max_width": 2000,
        "quality": 84,
    },
    {
        "drive_id": "1vuvV1e0k5cYAciBKyIybWV3eb5U0cdMp",
        "original": "8. Ảnh 3D.jpg",
        "output": "assets/media/home/lumi-hanoi-streetscape.webp",
        "phase": "Project / Signature source set",
        "kind": "Phối cảnh",
        "use": "Homepage secondary streetscape",
        "max_width": 1800,
        "quality": 84,
    },
    {
        "drive_id": "1gWmm74dKzFtuQpjBJK44rw9YVo05Fv9g",
        "original": "4. Ảnh 3D.jpg",
        "output": "assets/media/signature/lumi-signature-landscape.webp",
        "phase": "Signature",
        "kind": "Phối cảnh",
        "use": "Signature landscape / hero candidate",
        "max_width": 1800,
        "quality": 84,
    },
    {
        "drive_id": "14LEecNbBII5ahMGnVoq9ldGiFCMdEEk7",
        "original": "6. Ảnh 3D.jpg",
        "output": "assets/media/signature/lumi-signature-water-garden.webp",
        "phase": "Signature",
        "kind": "Phối cảnh",
        "use": "Signature landscape / water garden",
        "max_width": 1800,
        "quality": 84,
    },
    {
        "drive_id": "17_06GIk0BGmRxid4HNFQ6ykXXTkJ8oYq",
        "original": "Bể bơi resort Sole.JPG",
        "output": "assets/media/signature/lumi-signature-pool.webp",
        "phase": "Signature / Sole",
        "kind": "Phối cảnh",
        "use": "Signature pool / amenities",
        "max_width": 1600,
        "quality": 84,
    },
    {
        "drive_id": "1kb6IBIcrmwK_nXqKz8ot9VlV1D2CRdYw",
        "original": "Mặt bằng tổng.png",
        "output": "assets/media/masterplan/lumi-hanoi-masterplan.webp",
        "phase": "Project-wide",
        "kind": "Mặt bằng kỹ thuật",
        "use": "Overall masterplan",
        "lossless": True,
    },
    {
        "drive_id": "1l5ncI5S-eGYLTjsqhFmqhrusUiRNmceF",
        "original": "1-phối cảnh ban ngày.jpg",
        "output": "assets/media/prestige/lumi-prestige-hero.webp",
        "phase": "Prestige",
        "kind": "Phối cảnh",
        "use": "Prestige hero",
        "max_width": 1800,
        "quality": 84,
    },
    {
        "drive_id": "1itwQYzN7H_xyJDRIKgcvRYQNsVhUVs72",
        "original": "1 - Bể bơi cực quang.jpg",
        "output": "assets/media/prestige/lumi-prestige-aurora-pool.webp",
        "phase": "Prestige",
        "kind": "Phối cảnh",
        "use": "Prestige Aurora pool",
        "max_width": 1800,
        "quality": 84,
    },
    {
        "drive_id": "1p_4iGuw2Qo2kzVUdP_ZyiyY1Y1b0ehbt",
        "original": "6 - Vườn cực quang.jpg",
        "output": "assets/media/prestige/lumi-prestige-garden.webp",
        "phase": "Prestige",
        "kind": "Phối cảnh",
        "use": "Prestige landscape / amenities",
        "max_width": 1800,
        "quality": 84,
    },
    {
        "drive_id": "1OfZ7AxsOCezGxu7K3kHiUUjt-Au56Nm-",
        "original": "P1.T2-19, 21-22, 24-28, P2- 2-12, 14-19,21-28.jpg",
        "output": "assets/media/layouts/lumi-prestige-typical-floor.webp",
        "phase": "Prestige",
        "kind": "Mặt bằng kỹ thuật",
        "use": "Prestige typical-floor lightbox",
        "quality": 95,
    },
    {
        "drive_id": "1CnD6Bi3gXGbqw61iugntsfBonTr3RTem",
        "original": "Facade.jpg",
        "output": "assets/media/elite/lumi-elite-facade.webp",
        "phase": "Elite",
        "kind": "Phối cảnh",
        "use": "Elite hero / facade",
        "max_width": 1800,
        "quality": 84,
    },
    {
        "drive_id": "1sflufmGS6ZBs1zQ94kwlvWuxzqB90B-n",
        "original": "Bể bơi cực quang 50m.JPG",
        "output": "assets/media/elite/lumi-elite-aurora-pool.webp",
        "phase": "Elite",
        "kind": "Phối cảnh",
        "use": "Elite Aurora 50m pool",
        "max_width": 1800,
        "quality": 84,
    },
    {
        "drive_id": "1KN4V7DZ6IlO4ZGn-JP4qXuJpmWwpTj8K",
        "original": "Đại sảnh E1.JPG",
        "output": "assets/media/elite/lumi-elite-lobby-e1.webp",
        "phase": "Elite",
        "kind": "Phối cảnh",
        "use": "Elite 1 lobby",
        "max_width": 1600,
        "quality": 84,
    },
    {
        "drive_id": "1fnqn_VoG-7csnJFKtFJzNmBCILJ3ielO",
        "original": "MB LUMI GĐ3-01.jpg",
        "output": "assets/media/layouts/lumi-elite-masterplan.webp",
        "phase": "Elite",
        "kind": "Mặt bằng kỹ thuật",
        "use": "Elite technical plan lightbox",
        "quality": 95,
    },
]


def drive_url(file_id: str) -> str:
    return f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"


def download(file_id: str, attempts: int = 4) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(
                drive_url(file_id),
                headers={"User-Agent": "Mozilla/5.0 LumiHanoiMediaImporter/1.0"},
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read()
                content_type = response.headers.get("Content-Type", "")
            if len(data) < 20_000 or "text/html" in content_type.lower():
                raise RuntimeError(
                    f"Unexpected Drive response for {file_id}: {content_type}, {len(data)} bytes"
                )
            return data
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < attempts:
                time.sleep(attempt * 2)
    raise RuntimeError(f"Unable to download Drive file {file_id}: {last_error}")


def prepare_image(data: bytes, asset: dict) -> tuple[Image.Image, tuple[int, int]]:
    image = Image.open(BytesIO(data))
    image = ImageOps.exif_transpose(image).convert("RGB")
    original_size = image.size
    max_width = asset.get("max_width")
    if max_width and image.width > max_width:
        height = round(image.height * max_width / image.width)
        image = image.resize((max_width, height), Image.Resampling.LANCZOS)
    return image, original_size


def save_asset(asset: dict) -> dict:
    data = download(asset["drive_id"])
    image, original_size = prepare_image(data, asset)
    output = ROOT / asset["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    if asset.get("lossless"):
        image.save(output, "WEBP", lossless=True, method=6)
    else:
        image.save(output, "WEBP", quality=asset.get("quality", 84), method=6)
    return {
        **asset,
        "source_bytes": len(data),
        "output_bytes": output.stat().st_size,
        "source_dimensions": f"{original_size[0]}×{original_size[1]}",
        "output_dimensions": f"{image.width}×{image.height}",
    }


def create_og() -> dict:
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
    image.save(output, "WEBP", quality=84, method=6)
    return {"output": str(output.relative_to(ROOT)), "output_bytes": output.stat().st_size}


def format_kb(value: int) -> str:
    return f"{value / 1024:.0f} KB"


def write_manifest(results: list[dict], og: dict) -> None:
    lines = [
        "# Lumi Hanoi — verified media batch V4",
        "",
        "Batch ảnh dự án đã được chọn trước và nhập từ các file Google Drive đã xác minh. File phối cảnh phải được hiển thị công khai với nhãn **Phối cảnh**; không được diễn giải là ảnh hiện trạng hoặc bằng chứng vận hành.",
        "",
        "| Local path | Original Drive filename | Drive file ID | Phase | Type | Intended use | Source → output |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in results:
        lines.append(
            f"| `{item['output']}` | {item['original']} | `{item['drive_id']}` | {item['phase']} | {item['kind']} | {item['use']} | {item['source_dimensions']} / {format_kb(item['source_bytes'])} → {item['output_dimensions']} / {format_kb(item['output_bytes'])} |"
        )
    lines += [
        "",
        f"OG source crop generated at `{og['output']}` ({format_kb(og['output_bytes'])}).",
        "",
        "## Integration rules",
        "",
        "- Không dùng Drive URL làm `img src`; toàn bộ ảnh phải dùng file local trong repo.",
        "- Hero là LCP: không lazy-load, dùng `fetchpriority=\"high\"` và khai báo kích thước/aspect ratio ổn định.",
        "- Ảnh dưới fold dùng `loading=\"lazy\"` và `decoding=\"async\"`.",
        "- Mặt bằng kỹ thuật phải mở được bằng lightbox và đủ nét để đọc.",
        "- Giữ nguyên canonical, title/meta, schema, sitemap, robots và URL hiện tại.",
        "- Không suy ra ngày bàn giao hoặc trạng thái vận hành từ phối cảnh.",
    ]
    manifest = ROOT / "docs/media-batch-v4.md"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    results = []
    for index, asset in enumerate(ASSETS, start=1):
        print(f"[{index}/{len(ASSETS)}] {asset['original']}")
        result = save_asset(asset)
        results.append(result)
        print(
            f"  {result['source_dimensions']} {format_kb(result['source_bytes'])} -> "
            f"{result['output_dimensions']} {format_kb(result['output_bytes'])}"
        )
    og = create_og()
    write_manifest(results, og)
    print(f"Generated {len(results)} verified media files + OG crop.")


if __name__ == "__main__":
    main()
