#!/usr/bin/env python3
"""Build safe tower guides from the reviewed, group-level plan manifest."""
import json
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/floor-plans.json').read_text())
nav='<a href="/">Trang chủ</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a><a href="/lumi-signature/">Signature</a><a href="/lumi-prestige/">Prestige</a><a href="/lumi-elite/">Elite</a>'
def local(asset): return bool(asset and (ROOT/asset.lstrip('/')).is_file())
for phase in data['phases']:
 for tower in phase['towers']:
  groups=tower['groups']; complete=bool(groups) and all(local(g.get('asset')) for g in groups)
  cards=[]
  for group in groups:
   asset=group.get('asset'); figure=''
   if local(asset):
    alt=f"Mặt bằng {tower['label']} — {group['label']}"
    figure=f'<figure class="figure"><a href="{asset}" data-lightbox data-lightbox-alt="{escape(alt)}" data-lightbox-caption="{escape(alt)}"><img class="figure-image" src="{asset}" width="893" height="649" alt="{escape(alt)}" loading="lazy" decoding="async"></a><figcaption class="figure-caption">{escape(alt)}</figcaption></figure>'
   cards.append(f'<section class="floor-group"><h2>{escape(group["label"])}</h2>{figure}<p>Đối chiếu tệp nguồn: <strong>{escape(group["sourceFile"])}</strong>.</p></section>')
  if not cards: cards=['<p>Đối chiếu số tòa và tầng trong hồ sơ căn hộ trước khi sử dụng bản vẽ.</p>']
  robots='index,follow' if complete else 'noindex,follow'
  source=f"https://drive.google.com/drive/folders/{phase['trustedFloorPlanFolderId']}"
  slug=tower['slug']; label=escape(tower['label'])
  html=f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mặt bằng {label} | Lumi Hanoi</title><meta name="description" content="Nhóm tầng và hướng dẫn đối chiếu mặt bằng {label} tại Lumi Hanoi."><meta name="robots" content="{robots}"><link rel="canonical" href="https://lumi-hanoi.com/{slug}/"><link rel="stylesheet" href="/assets/css/site.css"><link rel="icon" href="/favicon.svg" type="image/svg+xml"></head><body><a class="skip-link" href="#main">Bỏ qua điều hướng</a><header class="site-header"><div class="container nav"><a class="brand" href="/"><span class="brand-mark">LH</span><span>LUMI HANOI</span></a><nav class="nav-links" aria-label="Điều hướng chính">{nav}</nav></div></header><main id="main"><div class="container breadcrumb"><a href="/">Trang chủ</a><span>/</span><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a><span>/</span>{label}</div><header class="article-hero"><div class="container"><p class="eyebrow">{escape(phase['name'])}</p><h1>Mặt bằng {label}</h1><p class="lead">Chọn đúng nhóm tầng trước khi đối chiếu mã căn, lõi thang, hướng và layout căn hộ.</p></div></header><div class="container article-layout"><article class="article">{''.join(cards)}<h2>Cách dùng tài liệu</h2><ol><li>Chốt tòa và tầng trên hồ sơ căn hộ.</li><li>Mở đúng nhóm tầng; không dùng tầng điển hình cho tầng chuyển tiếp.</li><li>Ghép mã căn với layout cùng mã và phiên bản.</li><li>Đọc riêng NFA/DTSD và GFA/DTXD.</li></ol><h2>Nguồn mặt bằng</h2><p>Đối chiếu tại <a href="{source}" rel="noopener noreferrer">thư mục mặt bằng {escape(phase['name'])}</a>. Phụ lục của căn hộ là căn cứ cuối cùng.</p><p><a class="button" href="/mat-bang-lumi-hanoi/">Trở lại trung tâm mặt bằng</a></p></article></div></main><footer class="site-footer"><div class="container"><p>Website thông tin độc lập, không phải website chính thức của CapitaLand Development.</p></div></footer><script src="/assets/js/site.js" defer></script></body></html>'''
  out=ROOT/slug/'index.html'; out.parent.mkdir(exist_ok=True); out.write_text(html)
