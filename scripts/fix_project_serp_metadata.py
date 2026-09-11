#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://lumi-hanoi.com"

# Pages where search intent is explicitly visual. These must never advertise a
# generic project render/landscape as their primary search/social image.
VISUAL_TARGETS = {
    "mat-bang-lumi-hanoi/lumi-signature/index.html": {
        "og_src": "/assets/media/signature/penthouse/s1-floor-35.webp",
        "hero_src": "/assets/media/signature/penthouse/s1-floor-35.webp",
        "width": 1980,
        "height": 1457,
        "alt": "Mặt bằng Lumi Signature — bản vẽ tòa S1 Lumi Hanoi",
    },
    "mat-bang-lumi-hanoi/lumi-prestige/index.html": {
        "og_src": "/assets/media/prestige/floor-plans/p1-t30.webp",
        "hero_src": "/assets/media/prestige/floor-plans/p1-t30.webp",
        "width": 1980,
        "height": 1453,
        "alt": "Mặt bằng Lumi Prestige — bản vẽ tòa P1 Lumi Hanoi",
    },
    "mat-bang-lumi-hanoi/lumi-elite/index.html": {
        "og_src": "/assets/media/elite/floor-plans/e1-t29.webp",
        "hero_src": "/assets/media/elite/floor-plans/e1-t29.webp",
        "width": 1980,
        "height": 1453,
        "alt": "Mặt bằng Lumi Elite — bản vẽ tòa E1 Lumi Hanoi",
    },
    "layout-can-ho-lumi-signature/index.html": {
        "og_src": "/assets/media/signature/unit-layouts/signature-s1-s5-1br-a1.webp",
        "hero_src": "/assets/media/signature/unit-layouts/signature-s1-s5-1br-a1.webp",
        "width": 1800,
        "height": 2400,
        "alt": "Layout căn hộ Lumi Signature — mẫu 1PN A1",
    },
    "layout-can-ho-lumi-prestige/index.html": {
        "og_src": "/assets/media/prestige/unit-layouts/prestige-layout-22-1br-medium.webp",
        "hero_src": "/assets/media/prestige/unit-layouts/prestige-layout-22-1br-medium.webp",
        "width": 3200,
        "height": 4267,
        "alt": "Layout căn hộ Lumi Prestige — bản vẽ 1BR Medium",
    },
    "tin-tuc/cach-doc-mat-bang-lumi-hanoi/index.html": {
        "og_src": "/assets/media/masterplan/lumi-hanoi-mat-bang-tong-the-og-1200x630.webp",
        "hero_src": "/assets/media/masterplan/lumi-hanoi-masterplan-1280.webp",
        "width": 1200,
        "height": 630,
        "hero_width": 1280,
        "hero_height": 853,
        "alt": "Mặt bằng tổng thể Lumi Hanoi — hướng dẫn đọc bản vẽ",
    },
    "tin-tuc/so-sanh-mat-bang-s1-s2-s3-s5-s6-lumi-signature/index.html": {
        "og_src": "/assets/media/signature/penthouse/s1-floor-35.webp",
        "hero_src": "/assets/media/signature/penthouse/s1-floor-35.webp",
        "width": 1980,
        "height": 1457,
        "alt": "Mặt bằng Lumi Signature — đối chiếu các tòa S1, S2, S3, S5, S6",
    },
    "tin-tuc/layout-can-ho-lumi-signature-1pn-2pn-3pn-duplex/index.html": {
        "og_src": "/assets/media/signature/unit-layouts/signature-s1-s5-1br-a1.webp",
        "hero_src": "/assets/media/signature/unit-layouts/signature-s1-s5-1br-a1.webp",
        "width": 1800,
        "height": 2400,
        "alt": "Layout căn hộ Lumi Signature — bản vẽ 1PN, 2PN, 3PN và Duplex",
    },
}

META_RE = re.compile(r"<meta\b[^>]*>", re.I)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
JSONLD_RE = re.compile(
    r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
    re.I | re.S,
)


def get_attr(tag: str, name: str) -> str | None:
    m = re.search(rf"\b{re.escape(name)}\s*=\s*([\"'])(.*?)\1", tag, re.I | re.S)
    return html.unescape(m.group(2)) if m else None


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", value))).strip()


def page_title(doc: str) -> str:
    m = TITLE_RE.search(doc)
    return clean_text(m.group(1)) if m else ""


