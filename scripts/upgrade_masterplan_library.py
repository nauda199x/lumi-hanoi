from pathlib import Path
import re

TODAY = "2026-09-10"
OFFICIAL_PROFILE = "https://www.capitaland.com/content/dam/sites/lumihanoi/vn/project-profile/"
OFFICIAL_PRESTIGE = "https://www.capitaland.com/sites/lumihanoi/vn/products/lumi-prestige/"
OFFICIAL_ELITE = "https://www.capitaland.com/sites/lumihanoi/vn/products/lumi-elite/"


def write_if_changed(path: str, text: str) -> None:
    p = Path(path)
    old = p.read_text(encoding="utf-8")
    if old != text:
        p.write_text(text, encoding="utf-8")
        print(f"updated {path}")
    else:
        print(f"unchanged {path}")


def ensure_robots(text: str, canonical_url: str) -> str:
    if 'name="robots"' in text:
        return text
    needle = f'<link rel="canonical" href="{canonical_url}">'
    replacement = '<meta name="robots" content="index,follow,max-image-preview:large">' + needle
    if needle not in text:
        raise RuntimeError(f"canonical not found: {canonical_url}")
    return text.replace(needle, replacement, 1)


def upgrade_hub() -> None:
    path = "mat-bang-lumi-hanoi/index.html"
    text = Path(path).read_text(encoding="utf-8")
    text = ensure_robots(text, "https://lumi-hanoi.com/mat-bang-lumi-hanoi/")
    text = re.sub(r'"dateModified":"\d{4}-\d{2}-\d{2}"', f'"dateModified":"{TODAY}"', text, count=1)

    if 'class="masterplan-library"' not in text:
        new_block = f'''<div class="masterplan-library" aria-labelledby="masterplan-library-title"><div class="masterplan-library-head"><p class="eyebrow">Bước 1 · Định vị toàn dự án</p><h2 id="masterplan-library-title">Mặt bằng tổng thể &amp; mặt bằng 3 phân khu Lumi Hanoi</h2><p>Bắt đầu từ sơ đồ 9 tòa để xác định đúng <strong>Signature · Prestige · Elite</strong>, sau đó mở mặt bằng cảnh quan từng phân khu trước khi đi xuống mặt bằng tầng của từng tòa.</p><p class="masterplan-source-note">Cấu trúc 9 tòa được đối chiếu theo <a href="{OFFICIAL_PROFILE}" target="_blank" rel="noopener">hồ sơ dự án CapitaLand ↗</a>. Sơ đồ 9 tòa dưới đây do lumi-hanoi.com biên tập để tra cứu; không thay thế bản vẽ kỹ thuật, HĐMB hoặc phụ lục của căn hộ.</p></div><div class="masterplan-library-grid"><article class="masterplan-card masterplan-card-featured"><a class="masterplan-card-media" href="/assets/media/masterplan/lumi-hanoi-9-toa-so-do-tra-cuu.svg" data-lightbox data-lightbox-alt="Sơ đồ tra cứu mặt bằng tổng thể Lumi Hanoi gồm 9 tòa Signature, Prestige và Elite" data-lightbox-caption="Sơ đồ tra cứu 9 tòa do lumi-hanoi.com biên tập từ cấu trúc tòa đã công bố; không phải bản vẽ kỹ thuật."><img src="/assets/media/masterplan/lumi-hanoi-9-toa-so-do-tra-cuu.svg" width="1600" height="1200" alt="Sơ đồ tra cứu mặt bằng tổng thể Lumi Hanoi gồm 9 tòa S1, S2, S3, S5, S6, P1, P2, E1, E2" loading="eager" decoding="async"></a><div class="masterplan-card-body"><span class="masterplan-tag">Toàn dự án · 9 tòa</span><h3>Mặt bằng tổng thể Lumi Hanoi</h3><p>Sơ đồ tra cứu nhanh 3 phân khu và 9 tòa. Từ đây đi tiếp vào mặt bằng thực của Signature, Prestige hoặc Elite.</p><div class="masterplan-chip-row"><a href="#signature">S1 · S2 · S3 · S5 · S6</a><a href="#prestige">P1 · P2</a><a href="#elite">E1 · E2</a></div></div></article><article class="masterplan-card"><a class="masterplan-card-media" href="/assets/media/masterplan/lumi-hanoi-masterplan-3840.webp" data-lightbox data-lightbox-alt="Mặt bằng cảnh quan Lumi Signature gồm S1, S2, S3, S5, S6" data-lightbox-caption="Mặt bằng cảnh quan Lumi Signature."><img src="/assets/media/masterplan/lumi-hanoi-masterplan-1280.webp" srcset="/assets/media/masterplan/lumi-hanoi-masterplan-640.webp 640w, /assets/media/masterplan/lumi-hanoi-masterplan-1280.webp 1280w, /assets/media/masterplan/lumi-hanoi-masterplan-1920.webp 1920w" sizes="(max-width:760px) calc(100vw - 48px), 420px" width="1280" height="853" alt="Mặt bằng cảnh quan Lumi Signature với các tòa S1, S2, S3, S5, S6" loading="lazy" decoding="async"></a><div class="masterplan-card-body"><span class="masterplan-tag">Signature</span><h3>Mặt bằng khu S</h3><p>Định vị 5 tòa S1, S2, S3, S5, S6 và hệ cảnh quan trước khi mở mặt bằng tầng.</p><a class="text-link" href="/mat-bang-lumi-hanoi/lumi-signature/">Xem mặt bằng Signature →</a></div></article><article class="masterplan-card"><a class="masterplan-card-media" href="/assets/media/floor-plans/lumi-prestige-masterplan.webp" data-lightbox data-lightbox-alt="Mặt bằng tổng Lumi Prestige gồm P1 và P2" data-lightbox-caption="Mặt bằng phân khu Lumi Prestige, dùng để định vị P1 và P2 trước khi xem mặt bằng tầng."><img src="/assets/media/floor-plans/lumi-prestige-masterplan.webp" width="1800" height="1013" alt="Mặt bằng tổng Lumi Prestige gồm hai tòa P1 và P2 tại Lumi Hanoi" loading="lazy" decoding="async"></a><div class="masterplan-card-body"><span class="masterplan-tag">Prestige</span><h3>Mặt bằng khu P</h3><p>Mở mặt bằng phân khu P để định vị P1, P2, cảnh quan và luồng tiếp cận trước khi tra cứu tầng.</p><a class="text-link" href="/mat-bang-lumi-hanoi/lumi-prestige/">Xem mặt bằng Prestige →</a></div></article><article class="masterplan-card"><a class="masterplan-card-media" href="/assets/media/floor-plans/lumi-elite-masterplan.webp" data-lightbox data-lightbox-alt="Mặt bằng tổng Lumi Elite gồm E1 và E2" data-lightbox-caption="Mặt bằng phân khu Lumi Elite, dùng để định vị E1 và E2 trước khi xem mặt bằng tầng."><img src="/assets/media/floor-plans/lumi-elite-masterplan.webp" width="1800" height="1350" alt="Mặt bằng tổng Lumi Elite gồm hai tòa E1 và E2 tại Lumi Hanoi" loading="lazy" decoding="async"></a><div class="masterplan-card-body"><span class="masterplan-tag">Elite</span><h3>Mặt bằng khu E</h3><p>Mở mặt bằng phân khu E để định vị E1, E2 và tương quan cảnh quan trước khi chọn đúng nhóm tầng.</p><a class="text-link" href="/mat-bang-lumi-hanoi/lumi-elite/">Xem mặt bằng Elite →</a></div></article></div></div></div></section>'''
        pattern = re.compile(r'<div class="masterplan-compact"><div><p class="eyebrow">Bước 1</p>.*?</a></div></div></section>', re.S)
        text, count = pattern.subn(new_block, text, count=1)
        if count != 1:
            raise RuntimeError("could not replace old Signature-only masterplan block")

    write_if_changed(path, text)


