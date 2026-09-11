from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-09-11"


def load(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def save(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    if old not in text:
        if new in text:
            return text
        raise SystemExit(f"Missing expected marker for {label}")
    return text.replace(old, new, 1)


registry_paths = [
    ROOT / "assets/data/drive-unit-layout-import.json",
    ROOT / "assets/data/drive-unit-layout-import-extra.json",
]
registry_items: list[dict] = []
for registry_path in registry_paths:
    registry_items.extend(json.loads(registry_path.read_text(encoding="utf-8"))["items"])

signature_items = [item for item in registry_items if item["phase"] == "signature"]
if len(signature_items) != 51:
    raise SystemExit(f"Expected 51 Signature records, got {len(signature_items)}")

by_drive_id = {item["driveId"]: item for item in signature_items}
if len(by_drive_id) != 51:
    raise SystemExit("Duplicate Signature Drive IDs")

missing_assets = []
for item in signature_items:
    asset = ROOT / item["localAsset"]
    if not asset.is_file() or asset.stat().st_size < 10_000:
        missing_assets.append(item["localAsset"])
if missing_assets:
    raise SystemExit("Missing Signature local assets:\n- " + "\n- ".join(missing_assets))

# Signature library: keep the 51-item source catalog but render every card from
# committed local WebP files. Private source files must never be skipped.
library_path = "layout-can-ho-lumi-signature/index.html"
library = load(library_path)
match = re.search(r"const signatureLayouts=(\[.*?\]);const esc=", library, flags=re.S)
if not match:
    raise SystemExit("Could not find Signature layout catalog in library page")
layouts = json.loads(match.group(1))
if len(layouts) != 51:
    raise SystemExit(f"Signature library declares {len(layouts)} layouts, expected 51")

for layout in layouts:
    item = by_drive_id.get(layout.get("id"))
    if not item:
        raise SystemExit(f"No registry mapping for library item {layout.get('name')}")
    asset_path = ROOT / item["localAsset"]
    with Image.open(asset_path) as image:
        width, height = image.size
    layout["asset"] = "/" + item["localAsset"]
    layout["width"] = width
    layout["height"] = height

catalog = json.dumps(layouts, ensure_ascii=False, separators=(",", ":"))
library = library[: match.start(1)] + catalog + library[match.end(1) :]
library = replace_once(
    library,
    "const src='https://drive.google.com/thumbnail?id='+encodeURIComponent(x.id)+'&sz=w2400';",
    "const src=x.asset;",
    label="local Signature image source",
)
old_img = """<img src="'+src+'" loading="lazy" decoding="async" alt="'+esc(alt)+'">"""
new_img = """<img src="'+src+'" loading="'+(i===0?'eager':'lazy')+'" decoding="async" width="'+x.width+'" height="'+x.height+'" alt="'+esc(alt)+'">"""
library = replace_once(library, old_img, new_img, label="Signature image intrinsic dimensions")

for value, anchor in (("1", "one-bedroom"), ("2", "two-bedroom"), ("3", "three-bedroom"), ("4", "duplex")):
    token = f'data-layout-filter="bedrooms" data-value="{value}"'
    anchored = f'id="{anchor}" data-layout-filter="bedrooms" data-value="{value}"'
    if anchored not in library:
        library = replace_once(library, token, anchored, label=f"{anchor} anchor")

if '<meta name="robots" content="index,follow,max-image-preview:large">' not in library:
    library = replace_once(
        library,
        '<meta name="description" content="Thư viện 51 layout căn hộ Lumi Signature: 1PN, 2PN, 3PN của S1, S2, S3, S5, S6 và 6 layout Duplex; lọc theo số phòng ngủ, xem phóng to.">',
        '<meta name="description" content="Thư viện 51 layout căn hộ Lumi Signature: 1PN, 2PN, 3PN của S1, S2, S3, S5, S6 và 6 layout Duplex; lọc theo số phòng ngủ, xem phóng to.">\n<meta name="robots" content="index,follow,max-image-preview:large">',
        label="Signature library robots",
    )
library = library.replace('"dateModified":"2026-08-28"', f'"dateModified":"{TODAY}"', 1)

old_side = '<aside class="side-nav"><strong>Tra cứu Signature</strong>'
new_side = '<aside class="side-nav"><strong>Tra cứu Signature</strong><a href="/lumi-signature/">Tổng quan Signature</a><a href="/can-ho-1-phong-ngu-lumi-hanoi/">Layout 1 phòng ngủ</a><a href="/can-ho-2-phong-ngu-lumi-hanoi/">Layout 2 phòng ngủ</a><a href="/can-ho-3-phong-ngu-lumi-hanoi/">Layout 3 phòng ngủ</a><a href="/duplex-penthouse-lumi-hanoi/">Duplex &amp; Penthouse</a>'
if new_side not in library:
    library = replace_once(library, old_side, new_side, label="Signature library internal links")
save(library_path, library)

# 3BR guide: the S6 G variants are committed local assets, not Drive-only data.
three_path = "can-ho-3-phong-ngu-lumi-hanoi/index.html"
three = load(three_path)
three = three.replace(
    "ngoài ra nguồn Drive còn có các biến thể planter-box C7G, C7AG và C8G đang được lưu riêng trong thư viện nguồn.",
    "ba biến thể planter-box C7G, C7AG và C8G cũng đã được nhập vào thư viện local và hiển thị trực tiếp bên dưới.",
    1,
)
if "signature-s6-3br-c8g.webp" not in three:
    marker = '          <figure class="figure"><a href="/assets/media/signature/unit-layouts/signature-s6-3br-c10c.webp"'
    if marker not in three:
        raise SystemExit("Could not find insertion marker for S6 G layouts")
    g_figures = '''          <figure class="figure"><a href="/assets/media/signature/unit-layouts/signature-s6-3br-c7g.webp" data-lightbox data-lightbox-alt="Layout 3BR C7G Lumi Signature S6" data-lightbox-caption="Lumi Signature · S6 · 3BR C7G"><img class="figure-image" src="/assets/media/signature/unit-layouts/signature-s6-3br-c7g.webp" loading="lazy" decoding="async" alt="Mặt bằng căn hộ 3 phòng ngủ C7G tòa S6 Lumi Signature" width="1800" height="2400"></a><figcaption class="figure-caption">Signature S6 — C7G</figcaption></figure>
          <figure class="figure"><a href="/assets/media/signature/unit-layouts/signature-s6-3br-c7ag.webp" data-lightbox data-lightbox-alt="Layout 3BR C7AG Lumi Signature S6" data-lightbox-caption="Lumi Signature · S6 · 3BR C7AG"><img class="figure-image" src="/assets/media/signature/unit-layouts/signature-s6-3br-c7ag.webp" loading="lazy" decoding="async" alt="Mặt bằng căn hộ 3 phòng ngủ C7AG tòa S6 Lumi Signature" width="1800" height="2400"></a><figcaption class="figure-caption">Signature S6 — C7AG</figcaption></figure>
          <figure class="figure"><a href="/assets/media/signature/unit-layouts/signature-s6-3br-c8g.webp" data-lightbox data-lightbox-alt="Layout 3BR C8G Lumi Signature S6" data-lightbox-caption="Lumi Signature · S6 · 3BR C8G"><img class="figure-image" src="/assets/media/signature/unit-layouts/signature-s6-3br-c8g.webp" loading="lazy" decoding="async" alt="Mặt bằng căn hộ 3 phòng ngủ C8G tòa S6 Lumi Signature" width="1800" height="2400"></a><figcaption class="figure-caption">Signature S6 — C8G</figcaption></figure>
'''
    three = three.replace(marker, g_figures + marker, 1)
save(three_path, three)

# Duplex/Penthouse guide: expose all six verified Signature source layouts and
# keep them clearly separated from the existing Elite Duplex data.
duplex_path = "duplex-penthouse-lumi-hanoi/index.html"
duplex = load(duplex_path)
duplex = duplex.replace(
    'content="Tra cứu Duplex và Penthouse Lumi Hanoi theo Signature, Prestige, Elite: ảnh layout Elite Duplex, mặt bằng tầng đỉnh, diện tích NFA/GFA và cách đối chiếu đúng căn."',
    'content="Tra cứu Duplex và Penthouse Lumi Hanoi theo Signature, Prestige, Elite: 6 layout Duplex Signature, bộ Duplex Elite, mặt bằng tầng đỉnh và cách đối chiếu đúng căn."',
    1,
)
duplex = duplex.replace(
    'content="Xem layout Duplex Elite và mặt bằng Penthouse Signature/Prestige theo đúng phân khu, tòa và tầng."',
    'content="Xem 6 layout Duplex Signature, bộ Duplex Elite và mặt bằng Penthouse theo đúng phân khu, tòa và tầng."',
    1,
)
duplex = duplex.replace(
    'https://lumi-hanoi.com/assets/media/elite/unit-layouts/elite-layout-source-01.webp',
    'https://lumi-hanoi.com/assets/media/signature/unit-layouts/signature-duplex-dl-01.webp',
)
duplex = duplex.replace(
    '<p class="notice"><strong>Đã bổ sung dữ liệu gốc:</strong> trang này hiện dùng trực tiếp ba layout Duplex Elite đã đưa vào repo, bên cạnh hệ mặt bằng Penthouse Signature và Prestige. Không cộng diện tích giữa hai mã hoặc hai biến thể khác nhau.</p>',
    '<p class="notice"><strong>Đã bổ sung dữ liệu gốc:</strong> trang này dùng trực tiếp 6 layout Duplex Signature DL-01 → DL-06 và ba layout Duplex Elite đã đưa vào repo, bên cạnh hệ mặt bằng Penthouse theo từng phân khu. Không dùng layout của phân khu này để đại diện cho phân khu khác.</p>',
    1,
)
if "signature-duplex-dl-06.webp" not in duplex:
    marker = '        <h2 id="elite-duplex">Duplex Lumi Elite — ba layout nguồn đã xác minh</h2>'
    if marker not in duplex:
        raise SystemExit("Could not find Signature Duplex insertion marker")
    figures = []
    for number in range(1, 7):
        code = f"DL-{number:02d}"
        asset = f"/assets/media/signature/unit-layouts/signature-duplex-dl-{number:02d}.webp"
        loading = "eager" if number == 1 else "lazy"
        figures.append(
            f'          <figure class="figure"><a href="{asset}" data-lightbox data-lightbox-alt="Layout Duplex {code} Lumi Signature" data-lightbox-caption="Lumi Signature · Duplex {code} · nguồn S1/S2/S3/S5"><img class="figure-image" src="{asset}" loading="{loading}" decoding="async" alt="Mặt bằng Duplex {code} Lumi Signature, bộ nguồn S1 S2 S3 S5" width="1800" height="2400"></a><figcaption class="figure-caption">Signature — Duplex {code}</figcaption></figure>'
        )
    signature_section = '''        <h2 id="signature-duplex">Duplex Lumi Signature — đủ 6 layout DL-01 → DL-06</h2>
        <p>Bộ nguồn Signature hiện có đủ sáu bản <strong>DL-01, DL-02, DL-03, DL-04, DL-05 và DL-06</strong>, được registry gắn với nhóm S1/S2/S3/S5. Website hiển thị trực tiếp bản WebP đã lưu local; với từng giao dịch vẫn cần quay lại mặt bằng đúng tòa, tầng và mã căn trước khi kết luận phạm vi áp dụng.</p>
        <div class="media-gallery">
''' + "\n".join(figures) + '''
        </div>
        <p><a class="btn" href="/layout-can-ho-lumi-signature/#duplex">Mở thư viện 51 layout Signature</a> <a class="btn" href="/mat-bang-lumi-hanoi/lumi-signature/">Đối chiếu mặt bằng Signature</a></p>

'''
    duplex = duplex.replace(marker, signature_section + marker, 1)
if '"Duplex Lumi Signature"' not in duplex:
    duplex = duplex.replace('"about":["Duplex Lumi Hanoi",', '"about":["Duplex Lumi Hanoi","Duplex Lumi Signature",', 1)
save(duplex_path, duplex)

# Fix empty hero alt text on the three phase guides and refresh Signature schema.
phase_alt = {
    "lumi-signature/index.html": ("lumi-signature-landscape-1600.webp", "Phối cảnh tổng thể Lumi Signature tại Lumi Hanoi"),
    "lumi-prestige/index.html": ("lumi-prestige-hero-1600.webp", "Phối cảnh Lumi Prestige tại Lumi Hanoi"),
    "lumi-elite/index.html": ("lumi-elite-facade-1600.webp", "Phối cảnh mặt đứng Lumi Elite tại Lumi Hanoi"),
}
for page_path, (filename, alt) in phase_alt.items():
    page = load(page_path)
    pattern = rf'(<img class="article-hero-media" src="[^"]*{re.escape(filename)}" )alt=""'
    page, count = re.subn(pattern, rf'\1alt="{alt}"', page, count=1)
    if count == 0 and f'alt="{alt}"' not in page:
        raise SystemExit(f"Could not set hero alt on {page_path}")
    if page_path == "lumi-signature/index.html":
        page = page.replace('"dateModified":"2026-08-23"', f'"dateModified":"{TODAY}"', 1)
    save(page_path, page)

# Validate phase order, SEO markers and local asset coverage.
for page_path in (
    "can-ho-1-phong-ngu-lumi-hanoi/index.html",
    "can-ho-2-phong-ngu-lumi-hanoi/index.html",
    "can-ho-3-phong-ngu-lumi-hanoi/index.html",
):
    page = load(page_path)
    for needle in ("<title>", "<h1>", 'rel="canonical"', 'application/ld+json', 'id="signature"', 'id="prestige"', 'id="elite"'):
        if needle not in page:
            raise SystemExit(f"{page_path} missing {needle}")
    if not (page.index('id="signature"') < page.index('id="prestige"') < page.index('id="elite"')):
        raise SystemExit(f"Wrong phase order in {page_path}")

library = load(library_path)
for anchor in ("one-bedroom", "two-bedroom", "three-bedroom", "duplex"):
    if f'id="{anchor}"' not in library:
        raise SystemExit(f"Signature library missing #{anchor}")
if "drive.google.com/thumbnail" in library:
    raise SystemExit("Signature library still depends on Drive thumbnails")
for item in signature_items:
    if "/" + item["localAsset"] not in library:
        raise SystemExit(f"Signature library missing local asset reference {item['localAsset']}")

three = load(three_path)
for asset in ("signature-s6-3br-c7g.webp", "signature-s6-3br-c7ag.webp", "signature-s6-3br-c8g.webp"):
    if asset not in three:
        raise SystemExit(f"3BR guide missing {asset}")

duplex = load(duplex_path)
for number in range(1, 7):
    asset = f"signature-duplex-dl-{number:02d}.webp"
    if asset not in duplex:
        raise SystemExit(f"Duplex guide missing {asset}")

print("Signature layout finalization OK: 51/51 local assets, 3 S6 G layouts, 6 Signature Duplex layouts, phase order and SEO markers validated.")
