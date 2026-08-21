#!/usr/bin/env python3
"""V5.2 regression checks for the floor-plan information architecture."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "data/floor-plans.json").read_text())
errors=[]
expected_folders={"Signature":"176CFkgekR1kcRxWGQF3XtkzkAOG_oG9C","Prestige":"1woZm0pruDuANNlPXmoNulP4lbvv-VKHm","Elite":"1atZNW5JhRQyM9j0LRBac3HePP371KAU7"}
expected_slugs={"toa-s1-lumi-hanoi","toa-s2-lumi-hanoi","toa-s3-lumi-hanoi","toa-s5-lumi-hanoi","toa-s6-lumi-hanoi","toa-p1-lumi-hanoi","toa-p2-lumi-hanoi","toa-elite-1-lumi-hanoi","toa-elite-2-lumi-hanoi"}
seen=set()
for phase in data["phases"]:
    if phase.get("trustedFolderId") != expected_folders.get(phase["name"]): errors.append(f"wrong trusted folder: {phase['name']}")
    for tower in phase["towers"]:
        slug=tower["slug"]; seen.add(slug)
        page=ROOT/slug/"index.html"
        if not page.is_file(): errors.append(f"missing root tower page: /{slug}/"); continue
        html=page.read_text()
        if f'https://lumi-hanoi.com/{slug}/' not in html: errors.append(f"bad canonical: {slug}")
        if not tower.get("groups"): errors.append(f"missing floor groups: {slug}")
        for group in tower.get("groups",[]):
            if group not in html: errors.append(f"group not rendered: {slug}: {group}")
        media=tower.get("media"); local=bool(media and (ROOT/media.lstrip('/')).is_file())
        indexed='name="robots" content="index,follow"' in html
        if indexed != local: errors.append(f"media/indexability gate failed: {slug}")
if seen != expected_slugs: errors.append(f"tower set mismatch: {seen ^ expected_slugs}")
public='\n'.join(p.read_text(errors='ignore') for p in ROOT.rglob('*.html'))
for phrase in ("Drive inaccessible","Codex sandbox","sandbox 403"):
    if phrase.lower() in public.lower(): errors.append(f"public infrastructure notice: {phrase}")
hub=(ROOT/'mat-bang-lumi-hanoi/index.html').read_text()
for token in ("Cách đọc mặt bằng từ tổng thể đến căn hộ","Chọn đúng nhóm tầng","NFA/DTSD","GFA/DTXD"):
    if token not in hub: errors.append(f"hub reading guide missing: {token}")
if errors:
    print("V5.2 QA FAILED\n- " + "\n- ".join(errors)); sys.exit(1)
print(f"V5.2 QA passed: {len(seen)} root tower pages; source mapping, floor groups, public-copy and media gates verified.")
