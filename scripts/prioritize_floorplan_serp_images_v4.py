#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

import prioritize_floorplan_serp_images_v3 as towers

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://lumi-hanoi.com"
TODAY = "2026-09-12"
DATA_PATH = ROOT / "assets/data/floor-plans.json"
SITEMAP_PATH = ROOT / "sitemap-images.xml"

PHASES = {
    "signature": {
        "label": "Lumi Signature",
        "towers": ["S1", "S2", "S3", "S5", "S6"],
        "page": ROOT / "mat-bang-lumi-hanoi/lumi-signature/index.html",
        "url": f"{SITE}/mat-bang-lumi-hanoi/lumi-signature/",
        "asset": "/assets/media/signature/floor-plans/signature-floorplan-overview-1200x630.webp",
        "alt": "Mặt bằng Lumi Signature gồm các tòa S1, S2, S3, S5 và S6",
    },
    "prestige": {
        "label": "Lumi Prestige",
        "towers": ["P1", "P2"],
        "page": ROOT / "mat-bang-lumi-hanoi/lumi-prestige/index.html",
        "url": f"{SITE}/mat-bang-lumi-hanoi/lumi-prestige/",
        "asset": "/assets/media/prestige/floor-plans/prestige-floorplan-overview-1200x630.webp",
        "alt": "Mặt bằng Lumi Prestige gồm hai tòa P1 và P2",
    },
    "elite": {
        "label": "Lumi Elite",
        "towers": ["E1", "E2"],
        "page": ROOT / "mat-bang-lumi-hanoi/lumi-elite/index.html",
        "url": f"{SITE}/mat-bang-lumi-hanoi/lumi-elite/",
        "asset": "/assets/media/elite/floor-plans/elite-floorplan-overview-1200x630.webp",
        "alt": "Mặt bằng Lumi Elite gồm hai tòa E1 và E2",
    },
}


def get_meta(doc: str, selector: str, key: str) -> str | None:
    pattern = re.compile(rf'<meta\b(?=[^>]*\b{selector}="{re.escape(key)}")[^>]*>', re.I)
    match = pattern.search(doc)
    if not match:
        return None
    content = re.search(r'\bcontent="([^"]*)"', match.group(0), re.I)
    return html.unescape(content.group(1)) if content else None


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
        return doc[:match.start()] + tag + doc[match.end():]
    return doc.replace('</head>', f'<meta {selector}="{key}" content="{escaped}"></head>', 1)


def representative(data: dict, tower: str) -> dict:
    plan = data["towers"][tower]["plans"][0]
    asset = plan.get("asset")
    if not asset:
        raise RuntimeError(f"{tower}: representative asset missing")
    local = ROOT / asset.lstrip("/")
    if not local.is_file():
        raise RuntimeError(f"{tower}: representative file missing: {asset}")
    width = int(plan.get("width") or 0)
    height = int(plan.get("height") or 0)
    if not width or not height:
        with Image.open(local) as image:
            width, height = image.size
    return {
        "asset": asset,
        "width": width,
        "height": height,
        "label": plan["label"],
    }


