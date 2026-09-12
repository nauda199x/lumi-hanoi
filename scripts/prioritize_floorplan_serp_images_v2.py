#!/usr/bin/env python3
from __future__ import annotations

import html
import io
import json
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://lumi-hanoi.com"
TODAY = "2026-09-12"
DATA_PATH = ROOT / "assets/data/floor-plans.json"
SITEMAP_PATH = ROOT / "sitemap-images.xml"

PHASE = {
    "S1": "signature", "S2": "signature", "S3": "signature", "S5": "signature", "S6": "signature",
    "P1": "prestige", "P2": "prestige", "E1": "elite", "E2": "elite",
}
TOWERS = list(PHASE)


def page_path(tower: str) -> Path:
    return ROOT / f"mat-bang-lumi-hanoi/lumi-{PHASE[tower]}/{tower.lower()}/index.html"


def page_url(tower: str) -> str:
    return f"{SITE}/mat-bang-lumi-hanoi/lumi-{PHASE[tower]}/{tower.lower()}/"


def meta(doc: str, selector: str, key: str) -> str | None:
    m = re.search(rf'<meta\b(?=[^>]*\b{selector}="{re.escape(key)}")[^>]*>', doc, re.I)
    if not m:
        return None
    c = re.search(r'\bcontent="([^"]*)"', m.group(0), re.I)
    return html.unescape(c.group(1)) if c else None


def set_meta(doc: str, selector: str, key: str, value: str) -> str:
    pattern = re.compile(rf'<meta\b(?=[^>]*\b{selector}="{re.escape(key)}")[^>]*>', re.I)
    m = pattern.search(doc)
    escaped = html.escape(str(value), quote=True)
    if m:
        tag = m.group(0)
        if re.search(r'\bcontent="[^"]*"', tag, re.I):
            tag = re.sub(r'\bcontent="[^"]*"', f'content="{escaped}"', tag, count=1, flags=re.I)
        else:
            tag = tag[:-1] + f' content="{escaped}">'
        return doc[:m.start()] + tag + doc[m.end():]
    return doc.replace('</head>', f'<meta {selector}="{key}" content="{escaped}"></head>', 1)


def fetch_drive(drive_id: str) -> Image.Image:
    urls = [
        f"https://drive.google.com/thumbnail?id={drive_id}&sz=w2400",
        f"https://lh3.googleusercontent.com/d/{drive_id}=w2400",
    ]
    last: Exception | None = None
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; LumiHanoiFloorplanBot/2.0)",
                "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
            })
            with urllib.request.urlopen(req, timeout=45) as response:
                content_type = response.headers.get("Content-Type", "")
                raw = response.read()
            if not raw or "text/html" in content_type.lower():
                raise RuntimeError(f"unexpected response {content_type or 'unknown'}")
            image = Image.open(io.BytesIO(raw))
            image.load()
            return image
        except Exception as exc:
            last = exc
    raise RuntimeError(f"cannot download Drive image {drive_id}: {last}")


