from __future__ import annotations

import re
import tempfile
from pathlib import Path

import gdown
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

ASSETS = [
    {
        "id": "1SPOvb-Hd5etWCPDO2pbFn-6yA72wqojQ",
        "dest": "assets/media/home/lumi-hanoi-tong-the.webp",
        "max_width": 1600,
        "quality": 76,
        "label": "Phối cảnh Lumi Hanoi",
    },
    {
        "id": "1scV0UszavNrIdm9gJVno8FhahhAGHYdq",
        "dest": "assets/media/signature/lumi-signature-phoi-canh.webp",
        "max_width": 1600,
        "quality": 76,
        "label": "Phối cảnh Lumi Signature",
    },
    {
        "id": "16g1VwjQMeytHqxQcgueMsSDUAS9G3yXL",
        "dest": "assets/media/prestige/lumi-prestige-phoi-canh.webp",
        "max_width": 1600,
        "quality": 76,
        "label": "Phối cảnh Lumi Prestige",
    },
    {
        "id": "1CnD6Bi3gXGbqw61iugntsfBonTr3RTem",
        "dest": "assets/media/elite/lumi-elite-phoi-canh.webp",
        "max_width": 1600,
        "quality": 76,
        "label": "Phối cảnh mặt đứng Lumi Elite",
    },
    {
        "id": "17_06GIk0BGmRxid4HNFQ6ykXXTkJ8oYq",
        "dest": "assets/media/signature/lumi-signature-be-boi-sole.webp",
        "max_width": 1400,
        "quality": 76,
        "label": "Phối cảnh bể bơi resort Sole – Lumi Signature",
    },
    {
        "id": "19x4OCPC4ek7Lb_zCZIRcQf9Du6Ohlv5d",
        "dest": "assets/media/prestige/lumi-prestige-aurora-sundeck.webp",
        "max_width": 1400,
        "quality": 76,
        "label": "Phối cảnh sân tắm nắng và bể Cực Quang – Lumi Prestige",
    },
    {
        "id": "1KN4V7DZ6IlO4ZGn-JP4qXuJpmWwpTj8K",
        "dest": "assets/media/elite/lumi-elite-dai-sanh-e1.webp",
        "max_width": 1400,
        "quality": 76,
        "label": "Phối cảnh đại sảnh Elite 1",
    },
    {
        "id": "1kb6IBIcrmwK_nXqKz8ot9VlV1D2CRdYw",
        "dest": "assets/media/masterplan/lumi-signature-facility-plan.webp",
        "max_width": 2000,
        "quality": 80,
        "label": "Mặt bằng tiện ích Lumi Signature",
    },
    {
        "id": "1FvjlIjErGhvMP7kjbfUm1EmxKT9mNBMJ",
        "dest": "assets/media/masterplan/lumi-prestige-facility-plan.webp",
        "max_width": 2000,
        "quality": 80,
        "label": "Mặt bằng tiện ích Lumi Prestige",
    },
    {
        "id": "1fnqn_VoG-7csnJFKtFJzNmBCILJ3ielO",
        "dest": "assets/media/masterplan/lumi-elite-masterplan.webp",
        "max_width": 2000,
        "quality": 80,
        "label": "Mặt bằng Lumi Elite – tài liệu giai đoạn 3",
    },
]