def upgrade_phase_page(path: str, phase: str) -> None:
    text = Path(path).read_text(encoding="utf-8")
    if phase == "prestige":
        canonical = "https://lumi-hanoi.com/mat-bang-lumi-hanoi/lumi-prestige/"
        image = "https://lumi-hanoi.com/assets/media/floor-plans/lumi-prestige-masterplan.webp"
        alt = "Mặt bằng tổng Lumi Prestige gồm hai tòa P1 và P2 tại Lumi Hanoi"
        width, height = "1800", "1013"
        official = OFFICIAL_PRESTIGE
        old_generic = "https://lumi-hanoi.com/assets/media/og/lumi-hanoi-og.webp"
        old_date = "2026-08-31"
        desc = "Bản mặt bằng tổng giúp định vị P1, P2, cảnh quan và hệ tiện ích của phân khu Prestige trước khi đi sâu vào mặt bằng từng tòa và từng nhóm tầng."
        extra = f'{desc}</p><p class="masterplan-source-note">Đối chiếu tên tòa P1–P2 và hệ mặt bằng theo <a href="{official}" target="_blank" rel="noopener">trang Lumi Prestige của CapitaLand ↗</a>. Ảnh trên website phục vụ tra cứu; hồ sơ căn cụ thể là căn cứ áp dụng.</p><a class="text-link" href="/assets/media/floor-plans/lumi-prestige-masterplan.webp" data-lightbox data-lightbox-alt="{alt}">Phóng to mặt bằng Prestige →</a>'
    else:
        canonical = "https://lumi-hanoi.com/mat-bang-lumi-hanoi/lumi-elite/"
        image = "https://lumi-hanoi.com/assets/media/floor-plans/lumi-elite-masterplan.webp"
        alt = "Mặt bằng tổng Lumi Elite gồm hai tòa E1 và E2 tại Lumi Hanoi"
        width, height = "1800", "1350"
        official = OFFICIAL_ELITE
        old_generic = "https://lumi-hanoi.com/assets/media/elite/lumi-elite-facade.webp"
        old_date = "2026-08-31"
        desc = "Bản mặt bằng tổng giúp định vị E1, E2 trong toàn khu, hướng Bắc và tương quan với các tòa Signature trước khi tra cứu mặt bằng chi tiết từng tòa."
        extra = f'{desc}</p><p class="masterplan-source-note">Đối chiếu tên tòa E1–E2 và hệ mặt bằng theo <a href="{official}" target="_blank" rel="noopener">trang Lumi Elite của CapitaLand ↗</a>. Ảnh trên website phục vụ tra cứu; hồ sơ căn cụ thể là căn cứ áp dụng.</p><a class="text-link" href="/assets/media/floor-plans/lumi-elite-masterplan.webp" data-lightbox data-lightbox-alt="{alt}">Phóng to mặt bằng Elite →</a>'

    text = ensure_robots(text, canonical)
    text = text.replace(f'<meta property="og:image" content="{old_generic}">', f'<meta property="og:image" content="{image}"><meta property="og:image:width" content="{width}"><meta property="og:image:height" content="{height}"><meta property="og:image:alt" content="{alt}">', 1)
    text = re.sub(r'<meta property="og:image:alt" content="[^"]*">(?=<meta name="twitter:card")', '', text, count=1)
    text = re.sub(r'<meta property="og:image:width" content="985"><meta property="og:image:height" content="633">', '', text, count=1)
    text = re.sub(r'<meta property="og:image:alt" content="Phối cảnh Lumi Elite E1 E2 tại Lumi Hanoi">', '', text, count=1)
    text = re.sub(r'<meta name="twitter:image" content="[^"]+">', f'<meta name="twitter:image" content="{image}"><meta name="twitter:image:alt" content="{alt}">', text, count=1)

    schema_old = f'"inLanguage":"vi-VN","dateModified":"{old_date}"'
    schema_new = f'"image":"{image}","primaryImageOfPage":{{"@type":"ImageObject","contentUrl":"{image}","width":{width},"height":{height}}},"inLanguage":"vi-VN","dateModified":"{TODAY}"'
    if schema_old in text:
        text = text.replace(schema_old, schema_new, 1)
    elif f'"dateModified":"{TODAY}"' not in text:
        text = re.sub(r'"dateModified":"\d{4}-\d{2}-\d{2}"', f'"dateModified":"{TODAY}"', text, count=1)

    if 'masterplan-source-note' not in text:
        text = text.replace(desc + '</p>', extra, 1)

    text = re.sub(r'<a class="masterplan-thumb" href="([^\"]+masterplan\.webp)" target="_blank" rel="noopener" aria-label="Mở mặt bằng tổng kích thước lớn">', r'<a class="masterplan-thumb" href="\1" data-lightbox aria-label="Mở mặt bằng tổng kích thước lớn">', text, count=1)
    write_if_changed(path, text)


