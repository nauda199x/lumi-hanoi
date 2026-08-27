#!/usr/bin/env python3
"""Static acceptance checks for Prestige floor plans on the canonical nested tower pages."""
from __future__ import annotations
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets/media/prestige/manifest.v8.json"
FLOOR_DATA = ROOT / "assets/data/floor-plans.json"
EXPECTED = {
    "11jadUR3YF3cIZd1MQ5Eg2tm5MQ_45PRF": ("P1", "Tầng 2–19, 21–22, 24–28", "assets/media/prestige/floor-plans/p1-t02-19-21-22-24-28.webp", "mat-bang-lumi-hanoi/lumi-prestige/p1/index.html", "p1-tang-2-19-21-22-24-28", 2400, 3200),
    "1ky6AoU-RKfkQQfPggTiTcfD286hP9c1-": ("P1", "Tầng 20", "assets/media/prestige/floor-plans/p1-t20.webp", "mat-bang-lumi-hanoi/lumi-prestige/p1/index.html", "p1-tang-20", 2400, 3200),
    "1EriYOtwKs3pD7ETAo_o8BnuNbvZrBaF5": ("P1", "Tầng 23", "assets/media/prestige/floor-plans/p1-t23.webp", "mat-bang-lumi-hanoi/lumi-prestige/p1/index.html", "p1-tang-23", 2400, 3200),
    "1vHglsZVk2aqp_t6aKvml1xQo17wQN9WR": ("P1", "Tầng 29", "assets/media/prestige/floor-plans/p1-t29.webp", "mat-bang-lumi-hanoi/lumi-prestige/p1/index.html", "p1-tang-29", 2400, 3200),
    "1k_KbeRS92wbVOTF4_XKh18D1kb-CareO": ("P2", "Tầng 2–12, 14–19, 21–28", "assets/media/prestige/floor-plans/p2-t02-12-14-19-21-28.webp", "mat-bang-lumi-hanoi/lumi-prestige/p2/index.html", "p2-tang-2-12-14-19-21-28", 2400, 3201),
    "1DGpCt-vZmqeokHQseBvivHTaOKKkWXRI": ("P2", "Tầng 13", "assets/media/prestige/floor-plans/p2-t13.webp", "mat-bang-lumi-hanoi/lumi-prestige/p2/index.html", "p2-tang-13", 2400, 3200),
    "11h2HZD-WUqcgPVdMh0gkxK95wjF9_T49": ("P2", "Tầng 20", "assets/media/prestige/floor-plans/p2-t20.webp", "mat-bang-lumi-hanoi/lumi-prestige/p2/index.html", "p2-tang-20", 2400, 3200),
    "13cMmDd-E23cakiNCzh68Lr8MmK_wRyRy": ("P2", "Tầng 29", "assets/media/prestige/floor-plans/p2-t29.webp", "mat-bang-lumi-hanoi/lumi-prestige/p2/index.html", "p2-tang-29", 2400, 3200),
}

def fail(message):
    print("FAIL:", message, file=sys.stderr)
    raise SystemExit(1)

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
assets = manifest.get("assets", [])
actual = {
    item["source"]["drive_file_id"]: (
        item["tower"], item["floor_group"], item["local_file"], item["rendered_page"],
        item["anchor"], item["width"], item["height"]
    )
    for item in assets
}
if manifest.get("version") != "8.1A" or len(assets) != 8 or actual != EXPECTED:
    fail("manifest must map the eight authoritative Prestige drawings to the canonical nested pages")
if len({hashlib.sha256((ROOT / item["local_file"]).read_bytes()).hexdigest() for item in assets}) != 8:
    fail("eight local derivatives must have distinct contents")

floor_data = json.loads(FLOOR_DATA.read_text(encoding="utf-8"))["towers"]
for drive_id, (tower, label, local, page, anchor, width, height) in EXPECTED.items():
    matches = [
        plan for plan in floor_data[tower]["plans"]
        if plan.get("driveId") == drive_id
    ]
    if len(matches) != 1:
        fail(f"{tower}: Drive ID must occur exactly once: {drive_id}")
    plan = matches[0]
    if (plan.get("label"), plan.get("anchor"), plan.get("asset")) != (label, anchor, "/" + local):
        fail(f"{tower}: floor-plan data mismatch for {drive_id}")
    if not (ROOT / local).is_file():
        fail("missing local derivative: " + local)

for tower in ("P1", "P2"):
    page = f"mat-bang-lumi-hanoi/lumi-prestige/{tower.lower()}/index.html"
    html = (ROOT / page).read_text(encoding="utf-8")
    canonical = f"https://lumi-hanoi.com/mat-bang-lumi-hanoi/lumi-prestige/{tower.lower()}/"
    if f'<link rel="canonical" href="{canonical}">' not in html:
        fail("canonical mismatch on " + page)
    if f"<h1>Mặt bằng tòa {tower} Lumi Hanoi</h1>" not in html:
        fail("H1 mismatch on " + page)
    if f'data-tower="{tower}"' not in html or "/assets/js/floor-plan-tower.js" not in html:
        fail("floor-plan renderer wiring missing on " + page)
    for drive_id, (item_tower, label, local, rendered_page, anchor, width, height) in EXPECTED.items():
        if item_tower == tower and (label not in html or f'href="#{anchor}"' not in html):
            fail(f"{page}: missing pre-rendered floor label/anchor for {drive_id}")

overview = (ROOT / "lumi-prestige/index.html").read_text(encoding="utf-8")
for tower in ("p1", "p2"):
    if f"/mat-bang-lumi-hanoi/lumi-prestige/{tower}/" not in overview:
        fail("Prestige overview must link canonical " + tower.upper() + " page")
if "/toa-prestige-" in overview or "/toa-p1-" in overview or "/toa-p2-" in overview:
    fail("Prestige overview still links a legacy tower URL")

print("PASS: eight authoritative Prestige drawings map to canonical P1/P2 pages and pre-rendered floor anchors")
