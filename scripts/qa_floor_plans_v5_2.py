#!/usr/bin/env python3
"""V5.2 regression checks: group-level provenance, media and indexing safety."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/floor-plans.json').read_text())
errors=[]
folders={'Signature':'176CFkgekR1kcRxWGQF3XtkzkAOG_oG9C','Prestige':'1woZm0pruDuANNlPXmoNulP4lbvv-VKHm','Elite':'1atZNW5JhRQyM9j0LRBac3HePP371KAU7'}
slugs={'toa-s1-lumi-hanoi','toa-s2-lumi-hanoi','toa-s3-lumi-hanoi','toa-s5-lumi-hanoi','toa-s6-lumi-hanoi','toa-p1-lumi-hanoi','toa-p2-lumi-hanoi','toa-elite-1-lumi-hanoi','toa-elite-2-lumi-hanoi'}
seen=set(); indexed=set()
for phase in data['phases']:
 if phase.get('trustedFloorPlanFolderId') != folders.get(phase['name']): errors.append(f"wrong floor-plan folder: {phase['name']}")
 for tower in phase['towers']:
  slug=tower['slug']; seen.add(slug); page=ROOT/slug/'index.html'
  if not page.is_file(): errors.append(f"missing root page: /{slug}/"); continue
  html=page.read_text(); groups=tower.get('groups',[])
  complete=bool(groups)
  for group in groups:
   for key in ('label','sourceFile','asset'):
    if key not in group: errors.append(f"group field {key} missing: {slug}")
   if group.get('label') not in html or group.get('sourceFile') not in html: errors.append(f"group not rendered: {slug}: {group.get('label')}")
   asset=group.get('asset'); valid=bool(asset and (ROOT/asset.lstrip('/')).is_file())
   complete &= valid
   if valid and asset not in html: errors.append(f"mapped asset not rendered: {slug}: {asset}")
  is_indexed='name="robots" content="index,follow"' in html
  if is_indexed: indexed.add(slug)
  if is_indexed != complete: errors.append(f"whole-inventory media gate failed: {slug}")
  if f'https://lumi-hanoi.com/{slug}/' not in html: errors.append(f"canonical mismatch: {slug}")
if seen != slugs: errors.append(f"tower URL set mismatch: {seen ^ slugs}")
public='\n'.join(p.read_text(errors='ignore') for p in ROOT.rglob('*.html'))
for phrase in ('Drive inaccessible','Codex sandbox','sandbox 403'):
 if phrase.casefold() in public.casefold(): errors.append(f"public infrastructure notice: {phrase}")
sitemap=(ROOT/'sitemap.xml').read_text()
for slug in slugs:
 present=f'https://lumi-hanoi.com/{slug}/' in sitemap
 if present != (slug in indexed): errors.append(f"sitemap/index mismatch: {slug}")
for token in ('Cách đọc mặt bằng từ tổng thể đến căn hộ','Chọn đúng nhóm tầng','NFA/DTSD','GFA/DTXD'):
 if token not in (ROOT/'mat-bang-lumi-hanoi/index.html').read_text(): errors.append(f"hub guide missing: {token}")
if errors: print('V5.2 QA FAILED\n- '+'\n- '.join(errors)); sys.exit(1)
print(f'V5.2 QA passed: {len(seen)} exact root URLs; every group mapping, source, media gate and sitemap state verified ({len(indexed)} complete).')