def upgrade_overview_page(path: str, phase: str) -> None:
    text = Path(path).read_text(encoding="utf-8")
    if phase == "prestige":
        canonical = "https://lumi-hanoi.com/lumi-prestige/"
        image = "https://lumi-hanoi.com/assets/media/floor-plans/lumi-prestige-masterplan.webp"
        alt = "Mặt bằng tổng Lumi Prestige P1 P2 tại Lumi Hanoi"
        headline = "Lumi Prestige"
        plan_url = "/mat-bang-lumi-hanoi/lumi-prestige/"
        plan_label = "Tra cứu mặt bằng tổng P1–P2 và mặt bằng từng tầng →"
    else:
        canonical = "https://lumi-hanoi.com/lumi-elite/"
        image = "https://lumi-hanoi.com/assets/media/floor-plans/lumi-elite-masterplan.webp"
        alt = "Mặt bằng tổng Lumi Elite E1 E2 tại Lumi Hanoi"
        headline = "Lumi Elite"
        plan_url = "/mat-bang-lumi-hanoi/lumi-elite/"
        plan_label = "Tra cứu mặt bằng tổng E1–E2 và mặt bằng từng tầng →"

    text = ensure_robots(text, canonical)
    text = re.sub(r'<meta name="twitter:card" content="summary">', '<meta name="twitter:card" content="summary_large_image">', text, count=1)
    text = re.sub(r'<meta property="og:image" content="https://lumi-hanoi.com/assets/media/og/lumi-hanoi-og.webp">', f'<meta property="og:image" content="{image}">', text, count=1)
    text = re.sub(r'<meta property="og:image:alt" content="[^"]*">', f'<meta property="og:image:alt" content="{alt}">', text, count=1)
    text = re.sub(r'<meta name="twitter:image" content="https://lumi-hanoi.com/assets/media/og/lumi-hanoi-og.webp">', f'<meta name="twitter:image" content="{image}">', text, count=1)
    text = re.sub(rf'"headline":"{re.escape(headline)}","dateModified":"\d{{4}}-\d{{2}}-\d{{2}}"', f'"headline":"{headline}","image":"{image}","dateModified":"{TODAY}"', text, count=1)

    marker = f'href="{plan_url}"'
    if marker not in text:
        insertion = f'<section class="section section-alt"><div class="container article"><p class="eyebrow">Mặt bằng phân khu</p><h2>Tra cứu mặt bằng {headline}</h2><p>Mở mặt bằng tổng phân khu trước, sau đó chọn đúng tòa và nhóm tầng để đối chiếu vị trí căn.</p><p><a class="btn btn-primary" href="{plan_url}">{plan_label}</a></p></div></section>'
        text = text.replace('</main>', insertion + '</main>', 1)
    write_if_changed(path, text)


