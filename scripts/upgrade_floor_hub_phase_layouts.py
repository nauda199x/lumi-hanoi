from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "mat-bang-lumi-hanoi" / "index.html"
CSS = ROOT / "assets" / "css" / "floor-plan-hub.css"

START = "<!-- PHASE-UNIT-LAYOUTS:START -->"
END = "<!-- PHASE-UNIT-LAYOUTS:END -->"
CSS_START = "/* PHASE-UNIT-LAYOUTS:START */"
CSS_END = "/* PHASE-UNIT-LAYOUTS:END */"

ASSETS = [
    "assets/media/signature/unit-layouts/signature-s1-s5-1br-a1.webp",
    "assets/media/signature/unit-layouts/signature-s1-s5-2br-b1.webp",
    "assets/media/signature/unit-layouts/signature-s1-s5-3br-c10a.webp",
    "assets/media/elite/unit-layouts/elite-layout-page-09.webp",
    "assets/media/elite/unit-layouts/elite-layout-page-11.webp",
    "assets/media/elite/unit-layouts/elite-layout-page-17.webp",
]

for asset in ASSETS:
    path = ROOT / asset
    if not path.exists() or path.stat().st_size < 10_000:
        raise SystemExit(f"Missing or invalid layout asset: {asset}")

section = f'''{START}
<section class="section section-alt phase-layout-library" id="phase-unit-layouts" aria-labelledby="phase-unit-layouts-title">
  <div class="container">
    <div class="section-head phase-head">
      <div>
        <p class="eyebrow">Layout căn hộ theo phân khu</p>
        <h2 id="phase-unit-layouts-title">Xem ngay layout khu Signature và Elite</h2>
        <p>Mặt bằng tầng cho biết căn nằm ở đâu trong tòa; <strong>layout căn hộ</strong> mới cho biết cách bố trí phòng bên trong. Trang tổng giờ hiển thị trực tiếp các mẫu tiêu biểu của khu S và khu E để không còn cảm giác thư viện chỉ có Prestige.</p>
      </div>
      <a class="text-link" href="/mat-bang-lumi-hanoi/layout-can-ho-lumi-hanoi/">Mở toàn bộ thư viện layout →</a>
    </div>

    <div class="phase-layout-group" aria-labelledby="signature-layout-preview-title">
      <div class="phase-layout-group-head">
        <div>
          <p class="eyebrow">Lumi Signature · khu S</p>
          <h3 id="signature-layout-preview-title">Layout 1PN · 2PN · 3PN khu S</h3>
          <p>Ba bản dưới đây là mẫu tiêu biểu từ bộ Signature S1/S2/S3/S5. S6 có bộ layout riêng và được giữ đầy đủ trong thư viện 51 layout Signature.</p>
        </div>
        <div class="phase-layout-actions" aria-label="Tra cứu layout Signature">
          <a href="/layout-can-ho-lumi-signature/">51 layout Signature</a>
          <a href="/duplex-penthouse-lumi-hanoi/#signature-duplex">Duplex DL-01 → DL-06</a>
        </div>
      </div>
      <div class="masterplan-library-grid phase-layout-grid">
        <article class="masterplan-card phase-layout-card">
          <a class="masterplan-card-media" href="/assets/media/signature/unit-layouts/signature-s1-s5-1br-a1.webp" data-lightbox data-lightbox-alt="Layout 1PN A1 Lumi Signature khu S" data-lightbox-caption="Lumi Signature · 1PN A1 · bộ S1/S2/S3/S5">
            <img src="/assets/media/signature/unit-layouts/signature-s1-s5-1br-a1.webp" width="1800" height="2400" alt="Mặt bằng căn hộ 1 phòng ngủ A1 Lumi Signature khu S" loading="lazy" decoding="async">
          </a>
          <div class="masterplan-card-body"><span class="masterplan-tag">Signature · 1PN</span><h3>A1 · 1 phòng ngủ</h3><p>Mẫu 1BR tiêu biểu của bộ S1/S2/S3/S5; dùng mặt bằng tòa để xác định đúng vị trí căn.</p><a class="text-link" href="/can-ho-1-phong-ngu-lumi-hanoi/#signature">Xem toàn bộ 1PN Signature →</a></div>
        </article>
        <article class="masterplan-card phase-layout-card">
          <a class="masterplan-card-media" href="/assets/media/signature/unit-layouts/signature-s1-s5-2br-b1.webp" data-lightbox data-lightbox-alt="Layout 2PN B1 Lumi Signature khu S" data-lightbox-caption="Lumi Signature · 2PN B1 · bộ S1/S2/S3/S5">
            <img src="/assets/media/signature/unit-layouts/signature-s1-s5-2br-b1.webp" width="1800" height="2400" alt="Mặt bằng căn hộ 2 phòng ngủ B1 Lumi Signature khu S" loading="lazy" decoding="async">
          </a>
          <div class="masterplan-card-body"><span class="masterplan-tag">Signature · 2PN</span><h3>B1 · 2 phòng ngủ</h3><p>Một trong nhiều họ B của Signature; trang 2PN tách riêng bộ khu S và bộ S6.</p><a class="text-link" href="/can-ho-2-phong-ngu-lumi-hanoi/#signature">Xem toàn bộ 2PN Signature →</a></div>
        </article>
        <article class="masterplan-card phase-layout-card">
          <a class="masterplan-card-media" href="/assets/media/signature/unit-layouts/signature-s1-s5-3br-c10a.webp" data-lightbox data-lightbox-alt="Layout 3PN C10A Lumi Signature khu S" data-lightbox-caption="Lumi Signature · 3PN C10A · bộ S1/S2/S3/S5">
            <img src="/assets/media/signature/unit-layouts/signature-s1-s5-3br-c10a.webp" width="1800" height="2400" alt="Mặt bằng căn hộ 3 phòng ngủ C10A Lumi Signature khu S" loading="lazy" decoding="async">
          </a>
          <div class="masterplan-card-body"><span class="masterplan-tag">Signature · 3PN</span><h3>C10A · 3 phòng ngủ</h3><p>Trang 3PN còn có C1/C3 và bộ S6 riêng, gồm cả C7G, C7AG và C8G.</p><a class="text-link" href="/can-ho-3-phong-ngu-lumi-hanoi/#signature">Xem toàn bộ 3PN Signature →</a></div>
        </article>
      </div>
    </div>

    <div class="phase-layout-group" aria-labelledby="elite-layout-preview-title">
      <div class="phase-layout-group-head">
        <div>
          <p class="eyebrow">Lumi Elite · khu E</p>
          <h3 id="elite-layout-preview-title">Layout 1PN · 2PN · 3PN khu E</h3>
          <p>Elite dùng bộ unit layout/eBrochure riêng. Các ảnh dưới đây là asset local của chính bộ Elite, không mượn layout Prestige để minh họa.</p>
        </div>
        <div class="phase-layout-actions" aria-label="Tra cứu layout Elite">
          <a href="/mat-bang-lumi-hanoi/lumi-elite/">Mặt bằng E1 · E2</a>
          <a href="/duplex-penthouse-lumi-hanoi/#elite-duplex">Duplex Elite</a>
        </div>
      </div>
      <div class="masterplan-library-grid phase-layout-grid">
        <article class="masterplan-card phase-layout-card">
          <a class="masterplan-card-media" href="/assets/media/elite/unit-layouts/elite-layout-page-09.webp" data-lightbox data-lightbox-alt="Layout căn hộ 1 phòng ngủ Lumi Elite khu E" data-lightbox-caption="Lumi Elite · nhóm 1BR · bộ unit layout/eBrochure Elite">
            <img src="/assets/media/elite/unit-layouts/elite-layout-page-09.webp" width="1800" height="2400" alt="Mặt bằng căn hộ 1 phòng ngủ Lumi Elite khu E từ bộ eBrochure" loading="lazy" decoding="async">
          </a>
          <div class="masterplan-card-body"><span class="masterplan-tag">Elite · 1PN</span><h3>1 phòng ngủ Elite</h3><p>Elite có các biến thể 1BR riêng; mở trang 1PN để đối chiếu mã, NFA/GFA và tòa E1/E2.</p><a class="text-link" href="/can-ho-1-phong-ngu-lumi-hanoi/#elite">Xem 1PN Elite →</a></div>
        </article>
        <article class="masterplan-card phase-layout-card">
          <a class="masterplan-card-media" href="/assets/media/elite/unit-layouts/elite-layout-page-11.webp" data-lightbox data-lightbox-alt="Layout 2PN Small Lumi Elite khu E" data-lightbox-caption="Lumi Elite · 2BR Small · NFA 53,8 m² · GFA 58,8 m²">
            <img src="/assets/media/elite/unit-layouts/elite-layout-page-11.webp" width="1800" height="2400" alt="Mặt bằng căn hộ 2 phòng ngủ Small Lumi Elite khu E" loading="lazy" decoding="async">
          </a>
          <div class="masterplan-card-body"><span class="masterplan-tag">Elite · 2PN</span><h3>2BR Small · 53,8 m² NFA</h3><p>Bộ Elite còn có các biến thể 2BR Medium và Large; vị trí thực tế phải đối chiếu E1/E2.</p><a class="text-link" href="/can-ho-2-phong-ngu-lumi-hanoi/#elite">Xem toàn bộ 2PN Elite →</a></div>
        </article>
        <article class="masterplan-card phase-layout-card">
          <a class="masterplan-card-media" href="/assets/media/elite/unit-layouts/elite-layout-page-17.webp" data-lightbox data-lightbox-alt="Layout 3PN Small C10B Lumi Elite khu E" data-lightbox-caption="Lumi Elite · 3BR Small C10B/C10BM · NFA 81,7 m² · GFA 88,4 m²">
            <img src="/assets/media/elite/unit-layouts/elite-layout-page-17.webp" width="1800" height="2400" alt="Mặt bằng căn hộ 3 phòng ngủ Small C10B Lumi Elite khu E" loading="lazy" decoding="async">
          </a>
          <div class="masterplan-card-body"><span class="masterplan-tag">Elite · 3PN</span><h3>C10B · 3 phòng ngủ</h3><p>Elite có bốn nhóm 3BR đã số hóa từ Small tới Extra Large, tách riêng khỏi Prestige.</p><a class="text-link" href="/can-ho-3-phong-ngu-lumi-hanoi/#elite">Xem toàn bộ 3PN Elite →</a></div>
        </article>
      </div>
    </div>

    <p class="notice phase-layout-note"><strong>Cách tra đúng:</strong> chọn phân khu → mở layout theo số phòng ngủ → quay lại mặt bằng đúng tòa và nhóm tầng. Không dùng layout khu S cho khu E, hoặc ngược lại.</p>
  </div>
</section>
{END}'''