def save_webp(image: Image.Image, path: Path) -> tuple[int, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = ImageOps.exif_transpose(image)
    if image.mode == "RGBA":
        bg = Image.new("RGB", image.size, "white")
        bg.paste(image, mask=image.getchannel("A"))
        image = bg
    elif image.mode != "RGB":
        image = image.convert("RGB")

    max_side = 2400
    w, h = image.size
    scale = min(1.0, max_side / max(w, h))
    if scale < 1:
        image = image.resize((round(w * scale), round(h * scale)), Image.Resampling.LANCZOS)

    for quality in (84, 78, 72, 66):
        image.save(path, "WEBP", quality=quality, method=6)
        if path.stat().st_size <= 1_200_000:
            return image.size
    raise RuntimeError(f"optimized floor plan is still too large: {path}")


def localize_representative_plans(data: dict) -> dict[str, dict]:
    chosen: dict[str, dict] = {}
    for tower in TOWERS:
        plans = data["towers"][tower]["plans"]
        if not plans:
            raise RuntimeError(f"{tower}: no floor-plan records")
        plan = plans[0]
        asset = plan.get("asset")
        local = ROOT / asset.lstrip("/") if asset else None

        if not asset or not local or not local.is_file():
            drive_id = plan.get("driveId")
            if not drive_id:
                raise RuntimeError(f"{tower}: representative plan has neither local asset nor Drive id")
            asset = f"/assets/media/{PHASE[tower]}/floor-plans/{tower.lower()}-typical.webp"
            local = ROOT / asset.lstrip("/")
            width, height = save_webp(fetch_drive(drive_id), local)
            plan["asset"] = asset
            plan["width"] = width
            plan["height"] = height
        else:
            with Image.open(local) as image:
                width, height = image.size
            plan["width"] = int(plan.get("width") or width)
            plan["height"] = int(plan.get("height") or height)

        chosen[tower] = {
            "asset": plan["asset"],
            "width": int(plan["width"]),
            "height": int(plan["height"]),
            "anchor": plan["anchor"],
            "label": plan["label"],
            "driveId": plan.get("driveId", ""),
        }

    data["version"] = "8.4"
    data["updated"] = TODAY
    return chosen


def patch_jsonld(doc: str, tower: str, chosen: dict) -> str:
    canonical = page_url(tower)
    absolute = SITE + chosen["asset"]
    caption = f'Mặt bằng tòa {tower} Lumi Hanoi — {chosen["label"]}'
    pattern = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.I | re.S)

    def repl(match: re.Match[str]) -> str:
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            return match.group(0)
        graph = payload.get("@graph") if isinstance(payload, dict) else None
        if not isinstance(graph, list):
            return match.group(0)
        primary_id = canonical + "#primaryimage"
        changed = False
        for node in graph:
            if not isinstance(node, dict):
                continue
            if node.get("@type") == "CollectionPage" and node.get("url") == canonical:
                node["dateModified"] = TODAY
                node["primaryImageOfPage"] = {"@id": primary_id}
                node["image"] = {"@id": primary_id}
                node["thumbnailUrl"] = absolute
                changed = True
            if node.get("@type") == "ImageObject" and str(node.get("@id", "")).endswith("#primaryimage"):
                node.update({
                    "@id": primary_id,
                    "url": absolute,
                    "contentUrl": absolute,
                    "width": chosen["width"],
                    "height": chosen["height"],
                    "caption": caption,
                    "inLanguage": "vi-VN",
                })
                changed = True
        if not changed:
            return match.group(0)
        return '<script type="application/ld+json">' + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + '</script>'

    return pattern.sub(repl, doc)


def representative_section(tower: str, chosen: dict) -> str:
    label = chosen["label"]
    alt = f"Mặt bằng tòa {tower} Lumi Hanoi — {label}"
    phase_label = PHASE[tower].capitalize()
    return (
        f'<section class="floor-plan-section floor-plan-primary" id="{chosen["anchor"]}" '
        f'data-primary-floor-plan data-tower="{tower}"><div class="plan-section-head"><div>'
        f'<p class="eyebrow">{phase_label} · {tower}</p><h2>{tower} — {html.escape(label)}</h2></div></div>'
        f'<figure class="figure floor-plan-figure"><a href="{chosen["asset"]}" data-lightbox '
        f'data-lightbox-alt="{html.escape(alt, quote=True)}" data-lightbox-caption="{tower} — {html.escape(label, quote=True)}">'
        f'<img class="figure-image floor-plan-image" src="{chosen["asset"]}" width="{chosen["width"]}" '
        f'height="{chosen["height"]}" alt="{html.escape(alt, quote=True)}" loading="eager" fetchpriority="high" decoding="async"></a>'
        f'<figcaption class="figure-caption">Mặt bằng {tower} Lumi Hanoi — {html.escape(label)}. '
        'Nhóm tầng đại diện; hãy chọn đúng tầng của căn để đối chiếu.</figcaption></figure></section>'
    )


