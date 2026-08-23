#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def write(path, text):
    (ROOT / path).write_text(text, encoding='utf-8')


def insert_before(html, anchor, block, label):
    if block.strip() in html:
        return html
    if anchor not in html:
        raise SystemExit(f'{label}: anchor not found: {anchor}')
    return html.replace(anchor, block + '\n' + anchor, 1)


def bump_modified(html):
    html = re.sub(r'"dateModified":"2026-08-\d{2}"', '"dateModified":"2026-08-23"', html, count=1)
    return html


signature_path = 'lumi-signature/index.html'
signature = read(signature_path)
sig_block = '''
<section aria-labelledby="signature-handover-source">
  <h2 id="signature-handover-source">Bàn giao Signature: căn thường, Duplex và Penthouse không giống nhau</h2>
  <p>Bộ tài liệu bàn giao Signature tách ba nhóm sản phẩm rất rõ. Căn 1–3 phòng ngủ theo hướng hoàn thiện; Duplex dùng tiêu chuẩn cơ bản; Penthouse ở trạng thái thô/cơ bản ở nhiều hạng mục. Vì vậy khi xem căn chuyển nhượng, cần xác định đúng loại căn trước khi đối chiếu thiết bị.</p>
  <table>
    <thead><tr><th>Nhóm sản phẩm</th><th>Mức bàn giao theo nguồn</th><th>Điểm cần nhớ</th></tr></thead>
    <tbody>
      <tr><td>1PN / 2PN / 3PN</td><td>Hoàn thiện</td><td>Sàn gỗ khu ở, tủ áo, tủ bếp, bếp/hút mùi TEKA hoặc tương đương, thiết bị vệ sinh, điều hòa, khóa thông minh.</td></tr>
      <tr><td>Duplex</td><td>Cơ bản</td><td>Sàn bê tông cốt thép thô, cầu thang bê tông thô, xử lý tường cơ bản; không nên áp tiêu chuẩn căn thường.</td></tr>
      <tr><td>Penthouse</td><td>Thô/cơ bản ở nhiều hạng mục</td><td>Sàn RC thô, cấu hình tường ngăn và MEP theo hồ sơ; điều hòa không phải gói hoàn thiện đầy đủ như căn thường.</td></tr>
    </tbody>
  </table>
  <p>Tài liệu nguồn cũng nhắc IGLOOHOME, FERMAX/PANASONIC, TEKA, INNOCI, FERROLI/ARISTON, PANASONIC và HAGER ở các nhóm áp dụng, thường đi kèm điều kiện “hoặc tương đương”. Xem bảng so sánh chi tiết, nguồn và ngày phát hành tại <a href="/noi-that-ban-giao-lumi-hanoi/">Nội thất bàn giao Lumi Hanoi</a>.</p>
</section>
'''
signature = insert_before(signature, '<h2>Signature phù hợp với nhu cầu nào?</h2>', sig_block, 'Signature')
signature = bump_modified(signature)
write(signature_path, signature)

prestige_path = 'lumi-prestige/index.html'
prestige = read(prestige_path)
prestige = prestige.replace('/toa-p1-lumi-hanoi/', '/toa-prestige-1-lumi-hanoi/')
prestige = prestige.replace('/toa-p2-lumi-hanoi/', '/toa-prestige-2-lumi-hanoi/')
pre_block = '''
<section aria-labelledby="prestige-handover-source">
  <h2 id="prestige-handover-source">Bàn giao Prestige theo tài liệu 03/06/2024</h2>
  <p>Slide đào tạo Prestige ghi phạm vi bàn giao dự kiến cho căn 1PN, 2PN, 3PN và 4PN. Ngoài hệ khóa thông minh, chuông hình, sàn gỗ, thiết bị vệ sinh, nước nóng, điều hòa và điện, bộ nguồn còn nêu một số chi tiết đáng chú ý khi so với các phân khu khác.</p>
  <table>
    <thead><tr><th>Hạng mục</th><th>Thông tin nguồn</th></tr></thead>
    <tbody>
      <tr><td>Logia</td><td>Lan can kính.</td></tr>
      <tr><td>Phòng ngủ master</td><td>Kính full-height.</td></tr>
      <tr><td>Bếp</td><td>TEKA hoặc tương đương: hob, hood, oven và sink/faucet.</td></tr>
      <tr><td>Khóa / intercom</td><td>IGLOOHOME 5-in-1 hoặc tương đương; FERMAX/PANASONIC hoặc tương đương.</td></tr>
    </tbody>
  </table>
  <p>Chi tiết thương hiệu, model và phạm vi cuối cùng phải theo phụ lục kỹ thuật của căn cụ thể. Xem đối chiếu Signature–Prestige–Elite tại <a href="/noi-that-ban-giao-lumi-hanoi/">Nội thất bàn giao Lumi Hanoi</a>.</p>
</section>
'''
prestige = insert_before(prestige, '<h2>Bàn giao nâng cấp: đọc đúng mức độ</h2>', pre_block, 'Prestige')
prestige = bump_modified(prestige)
write(prestige_path, prestige)

elite_path = 'lumi-elite/index.html'
elite = read(elite_path)
elite_block = '''
<section aria-labelledby="elite-handover-source">
  <h2 id="elite-handover-source">Bàn giao Elite: hai chi tiết nguồn rất đáng chú ý</h2>
  <p>Danh mục bàn giao dự kiến Elite tháng 08/2024 áp dụng cho nhóm 1PN, 2PN và 3PN, với hệ khóa thông minh, chuông hình, sàn gỗ khu ở, tủ bếp, thiết bị vệ sinh, nước nóng, điều hòa và điện theo bộ thương hiệu dự kiến của dự án.</p>
  <ul>
    <li><strong>Kính full-height cho toàn bộ phòng ngủ</strong>, thay vì cách mô tả Prestige nhấn mạnh riêng phòng ngủ master.</li>
    <li><strong>Căn 3PN có dishwasher TEKA hoặc tương đương</strong>, ngoài hob, hood và oven trong bộ bếp nguồn.</li>
  </ul>
  <p>Tài liệu thương hiệu/thiết bị còn minh họa IGLOOHOME, TEKA, INNOCI và PANASONIC. Cách diễn đạt trên website giữ trạng thái “dự kiến/hoặc tương đương”, không suy ra model cụ thể. Xem bảng so sánh đầy đủ tại <a href="/noi-that-ban-giao-lumi-hanoi/">Nội thất bàn giao Lumi Hanoi</a>.</p>
</section>
'''
elite = insert_before(elite, '<h2>Mật độ và trải nghiệm khép kín</h2>', elite_block, 'Elite')
elite = bump_modified(elite)
write(elite_path, elite)

print('Applied V8.6 handover enrichment to Signature, Prestige and Elite.')