def upgrade_css() -> None:
    path = "assets/css/floor-plan-hub.css"
    text = Path(path).read_text(encoding="utf-8")
    marker = "/* V8.3 — masterplan library */"
    if marker not in text:
        text += '''\n/* V8.3 — masterplan library */\n.masterplan-library{margin-top:.25rem}.masterplan-library-head{max-width:900px;margin-bottom:1.45rem}.masterplan-library-head h2{margin:.2rem 0 .75rem;font-size:clamp(2rem,4vw,3.2rem);letter-spacing:-.025em}.masterplan-library-head>p{line-height:1.7}.masterplan-source-note{margin-top:.8rem;padding-left:1rem;border-left:3px solid #b99156;color:var(--muted,#666);font-size:.9rem}.masterplan-source-note a{font-weight:700}.masterplan-library-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}.masterplan-card{overflow:hidden;border:1px solid var(--line,#d8d1c5);border-radius:20px;background:#fff;box-shadow:0 12px 34px rgba(25,29,25,.06)}.masterplan-card-featured{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,1.3fr) minmax(300px,.7fr)}.masterplan-card-media{display:block;min-height:240px;overflow:hidden;background:#f3efe6}.masterplan-card:not(.masterplan-card-featured) .masterplan-card-media{aspect-ratio:4/3}.masterplan-card-media img{display:block;width:100%;height:100%;object-fit:contain;transition:transform .24s ease}.masterplan-card-media:hover img{transform:scale(1.015)}.masterplan-card-body{padding:1.15rem 1.2rem 1.3rem}.masterplan-card-featured .masterplan-card-body{display:flex;flex-direction:column;justify-content:center;padding:clamp(1.3rem,3vw,2.2rem)}.masterplan-tag{display:inline-flex;width:max-content;padding:.34rem .55rem;border-radius:999px;background:#efe9dc;color:#5f5546;font-size:.7rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase}.masterplan-card h3{margin:.55rem 0 .55rem;font-size:clamp(1.35rem,2.5vw,2rem)}.masterplan-card p{margin:0 0 .85rem;line-height:1.58;color:var(--muted,#666)}.masterplan-chip-row{display:flex;flex-wrap:wrap;gap:.45rem;margin-top:.35rem}.masterplan-chip-row a{padding:.42rem .58rem;border-radius:999px;background:#f4f1ea;color:var(--ink,#1c201d);font-size:.78rem;font-weight:700;text-decoration:none}.masterplan-chip-row a:hover{background:#ebe4d7}.masterplan-card .text-link{display:inline-block;margin-top:.2rem}\n@media(max-width:900px){.masterplan-library-grid{grid-template-columns:1fr 1fr}.masterplan-card-featured{grid-column:1/-1;grid-template-columns:1fr}.masterplan-card-featured .masterplan-card-media{aspect-ratio:4/3}.masterplan-card-featured .masterplan-card-body{padding:1.2rem}}\n@media(max-width:620px){.masterplan-library-grid{grid-template-columns:1fr}.masterplan-card-featured{grid-column:auto}.masterplan-card-media,.masterplan-card:not(.masterplan-card-featured) .masterplan-card-media,.masterplan-card-featured .masterplan-card-media{aspect-ratio:4/3;min-height:0}.masterplan-card{border-radius:16px}.masterplan-library-head h2{font-size:2rem}}\n'''
    write_if_changed(path, text)