html = PAGE.read_text(encoding="utf-8")

# Keep the page idempotent if this script is run again.
if START in html and END in html:
    html = re.sub(re.escape(START) + r".*?" + re.escape(END), section, html, count=1, flags=re.S)
else:
    anchor = '<div class="container"><section class="cutaway-teaser" aria-label="Khám phá mặt bằng 3D">'
    if anchor not in html:
        raise SystemExit("Could not find insertion point before 3D teaser")
    html = html.replace(anchor, section + anchor, 1)

# Add a high-visibility jump link near the hero.
if 'href="#phase-unit-layouts"' not in html:
    old = '<nav class="hub-jump"><a href="/mat-bang-lumi-hanoi/layout-can-ho-lumi-hanoi/"><strong>Xem layout căn hộ · 1PN–4PN</strong></a>'
    new = '<nav class="hub-jump"><a href="#phase-unit-layouts"><strong>Xem layout khu S &amp; E</strong></a><a href="/mat-bang-lumi-hanoi/layout-can-ho-lumi-hanoi/"><strong>Toàn bộ layout · 1PN–4PN</strong></a>'
    if old not in html:
        raise SystemExit("Could not find hero jump navigation")
    html = html.replace(old, new, 1)

# Make the lower quick-navigation heading representative of the whole project, not only Prestige.
html = html.replace(
    '<h2 id="floor-quick-title">Đi thẳng tới P1, P2 và thư viện layout</h2>',
    '<h2 id="floor-quick-title">Đi thẳng tới 9 tòa và thư viện layout</h2>',
)
html = html.replace(
    'Các đường dẫn dưới đây giữ cấu trúc phân khu → tòa → layout rõ ràng để người đọc và công cụ tìm kiếm hiểu đúng quan hệ giữa các trang.',
    'Các đường dẫn dưới đây nối rõ phân khu → tòa → layout để người đọc và công cụ tìm kiếm hiểu đúng quan hệ giữa Signature, Prestige, Elite và từng loại căn.',
)

