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
    "S1": "signature",
    "S2": "signature",
    "S3": "signature",
    "S5": "signature",
    "S6": "signature",
    "P1": "prestige",
    "P2": "prestige",
    "E1": "elite",
    "E2": "elite",
}
TOWER_ORDER = ["S1", "S2", "S3", "S5", "S6", "P1", "P2", "E1", "E2"]
SIGNATURE_TOWERS = {"S1", "S2", "S3", "S5", "S6"}


def page_path(tower: str) -> Path:
    return ROOT / f"mat-bang-lumi-hanoi/lumi-{PHASE[tower]}/{tower.lower()}/index.html"


def page_url(tower: str) -> str:
    return f"{SITE}/mat-bang-lumi-hanoi/lumi-{PHASE[tower]}/{tower.lower()}/"


def get_meta(doc: str, selector: str, key: str) -> str | None:
    pattern = re.compile(rf'<meta\b(?=[^>]*\b{selector}="{re.escape(key)}")[^>]*>', re.I)
    match = pattern.search(doc)
    if not match:
        return None
    value = re.search(r'\bcontent="([^"]*)"', match.group(0), re.I)
    return html.unescape(value.group(1)) if value else None


def set_meta(doc: str, selector: str, key: str, value: str) -> str:
    pattern = re.compile(rf'<meta\b(?=[^>]*\b{selector}="{re.escape(key)}")[^>]*>', re.I)
    match = pattern.search(doc)
    escaped = html.escape(str(value), quote=True)
    if match:
        tag = match.group(0)
        if re.search(r'\bcontent="[^"]*"', tag, re.I):
            tag = re.sub(r'\bcontent="[^"]*"', f'content="{escaped}"', tag, count=1, flags=re.I)
        else:
            tag = tag[:-1] + f' content="{escaped}">'
        return doc[: match.start()] + tag + doc[match.end() :]
    return doc.replace("</head>", f'<meta {selector}="{key}" content="{escaped}"></head>', 1)


def download_drive_image(drive_id: str) -> Image.Image:
    urls = [
        f"https://drive.google.com/thumbnail?id={drive_id}&sz=w2400",
        f"https://lh3.googleusercontent.com/d/{drive_id}=w2400",
    ]
    last_error: Exception | None = None
    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; LumiHanoiFloorplanBot/1.0)",
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=45) as response:
                content_type = response.headers.get("Content-Type", "")
                raw = response.read()
            if not raw or "text/html" in content_type.lower():
                raise RuntimeError(f"unexpected response {content_type or 'unknown'}")
            image = Image.open(io.BytesIO(raw))
            image.load()
            return image
        except Exception as exc:  # pragma: no cover - network fallback
            last_error = exc
    raise RuntimeError(f"cannot download Drive image {drive_id}: {last_error}")


def save_webp(image: Image.Image, destination: Path) -> tuple[int, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    image = ImageOps.exif_transpose(image)
    if image.mode not in {"RGB", "RGBA"}:
        image = image.convert("RGB")
    elif image.mode == "RGBA":
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.getchannel("A"))
        image = background

    max_side = 2400
    width, height = image.size
    scale = min(1.0, max_side / max(width, height))
    if scale < 1.0:
        image = image.resize((round(width * scale), round(height * scale)), Image.Resampling.LANCZOS)
    image.save(destination, "WEBP", quality=84, method=6)
    return image.size


