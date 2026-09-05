#!/usr/bin/env python3
"""Generate marketplace SEO pages with arithmetic averages on the market price page.

The base marketplace generator remains responsible for listing pages, sitemaps and
market aggregation. For the price page, its statistics function is switched from
median to arithmetic mean before generation, then the explanatory copy is kept in
sync with that methodology.
"""
import re
from statistics import mean

import generate_marketplace_seo as gen


def update_price_methodology_copy() -> None:
    path = gen.PRICE_PAGE
    if not path.exists():
        return

    raw = path.read_text(encoding="utf-8")
    replacements = {
        "giá bán/thuê trung vị": "giá bán/thuê trung bình",
        "Giá trung vị và giá trên mét vuông được tính từ giá rao và diện tích của các tin đang công khai; không phải giá giao dịch công chứng.":
            "Giá trung bình và giá trung bình trên mét vuông được tính từ giá rao và diện tích của các tin đang công khai; không phải giá giao dịch công chứng.",
        "Giá/m² được tính bằng giá rao chia cho diện tích khai báo của từng tin đủ dữ liệu, sau đó dùng trung vị để giảm ảnh hưởng của các mức giá quá cao hoặc quá thấp.":
            "Giá/m² được tính bằng giá rao chia cho diện tích khai báo của từng tin đủ dữ liệu, sau đó lấy trung bình cộng đơn giá/m² của các tin trong cùng nhóm.",
        "Giá bán trung vị": "Giá bán trung bình",
        "Giá/m² trung vị": "Giá/m² trung bình",
        "Dùng trung vị, không dùng trung bình": "Trung bình cộng từ các tin đủ dữ liệu",
        "Giá thuê trung vị": "Giá thuê trung bình",
        ">Trung vị</th>": ">Trung bình</th>",
        "Với mỗi nhóm, chúng tôi ưu tiên <strong>trung vị</strong> thay vì trung bình cộng để một tin quá cao hoặc quá thấp không kéo sai toàn bộ kết quả.":
            "Với mỗi nhóm, hệ thống tính <strong>trung bình cộng</strong> từ các tin đủ dữ liệu để phản ánh mức giá rao bình quân của nguồn hàng đang công khai.",
        "Dùng trung vị cho giá và giá/m².": "Dùng trung bình cộng cho giá và giá/m².",
        "<details><summary>Vì sao dùng trung vị?</summary><p>Trung vị ít bị méo bởi một vài mức giá bất thường hơn trung bình cộng, đặc biệt khi số tin của một nhóm còn chưa lớn.</p></details>":
            "<details><summary>Giá trung bình được tính thế nào?</summary><p>Hệ thống cộng các mức giá hợp lệ trong từng nhóm rồi chia cho số tin đủ dữ liệu. Giá/m² trung bình được tính từ đơn giá/m² của từng tin đủ giá và diện tích.</p></details>",
    }
    for old, new in replacements.items():
        raw = raw.replace(old, new)

    if "trung vị" in raw.lower():
        raise RuntimeError("Price page still contains median wording after average conversion")

    path.write_text(raw, encoding="utf-8")


def remove_rental_ppsm_display() -> None:
    """Keep rental market pricing in monthly totals; price/m² remains sale-only."""
    path = gen.PRICE_PAGE
    if not path.exists():
        return

    raw = path.read_text(encoding="utf-8")
    rent_marker = '<div class="market-table-head"><div><p class="eyebrow">Cho thuê</p><h3>Giá rao thuê theo loại căn</h3></div><a href="/cho-thue-lumi-hanoi/">Xem quỹ thuê →</a></div>'
    start = raw.find(rent_marker)
    if start < 0:
        raise RuntimeError("Could not locate rental price table")

    card_start = raw.rfind('<div class="market-table-card">', 0, start)
    next_card = raw.find('<div class="market-table-card">', start + len(rent_marker))
    if card_start < 0 or next_card < 0:
        raise RuntimeError("Could not isolate rental price table")

    block = raw[card_start:next_card]
    block = block.replace('<th>Giá/m²/tháng</th>', '')
    block = re.sub(
        r'(<tr><th>[^<]+</th><td>[^<]*</td><td>[^<]*</td><td>[^<]*</td>)<td>[^<]*</td>(</tr>)',
        r'\1\2',
        block,
    )
    raw = raw[:card_start] + block + raw[next_card:]

    # Shop rental pricing follows the same rule: show total monthly rent only.
    raw = re.sub(
        r'(<dt>Shop đang thuê</dt><dd>[^<]*?) · khoảng [^<]*(</dd>)',
        r'\1\2',
        raw,
        count=1,
    )

    if "Giá/m²/tháng" in raw:
        raise RuntimeError("Rental price/m² column still present after cleanup")

    path.write_text(raw, encoding="utf-8")


def main() -> None:
    # generate_marketplace_seo imports `median` into module scope. Rebinding that
    # symbol makes all price-page aggregate calculations use arithmetic mean,
    # including overall, unit-type, phase and shop statistics.
    gen.median = mean
    gen.main()
    update_price_methodology_copy()
    remove_rental_ppsm_display()
    print("Market price page: arithmetic-average methodology applied; rental price/m² hidden")


if __name__ == "__main__":
    main()
