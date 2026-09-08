"""Build display-size photos with Pillow; retain original assets and zoom links.

Run explicitly when these editorial photos change. The website serves the
committed files directly and does not require Pillow or an image service.
"""
from pathlib import Path
from html.parser import HTMLParser
from io import BytesIO
import re
import json

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = [
    "home/lumi-hanoi-overview.webp",
    "home/lumi-hanoi-streetscape.webp",
    "signature/lumi-signature-landscape.webp",
    "prestige/lumi-prestige-hero.webp",
    "elite/lumi-elite-facade.webp",
    "signature/lumi-signature-water-garden.webp",
    "signature/lumi-signature-pool.webp",
    "prestige/lumi-prestige-garden.webp",
    "prestige/lumi-prestige-aurora-pool.webp",
    "elite/lumi-elite-aurora-pool.webp",
    "progress/lumi-hanoi-tien-do-thang-07-2026-tong-the.webp",
]


def build_photos():
    from PIL import Image, ImageOps
    output = ROOT / "assets/media/responsive"
    output.mkdir(exist_ok=True)
    manifests = {}
    before = after = 0
    for name in PHOTOS:
        source = ROOT / "assets/media" / name
        image = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
        widths = sorted({min(640, image.width), min(960, image.width), image.width})
        variants = {"webp": [], "avif": []}
        for width in widths:
            resized = image.resize((width, round(image.height * width / image.width)), Image.Resampling.LANCZOS)
            for fmt in variants:
                file = output / f"{source.stem}-{width}.{fmt}"
                options = dict(quality=80, method=6) if fmt == "webp" else dict(quality=55, speed=6)
                encoded = BytesIO()
                resized.save(encoded, format=fmt.upper(), **options)
                payload = encoded.getvalue()
                if not payload:
                    raise RuntimeError(f"Image encoder returned no bytes: {file}")
                if fmt == "webp" and width == image.width and len(payload) >= source.stat().st_size:
                    payload = source.read_bytes()
                temporary = file.with_suffix(file.suffix + ".tmp")
                temporary.write_bytes(payload)
                temporary.replace(file)
                variants[fmt].append(("/" + str(file.relative_to(ROOT)), width))
        manifests["/assets/media/" + name] = {"sources": variants, "width": image.width, "height": image.height}
        before += source.stat().st_size
        after += (ROOT / variants["avif"][-1][0].lstrip("/")).stat().st_size
    print(f"Full-width photos: {before:,} bytes original → {after:,} bytes AVIF ({1-after/before:.0%} smaller)")
    (ROOT / "assets/data/responsive-photos.json").write_text(json.dumps(manifests, ensure_ascii=False, indent=2) + "\n")
    return manifests


class PhotoMarkup(HTMLParser):
    def __init__(self, manifests):
        super().__init__(convert_charrefs=False)
        self.manifests = manifests
        self.replacements = {}

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag != "img" or data.get("src") not in self.manifests or "srcset" in data:
            return
        original = self.get_starttag_text()
        photo = self.manifests[data["src"]]
        variants = photo["sources"]
        sizes = "100vw" if any(c in data.get("class", "") for c in ("home-hero-media", "article-hero-media", "overview-hero-media")) else "(max-width: 900px) calc(100vw - 32px), 985px"
        srcsets = {fmt: ", ".join(f"{url} {width}w" for url, width in values) for fmt, values in variants.items()}
        # The fallback is an optimized WebP; links to the original stay intact.
        fallback = variants["webp"][-1][0]
        image = original.replace(data["src"], fallback, 1)
        image = re.sub(r'\s(?:width|height)="[^"]*"', '', image)
        image = re.sub(r"\s*/?>$", f' width="{photo["width"]}" height="{photo["height"]}" srcset="{srcsets["webp"]}" sizes="{sizes}">', image)
        self.replacements[original] = (
            '<picture class="responsive-photo">'
            f'<source type="image/avif" srcset="{srcsets["avif"]}" sizes="{sizes}">'
            + image + '</picture>'
        )


def apply_markup(root=ROOT):
    """Keep scheduled SEO renders on the same media and asset versions; no Pillow."""
    manifests = json.loads((ROOT / "assets/data/responsive-photos.json").read_text())
    changed = count = 0
    for path in root.rglob("*.html"):
        if ".git" in path.parts or "node_modules" in path.parts:
            continue
        original = path.read_text()
        parser = PhotoMarkup(manifests)
        parser.feed(original)
        updated = original
        for old, new in parser.replacements.items():
            count += updated.count(old)
            updated = updated.replace(old, new)
        updated = re.sub(r'<picture class="responsive-photo">.*?</picture>',
                         lambda m: re.sub(r'sizes="[^"]*"', 'sizes="100vw"', m[0])
                         if re.search(r'class="[^"]*(?:home|article|overview)-hero-media', m[0]) else m[0], updated, flags=re.S)
        for asset in ["assets/css/site.css", "assets/js/site.js", "assets/css/marketplace-inventory.css", "assets/js/marketplace-inventory.js"]:
            version = {"assets/css/site.css": "20260907-layoutfix1", "assets/js/marketplace-inventory.js": "20260908-detail-links1"}.get(asset, "20260907-performance1")
            updated = re.sub(re.escape('/' + asset) + r'(?:\?v=[\w.-]+)?(?=["\x27])', '/' + asset + '?v=' + version, updated)
        if 'data-inventory' in updated and 'document.documentElement.classList.add("js")' not in updated:
            updated = updated.replace('<head>', '<head>\n  <script>document.documentElement.classList.add("js");</script>', 1)
        if updated != original:
            path.write_text(updated)
            changed += 1
    print(f"Updated {count} image placements across {changed} pages; original photo and floor-plan assets retained.")


def main():
    build_photos()
    apply_markup()


if __name__ == "__main__":
    main()