def localize_signature_typical(data: dict) -> dict[str, dict]:
    selected: dict[str, dict] = {}
    for tower in TOWER_ORDER:
        plans = data["towers"][tower]["plans"]
        if not plans:
            raise RuntimeError(f"{tower}: no floor plans")
        plan = plans[0]
        if tower in SIGNATURE_TOWERS:
            drive_id = plan.get("driveId")
            if not drive_id:
                raise RuntimeError(f"{tower}: missing Drive id for representative plan")
            asset = f"/assets/media/signature/floor-plans/{tower.lower()}-typical.webp"
            destination = ROOT / asset.lstrip("/")
            image = download_drive_image(drive_id)
            width, height = save_webp(image, destination)
            if destination.stat().st_size > 1_200_000:
                raise RuntimeError(f"{tower}: representative WebP is unexpectedly large")
            plan["asset"] = asset
            plan["width"] = width
            plan["height"] = height
        else:
            asset = plan.get("asset")
            if not asset or not (ROOT / asset.lstrip("/")).is_file():
                raise RuntimeError(f"{tower}: first/typical plan must already be a local asset")
            with Image.open(ROOT / asset.lstrip("/")) as image:
                width, height = image.size
            plan["width"] = int(plan.get("width") or width)
            plan["height"] = int(plan.get("height") or height)

        selected[tower] = {
            "asset": plan["asset"],
            "width": int(plan["width"]),
            "height": int(plan["height"]),
            "anchor": plan["anchor"],
            "label": plan["label"],
        }
    data["version"] = "8.4"
    data["updated"] = TODAY
    return selected


def patch_jsonld(doc: str, tower: str, selected: dict) -> str:
    canonical = page_url(tower)
    absolute = SITE + selected["asset"]
    caption = f'Mặt bằng tòa {tower} Lumi Hanoi — {selected["label"]}'

    script_pattern = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S | re.I)

    def replace(match: re.Match[str]) -> str:
        raw = match.group(1)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return match.group(0)
        graph = payload.get("@graph") if isinstance(payload, dict) else None
        if not isinstance(graph, list):
            return match.group(0)
        changed = False
        primary_id = canonical + "#primaryimage"
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
                node["@id"] = primary_id
                node["url"] = absolute
                node["contentUrl"] = absolute
                node["width"] = selected["width"]
                node["height"] = selected["height"]
                node["caption"] = caption
                node["inLanguage"] = "vi-VN"
                changed = True
        if not changed:
            return match.group(0)
        return '<script type="application/ld+json">' + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "</script>"

    return script_pattern.sub(replace, doc)


def patch_primary_section(doc: str, tower: str, selected: dict) -> str:
    phase_label = PHASE[tower].capitalize()
    label = selected["label"]
    alt = f"Mặt bằng tòa {tower} Lumi Hanoi — {label}"
    section = (
        f'<section class="floor-plan-section floor-plan-primary" id="{selected["anchor"]}" '
        f'data-primary-floor-plan data-tower="{tower}"><div class="plan-section-head"><div>'
        f'<p class="eyebrow">{phase_label} · {tower}</p><h2>{tower} — {label}</h2></div></div>'
        f'<figure class="figure floor-plan-figure"><a href="{selected["asset"]}" data-lightbox '
        f'data-lightbox-alt="{html.escape(alt, quote=True)}" data-lightbox-caption="{tower} — {html.escape(label, quote=True)}">'
        f'<img class="figure-image floor-plan-image" src="{selected["asset"]}" width="{selected["width"]}" '
        f'height="{selected["height"]}" alt="{html.escape(alt, quote=True)}" loading="eager" fetchpriority="high" decoding="async"></a>'
        f'<figcaption class="figure-caption">Mặt bằng {tower} Lumi Hanoi — {html.escape(label)}. '
        f'Đây là nhóm tầng đại diện; chọn đúng tầng của căn ở danh sách phía trên.</figcaption></figure></section>'
    )
    pattern = re.compile(r'<section class="floor-plan-section floor-plan-primary"\b.*?</section>', re.S | re.I)
    if not pattern.search(doc):
        raise RuntimeError(f"{tower}: missing primary floor-plan section")
    return pattern.sub(section, doc, count=1)


