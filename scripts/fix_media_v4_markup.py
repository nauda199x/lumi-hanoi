from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HTML_FILES = [
    ROOT / "index.html",
    ROOT / "lumi-signature/index.html",
    ROOT / "lumi-prestige/index.html",
    ROOT / "lumi-elite/index.html",
    ROOT / "mat-bang-lumi-hanoi/index.html",
    ROOT / "tien-ich-lumi-hanoi/index.html",
]

DIMENSIONS = {
    "/assets/media/home/lumi-hanoi-hero.webp": (1600, 1200),
    "/assets/media/home/lumi-hanoi-streetscape.webp": (1600, 1200),
    "/assets/media/masterplan/lumi-hanoi-masterplan.webp": (2000, 1432),
    "/assets/media/signature/lumi-signature-landscape.webp": (1600, 1200),
    "/assets/media/signature/lumi-signature-water-garden.webp": (1600, 1200),
    "/assets/media/signature/lumi-signature-pool.webp": (1400, 915),
    "/assets/media/prestige/lumi-prestige-hero.webp": (1600, 900),
    "/assets/media/prestige/lumi-prestige-aurora-pool.webp": (1600, 900),
    "/assets/media/prestige/lumi-prestige-garden.webp": (1600, 900),
    "/assets/media/layouts/lumi-prestige-typical-floor.webp": (1080, 1528),
    "/assets/media/elite/lumi-elite-facade.webp": (1474, 982),
    "/assets/media/elite/lumi-elite-aurora-pool.webp": (1400, 933),
    "/assets/media/elite/lumi-elite-lobby-e1.webp": (1400, 1050),
    "/assets/media/layouts/lumi-elite-masterplan.webp": (2000, 1331),
}


def fix_dimensions(text: str) -> tuple[str, int]:
    changes = 0
    for src, (width, height) in DIMENSIONS.items():
        pattern = re.compile(
            rf'(<img\b[^>]*?src="{re.escape(src)}"[^>]*?)width="\d+"\s+height="\d+"',
            flags=re.DOTALL,
        )

        def repl(match: re.Match[str]) -> str:
            nonlocal changes
            changes += 1
            return f'{match.group(1)}width="{width}" height="{height}"'

        text = pattern.sub(repl, text)
    return text, changes


def main() -> None:
    total = 0
    for path in HTML_FILES:
        text = path.read_text(encoding="utf-8")
        text, changes = fix_dimensions(text)

        if path.name == "index.html" and path.parent == ROOT:
            text = text.replace(
                'alt="Phối cảnh tuyến phố thương mại tại Lumi Hanoi"',
                'alt="Phối cảnh Lumi Hanoi"',
            ).replace(
                'Phối cảnh tuyến phố thương mại tại Lumi Hanoi. Nguồn: tài liệu dự án.',
                'Phối cảnh Lumi Hanoi. Nguồn: tài liệu dự án.',
            )

        path.write_text(text, encoding="utf-8")
        total += changes
        print(f"{path.relative_to(ROOT)}: corrected {changes} image dimension declaration(s)")

    if total < 20:
        raise RuntimeError(f"Expected at least 20 dimension corrections, got {total}")

    media_map = ROOT / "docs/media-map.md"
    text = media_map.read_text(encoding="utf-8")
    replacements = {
        "`2. Ảnh 3D.jpg` · Drive ID `1BaS4oH7XAePOnPiWz58fgVeV5i_sWc7a`": "`5. Ảnh 3D.jpg` · Drive ID `1BaS4oH7XAePOnPiWz58fgVeV5i_sWc7a`",
        "`6. Ảnh 3D.jpg` · Drive ID `1vuvV1e0k5cYAciBKyIybWV3eb5U0cdMp`": "`8. Ảnh 3D.jpg` · Drive ID `1vuvV1e0k5cYAciBKyIybWV3eb5U0cdMp`",
        "`2. Ảnh 3D.jpg` · Drive ID `1gWmm74dKzFtuQpjBJK44rw9YVo05Fv9g`": "`4. Ảnh 3D.jpg` · Drive ID `1gWmm74dKzFtuQpjBJK44rw9YVo05Fv9g`",
        "`4. Ảnh 3D.jpg` · Drive ID `14LEecNbBII5ahMGnVoq9ldGiFCMdEEk7`": "`6. Ảnh 3D.jpg` · Drive ID `14LEecNbBII5ahMGnVoq9ldGiFCMdEEk7`",
        "**Media infrastructure completed; real project assets remain pending.**": "**V4 verified project media is integrated locally; future additions remain curated and source-checked.**",
    }
    for old, new in replacements.items():
        if old not in text:
            raise RuntimeError(f"Expected media-map text not found: {old}")
        text = text.replace(old, new)
    media_map.write_text(text, encoding="utf-8")
    print("docs/media-map.md: corrected V4 source filenames and integration status")


if __name__ == "__main__":
    main()
