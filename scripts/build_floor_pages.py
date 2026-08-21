#!/usr/bin/env python3
"""Build tower guides from the reviewed floor-plan manifest."""
import json
from pathlib import Path
from html import escape
ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "data/floor-plans.json").read_text())
nav = '<a href="/">Trang chủ</a><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a><a href="/lumi-signature/">Signature</a><a href="/lumi-prestige/">Prestige</a><a href="/lumi-elite/">Elite</a>'
for phase in data["phases"]:
    for tower in phase["towers"]:
        media = tower.get("media")
        # A locally reviewed plan is a hard publishing gate, not an optional enhancement.
        robots = "index,follow" if media and (ROOT / media.lstrip("/")).is_file() else "noindex,follow"
        groups = "".join(f"<li>{escape(group)}</li>" for group in tower["groups"])
        figure = ""
        if media:
            figure = f'''<figure class="figure"><a href="{media}" data-lightbox data-lightbox-alt="Mặt bằng {escape(tower['label'])}" data-lightbox-caption="Mặt bằng nguồn đã kiểm duyệt — mở ảnh lớn để đọc ký hiệu."><img class="figure-image" src="{media}" width="893" height="649" alt="Mặt bằng {escape(tower['label'])}" decoding="async"></a><figcaption class="figure-caption">Mặt bằng nguồn đã kiểm duyệt — mở ảnh lớn để đọc ký hiệu.</figcaption></figure>'''
        source = f"https://drive.google.com/drive/folders/{phase['trustedFolderId']}"
        html = f'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mặt bằng {escape(tower['label'])} | Lumi Hanoi</title><meta name="description" content="Nhóm tầng và hướng dẫn đối chiếu mặt bằng {escape(tower['label'])} tại Lumi Hanoi."><meta name="robots" content="{robots}">
<link rel="canonical" href="https://lumi-hanoi.com/{tower['slug']}/"><link rel="stylesheet" href="/assets/css/site.css"><link rel="icon" href="/favicon.svg" type="image/svg+xml"></head>
<body><a class="skip-link" href="#main">Bỏ qua điều hướng</a><header class="site-header"><div class="container nav"><a class="brand" href="/"><span class="brand-mark">LH</span><span>LUMI HANOI</span></a><nav class="nav-links" aria-label="Điều hướng chính">{nav}</nav></div></header>
<main id="main"><div class="container breadcrumb"><a href="/">Trang chủ</a><span>/</span><a href="/mat-bang-lumi-hanoi/">Mặt bằng</a><span>/</span>{escape(tower['label'])}</div><header class="article-hero"><div class="container"><p class="eyebrow">{escape(phase['name'])}</p><h1>Mặt bằng {escape(tower['label'])}</h1><p class="lead">Chọn đúng nhóm tầng trước khi đối chiếu mã căn, lõi thang, hướng và layout căn hộ.</p></div></header><div class="container article-layout"><article class="article">{figure}<h2>Các nhóm mặt bằng cần đối chiếu</h2><ul>{groups}</ul><h2>Cách dùng tài liệu</h2><ol><li>Chốt tòa và tầng trên hồ sơ căn hộ.</li><li>Mở đúng nhóm tầng; không dùng một tầng điển hình cho tầng chuyển tiếp.</li><li>Ghép mã căn trên tầng với layout cùng mã và phiên bản.</li><li>Đọc riêng NFA/DTSD và GFA/DTXD; ưu tiên phụ lục hợp đồng.</li></ol><h2>Nguồn mặt bằng</h2><p>Danh mục được đối chiếu từ <a href="{source}" rel="noopener noreferrer">thư mục mặt bằng {escape(phase['name'])}</a> do dự án cung cấp. Bản vẽ áp dụng cho căn cụ thể và phụ lục hợp đồng luôn là căn cứ cuối cùng.</p><p><a class="button" href="/mat-bang-lumi-hanoi/">Trở lại trung tâm mặt bằng</a></p></article></div></main><footer class="site-footer"><div class="container"><p>Website thông tin độc lập, không phải website chính thức của CapitaLand Development.</p></div></footer><script src="/assets/js/site.js" defer></script></body></html>'''
        out = ROOT / tower["slug"] / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(html)