def patch_tower_body(doc: str, tower: str, chosen: dict) -> str:
    alt = f'Mặt bằng tòa {tower} Lumi Hanoi — {chosen["label"]}'
    hero_img = (
        f'<img class="article-hero-media tower-serp-plan" src="{chosen["asset"]}" '
        f'width="{chosen["width"]}" height="{chosen["height"]}" alt="{html.escape(alt, quote=True)}" '
        'loading="eager" fetchpriority="high" decoding="async">'
    )
    hero = re.search(r'<header class="article-hero tower-hero">.*?</header>', doc, re.I | re.S)
    if not hero:
        raise RuntimeError(f"{tower}: tower hero missing")
    block = hero.group(0)
    img_pattern = re.compile(r'<img\b[^>]*class="[^"]*article-hero-media[^"]*"[^>]*>', re.I)
    if not img_pattern.search(block):
        raise RuntimeError(f"{tower}: hero image missing")
    block = img_pattern.sub(hero_img, block, count=1)
    doc = doc[:hero.start()] + block + doc[hero.end():]

    new_section = representative_section(tower, chosen)
    primary_pattern = re.compile(r'<section class="floor-plan-section floor-plan-primary"\b.*?</section>', re.I | re.S)
    if primary_pattern.search(doc):
        doc = primary_pattern.sub(new_section, doc, count=1)
    else:
        selected_pattern = re.compile(
            rf'<section\b[^>]*id="{re.escape(chosen["anchor"])}"[^>]*>.*?</section>', re.I | re.S
        )
        if not selected_pattern.search(doc):
            raise RuntimeError(f"{tower}: representative floor section missing")
        doc = selected_pattern.sub(new_section, doc, count=1)
    return doc


def patch_page(tower: str, chosen: dict) -> None:
    path = page_path(tower)
    doc = path.read_text(encoding="utf-8")
    absolute = SITE + chosen["asset"]
    alt = f'Mặt bằng tòa {tower} Lumi Hanoi — {chosen["label"]}'

    doc = set_meta(doc, "property", "og:image", absolute)
    doc = set_meta(doc, "property", "og:image:type", "image/webp")
    doc = set_meta(doc, "property", "og:image:width", str(chosen["width"]))
    doc = set_meta(doc, "property", "og:image:height", str(chosen["height"]))
    doc = set_meta(doc, "property", "og:image:alt", alt)
    doc = set_meta(doc, "name", "twitter:card", "summary_large_image")
    doc = set_meta(doc, "name", "twitter:image", absolute)
    doc = set_meta(doc, "name", "twitter:image:alt", alt)
    doc = patch_jsonld(doc, tower, chosen)
    doc = patch_tower_body(doc, tower, chosen)
    path.write_text(doc, encoding="utf-8")


def patch_image_sitemap(chosen: dict[str, dict]) -> None:
    xml = SITEMAP_PATH.read_text(encoding="utf-8")
    for tower in TOWERS:
        loc = page_url(tower)
        image_loc = SITE + chosen[tower]["asset"]
        block_pattern = re.compile(rf'(<url>\s*<loc>{re.escape(loc)}</loc>)(.*?)(</url>)', re.S)
        m = block_pattern.search(xml)
        image_tag = f"\n    <image:image>\n      <image:loc>{image_loc}</image:loc>\n    </image:image>"
        if m:
            body = m.group(2)
            if image_loc not in body:
                body = image_tag + body
                xml = xml[:m.start()] + m.group(1) + body + m.group(3) + xml[m.end():]
        else:
            xml = xml.replace(
                "</urlset>",
                f"  <url>\n    <loc>{loc}</loc>{image_tag}\n  </url>\n</urlset>",
            )
    SITEMAP_PATH.write_text(xml, encoding="utf-8")


def verify(data: dict, chosen: dict[str, dict]) -> None:
    for tower in TOWERS:
        c = chosen[tower]
        local = ROOT / c["asset"].lstrip("/")
        if not local.is_file():
            raise RuntimeError(f"{tower}: local representative file missing")
        doc = page_path(tower).read_text(encoding="utf-8")
        absolute = SITE + c["asset"]
        if meta(doc, "property", "og:image") != absolute:
            raise RuntimeError(f"{tower}: og:image mismatch")
        if meta(doc, "name", "twitter:image") != absolute:
            raise RuntimeError(f"{tower}: twitter:image mismatch")
        if f'src="{c["asset"]}"' not in doc:
            raise RuntimeError(f"{tower}: representative image is not visible")
        if f'id="{c["anchor"]}" data-primary-floor-plan' not in doc:
            raise RuntimeError(f"{tower}: representative floor is not marked primary")
        if data["towers"][tower]["plans"][0].get("asset") != c["asset"]:
            raise RuntimeError(f"{tower}: manifest representative asset mismatch")


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    chosen = localize_representative_plans(data)
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for tower in TOWERS:
        patch_page(tower, chosen[tower])
    patch_image_sitemap(chosen)
    verify(data, chosen)
    for tower in TOWERS:
        c = chosen[tower]
        print(f"{tower}: {c['label']} -> {c['asset']}")


if __name__ == "__main__":
    main()