def page_h1(doc: str) -> str:
    m = H1_RE.search(doc)
    return clean_text(m.group(1)) if m else page_title(doc)


def get_meta(doc: str, selector: str, key: str) -> str | None:
    for m in META_RE.finditer(doc):
        tag = m.group(0)
        if get_attr(tag, selector) == key:
            return get_attr(tag, "content")
    return None


def set_meta(doc: str, selector: str, key: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    for m in META_RE.finditer(doc):
        tag = m.group(0)
        if get_attr(tag, selector) != key:
            continue
        if re.search(r"\bcontent\s*=", tag, re.I):
            new_tag = re.sub(
                r"\bcontent\s*=\s*([\"']).*?\1",
                f'content="{escaped}"',
                tag,
                count=1,
                flags=re.I | re.S,
            )
        else:
            new_tag = tag[:-1] + f' content="{escaped}">'
        return doc[: m.start()] + new_tag + doc[m.end() :]
    if "</head>" not in doc:
        raise RuntimeError(f"Cannot add meta {key}: </head> missing")
    return doc.replace("</head>", f'<meta {selector}="{key}" content="{escaped}"></head>', 1)


def absolute(src: str) -> str:
    if src.startswith("https://") or src.startswith("http://"):
        return src
    return SITE + (src if src.startswith("/") else "/" + src)


def local_asset_exists(src: str) -> bool:
    parsed = urlparse(src)
    if parsed.netloc and parsed.netloc not in {"lumi-hanoi.com", "www.lumi-hanoi.com"}:
        return True
    return (ROOT / parsed.path.lstrip("/")).is_file()


def update_jsonld_images(doc: str, new_image: str, old_image: str | None) -> str:
    def mutate_node(node):
        if isinstance(node, list):
            return [mutate_node(item) for item in node]
        if not isinstance(node, dict):
            return node
        node = {key: mutate_node(value) for key, value in node.items()}
        node_type = node.get("@type")
        types = set(node_type if isinstance(node_type, list) else [node_type])
        if types & {"Article", "NewsArticle", "BlogPosting", "CollectionPage", "WebPage"}:
            current = node.get("image")
            if current is None or (isinstance(current, str) and old_image and current == old_image):
                node["image"] = new_image
            if isinstance(node.get("thumbnailUrl"), str) and old_image and node["thumbnailUrl"] == old_image:
                node["thumbnailUrl"] = new_image
        if node.get("@type") == "ImageObject" and old_image:
            for key in ("url", "contentUrl"):
                if node.get(key) == old_image:
                    node[key] = new_image
        return node

    def repl(match: re.Match) -> str:
        raw = match.group(2).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            if old_image:
                raw = raw.replace(old_image, new_image)
            return match.group(1) + raw + match.group(3)
        data = mutate_node(data)
        return match.group(1) + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + match.group(3)

    return JSONLD_RE.sub(repl, doc)


def replace_article_hero(doc: str, src: str, alt_text: str, width: int, height: int) -> tuple[str, bool]:
    hero = re.search(r'<header\b[^>]*class="[^"]*article-hero[^"]*"[^>]*>.*?</header>', doc, re.I | re.S)
    if not hero:
        return doc, False
    block = hero.group(0)
    media = re.search(r'<picture\b[^>]*>.*?article-hero-media.*?</picture>', block, re.I | re.S)
    if not media:
        media = re.search(r'<img\b[^>]*class="[^"]*article-hero-media[^"]*"[^>]*>', block, re.I | re.S)
    if not media:
        return doc, False
    replacement = (
        f'<img class="article-hero-media serp-intent-hero" src="{html.escape(src, quote=True)}" '
        f'width="{width}" height="{height}" alt="{html.escape(alt_text, quote=True)}" '
        'loading="eager" fetchpriority="high" decoding="async">'
    )
    new_block = block[: media.start()] + replacement + block[media.end() :]
    return doc[: hero.start()] + new_block + doc[hero.end() :], True


def apply_visual_target(doc: str, target: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    og_src = target["og_src"]
    hero_src = target["hero_src"]
    og_abs = absolute(og_src)
    old_og = get_meta(doc, "property", "og:image")

    if not local_asset_exists(og_src):
        raise RuntimeError(f"Missing target image: {og_src}")
    if not local_asset_exists(hero_src):
        raise RuntimeError(f"Missing target hero: {hero_src}")

    # Replace stale image references in the head first so existing JSON-LD stays aligned.
    if old_og and old_og != og_abs and "</head>" in doc:
        head, tail = doc.split("</head>", 1)
        head = head.replace(old_og, og_abs)
        doc = head + "</head>" + tail

    doc = set_meta(doc, "property", "og:image", og_abs)
    doc = set_meta(doc, "property", "og:image:type", "image/webp")
    doc = set_meta(doc, "property", "og:image:width", str(target["width"]))
    doc = set_meta(doc, "property", "og:image:height", str(target["height"]))
    doc = set_meta(doc, "property", "og:image:alt", target["alt"])
    doc = set_meta(doc, "name", "twitter:card", "summary_large_image")
    doc = set_meta(doc, "name", "twitter:image", og_abs)
    doc = set_meta(doc, "name", "twitter:image:alt", target["alt"])
    doc = update_jsonld_images(doc, og_abs, old_og)

    hero_width = int(target.get("hero_width", target["width"]))
    hero_height = int(target.get("hero_height", target["height"]))
    doc, hero_changed = replace_article_hero(doc, hero_src, target["alt"], hero_width, hero_height)
    reasons.append("aligned OG/Twitter/JSON-LD with a real floor-plan or unit-layout image")
    if hero_changed:
        reasons.append("replaced generic first hero image with search-intent visual")
    return doc, reasons


def apply_metadata_hygiene(doc: str) -> tuple[str, list[str]]:
    reasons: list[str] = []
    og = get_meta(doc, "property", "og:image")
    if not og:
        return doc, reasons

    fallback_alt = page_h1(doc) or page_title(doc) or "Lumi Hanoi"
    og_alt = get_meta(doc, "property", "og:image:alt")
    if not og_alt:
        doc = set_meta(doc, "property", "og:image:alt", fallback_alt)
        og_alt = fallback_alt
        reasons.append("added missing og:image:alt")

    if get_meta(doc, "name", "twitter:card") != "summary_large_image":
        doc = set_meta(doc, "name", "twitter:card", "summary_large_image")
        reasons.append("enabled large Twitter/social image card")
    if get_meta(doc, "name", "twitter:image") != og:
        doc = set_meta(doc, "name", "twitter:image", og)
        reasons.append("aligned twitter:image with og:image")
    if get_meta(doc, "name", "twitter:image:alt") != og_alt:
        doc = set_meta(doc, "name", "twitter:image:alt", og_alt)
        reasons.append("aligned twitter:image:alt")

    robots = get_meta(doc, "name", "robots")
    if robots and "noindex" not in robots.lower() and "max-image-preview:large" not in robots.lower():
        doc = set_meta(doc, "name", "robots", robots.rstrip(", ") + ",max-image-preview:large")
        reasons.append("enabled max-image-preview:large")
    return doc, reasons


def append_css() -> bool:
    path = ROOT / "assets/css/site.css"
    css = path.read_text(encoding="utf-8")
    marker = "/* SERP-INTENT-HERO:START */"
    if marker in css:
        return False
    css += """

/* SERP-INTENT-HERO:START */
/* Visual-intent SEO pages show a real plan/layout first instead of a generic render. */
.article-hero .serp-intent-hero{object-fit:contain;object-position:center;background:#f7f4ed;opacity:.44}
@media(max-width:700px){.article-hero .serp-intent-hero{object-fit:contain;opacity:.40}}
/* SERP-INTENT-HERO:END */
"""
    path.write_text(css, encoding="utf-8")
    return True


def main() -> None:
    changes = []
    scanned = 0
    for path in sorted(ROOT.rglob("*.html")):
        if any(part in {".git", "node_modules"} for part in path.parts):
            continue
        scanned += 1
        rel = str(path.relative_to(ROOT))
        original = path.read_text(encoding="utf-8")
        doc = original
        reasons: list[str] = []

        target = VISUAL_TARGETS.get(rel)
        if target:
            doc, visual_reasons = apply_visual_target(doc, target)
            reasons.extend(visual_reasons)

        doc, hygiene_reasons = apply_metadata_hygiene(doc)
        reasons.extend(hygiene_reasons)

        if doc != original:
            path.write_text(doc, encoding="utf-8")
            changes.append({"path": rel, "reasons": reasons})

    css_changed = append_css()
    print(json.dumps({
        "scanned_html": scanned,
        "changed_html": len(changes),
        "visual_targets": len(VISUAL_TARGETS),
        "css_changed": css_changed,
        "changes": changes,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
