#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://lumi-hanoi.com"
SITE_HOSTS = {"lumi-hanoi.com", "www.lumi-hanoi.com"}
TOWER_PAGES = {
    "mat-bang-lumi-hanoi/lumi-signature/s1/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s2/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s3/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s5/index.html",
    "mat-bang-lumi-hanoi/lumi-signature/s6/index.html",
    "mat-bang-lumi-hanoi/lumi-prestige/p1/index.html",
    "mat-bang-lumi-hanoi/lumi-prestige/p2/index.html",
    "mat-bang-lumi-hanoi/lumi-elite/e1/index.html",
    "mat-bang-lumi-hanoi/lumi-elite/e2/index.html",
}
VISUAL_TARGETS = {
    "mat-bang-lumi-hanoi/lumi-signature/index.html": "/assets/media/signature/floor-plans/signature-floorplan-overview-1200x630.webp",
    "mat-bang-lumi-hanoi/lumi-prestige/index.html": "/assets/media/prestige/floor-plans/prestige-floorplan-overview-1200x630.webp",
    "mat-bang-lumi-hanoi/lumi-elite/index.html": "/assets/media/elite/floor-plans/elite-floorplan-overview-1200x630.webp",
    "layout-can-ho-lumi-signature/index.html": "/assets/media/signature/unit-layouts/signature-s1-s5-1br-a1.webp",
    "layout-can-ho-lumi-prestige/index.html": "/assets/media/prestige/unit-layouts/prestige-layout-22-1br-medium.webp",
    "tin-tuc/cach-doc-mat-bang-lumi-hanoi/index.html": "/assets/media/masterplan/lumi-hanoi-mat-bang-tong-the-og-1200x630.webp",
    "tin-tuc/so-sanh-mat-bang-s1-s2-s3-s5-s6-lumi-signature/index.html": "/assets/media/signature/penthouse/s1-floor-35.webp",
    "tin-tuc/layout-can-ho-lumi-signature-1pn-2pn-3pn-duplex/index.html": "/assets/media/signature/unit-layouts/signature-s1-s5-1br-a1.webp",
}
VISUAL_HERO_TARGETS = {
    **{k: v for k, v in VISUAL_TARGETS.items()},
    "tin-tuc/cach-doc-mat-bang-lumi-hanoi/index.html": "/assets/media/masterplan/lumi-hanoi-masterplan-1280.webp",
}
PHASE_CARD_EXPECTATIONS = {
    "mat-bang-lumi-hanoi/lumi-signature/index.html": {
        "S1": "/assets/media/signature/floor-plans/s1-typical.webp",
        "S2": "/assets/media/signature/floor-plans/s2-typical.webp",
        "S3": "/assets/media/signature/floor-plans/s3-typical.webp",
        "S5": "/assets/media/signature/floor-plans/s5-typical.webp",
        "S6": "/assets/media/signature/floor-plans/s6-typical.webp",
    },
    "mat-bang-lumi-hanoi/lumi-prestige/index.html": {
        "P1": "/assets/media/prestige/floor-plans/p1-t02-19-21-22-24-28.webp",
        "P2": "/assets/media/prestige/floor-plans/p2-t02-12-14-19-21-28.webp",
    },
    "mat-bang-lumi-hanoi/lumi-elite/index.html": {
        "E1": "/assets/media/elite/floor-plans/e1-typical.webp",
        "E2": "/assets/media/elite/floor-plans/e2-typical.webp",
    },
}
GENERIC_VISUAL_TOKENS = ("landscape", "streetscape", "lumi-hanoi-og", "-hero-")


def attr(tag: str, name: str) -> str | None:
    m = re.search(rf'\b{re.escape(name)}\s*=\s*(["\'])(.*?)\1', tag, re.I | re.S)
    return html.unescape(m.group(2)) if m else None


def meta(doc: str, selector: str, key: str) -> str | None:
    for m in re.finditer(r'<meta\b[^>]*>', doc, re.I):
        tag = m.group(0)
        if attr(tag, selector) == key:
            return attr(tag, 'content')
    return None


def title(doc: str) -> str:
    m = re.search(r'<title>(.*?)</title>', doc, re.I | re.S)
    return re.sub(r'<[^>]+>', '', html.unescape(m.group(1))).strip() if m else ''


def local_asset(url: str) -> Path | None:
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc not in SITE_HOSTS:
        return None
    return ROOT / parsed.path.lstrip('/')