def download_and_optimize() -> dict[str, tuple[int, int]]:
    dimensions: dict[str, tuple[int, int]] = {}
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        for idx, item in enumerate(ASSETS):
            source = temp / f"source-{idx}"
            print(f"Downloading {item['label']} ({item['id']})")
            downloaded = gdown.download(id=item["id"], output=str(source), quiet=False)
            if not downloaded or not source.exists() or source.stat().st_size < 10_000:
                raise RuntimeError(f"Could not download Drive file {item['id']}")

            with Image.open(source) as raw:
                image = raw.convert("RGB")
                max_width = int(item["max_width"])
                if image.width > max_width:
                    height = round(image.height * max_width / image.width)
                    image = image.resize((max_width, height), Image.Resampling.LANCZOS)

                destination = ROOT / item["dest"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                image.save(destination, "WEBP", quality=int(item["quality"]), method=6)
                dimensions[item["dest"]] = image.size
                print(f"Saved {destination.relative_to(ROOT)} {image.size} {destination.stat().st_size} bytes")
    return dimensions


def img(path: str, alt: str, width: int, height: int, *, lazy: bool = True, classes: str = "") -> str:
    loading = ' loading="lazy"' if lazy else ""
    cls = f' class="{classes}"' if classes else ""
    return (
        f'<img src="/{path}" alt="{alt}" width="{width}" height="{height}"'
        f'{loading} decoding="async"{cls}>'
    )


def figure(path: str, alt: str, caption: str, width: int, height: int, *, lightbox: bool = False) -> str:
    image = img(path, alt, width, height, lazy=True, classes="figure-image")
    if lightbox:
        visual = (
            f'<a href="/{path}" data-lightbox data-lightbox-alt="{alt}" '
            f'data-lightbox-caption="{caption}">{image}</a>'
        )
    else:
        visual = image
    return (
        '<figure class="figure real-media-figure">'
        f'{visual}'
        f'<figcaption class="figure-caption">{caption}'
        '<span class="figure-source">Nguồn: tài liệu dự án Lumi Hanoi. Hình ảnh phối cảnh/thiết kế, không phải ảnh vận hành thực tế.</span>'
        '</figcaption></figure>'
    )


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    (ROOT / path).write_text(content, encoding="utf-8")


def add_og(html: str, image_path: str) -> str:
    if 'property="og:image"' in html:
        return html
    marker = '<meta name="twitter:card" content="summary">'
    addition = (
        f'<meta property="og:image" content="https://lumi-hanoi.com/{image_path}">\n'
        '<meta property="og:image:width" content="1600">\n'
        '<meta property="og:image:height" content="900">\n'
        '<meta name="twitter:card" content="summary_large_image">'
    )
    if marker not in html:
        raise RuntimeError("twitter card marker missing")
    return html.replace(marker, addition, 1)


def hero_gallery(html: str, gallery_html: str) -> str:
    marker = '</header>\n          <div class="container article-layout">'
    if marker not in html:
        raise RuntimeError("article hero insertion marker missing")
    return html.replace(
        marker,
        '</header>\n          <div class="container article-media-shell">' + gallery_html + '</div>\n          <div class="container article-layout">',
        1,
    )


def integrate_home(dim: dict[str, tuple[int, int]]) -> None:
    path = "index.html"
    html = read(path)
    html = add_og(html, "assets/media/home/lumi-hanoi-tong-the.webp")

    cards = [
        ("01", "assets/media/signature/lumi-signature-phoi-canh.webp", "Phối cảnh Lumi Signature"),
        ("02", "assets/media/prestige/lumi-prestige-phoi-canh.webp", "Phối cảnh Lumi Prestige"),
        ("03", "assets/media/elite/lumi-elite-phoi-canh.webp", "Phối cảnh Lumi Elite"),
    ]
    for index, media_path, alt in cards:
        w, h = dim[media_path]
        marker = f'<span class="phase-index">{index}</span>'
        visual = (
            '<figure class="phase-card-media">'
            + img(media_path, alt, w, h, lazy=True)
            + '<figcaption>Phối cảnh</figcaption></figure>'
        )
        if marker not in html:
            raise RuntimeError(f"phase card {index} missing")
        html = html.replace(marker, visual + marker, 1)

    amenity_items = [
        ("assets/media/signature/lumi-signature-be-boi-sole.webp", "Phối cảnh bể bơi resort Sole – Lumi Signature", "Signature · Bể bơi Sole"),
        ("assets/media/prestige/lumi-prestige-aurora-sundeck.webp", "Phối cảnh sân tắm nắng và bể Cực Quang – Lumi Prestige", "Prestige · Aurora Sundeck"),
        ("assets/media/elite/lumi-elite-dai-sanh-e1.webp", "Phối cảnh đại sảnh Elite 1", "Elite · Đại sảnh E1"),
    ]
    cards_html = []
    for media_path, alt, label in amenity_items:
        w, h = dim[media_path]
        cards_html.append(
            '<figure class="amenity-media-card">'
            + img(media_path, alt, w, h, lazy=True)
            + f'<figcaption><strong>{label}</strong><span>Phối cảnh từ tài liệu dự án</span></figcaption></figure>'
        )
    amenity_gallery = '<div class="container amenity-media-grid">' + ''.join(cards_html) + '</div>'
    pattern = r'(<section class="section amenities-intro">.*?)(</section>)'
    if not re.search(pattern, html, flags=re.S):
        raise RuntimeError("amenities intro section missing")
    html = re.sub(pattern, lambda m: m.group(1) + amenity_gallery + m.group(2), html, count=1, flags=re.S)
    write(path, html)


def integrate_phase(path: str, og_path: str, items: list[tuple[str, str, str]], dim: dict[str, tuple[int, int]]) -> None:
    html = read(path)
    html = add_og(html, og_path)
    figures = []
    for media_path, alt, caption in items:
        w, h = dim[media_path]
        figures.append(figure(media_path, alt, caption, w, h, lightbox=False))
    gallery = '<div class="phase-media-gallery">' + ''.join(figures) + '</div>'
    html = hero_gallery(html, gallery)
    write(path, html)


def integrate_plans(dim: dict[str, tuple[int, int]]) -> None:
    path = "mat-bang-lumi-hanoi/index.html"
    html = read(path)
    items = [
        ("assets/media/masterplan/lumi-signature-facility-plan.webp", "Mặt bằng tiện ích Lumi Signature", "Mặt bằng tiện ích Lumi Signature"),
        ("assets/media/masterplan/lumi-prestige-facility-plan.webp", "Mặt bằng tiện ích Lumi Prestige", "Mặt bằng tiện ích Lumi Prestige"),
        ("assets/media/masterplan/lumi-elite-masterplan.webp", "Mặt bằng Lumi Elite giai đoạn 3", "Mặt bằng Lumi Elite – tài liệu giai đoạn 3"),
    ]
    figures = []
    for media_path, alt, caption in items:
        w, h = dim[media_path]
        figures.append(figure(media_path, alt, caption, w, h, lightbox=True))
    gallery = (
        '<section class="technical-media-section">'
        '<div class="media-section-head"><p class="eyebrow">Tài liệu mặt bằng</p><h2>Ba bộ mặt bằng theo phân khu</h2>'
        '<p>Các bản dưới đây thuộc từng phân khu, không phải một bản masterplan duy nhất cho toàn bộ 9 tòa. Nhấn vào ảnh để xem lớn.</p></div>'
        '<div class="technical-plan-gallery">' + ''.join(figures) + '</div></section>'
    )
    html = hero_gallery(html, gallery)
    write(path, html)


def integrate_amenities(dim: dict[str, tuple[int, int]]) -> None:
    path = "tien-ich-lumi-hanoi/index.html"
    html = read(path)
    items = [
        ("assets/media/signature/lumi-signature-be-boi-sole.webp", "Phối cảnh bể bơi resort Sole tại Lumi Signature", "Phối cảnh bể bơi resort Sole – Lumi Signature"),
        ("assets/media/prestige/lumi-prestige-aurora-sundeck.webp", "Phối cảnh sân tắm nắng Aurora tại Lumi Prestige", "Phối cảnh sân tắm nắng & bể Cực Quang – Lumi Prestige"),
        ("assets/media/elite/lumi-elite-dai-sanh-e1.webp", "Phối cảnh đại sảnh Elite 1", "Phối cảnh đại sảnh Elite 1 – Lumi Elite"),
    ]
    figures = []
    for media_path, alt, caption in items:
        w, h = dim[media_path]
        figures.append(figure(media_path, alt, caption, w, h, lightbox=True))
    gallery = (
        '<section class="technical-media-section amenities-media-section">'
        '<div class="media-section-head"><p class="eyebrow">Phối cảnh tiện ích</p><h2>Mỗi phân khu một lớp trải nghiệm</h2>'
        '<p>Hình ảnh dưới đây là phối cảnh từ tài liệu dự án; không được hiểu là ảnh hiện trạng hay xác nhận tiện ích đã vận hành.</p></div>'
        '<div class="technical-plan-gallery">' + ''.join(figures) + '</div></section>'
    )
    html = hero_gallery(html, gallery)
    write(path, html)


def append_css() -> None:
    path = ROOT / "assets/css/site.css"
    css = path.read_text(encoding="utf-8")
    marker = "/* V4 real Lumi project media */"
    if marker in css:
        return
    css += r'''

/* V4 real Lumi project media */
.home-hero{background:linear-gradient(90deg,rgba(20,23,21,.86) 0%,rgba(20,23,21,.62) 44%,rgba(20,23,21,.24) 100%),url("/assets/media/home/lumi-hanoi-tong-the.webp") center 48%/cover no-repeat}.home-hero:after{display:none}.phase-grid .card{overflow:hidden;padding:0}.phase-grid .card>.phase-index,.phase-grid .card>div{margin-inline:28px}.phase-grid .card>div{margin-bottom:28px}.phase-card-media{position:relative;margin:0 0 24px;aspect-ratio:16/9;overflow:hidden;background:#d8cfbf}.phase-card-media img{width:100%;height:100%;object-fit:cover}.phase-card-media figcaption{position:absolute;right:10px;bottom:9px;padding:4px 8px;background:rgba(25,27,25,.75);color:#fff;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase}.amenity-media-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;padding-bottom:42px}.amenity-media-card{margin:0;background:var(--paper);border:1px solid var(--line)}.amenity-media-card img{width:100%;aspect-ratio:16/10;object-fit:cover}.amenity-media-card figcaption{display:flex;flex-direction:column;gap:3px;padding:14px 16px}.amenity-media-card figcaption strong{font-family:Georgia,"Times New Roman",serif;font-weight:500}.amenity-media-card figcaption span{color:var(--muted);font-size:.78rem}.article-media-shell{padding-top:34px}.phase-media-gallery{display:grid;grid-template-columns:1.45fr 1fr;gap:18px}.phase-media-gallery .figure{margin:0}.phase-media-gallery .figure-image{width:100%;aspect-ratio:16/9;object-fit:cover}.phase-media-gallery .figure:nth-child(2) .figure-image{height:100%;min-height:260px}.real-media-figure{overflow:hidden}.real-media-figure .figure-caption{padding-inline:2px}.figure-source{display:block}.technical-media-section{padding:8px 0 16px}.media-section-head{max-width:800px;margin-bottom:24px}.media-section-head h2{font-size:clamp(1.8rem,3.2vw,2.7rem);margin-bottom:12px}.media-section-head>p:last-child{color:var(--muted)}.technical-plan-gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.technical-plan-gallery .figure{margin:0}.technical-plan-gallery .figure-image{width:100%;aspect-ratio:4/3;object-fit:contain;background:#fff}.technical-plan-gallery a{display:block}.technical-plan-gallery .figure-caption{font-size:.92rem}.technical-plan-gallery .figure-source{font-size:.74rem}.lightbox img{background:#fff}
@media(max-width:800px){.home-hero{background-position:58% center}.amenity-media-grid,.technical-plan-gallery{grid-template-columns:1fr}.phase-media-gallery{grid-template-columns:1fr}.phase-media-gallery .figure-image{aspect-ratio:16/10}.article-media-shell{padding-top:22px}.amenity-media-card img{aspect-ratio:16/9}}
'''
    path.write_text(css, encoding="utf-8")


def write_source_doc(dim: dict[str, tuple[int, int]]) -> None:
    lines = [
        "# Media sources V4 — Lumi Hanoi",
        "",
        "Ngày tích hợp: 2026-08-19.",
        "",
        "Các tệp dưới đây được lấy từ bộ tài liệu dự án do chủ sở hữu website cung cấp. Public pages dùng bản WebP tối ưu cục bộ; không hotlink Google Drive.",
        "",
        "| Local asset | Drive file ID | Nội dung | Kích thước WebP |",
        "|---|---|---|---|",
    ]
    for item in ASSETS:
        w, h = dim[item["dest"]]
        lines.append(f"| `{item['dest']}` | `{item['id']}` | {item['label']} | {w}×{h} |")
    lines += [
        "",
        "## Quy tắc diễn giải",
        "",
        "- Ảnh render được ghi rõ là **phối cảnh**; không mô tả như ảnh hiện trạng.",
        "- Ba ảnh mặt bằng là tài liệu theo từng phân khu; không gọi chúng là masterplan duy nhất của toàn dự án.",
        "- Không dùng ảnh để suy ra tình trạng vận hành, ngày bàn giao, giá hoặc quỹ căn.",
    ]
    write("docs/media-sources-v4.md", "\n".join(lines) + "\n")


def main() -> None:
    dim = download_and_optimize()
    append_css()
    integrate_home(dim)
    integrate_phase(
        "lumi-signature/index.html",
        "assets/media/signature/lumi-signature-phoi-canh.webp",
        [
            ("assets/media/signature/lumi-signature-phoi-canh.webp", "Phối cảnh Lumi Signature", "Phối cảnh Lumi Signature"),
            ("assets/media/signature/lumi-signature-be-boi-sole.webp", "Phối cảnh bể bơi resort Sole tại Lumi Signature", "Phối cảnh bể bơi resort Sole – Lumi Signature"),
        ],
        dim,
    )
    integrate_phase(
        "lumi-prestige/index.html",
        "assets/media/prestige/lumi-prestige-phoi-canh.webp",
        [
            ("assets/media/prestige/lumi-prestige-phoi-canh.webp", "Phối cảnh Lumi Prestige", "Phối cảnh Lumi Prestige"),
            ("assets/media/prestige/lumi-prestige-aurora-sundeck.webp", "Phối cảnh sân tắm nắng Aurora tại Lumi Prestige", "Phối cảnh sân tắm nắng & bể Cực Quang – Lumi Prestige"),
        ],
        dim,
    )
    integrate_phase(
        "lumi-elite/index.html",
        "assets/media/elite/lumi-elite-phoi-canh.webp",
        [
            ("assets/media/elite/lumi-elite-phoi-canh.webp", "Phối cảnh mặt đứng Lumi Elite", "Phối cảnh mặt đứng Lumi Elite"),
            ("assets/media/elite/lumi-elite-dai-sanh-e1.webp", "Phối cảnh đại sảnh Elite 1", "Phối cảnh đại sảnh Elite 1 – Lumi Elite"),
        ],
        dim,
    )
    integrate_plans(dim)
    integrate_amenities(dim)
    write_source_doc(dim)


if __name__ == "__main__":
    main()
