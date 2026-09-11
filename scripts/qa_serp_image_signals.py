#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
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


def attr(tag: str, name: str) -> str | None:
    m = re.search(rf'\b{re.escape(name)}="([^"]*)"', tag, re.I)
    return html.unescape(m.group(1)) if m else None


def meta(doc: str, selector: str, key: str) -> str | None:
    m = re.search(rf'<meta\b(?=[^>]*\b{selector}="{re.escape(key)}")[^>]*>', doc, re.I)
    return attr(m.group(0), "content") if m else None


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
    hero = re.search(r'<header class="article-hero tower-hero">.*?</header>', doc, re.I | re.S)
    if not hero:
        return None
    image = re.search(r'<img\b[^>]*class="[^"]*article-hero-media[^"]*"[^>]*>', hero.group(0), re.I)
    return attr(image.group(0), 'src') if image else None


def main() -> None:
    warnings: list[dict] = []
    errors: list[str] = []
    scanned = 0
    indexable = 0

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

        page_issues = []
        if not og:
            page_issues.append('missing og:image')
        else:
            asset = local_asset(og)
            if asset is not None and not asset.is_file():
                page_issues.append(f'og:image asset missing: {asset.relative_to(ROOT)}')
            if twitter and twitter != og:
                page_issues.append('twitter:image differs from og:image')
            if not og_alt:
                page_issues.append('missing og:image:alt')
        if robots and 'index' in robots and 'max-image-preview:large' not in robots:
            page_issues.append('missing max-image-preview:large')
        if page_issues:
            warnings.append({'path': rel, 'title': page_title, 'issues': page_issues})

        if rel in TOWER_PAGES:
            primary = primary_floorplan(doc)
            # Elite pages predate the explicit data-primary marker. Their verified
            # local OG/schema image is the canonical floor-plan image to align to.
            expected_src = primary or local_src(og)
            hero = hero_media(doc)
            expected = f'https://lumi-hanoi.com{expected_src}' if expected_src else None
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

    print(json.dumps({
        'scanned_html': scanned,
        'indexable_html': indexable,
        'warning_pages': len(warnings),
        'warnings': warnings,
        'strict_errors': errors,
    }, ensure_ascii=False, indent=2))

    if errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