def local_src(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc not in SITE_HOSTS:
        return None
    return parsed.path if parsed.path.startswith('/') else '/' + parsed.path


def primary_floorplan(doc: str) -> str | None:
    section = re.search(r'<section\b[^>]*data-primary-floor-plan[^>]*>.*?</section>', doc, re.I | re.S)
    if not section:
        return None
    image = re.search(r'<img\b[^>]*class="[^"]*floor-plan-image[^"]*"[^>]*>', section.group(0), re.I)
    return attr(image.group(0), 'src') if image else None


def hero_media(doc: str) -> str | None:
    hero = re.search(r'<header\b[^>]*class="[^"]*article-hero[^"]*"[^>]*>.*?</header>', doc, re.I | re.S)
    if not hero:
        return None
    image = re.search(r'<img\b[^>]*class="[^"]*article-hero-media[^"]*"[^>]*>', hero.group(0), re.I)
    return attr(image.group(0), 'src') if image else None


def visual_intent(page_title: str) -> bool:
    lowered = page_title.lower()
    if 'đã chuyển' in lowered or 'chuyển trang' in lowered:
        return False
    return 'mặt bằng' in lowered or 'layout' in lowered


def main() -> None:
    warnings: list[dict] = []
    errors: list[str] = []
    scanned = 0
    indexable = 0
    visual_pages = 0

    for path in sorted(ROOT.rglob('*.html')):
        if any(part in {'.git', 'node_modules'} for part in path.parts):
            continue
        scanned += 1
        rel = str(path.relative_to(ROOT))
        doc = path.read_text(encoding='utf-8')
        robots = (meta(doc, 'name', 'robots') or '').lower()
        if 'noindex' in robots:
            continue
        indexable += 1
        page_title = title(doc)
        og = meta(doc, 'property', 'og:image')
        twitter = meta(doc, 'name', 'twitter:image')
        og_alt = meta(doc, 'property', 'og:image:alt')
        twitter_alt = meta(doc, 'name', 'twitter:image:alt')

        page_issues = []
        if not og:
            page_issues.append('missing og:image')
        else:
            asset = local_asset(og)
            if asset is not None and not asset.is_file():
                page_issues.append(f'og:image asset missing: {asset.relative_to(ROOT)}')
            if twitter != og:
                page_issues.append('twitter:image missing or differs from og:image')
            if not og_alt:
                page_issues.append('missing og:image:alt')
            if not twitter_alt:
                page_issues.append('missing twitter:image:alt')
        if robots and 'index' in robots and 'max-image-preview:large' not in robots:
            page_issues.append('missing max-image-preview:large')
        if page_issues:
            warnings.append({'path': rel, 'title': page_title, 'issues': page_issues})

        if visual_intent(page_title):
            visual_pages += 1
            if not og:
                errors.append(f'{rel}: visual-intent page has no og:image')
            elif any(token in og.lower() for token in GENERIC_VISUAL_TOKENS):
                errors.append(f'{rel}: visual-intent page still uses generic image {og}')

        if rel in TOWER_PAGES:
            primary = primary_floorplan(doc)
            expected_src = primary or local_src(og)
            hero = hero_media(doc)
            expected = f'{SITE}{expected_src}' if expected_src else None
            if not expected_src:
                errors.append(f'{rel}: no verified local floor-plan image')
            elif not (ROOT / expected_src.lstrip('/')).is_file():
                errors.append(f'{rel}: expected floor-plan asset is not local')
            if expected and og != expected:
                errors.append(f'{rel}: og:image does not equal verified floor plan')
            if expected and twitter != expected:
                errors.append(f'{rel}: twitter:image does not equal verified floor plan')
            if expected_src and hero != expected_src:
                errors.append(f'{rel}: first tower hero image does not equal verified floor plan')
            if expected and expected not in doc.split('</head>', 1)[0]:
                errors.append(f'{rel}: verified floor-plan image is absent from head/schema')
            if 'max-image-preview:large' not in robots:
                errors.append(f'{rel}: large image preview is not enabled')

        if rel in VISUAL_TARGETS:
            expected_src = VISUAL_TARGETS[rel]
            expected = SITE + expected_src
            expected_hero = VISUAL_HERO_TARGETS[rel]
            hero = hero_media(doc)
            if not (ROOT / expected_src.lstrip('/')).is_file():
                errors.append(f'{rel}: configured OG asset is missing')
            if not (ROOT / expected_hero.lstrip('/')).is_file():
                errors.append(f'{rel}: configured hero asset is missing')
            if og != expected:
                errors.append(f'{rel}: og:image is not the configured intent image')
            if twitter != expected:
                errors.append(f'{rel}: twitter:image is not the configured intent image')
            if hero != expected_hero:
                errors.append(f'{rel}: first hero image is not the configured intent image')
            if not og_alt:
                errors.append(f'{rel}: intent image is missing og:image:alt')

        if rel in PHASE_CARD_EXPECTATIONS:
            if 'max-image-preview:large' not in robots:
                errors.append(f'{rel}: phase landing does not enable large image previews')
            for tower, expected_src in PHASE_CARD_EXPECTATIONS[rel].items():
                if not (ROOT / expected_src.lstrip('/')).is_file():
                    errors.append(f'{rel}: local card asset missing for {tower}: {expected_src}')
                if f'src="{expected_src}"' not in doc:
                    errors.append(f'{rel}: tower card {tower} does not use its representative local floor plan')
                if f'/{tower.lower()}/' not in doc:
                    errors.append(f'{rel}: tower card/link missing for {tower}')

    print(json.dumps({
        'scanned_html': scanned,
        'indexable_html': indexable,
        'visual_intent_pages': visual_pages,
        'warning_pages': len(warnings),
        'warnings': warnings,
        'strict_errors': errors,
    }, ensure_ascii=False, indent=2))

    if errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
