#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'assets/data/visual-library-v8.7.json').read_text(encoding='utf-8'))
ASSETS = DATA['assets']


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding='utf-8')


def dimensions(asset: dict) -> tuple[int, int]:
    with Image.open(ROOT / asset['localFile']) as image:
        return image.width, image.height


def figure(asset: dict) -> str:
    w, h = dimensions(asset)
    local = '/' + asset['localFile']
    source = f"https://drive.google.com/file/d/{asset['driveId']}/view"
    return (
        '<figure class="figure">'
        f'<a href="{local}" data-lightbox data-lightbox-alt="{asset["alt"]}" '
        f'data-lightbox-caption="{asset["label"]} — phối cảnh 3D từ bộ tài liệu nguồn.">'
        f'<img class="figure-image" src="{local}" width="{w}" height="{h}" alt="{asset["alt"]}" loading="lazy" decoding="async"></a>'
        f'<figcaption class="figure-caption">{asset["label"]}'
        f'<span class="figure-source">Nguồn: <a href="{source}" rel="noopener noreferrer">{asset["sourceName"]}</a></span>'
        '</figcaption></figure>'
    )


def gallery(items: list[dict], feature: bool = True) -> str:
    cls = 'media-gallery media-gallery-feature' if feature else 'media-gallery'
    return f'<div class="{cls}">' + ''.join(figure(item) for item in items) + '</div>'


def insert_before_article_end(path: str, marker: str, block: str) -> None:
    html = read(path)
    if marker in html:
        return
    if '</article>' not in html:
        raise SystemExit(f'{path}: missing </article>')
    html = html.replace('</article>', block + '\n</article>', 1)
    html = re.sub(r'"dateModified":"2026-08-\d{2}"', '"dateModified":"2026-08-23"', html, count=1)
    write(path, html)


signature = [a for a in ASSETS if a['phase'] == 'signature']
sig_generic = [a for a in signature if a['scope'] == 'indoor']
sig_tower = {a['tower']: a for a in signature if a['scope'] == 'tower'}

# Signature visual library: 13 existing outdoor + 8 local indoor = 21 curated views.
path = 'phoi-canh-lumi-signature/index.html'
html = read(path)
if 'signature-indoor-v8-7' not in html:
    html = html.replace('Phối cảnh 3D Lumi Signature: 13 hình tiện ích chọn lọc', 'Phối cảnh 3D Lumi Signature: 21 hình trong nhà & ngoài trời')
    html = html.replace('Thư viện 13 phối cảnh 3D Lumi Signature chọn lọc từ bộ tài liệu nguồn: cảnh quan, phố thương mại, Sole, bể bơi, sân chơi, thể thao, skywalk và hầm xe.', 'Thư viện 21 phối cảnh 3D Lumi Signature chọn lọc từ bộ tài liệu nguồn: cảnh quan, tiện ích ngoài trời, đại sảnh, coworking, gym, yoga, phòng tiệc và phòng chiếu phim.')
    html = html.replace('13 hình được chọn từ đúng thư mục nguồn Outdoor Facilities để xem nhanh cảnh quan, tiện ích và trải nghiệm không gian của Signature.', '21 hình chọn lọc từ hai thư mục Outdoor Facilities và Indoor Facilities để xem đồng thời cảnh quan, tiện ích và không gian trong nhà của Signature.')
    block = '''
<section id="signature-indoor-v8-7" aria-labelledby="signature-indoor-title">
  <p class="eyebrow">Indoor Facilities · nguồn Drive</p>
  <h2 id="signature-indoor-title">Không gian trong nhà Lumi Signature</h2>
  <p>Bộ Indoor Facilities bổ sung phần mà thư viện trước đây còn thiếu: đại sảnh theo tòa, không gian làm việc, vận động và sinh hoạt cộng đồng. Ảnh đã được chuyển sang WebP local để tải nhanh hơn; liên kết nguồn Drive gốc vẫn được giữ trong từng chú thích.</p>
''' + gallery(signature) + '''
  <p class="notice"><strong>Lưu ý:</strong> đây là phối cảnh thiết kế, không phải ảnh hiện trạng hay bằng chứng rằng một tiện ích đã vận hành. Tên tòa chỉ được gắn khi chính tên tệp nguồn xác định S1, S2 hoặc S3.</p>
</section>
'''
    html = html.replace('</article>', block + '\n</article>', 1)
    html = re.sub(r'"dateModified":"2026-08-\d{2}"', '"dateModified":"2026-08-23"', html, count=1)
    write(path, html)

