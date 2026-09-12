#!/usr/bin/env python3
from __future__ import annotations

import html
import re

import prioritize_floorplan_serp_images_v2 as base


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

    new_section = base.representative_section(tower, chosen)
    primary_pattern = re.compile(
        r'<section\b(?=[^>]*class="[^"]*floor-plan-primary[^"]*")[^>]*>.*?</section>',
        re.I | re.S,
    )
    if primary_pattern.search(doc):
        return primary_pattern.sub(new_section, doc, count=1)

    selected_pattern = re.compile(
        rf'<section\b[^>]*id="{re.escape(chosen["anchor"])}"[^>]*>.*?</section>',
        re.I | re.S,
    )
    if not selected_pattern.search(doc):
        raise RuntimeError(f"{tower}: representative floor section missing")
    return selected_pattern.sub(new_section, doc, count=1)


base.patch_tower_body = patch_tower_body

if __name__ == "__main__":
    base.main()
