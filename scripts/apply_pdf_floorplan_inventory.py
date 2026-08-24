#!/usr/bin/env python3
"""Integrate PDF-derived floor plans into the public 9-tower lookup experience."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def sub_once(text: str, pattern: str, replacement: str, label: str) -> str:
    result, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one regex match, found {count}")
    return result


def plan(label: str, anchor: str, asset: str, drive_id: str, source: str) -> dict:
    return {
        "label": label,
        "anchor": anchor,
        "asset": asset,
        "driveId": drive_id,
        "source": source,
        "width": 1980,
        "height": 1453,
    }


def update_manifest() -> None:
    path = ROOT / "assets/data/floor-plans.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    additions = {
        "S1": [plan("Tầng 35", "s1-tang-35", "/assets/media/signature/penthouse/s1-floor-35.webp", "1E8bquyIGKfjJmzw1DMFz7QhauYp_M91K", "Signature 1 _ Floor 35.pdf")],
        "S2": [plan("Tầng 35", "s2-tang-35", "/assets/media/signature/penthouse/s2-floor-35.webp", "11Jj-zHsk1Tk84aFhuzcUDkZiKSZXYqHn", "Signature 2 _ Floor 35.pdf")],
        "S3": [plan("Tầng 35", "s3-tang-35", "/assets/media/signature/penthouse/s3-floor-35.webp", "1vMyv4hj7SYKgTlzge7-2opnkCbHU0FFo", "Signature 3 _ Floor 35.pdf")],
        "S5": [plan("Tầng 34", "s5-tang-34", "/assets/media/signature/penthouse/s5-floor-34.webp", "1bTusfxZrbE9ZAuDLUvF4tDIXUWfpbgUJ", "Signature 5 _ Floor 34.pdf")],
        "S6": [
            plan("Tầng 34", "s6-tang-34", "/assets/media/signature/penthouse/s6-floor-34.webp", "1GbYNZe3MJtbe497rrxwmeEv6HfLCHL4i", "Signature 6 _ Floor 34-35.pdf"),
            plan("Tầng 35", "s6-tang-35", "/assets/media/signature/penthouse/s6-floor-35.webp", "1GbYNZe3MJtbe497rrxwmeEv6HfLCHL4i", "Signature 6 _ Floor 34-35.pdf"),
        ],
        "P1": [plan("Tầng 30", "p1-tang-30", "/assets/media/prestige/floor-plans/p1-t30.webp", "19-uso6U9FWLVs-uN68nqMzKWq6Joxcny", "Prestige 1 _ Floor 29-30.pdf")],
        "P2": [plan("Tầng 30", "p2-tang-30", "/assets/media/prestige/floor-plans/p2-t30.webp", "13XRjgsJbuvXJrymVCBUfucYI4ZM251Qu", "Prestige 2_ Floor 29-30.pdf")],
        "E1": [plan("Tầng 29", "e1-tang-29", "/assets/media/elite/floor-plans/e1-t29.webp", "1yfcTt8xlQ7_yVABnKUuqnS1JY0Ty7ZbM", "Lumi Elite 1 _ Floor 29.pdf")],
        "E2": [
            plan("Tầng 24", "e2-tang-24", "/assets/media/elite/floor-plans/e2-t24.webp", "1zqhh1L1f4Nbo4I-ecD1YbgO3y26_fdgU", "Elite 2 _ Floor 24.pdf"),
            plan("Tầng 29", "e2-tang-29", "/assets/media/elite/floor-plans/e2-t29.webp", "1zNXaIpnwT5wCTrxl8Q7bG7Cg5n7NJ1Gz", "Lumi Elite 2 _ Floor 29.pdf"),
        ],
    }
    for tower, records in additions.items():
        plans = data["towers"][tower]["plans"]
        anchors = {item["anchor"] for item in plans}
        for record in records:
            if record["anchor"] not in anchors:
                plans.append(record)
    data["supplemental"] = []
    data["version"] = "8.3"
    data["updated"] = "2026-08-24"
    data["notes"] = "Single source of truth for 9 tower lookup pages. PDF-only top/special floors are converted to local WebP previews and kept as in-page floor groups."
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def update_renderer() -> None:
    path = ROOT / "assets/js/floor-plan-tower.js"
    text = path.read_text(encoding="utf-8")
    old = '<img class="figure-image floor-plan-image" src="${esc(src)}" width="2400" height="3200" alt="Mặt bằng tòa ${esc(tower)} Lumi Hanoi — ${esc(p.label)}" loading="lazy" decoding="async">'
    new = '<img class="figure-image floor-plan-image" src="${esc(src)}" width="${esc(p.width||2400)}" height="${esc(p.height||3200)}" alt="Mặt bằng tòa ${esc(tower)} Lumi Hanoi — ${esc(p.label)}" loading="lazy" decoding="async">'
    text = replace_once(text, old, new, "dynamic image dimensions")
    path.write_text(text, encoding="utf-8")


def update_prestige_pages() -> None:
    replacements = {
        "toa-prestige-1-lumi-hanoi/index.html": [
            ("theo 4 nhóm tầng Prestige", "theo 5 nhóm tầng Prestige"),
            ("4 nhóm tầng kỹ thuật của P1, gồm tầng 20, 23 và 29 riêng, liên kết trực tiếp tới thư viện layout Prestige.", "5 nhóm tầng kỹ thuật của P1, gồm tầng 20, 23, 29 và tầng 30 Penthouse riêng, liên kết trực tiếp tới thư viện layout Prestige."),
        ],
        "toa-prestige-2-lumi-hanoi/index.html": [
            ("theo 4 nhóm tầng Prestige", "theo 5 nhóm tầng Prestige"),
            ("4 nhóm tầng kỹ thuật của P2, gồm tầng 13, 20 và 29 riêng, liên kết trực tiếp tới thư viện layout Prestige.", "5 nhóm tầng kỹ thuật của P2, gồm tầng 13, 20, 29 và tầng 30 Penthouse riêng, liên kết trực tiếp tới thư viện layout Prestige."),
        ],
    }
    for rel, pairs in replacements.items():
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        for old, new in pairs:
            if old not in text:
                raise RuntimeError(f"{rel}: missing expected copy: {old}")
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")


def update_elite_pages() -> None:
    e1_path = ROOT / "toa-elite-1-lumi-hanoi/index.html"
    e1 = e1_path.read_text(encoding="utf-8")
    e1 = e1.replace("theo 4 nhóm tầng đã xác thực", "theo 5 nhóm tầng đã xác thực")
    e1 = replace_once(e1, "4 nhóm mặt bằng được giữ đúng theo tên và phạm vi tầng trên tài liệu nguồn.", "5 nhóm mặt bằng được giữ đúng theo tên và phạm vi tầng trên tài liệu nguồn, gồm mặt bằng Penthouse tầng 29.", "E1 lead")
    e1 = replace_once(
        e1,
        '<a href="#e1-tang-18-20-22-24-26-28">Tầng 18, 20, 22, 24, 26, 28</a></nav>',
        '<a href="#e1-tang-18-20-22-24-26-28">Tầng 18, 20, 22, 24, 26, 28</a><a href="#e1-tang-29">Tầng 29 · Penthouse</a></nav>',
        "E1 nav",
    )
    e1_section = '<section class="floor-plan-section" id="e1-tang-29" data-tower="E1" data-floor-group="Tầng 29"><div class="plan-section-head"><div><p class="eyebrow">Elite · E1</p><h2>E1 — Tầng 29</h2></div><a class="source-mini" href="https://drive.google.com/file/d/1yfcTt8xlQ7_yVABnKUuqnS1JY0Ty7ZbM/view" rel="noopener noreferrer">Bản nguồn ↗</a></div><figure class="figure floor-plan-figure"><a href="/assets/media/elite/floor-plans/e1-t29.webp" data-lightbox data-lightbox-alt="Mặt bằng tầng 29 Penthouse tòa E1 Lumi Hanoi" data-lightbox-caption="Tòa E1 — Tầng 29 Penthouse"><img class="figure-image floor-plan-image" src="/assets/media/elite/floor-plans/e1-t29.webp" width="1980" height="1453" alt="Mặt bằng tầng 29 Penthouse tòa E1 Lumi Hanoi" loading="lazy" decoding="async"></a><figcaption class="figure-caption">Mặt bằng E1 — Tầng 29 Penthouse.</figcaption></figure></section>'
    e1 = replace_once(e1, "<h2>Tiếp tục từ tầng tới căn hộ</h2>", e1_section + "<h2>Tiếp tục từ tầng tới căn hộ</h2>", "E1 floor 29 section")
    e1_path.write_text(e1, encoding="utf-8")

    e2_path = ROOT / "toa-elite-2-lumi-hanoi/index.html"
    e2 = e2_path.read_text(encoding="utf-8")
    old_desc = "Tra cứu mặt bằng tòa E2 Lumi Hanoi theo 5 nguồn mặt bằng: 4 nhóm ảnh kỹ thuật và PDF riêng tầng 24; mở bản vẽ để đọc mã căn, lõi thang và chú giải."
    new_desc = "Tra cứu mặt bằng tòa E2 Lumi Hanoi theo 6 nhóm tầng đã xác thực, gồm tầng 24 và tầng 29 Penthouse; mở ảnh kỹ thuật để đọc mã căn, lõi thang và chú giải."
    if old_desc not in e2:
        raise RuntimeError("E2 description copy not found")
    e2 = e2.replace(old_desc, new_desc)
    e2 = replace_once(e2, "5 nguồn mặt bằng được giữ đúng theo tên và phạm vi tầng trên tài liệu nguồn.", "6 nhóm mặt bằng được giữ đúng theo tên và phạm vi tầng trên tài liệu nguồn, gồm tầng 24 và tầng 29 Penthouse.", "E2 lead")
    e2 = replace_once(
        e2,
        '<a href="#e2-tang-24">Tầng 24 · PDF</a></nav>',
        '<a href="#e2-tang-24">Tầng 24</a><a href="#e2-tang-29">Tầng 29 · Penthouse</a></nav>',
        "E2 nav",
    )
    e2_t24 = '<section class="floor-plan-section" id="e2-tang-24" data-tower="E2" data-floor-group="Tầng 24"><div class="plan-section-head"><div><p class="eyebrow">Elite · E2</p><h2>E2 — Tầng 24</h2></div><a class="source-mini" href="https://drive.google.com/file/d/1zqhh1L1f4Nbo4I-ecD1YbgO3y26_fdgU/view" rel="noopener noreferrer">Bản nguồn ↗</a></div><figure class="figure floor-plan-figure"><a href="/assets/media/elite/floor-plans/e2-t24.webp" data-lightbox data-lightbox-alt="Mặt bằng tầng 24 tòa E2 Lumi Hanoi" data-lightbox-caption="Tòa E2 — Tầng 24"><img class="figure-image floor-plan-image" src="/assets/media/elite/floor-plans/e2-t24.webp" width="1980" height="1453" alt="Mặt bằng tầng 24 tòa E2 Lumi Hanoi" loading="lazy" decoding="async"></a><figcaption class="figure-caption">Mặt bằng E2 — Tầng 24.</figcaption></figure></section>'
    e2 = sub_once(e2, r'<section class="floor-plan-section supplemental-plan" id="e2-tang-24">.*?</section>', e2_t24, "E2 floor 24 PDF card")
    e2_t29 = '<section class="floor-plan-section" id="e2-tang-29" data-tower="E2" data-floor-group="Tầng 29"><div class="plan-section-head"><div><p class="eyebrow">Elite · E2</p><h2>E2 — Tầng 29</h2></div><a class="source-mini" href="https://drive.google.com/file/d/1zNXaIpnwT5wCTrxl8Q7bG7Cg5n7NJ1Gz/view" rel="noopener noreferrer">Bản nguồn ↗</a></div><figure class="figure floor-plan-figure"><a href="/assets/media/elite/floor-plans/e2-t29.webp" data-lightbox data-lightbox-alt="Mặt bằng tầng 29 Penthouse tòa E2 Lumi Hanoi" data-lightbox-caption="Tòa E2 — Tầng 29 Penthouse"><img class="figure-image floor-plan-image" src="/assets/media/elite/floor-plans/e2-t29.webp" width="1980" height="1453" alt="Mặt bằng tầng 29 Penthouse tòa E2 Lumi Hanoi" loading="lazy" decoding="async"></a><figcaption class="figure-caption">Mặt bằng E2 — Tầng 29 Penthouse.</figcaption></figure></section>'
    e2 = replace_once(e2, "<h2>Tiếp tục từ tầng tới căn hộ</h2>", e2_t29 + "<h2>Tiếp tục từ tầng tới căn hộ</h2>", "E2 floor 29 section")
    e2_path.write_text(e2, encoding="utf-8")


def update_hub() -> None:
    path = ROOT / "mat-bang-lumi-hanoi/index.html"
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, "<strong>54+</strong><span>bản/nhóm tầng xác thực</span>", "<strong>65</strong><span>bản/nhóm tầng xác thực</span>", "hub total")
    for tower, old_count, new_count in [("S1", 7, 8), ("S2", 7, 8), ("S3", 7, 8), ("S5", 7, 8), ("S6", 10, 12)]:
        text = replace_once(text, f'<h3>{tower}</h3><span class="tower-count">{old_count} nhóm tầng</span>', f'<h3>{tower}</h3><span class="tower-count">{new_count} nhóm tầng</span>', f"hub {tower} count")
    text = replace_once(text, "8 bản mặt bằng tầng đã có asset WebP local trong repo", "10 bản mặt bằng tầng đã có asset WebP local trong repo, gồm cả tầng 30 Penthouse của P1 và P2", "hub Prestige copy")
    text = replace_once(text, '<h3>P1</h3><span class="tower-count">4 nhóm tầng</span>', '<h3>P1</h3><span class="tower-count">5 nhóm tầng</span>', "hub P1 count")
    text = replace_once(text, '<span>T23</span><span>T29</span></div><a class="btn tower-card-cta" href="/toa-prestige-1-lumi-hanoi/">', '<span>T23</span><span>T29</span><span>T30</span></div><a class="btn tower-card-cta" href="/toa-prestige-1-lumi-hanoi/">', "hub P1 chip")
    text = replace_once(text, '<h3>P2</h3><span class="tower-count">4 nhóm tầng</span>', '<h3>P2</h3><span class="tower-count">5 nhóm tầng</span>', "hub P2 count")
    text = replace_once(text, '<span>T13</span><span>T20</span><span>T29</span></div><a class="btn tower-card-cta" href="/toa-prestige-2-lumi-hanoi/">', '<span>T13</span><span>T20</span><span>T29</span><span>T30</span></div><a class="btn tower-card-cta" href="/toa-prestige-2-lumi-hanoi/">', "hub P2 chip")
    text = replace_once(text, "Brochure đã được phân nhóm đúng E1/E2; E2 có thêm PDF tầng 24 riêng.", "Brochure đã được phân nhóm đúng E1/E2; các PDF tầng đặc biệt đã được chuyển thành ảnh WebP để tra cứu trực tiếp.", "hub Elite copy")
    text = replace_once(text, '<h3>E1</h3><span class="tower-count">4 nhóm tầng</span>', '<h3>E1</h3><span class="tower-count">5 nhóm tầng</span>', "hub E1 count")
    text = replace_once(text, '<h3>E2</h3><span class="tower-count">4 nhóm + PDF T24</span>', '<h3>E2</h3><span class="tower-count">6 nhóm tầng</span>', "hub E2 count")
    path.write_text(text, encoding="utf-8")


def update_qa() -> None:
    path = ROOT / "scripts/qa_floorplans_v8_2.py"
    text = path.read_text(encoding="utf-8")
    text = replace_once(text, '== 54, "expected 54 image plan records"', '== 65, "expected 65 image plan records after PDF conversion"', "QA image count")
    text = sub_once(
        text,
        r'    supplemental = data\.get\("supplemental", \[\]\)\n    assert len\(supplemental\) == 1, "expected exactly one supplemental record"\n    e2_pdf = supplemental\[0\]\n    assert e2_pdf\.get\("tower"\) == "E2" and e2_pdf\.get\("floorLabel"\) == "Tầng 24"\n    assert e2_pdf\.get\("sourceDriveId"\) == "1zqhh1L1f4Nbo4I-ecD1YbgO3y26_fdgU"\n',
        '    supplemental = data.get("supplemental", [])\n    assert not supplemental, "PDF-only floor plans must be converted to normal image records"\n',
        "QA supplemental block",
    )
    text = replace_once(
        text,
        '            if phase == "prestige":\n                asset = plan.get("asset")\n                assert asset, f"{tower}: Prestige plan missing local asset"\n                assert (ROOT / asset.lstrip("/")).exists(), f"{tower}: missing {asset}"',
        '            asset = plan.get("asset")\n            if asset:\n                assert (ROOT / asset.lstrip("/")).exists(), f"{tower}: missing {asset}"\n            if phase == "prestige":\n                assert asset, f"{tower}: Prestige plan missing local asset"',
        "QA asset checks",
    )
    text = sub_once(
        text,
        r'    e2 = read\("toa-elite-2-lumi-hanoi/index\.html"\)\n    assert e2_pdf\["sourceDriveId"\] in e2, "E2 floor-24 PDF missing from page"\n    assert "5 nguồn mặt bằng" in e2, "E2 source-count copy is inconsistent"\n',
        '    e2 = read("toa-elite-2-lumi-hanoi/index.html")\n    assert "/assets/media/elite/floor-plans/e2-t24.webp" in e2, "E2 floor-24 WebP missing from page"\n    assert "/assets/media/elite/floor-plans/e2-t29.webp" in e2, "E2 floor-29 WebP missing from page"\n    assert "6 nhóm mặt bằng" in e2, "E2 floor-group copy is inconsistent"\n',
        "QA E2 block",
    )
    text = text.replace("PASS: V8.2 floor-plan hub — 9 towers, 54 images, E2 floor-24 PDF, canonical/sitemap/redirect checks", "PASS: V8.3 floor-plan hub — 9 towers, 65 images including converted PDF floors, canonical/sitemap/redirect checks")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    update_manifest()
    update_renderer()
    update_prestige_pages()
    update_elite_pages()
    update_hub()
    update_qa()
    print("Applied V8.3 PDF floor-plan inventory integration.")


if __name__ == "__main__":
    main()