# Signature phase overview: generic indoor experiences, not tower-specific lobby claims.
sig_phase_block = '''
<section id="signature-indoor-preview-v8-7" aria-labelledby="signature-indoor-preview-title">
  <h2 id="signature-indoor-preview-title">Tiện ích trong nhà Signature qua phối cảnh nguồn</h2>
  <p>Ngoài cảnh quan ngoài trời, bộ tài liệu Signature còn có các không gian trong nhà phục vụ giải trí, làm việc, vận động và gặp gỡ cư dân. Các ảnh dưới đây được chọn theo tên tệp nguồn rõ ràng và đã tối ưu WebP local.</p>
''' + gallery(sig_generic) + '''
  <p><a class="btn" href="/phoi-canh-lumi-signature/#signature-indoor-v8-7">Xem đầy đủ phối cảnh trong nhà Signature</a></p>
</section>
'''
insert_before_article_end('lumi-signature/index.html', 'signature-indoor-preview-v8-7', sig_phase_block)

for tower, slug in [('S1','toa-signature-1-lumi-hanoi/index.html'), ('S2','toa-signature-2-lumi-hanoi/index.html'), ('S3','toa-signature-3-lumi-hanoi/index.html')]:
    asset = sig_tower[tower]
    block = f'''
<section id="{tower.lower()}-lobby-v8-7" aria-labelledby="{tower.lower()}-lobby-title">
  <h2 id="{tower.lower()}-lobby-title">Phối cảnh đại sảnh {tower}</h2>
  <p>Tên tệp nguồn xác định trực tiếp đây là đại sảnh {tower}; ảnh được dùng để hình dung ngôn ngữ thiết kế, không thay cho hiện trạng bàn giao.</p>
  {gallery([asset])}
</section>
'''
    insert_before_article_end(slug, f'{tower.lower()}-lobby-v8-7', block)

elite = [a for a in ASSETS if a['phase'] == 'elite']
e1 = [a for a in elite if a.get('tower') == 'E1']
e2 = [a for a in elite if a.get('tower') == 'E2']
elite_outdoor = [a for a in elite if a['scope'] == 'outdoor']

elite_phase_block = '''
<section id="elite-visual-library-v8-7" aria-labelledby="elite-visual-library-title">
  <p class="eyebrow">Visual library · nguồn Drive</p>
  <h2 id="elite-visual-library-title">Không gian E1, E2 và Vườn Stella</h2>
  <p>Kho phối cảnh Elite có đủ dữ liệu để phân biệt trải nghiệm từng tòa thay vì chỉ dùng vài ảnh đại diện. Bộ chọn dưới đây ưu tiên các tệp có tên không gian và tòa rõ ràng.</p>
  <h3>Elite 1</h3>
''' + gallery(e1) + '''
  <h3>Elite 2</h3>
''' + gallery(e2) + '''
  <h3>Cảnh quan Stella</h3>
''' + gallery(elite_outdoor) + '''
  <p class="notice"><strong>Phối cảnh thiết kế:</strong> các hình mô tả ý tưởng không gian tại thời điểm tài liệu được phát hành; trạng thái hoàn thiện và vận hành cần kiểm tra bằng tài liệu/hiện trạng mới nhất.</p>
</section>
'''
insert_before_article_end('lumi-elite/index.html', 'elite-visual-library-v8-7', elite_phase_block)

e1_block = '''
<section id="elite-e1-visual-v8-7" aria-labelledby="elite-e1-visual-title">
  <h2 id="elite-e1-visual-title">Không gian riêng được gắn nguồn Elite 1</h2>
  <p>Ba phối cảnh dưới đây có tên tệp gắn trực tiếp với E1: sảnh tiệc & rượu vang, phòng tiệc và bể Spa Stella. Chúng bổ sung góc nhìn sử dụng bên cạnh mặt bằng tầng.</p>
''' + gallery(e1) + '''
</section>
'''
insert_before_article_end('toa-elite-1-lumi-hanoi/index.html', 'elite-e1-visual-v8-7', e1_block)

e2_block = '''
<section id="elite-e2-visual-v8-7" aria-labelledby="elite-e2-visual-title">
  <h2 id="elite-e2-visual-title">Không gian riêng được gắn nguồn Elite 2</h2>
  <p>Bộ nguồn E2 có đại sảnh, sảnh cư dân, coworking và phòng chơi game gia đình. Các phối cảnh này giúp người xem hiểu rõ hơn lớp tiện ích trong nhà của tòa.</p>
''' + gallery(e2) + '''
</section>
'''
insert_before_article_end('toa-elite-2-lumi-hanoi/index.html', 'elite-e2-visual-v8-7', e2_block)

print('Applied V8.7 visual-library sections to Signature and Elite pages.')