def create_phase_overview(phase: str, config: dict, data: dict) -> None:
    out = ROOT / config["asset"].lstrip("/")
    out.parent.mkdir(parents=True, exist_ok=True)

    canvas = Image.new("RGB", (1200, 630), "#f5f1e8")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((32, 32, 1168, 598), fill="#fbfaf7", outline="#d7d0c2", width=2)
    draw.text((58, 50), config["label"].upper(), fill="#1a1a18")
    draw.text((58, 72), "FLOOR PLAN OVERVIEW", fill="#6d675d")

    towers_list = config["towers"]
    gap = 18
    left = 58
    top = 112
    bottom = 560
    available = 1084
    cell_w = int((available - gap * (len(towers_list) - 1)) / len(towers_list))
    cell_h = bottom - top

    for index, tower in enumerate(towers_list):
        info = representative(data, tower)
        source_path = ROOT / info["asset"].lstrip("/")
        with Image.open(source_path) as source:
            source = ImageOps.exif_transpose(source).convert("RGB")
            thumb = ImageOps.contain(source, (cell_w - 20, cell_h - 48), Image.Resampling.LANCZOS)
        x0 = left + index * (cell_w + gap)
        y0 = top
        draw.rounded_rectangle((x0, y0, x0 + cell_w, y0 + cell_h), radius=12, fill="#ffffff", outline="#ded8cc", width=2)
        px = x0 + (cell_w - thumb.width) // 2
        py = y0 + 30 + (cell_h - 48 - thumb.height) // 2
        canvas.paste(thumb, (px, py))
        label = tower
        bbox = draw.textbbox((0, 0), label)
        tw = bbox[2] - bbox[0]
        draw.text((x0 + (cell_w - tw) // 2, y0 + 9), label, fill="#11110f")

    canvas.save(out, "WEBP", quality=86, method=6)
    if out.stat().st_size > 700_000:
        canvas.save(out, "WEBP", quality=78, method=6)


def patch_jsonld(doc: str, phase: str, config: dict, data: dict) -> str:
    absolute = SITE + config["asset"]
    canonical = config["url"]
    tower_images = {
        tower: SITE + representative(data, tower)["asset"]
        for tower in config["towers"]
    }
    pattern = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.I | re.S)

    def repl(match: re.Match[str]) -> str:
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            return match.group(0)
        graph = payload.get("@graph") if isinstance(payload, dict) else None
        if not isinstance(graph, list):
            return match.group(0)
        changed = False
        for node in graph:
            if not isinstance(node, dict):
                continue
            if node.get("@type") == "CollectionPage" and node.get("url") == canonical:
                node["dateModified"] = TODAY
                node["image"] = absolute
                node["primaryImageOfPage"] = {
                    "@type": "ImageObject",
                    "contentUrl": absolute,
                    "width": 1200,
                    "height": 630,
                    "caption": config["alt"],
                }
                parts = node.get("hasPart")
                if isinstance(parts, list):
                    for part in parts:
                        if not isinstance(part, dict):
                            continue
                        part_url = str(part.get("url", ""))
                        for tower, image_url in tower_images.items():
                            if f'/{tower.lower()}/' in part_url:
                                part["image"] = image_url
                                break
                changed = True
        if not changed:
            return match.group(0)
        return '<script type="application/ld+json">' + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + '</script>'

    return pattern.sub(repl, doc)


def patch_hero(doc: str, config: dict) -> str:
    hero = re.search(r'<header\b[^>]*class="[^"]*article-hero[^"]*"[^>]*>.*?</header>', doc, re.I | re.S)
    if not hero:
        raise RuntimeError(f"{config['label']}: hero missing")
    block = hero.group(0)
    img_pattern = re.compile(r'<img\b[^>]*class="[^"]*article-hero-media[^"]*"[^>]*>', re.I)
    if not img_pattern.search(block):
        raise RuntimeError(f"{config['label']}: hero image missing")
    image = (
        f'<img class="article-hero-media serp-intent-hero" src="{config["asset"]}" '
        f'width="1200" height="630" alt="{html.escape(config["alt"], quote=True)}" '
        'loading="eager" fetchpriority="high" decoding="async">'
    )
    block = img_pattern.sub(image, block, count=1)
    return doc[:hero.start()] + block + doc[hero.end():]


def patch_cards(doc: str, config: dict, data: dict) -> str:
    for tower in config["towers"]:
        info = representative(data, tower)
        href = f'/mat-bang-lumi-hanoi/lumi-{phase_for_tower(tower)}/{tower.lower()}/'
        pattern = re.compile(
            rf'<a class="tower-card-media" href="{re.escape(href)}">.*?</a>',
            re.I | re.S,
        )
        replacement = (
            f'<a class="tower-card-media" href="{href}">'
            f'<img src="{info["asset"]}" width="{info["width"]}" height="{info["height"]}" '
            f'alt="Mặt bằng {tower} Lumi Hanoi — {html.escape(info["label"], quote=True)}" '
            'loading="lazy" decoding="async"></a>'
        )
        doc, count = pattern.subn(replacement, doc, count=1)
        if count != 1:
            raise RuntimeError(f"{config['label']}: tower card {tower} not found")
    return doc


def phase_for_tower(tower: str) -> str:
    if tower.startswith("S"):
        return "signature"
    if tower.startswith("P"):
        return "prestige"
    return "elite"


def patch_page(phase: str, config: dict, data: dict) -> None:
    doc = config["page"].read_text(encoding="utf-8")
    absolute = SITE + config["asset"]
    robots = get_meta(doc, "name", "robots") or "index,follow"
    robots_parts = [part.strip() for part in robots.split(",") if part.strip()]
    if "max-image-preview:large" not in robots_parts:
        robots_parts.append("max-image-preview:large")
    doc = set_meta(doc, "name", "robots", ",".join(robots_parts))
    doc = set_meta(doc, "property", "og:image", absolute)
    doc = set_meta(doc, "property", "og:image:type", "image/webp")
    doc = set_meta(doc, "property", "og:image:width", "1200")
    doc = set_meta(doc, "property", "og:image:height", "630")
    doc = set_meta(doc, "property", "og:image:alt", config["alt"])
    doc = set_meta(doc, "name", "twitter:card", "summary_large_image")
    doc = set_meta(doc, "name", "twitter:image", absolute)
    doc = set_meta(doc, "name", "twitter:image:alt", config["alt"])
    doc = patch_jsonld(doc, phase, config, data)
    doc = patch_hero(doc, config)
    doc = patch_cards(doc, config, data)
    config["page"].write_text(doc, encoding="utf-8")


def patch_sitemap(data: dict) -> None:
    xml = SITEMAP_PATH.read_text(encoding="utf-8")
    for phase, config in PHASES.items():
        images = [SITE + config["asset"]] + [SITE + representative(data, t)["asset"] for t in config["towers"]]
        image_tags = "".join(
            f"\n    <image:image>\n      <image:loc>{image}</image:loc>\n    </image:image>"
            for image in images
        )
        pattern = re.compile(rf'(<url>\s*<loc>{re.escape(config["url"])}</loc>)(.*?)(</url>)', re.S)
        match = pattern.search(xml)
        if not match:
            block = f"  <url>\n    <loc>{config['url']}</loc>{image_tags}\n  </url>\n"
            xml = xml.replace("</urlset>", block + "</urlset>")
            continue
        body = re.sub(r'\s*<image:image>.*?</image:image>', '', match.group(2), flags=re.S)
        replacement = match.group(1) + image_tags + body + match.group(3)
        xml = xml[:match.start()] + replacement + xml[match.end():]
    SITEMAP_PATH.write_text(xml, encoding="utf-8")


def verify(data: dict) -> None:
    for phase, config in PHASES.items():
        overview = ROOT / config["asset"].lstrip("/")
        if not overview.is_file():
            raise RuntimeError(f"{phase}: overview image missing")
        with Image.open(overview) as image:
            if image.size != (1200, 630):
                raise RuntimeError(f"{phase}: overview image dimensions are not 1200x630")
        doc = config["page"].read_text(encoding="utf-8")
        absolute = SITE + config["asset"]
        if get_meta(doc, "property", "og:image") != absolute:
            raise RuntimeError(f"{phase}: og:image mismatch")
        if get_meta(doc, "name", "twitter:image") != absolute:
            raise RuntimeError(f"{phase}: twitter:image mismatch")
        if f'src="{config["asset"]}"' not in doc:
            raise RuntimeError(f"{phase}: overview hero is not visible")
        robots = get_meta(doc, "name", "robots") or ""
        if "max-image-preview:large" not in robots:
            raise RuntimeError(f"{phase}: large image preview missing")
        for tower in config["towers"]:
            info = representative(data, tower)
            if f'src="{info["asset"]}"' not in doc:
                raise RuntimeError(f"{phase}: local tower card missing for {tower}")
            if f'/{tower.lower()}/' not in doc:
                raise RuntimeError(f"{phase}: tower link missing for {tower}")


def main() -> None:
    # Keep the already-successful tower representative optimization as the first stage.
    towers.base.main()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for phase, config in PHASES.items():
        create_phase_overview(phase, config, data)
        patch_page(phase, config, data)
    patch_sitemap(data)
    verify(data)
    for phase, config in PHASES.items():
        print(f"{phase}: {config['asset']} + local tower cards")


if __name__ == "__main__":
    main()