def patch_hero(doc: str, tower: str, selected: dict) -> str:
    label = selected["label"]
    alt = f"Mặt bằng tòa {tower} Lumi Hanoi — {label}"
    image = (
        f'<img class="article-hero-media tower-serp-plan" src="{selected["asset"]}" '
        f'width="{selected["width"]}" height="{selected["height"]}" alt="{html.escape(alt, quote=True)}" '
        'loading="eager" fetchpriority="high" decoding="async">'
    )
    hero_pattern = re.compile(r'<header class="article-hero tower-hero">.*?</header>', re.S | re.I)
    match = hero_pattern.search(doc)
    if not match:
        raise RuntimeError(f"{tower}: missing tower hero")
    block = match.group(0)
    image_pattern = re.compile(r'<img\b[^>]*class="[^"]*article-hero-media[^"]*"[^>]*>', re.I)
    if not image_pattern.search(block):
        raise RuntimeError(f"{tower}: missing hero image")
    block = image_pattern.sub(image, block, count=1)
    return doc[: match.start()] + block + doc[match.end() :]


def patch_page(tower: str, selected: dict) -> None:
    path = page_path(tower)
    doc = path.read_text(encoding="utf-8")
    absolute = SITE + selected["asset"]
    alt = f'Mặt bằng tòa {tower} Lumi Hanoi — {selected["label"]}'

    doc = set_meta(doc, "property", "og:image", absolute)
    doc = set_meta(doc, "property", "og:image:type", "image/webp")
    doc = set_meta(doc, "property", "og:image:width", str(selected["width"]))
    doc = set_meta(doc, "property", "og:image:height", str(selected["height"]))
    doc = set_meta(doc, "property", "og:image:alt", alt)
    doc = set_meta(doc, "name", "twitter:card", "summary_large_image")
    doc = set_meta(doc, "name", "twitter:image", absolute)
    doc = set_meta(doc, "name", "twitter:image:alt", alt)
    doc = patch_jsonld(doc, tower, selected)
    doc = patch_hero(doc, tower, selected)
    doc = patch_primary_section(doc, tower, selected)
    path.write_text(doc, encoding="utf-8")


def patch_image_sitemap(selected: dict[str, dict]) -> None:
    xml = SITEMAP_PATH.read_text(encoding="utf-8")
    for tower in TOWER_ORDER:
        loc = page_url(tower)
        image_loc = SITE + selected[tower]["asset"]
        pattern = re.compile(
            rf'(<url>\s*<loc>{re.escape(loc)}</loc>)(.*?)(</url>)',
            re.S,
        )
        match = pattern.search(xml)
        image_tag = f"\n    <image:image>\n      <image:loc>{image_loc}</image:loc>\n    </image:image>"
        if match:
            body = match.group(2)
            if image_loc not in body:
                body = image_tag + body
                xml = xml[: match.start()] + match.group(1) + body + match.group(3) + xml[match.end() :]
        else:
            block = (
                "  <url>\n"
                f"    <loc>{loc}</loc>"
                f"{image_tag}\n"
                "  </url>\n"
            )
            xml = xml.replace("</urlset>", block + "</urlset>")
    SITEMAP_PATH.write_text(xml, encoding="utf-8")


def verify(data: dict, selected: dict[str, dict]) -> None:
    for tower in TOWER_ORDER:
        choice = selected[tower]
        local_file = ROOT / choice["asset"].lstrip("/")
        if not local_file.is_file():
            raise RuntimeError(f"{tower}: local representative image missing")
        doc = page_path(tower).read_text(encoding="utf-8")
        absolute = SITE + choice["asset"]
        if get_meta(doc, "property", "og:image") != absolute:
            raise RuntimeError(f"{tower}: og:image mismatch")
        if f'src="{choice["asset"]}"' not in doc:
            raise RuntimeError(f"{tower}: representative image not visible in HTML")
        if f'id="{choice["anchor"]}" data-primary-floor-plan' not in doc:
            raise RuntimeError(f"{tower}: typical group is not primary")
        if data["towers"][tower]["plans"][0].get("asset") != choice["asset"]:
            raise RuntimeError(f"{tower}: manifest first plan not aligned")


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    selected = localize_signature_typical(data)
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    for tower in TOWER_ORDER:
        patch_page(tower, selected[tower])
    patch_image_sitemap(selected)
    verify(data, selected)
    for tower in TOWER_ORDER:
        choice = selected[tower]
        print(f"{tower}: {choice['label']} -> {choice['asset']}")


if __name__ == "__main__":
    main()