# Strengthen the main description now that phase-specific layouts are visible directly on the hub.
html = html.replace(
    'Trung tâm tra cứu mặt bằng Lumi Hanoi: 9 tòa S1, S2, S3, S5, S6, P1, P2, E1, E2; xem mặt bằng theo tòa hoặc layout căn hộ theo 1PN–4PN.',
    'Trung tâm tra cứu mặt bằng Lumi Hanoi: 9 tòa S1, S2, S3, S5, S6, P1, P2, E1, E2; xem mặt bằng theo tòa và layout căn hộ Signature, Prestige, Elite theo 1PN–4PN.',
)

required_html = [
    'id="phase-unit-layouts"',
    'signature-s1-s5-1br-a1.webp',
    'signature-s1-s5-2br-b1.webp',
    'signature-s1-s5-3br-c10a.webp',
    'elite-layout-page-09.webp',
    'elite-layout-page-11.webp',
    'elite-layout-page-17.webp',
    'Xem layout khu S &amp; E',
]
for marker in required_html:
    if marker not in html:
        raise SystemExit(f"Missing required hub marker after update: {marker}")

PAGE.write_text(html, encoding="utf-8")

css = CSS.read_text(encoding="utf-8")
css_block = f'''\n{CSS_START}
.phase-layout-library{{scroll-margin-top:90px}}
.phase-layout-library .phase-head{{margin-bottom:2rem}}
.phase-layout-group{{margin-top:2.4rem}}
.phase-layout-group:first-of-type{{margin-top:.5rem}}
.phase-layout-group-head{{display:flex;align-items:end;justify-content:space-between;gap:2rem;margin-bottom:1rem}}
.phase-layout-group-head>div:first-child{{max-width:760px}}
.phase-layout-group-head h3{{margin:.2rem 0 .55rem;font-size:clamp(1.65rem,3vw,2.35rem)}}
.phase-layout-group-head p{{margin:.2rem 0;line-height:1.65}}
.phase-layout-actions{{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:.5rem}}
.phase-layout-actions a{{display:inline-flex;padding:.55rem .72rem;border:1px solid var(--line,#d8d1c5);border-radius:999px;background:#fff;color:var(--ink,#1c201d);font-size:.78rem;font-weight:750;text-decoration:none}}
.phase-layout-actions a:hover{{background:#f4f1ea}}
.phase-layout-card .masterplan-card-media{{aspect-ratio:4/3;background:#fff}}
.phase-layout-card .masterplan-card-media img{{object-fit:contain;padding:.45rem}}
.phase-layout-card .masterplan-card-body{{display:flex;min-height:220px;flex-direction:column}}
.phase-layout-card .masterplan-card-body .text-link{{margin-top:auto;padding-top:.45rem}}
.phase-layout-note{{margin-top:2rem}}
@media(max-width:760px){{.phase-layout-library .phase-head,.phase-layout-group-head{{display:block}}.phase-layout-actions{{justify-content:flex-start;margin-top:.9rem}}.phase-layout-card .masterplan-card-body{{min-height:0}}}}
{CSS_END}\n'''

if CSS_START in css and CSS_END in css:
    css = re.sub(re.escape(CSS_START) + r".*?" + re.escape(CSS_END), css_block.strip(), css, count=1, flags=re.S)
else:
    css = css.rstrip() + "\n" + css_block

for marker in [".phase-layout-library", ".phase-layout-card", ".phase-layout-actions"]:
    if marker not in css:
        raise SystemExit(f"Missing required CSS marker: {marker}")

CSS.write_text(css, encoding="utf-8")

print("Updated floor-plan hub with visible Signature and Elite unit-layout previews.")