def upgrade_sitemap() -> None:
    path = "sitemap.xml"
    text = Path(path).read_text(encoding="utf-8")
    urls = [
        "https://lumi-hanoi.com/mat-bang-lumi-hanoi/",
        "https://lumi-hanoi.com/mat-bang-lumi-hanoi/lumi-prestige/",
        "https://lumi-hanoi.com/mat-bang-lumi-hanoi/lumi-elite/",
        "https://lumi-hanoi.com/lumi-prestige/",
        "https://lumi-hanoi.com/lumi-elite/",
    ]
    for url in urls:
        pattern = re.compile(rf'(<url><loc>{re.escape(url)}</loc><lastmod>)\d{{4}}-\d{{2}}-\d{{2}}(</lastmod>)')
        text = pattern.sub(rf'\g<1>{TODAY}\g<2>', text, count=1)
    write_if_changed(path, text)


if __name__ == "__main__":
    upgrade_hub()
    upgrade_phase_page("mat-bang-lumi-hanoi/lumi-prestige/index.html", "prestige")
    upgrade_phase_page("mat-bang-lumi-hanoi/lumi-elite/index.html", "elite")
    upgrade_overview_page("lumi-prestige/index.html", "prestige")
    upgrade_overview_page("lumi-elite/index.html", "elite")
    upgrade_css()
    upgrade_sitemap()
