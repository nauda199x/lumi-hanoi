#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'tien-ich-lumi-hanoi/index.html'
html = PATH.read_text(encoding='utf-8')

replacements = {
    '<title>Tiện ích Lumi Hanoi: hơn 80 tiện ích, cảnh quan và vận hành</title>': '<title>Tiện ích Lumi Hanoi: bể bơi, thể thao, cảnh quan &amp; tiện ích</title>',
    '<meta name="description" content="Phân tích tiện ích Lumi Hanoi theo nhu cầu: hơn 80 hạng mục, 15 sân thể thao, bể bơi Sole–Aurora–Stella, cảnh quan và lưu ý phối cảnh.">': '<meta name="description" content="Tra cứu tiện ích Lumi Hanoi theo Signature, Prestige, Elite: bể bơi Sole–Aurora–Stella, thể thao, trẻ em, coworking, cảnh quan và phối cảnh nguồn.">',
    '<meta property="og:title" content="Tiện ích Lumi Hanoi: hơn 80 tiện ích, cảnh quan và vận hành">': '<meta property="og:title" content="Tiện ích Lumi Hanoi: bể bơi, thể thao, cảnh quan &amp; tiện ích">',
    '<meta property="og:description" content="Phân tích tiện ích Lumi Hanoi theo nhu cầu: hơn 80 hạng mục, 15 sân thể thao, bể bơi Sole–Aurora–Stella, cảnh quan và lưu ý phối cảnh.">': '<meta property="og:description" content="Tra cứu tiện ích Lumi Hanoi theo Signature, Prestige, Elite: bể bơi, thể thao, trẻ em, coworking, cảnh quan và phối cảnh nguồn.">',
    '<p>Tài liệu CapitaLand mô tả hơn 80 tiện ích trên toàn dự án, 15 sân thể thao và nhiều bể bơi; riêng trang Signature dùng mốc 80 tiện ích. Các con số cho biết độ rộng chương trình thiết kế, nhưng chưa nói tiện ích nào thuộc phân khu nào, điều kiện tiếp cận hay trạng thái vận hành. Vì vậy, cách đọc hữu ích là nhóm theo nhu cầu cư dân.</p>': '''<p>Kho tài liệu dự án có nhiều phiên bản và phạm vi đếm tiện ích khác nhau. Vì vậy trang này không dùng một con số duy nhất làm tiêu đề SEO. Cách tra cứu hữu ích hơn là đi theo phân khu, khu cảnh quan và nhu cầu sử dụng, sau đó đối chiếu tên tiện ích với đúng sơ đồ/tài liệu nguồn.</p>\n\n        <h2>Vì sao có tài liệu ghi “&gt;100 tiện ích”, trong khi bộ khác đánh số đến 88?</h2>\n        <p><em>Lumi Hanoi - Project Introduction (for release) - VIE - Final 12</em>, sửa đổi ngày 13/12/2023, ghi ở phần tổng quan dự án: <strong>&gt;100 tiện ích đa dạng độc bản</strong> và khoảng <strong>4,3 ha cảnh quan</strong>. Trong khi đó, eBrochure Lumi Elite ngày 18/08/2024 trình bày một sơ đồ tiện ích có các hạng mục được đánh số tới <strong>88</strong>, đồng thời nội dung sơ đồ bao gồm tên tiện ích thuộc cả các vùng Prestige/Aurora và Elite/Stella.</p>\n        <p>Hai mốc này không nên bị ép thành một con số “đúng tuyệt đối” vì tài liệu khác thời điểm và có thể khác phạm vi đếm. Website giữ cả hai như dữ liệu có niên đại, nhưng khi mô tả trải nghiệm sẽ ưu tiên <strong>tên tiện ích cụ thể + phân khu + nguồn</strong> thay vì quảng bá bằng số lượng.</p>\n        <div class="source-list"><strong>Nguồn đối chiếu số lượng tiện ích</strong><ul><li><a href="https://drive.google.com/file/d/106xs0YINtuQcBADM7J401QzwIaFv-erF/view" rel="noopener noreferrer">Project Introduction - VIE - Final 12</a>, 13/12/2023 — ghi &gt;100 tiện ích và ~4,3 ha cảnh quan.</li><li><a href="https://drive.google.com/file/d/1lHh0HKxvkBdCZ2ojHvlKvStAbpu-s_eg/view" rel="noopener noreferrer">LumiElite_eBrochure.pdf</a>, nguồn 18/08/2024 — sơ đồ tiện ích đánh số tới 88.</li></ul></div>''',
    '<p><a class="btn" href="/phoi-canh-lumi-signature/">Xem đủ 13 phối cảnh 3D Lumi Signature</a></p>': '<p><a class="btn" href="/phoi-canh-lumi-signature/">Xem đủ 21 phối cảnh 3D Lumi Signature</a></p>',
    '<p>15 sân thể thao là số liệu dự án được công bố. Các trang tiện ích còn nêu gym, yoga, Pilates, sauna, sân tennis, sân đa năng và khu tập ngoài trời. Người tập đều đặn nên xem vị trí, kích thước, thông gió, thiết bị, đặt chỗ và mật độ sử dụng — những yếu tố phối cảnh không trả lời.</p>': '<p>Các bộ tài liệu tiện ích nêu gym, yoga, Pilates, sauna, sân tennis, sân đa năng và khu tập ngoài trời. Người tập đều đặn nên xem đúng vị trí trên sơ đồ phân khu, kích thước, thông gió, thiết bị, quy định đặt chỗ và mật độ sử dụng — những yếu tố phối cảnh không trả lời.</p>',
}

for old, new in replacements.items():
    if old not in html:
        raise SystemExit(f'Expected source text not found: {old[:90]}')
    html = html.replace(old, new, 1)

PATH.write_text(html, encoding='utf-8')
print('Applied V8.8 amenity source-scope reconciliation.')
