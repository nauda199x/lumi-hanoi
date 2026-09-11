#!/usr/bin/env python3
"""Enrich the Lumi Hanoi price page with market index and sale-price history.

Runs after the marketplace SEO generator. Values come only from approved public
listings with a valid price and area. Apartment and shop statistics stay separate.
The sale-price history stores one real monthly snapshot and never fabricates
historical points.
"""
from __future__ import annotations

import json
import re
from datetime import date
from statistics import mean

import generate_marketplace_seo as gen

TOWER_INDEX_START = "<!-- MARKET-TOWER-INDEX:START -->"
TOWER_INDEX_END = "<!-- MARKET-TOWER-INDEX:END -->"
SALE_HISTORY_START = "<!-- SALE-PRICE-HISTORY:START -->"
SALE_HISTORY_END = "<!-- SALE-PRICE-HISTORY:END -->"
HISTORY_PATH = gen.ROOT / "data" / "lumi-sale-price-history.json"
TOWERS = (
    ("S1", "Signature"),
    ("S2", "Signature"),
    ("S3", "Signature"),
    ("S5", "Signature"),
    ("S6", "Signature"),
    ("P1", "Prestige"),
    ("P2", "Prestige"),
    ("E1", "Elite"),
    ("E2", "Elite"),
)


def tower_rows(listings: list[dict], listing_type: str, tower: str) -> list[dict]:
    rows = []
    for listing in listings:
        if listing.get("listing_type") != listing_type:
            continue
        if gen.clean(listing.get("tower")).upper() != tower:
            continue
        unit = gen.clean(listing.get("unit_type"))
        if unit not in gen.APARTMENT_UNIT_TYPES:
            continue
        price = gen.numeric(listing.get("price_vnd"))
        area = gen.numeric(listing.get("area_sqm"))
        if not price or not area:
            continue
        rows.append(listing)
    return rows


def average_stats(rows: list[dict]) -> dict[str, float | int | None]:
    pairs = [
        (gen.numeric(row.get("price_vnd")), gen.numeric(row.get("area_sqm")))
        for row in rows
    ]
    pairs = [(price, area) for price, area in pairs if price and area]
    if not pairs:
        return {"count": 0, "price": None, "ppsm": None}
    prices = [price for price, _ in pairs]
    return {
        "count": len(pairs),
        "price": mean(prices),
        "ppsm": mean(price / area for price, area in pairs),
    }


def inventory_link(listing_type: str, tower: str) -> str:
    segment = "cho-thue-lumi-hanoi" if listing_type == "rent" else "mua-ban-lumi-hanoi"
    return f"/{segment}/#tower={tower}"


def count_link(listing_type: str, tower: str, count: int) -> str:
    label = f"{count} tin" if count else "0 tin"
    return f'<a href="{gen.esc(inventory_link(listing_type, tower))}">{label}</a>'


def render_row(listings: list[dict], tower: str, phase: str) -> str:
    sale = average_stats(tower_rows(listings, "sale", tower))
    rent = average_stats(tower_rows(listings, "rent", tower))
    sale_price = gen.format_market_price(sale["price"], "sale") if sale["count"] else "—"
    sale_ppsm = gen.format_market_ppsm(sale["ppsm"], "sale") if sale["count"] else "—"
    rent_price = gen.format_market_price(rent["price"], "rent") if rent["count"] else "—"
    floor_url = gen.tower_link(tower)
    return (
        "<tr>"
        f'<th><a href="{gen.esc(floor_url)}">Tòa {gen.esc(tower)}</a></th>'
        f"<td>{gen.esc(phase)}</td>"
        f'<td>{count_link("sale", tower, int(sale["count"]))}</td>'
        f"<td>{gen.esc(sale_price)}</td>"
        f"<td>{gen.esc(sale_ppsm)}</td>"
        f'<td>{count_link("rent", tower, int(rent["count"]))}</td>'
        f"<td>{gen.esc(rent_price)}</td>"
        "</tr>"
    )


def render_tower_index(listings: list[dict]) -> str:
    rows = "\n        ".join(render_row(listings, tower, phase) for tower, phase in TOWERS)
    return f"""{TOWER_INDEX_START}
    <div class="market-table-card market-tower-index">
      <div class="market-table-head">
        <div><p class="eyebrow">Theo từng tòa</p><h3>Market Index S1–S6, P1–P2, E1–E2</h3></div>
        <a href="/mat-bang-lumi-hanoi/">Xem thư viện mặt bằng →</a>
      </div>
      <p class="market-index-note">Đối chiếu nguồn cung và giá chào theo từng tòa. Nhấn tên tòa để xem mặt bằng; nhấn số tin để mở quỹ căn đang bán hoặc cho thuê đã lọc đúng tòa.</p>
      <div class="market-table-scroll"><table>
        <thead><tr><th>Tòa</th><th>Phân khu</th><th>Tin bán</th><th>Giá bán TB</th><th>Giá/m² TB</th><th>Tin thuê</th><th>Giá thuê TB</th></tr></thead>
        <tbody>
        {rows}
        </tbody>
      </table></div>
      <p class="market-index-source">Chỉ tính căn hộ có đủ giá rao và diện tích trong các tin đã duyệt đang công khai. Đây là giá chào tham khảo, không phải giá giao dịch công chứng.</p>
    </div>
{TOWER_INDEX_END}"""


def load_history() -> dict:
    if not HISTORY_PATH.exists():
        return {
            "metric": "average_asking_price_per_sqm",
            "unit": "VND/m2",
            "source": "Approved public apartment sale listings on lumi-hanoi.com",
            "series": [],
        }
    try:
        payload = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    series = payload.get("series")
    if not isinstance(series, list):
        series = []
    payload["metric"] = "average_asking_price_per_sqm"
    payload["unit"] = "VND/m2"
    payload["source"] = "Approved public apartment sale listings on lumi-hanoi.com"
    payload["series"] = series
    return payload


def record_monthly_sale_snapshot(listings: list[dict]) -> dict:
    history = load_history()
    stats = average_stats(gen.market_rows(listings, "sale"))
    if int(stats["count"] or 0) < 3 or not stats["ppsm"]:
        return history

    today = date.today()
    point = {
        "month": today.strftime("%Y-%m"),
        "average_ppsm": int(round(float(stats["ppsm"]))),
        "average_price": int(round(float(stats["price"] or 0))),
        "listing_count": int(stats["count"]),
        "captured_at": today.isoformat(),
    }
    clean_series = [
        item for item in history["series"]
        if isinstance(item, dict) and re.fullmatch(r"\d{4}-\d{2}", str(item.get("month", "")))
    ]
    by_month = {str(item["month"]): item for item in clean_series}
    by_month[point["month"]] = point
    history["series"] = [by_month[key] for key in sorted(by_month)]
    history["updated_at"] = today.isoformat()

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(
        json.dumps(history, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return history


def month_label(value: str) -> str:
    match = re.fullmatch(r"(\d{4})-(\d{2})", value or "")
    return f"T{int(match.group(2))}/{match.group(1)}" if match else value


def million_ppsm(value: int | float) -> str:
    amount = float(value) / 1_000_000
    return f"{amount:.1f}".replace(".", ",") + " tr/m²"


def smooth_path(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    if len(points) == 1:
        x, y = points[0]
        return f"M {x:.1f} {y:.1f}"
    parts = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        mid_x = (x0 + x1) / 2
        parts.append(
            f"C {mid_x:.1f} {y0:.1f}, {mid_x:.1f} {y1:.1f}, {x1:.1f} {y1:.1f}"
        )
    return " ".join(parts)


def history_chart_svg(series: list[dict]) -> str:
    width, height = 920, 300
    left, right, top, bottom = 74, 26, 26, 56
    plot_w = width - left - right
    plot_h = height - top - bottom

    values = [float(item["average_ppsm"]) for item in series if item.get("average_ppsm")]
    if not values:
        return ""

    low, high = min(values), max(values)
    if low == high:
        pad = max(low * 0.06, 5_000_000)
    else:
        pad = max((high - low) * 0.18, 2_000_000)
    y_min, y_max = max(0.0, low - pad), high + pad

    points: list[tuple[float, float]] = []
    for index, value in enumerate(values):
        x = left + (plot_w / (len(values) - 1) * index if len(values) > 1 else plot_w / 2)
        y = top + (y_max - value) / (y_max - y_min) * plot_h
        points.append((x, y))

    path = smooth_path(points)
    area = ""
    if len(points) > 1:
        area = (
            path
            + f" L {points[-1][0]:.1f} {top + plot_h:.1f}"
            + f" L {points[0][0]:.1f} {top + plot_h:.1f} Z"
        )

    grids = []
    y_labels = []
    for index in range(5):
        y = top + plot_h * index / 4
        value = y_max - (y_max - y_min) * index / 4
        grids.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" class="sale-history-grid"/>'
        )
        y_labels.append(
            f'<text x="{left-12}" y="{y+4:.1f}" text-anchor="end" class="sale-history-axis">{value/1_000_000:.0f}</text>'
        )

    label_indexes = list(range(len(series)))
    if len(series) > 7:
        step = max(1, (len(series) - 1) // 5)
        label_indexes = sorted(set([0, len(series) - 1] + list(range(0, len(series), step))))
    x_labels = []
    for index in label_indexes:
        x, _ = points[index]
        x_labels.append(
            f'<text x="{x:.1f}" y="{height-18}" text-anchor="middle" class="sale-history-axis">{gen.esc(month_label(str(series[index]["month"])))}</text>'
        )

    dots = []
    for index, ((x, y), item) in enumerate(zip(points, series)):
        extra = " sale-history-dot--latest" if index == len(points) - 1 else ""
        dots.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{6 if index == len(points)-1 else 4}" class="sale-history-dot{extra}">'
            f'<title>{gen.esc(month_label(str(item["month"])))}: {gen.esc(million_ppsm(item["average_ppsm"]))} · {int(item.get("listing_count") or 0)} tin</title>'
            "</circle>"
        )

    if len(points) == 1:
        x, y = points[0]
        single_hint = (
            f'<text x="{x:.1f}" y="{max(top+18, y-20):.1f}" text-anchor="middle" class="sale-history-single">'
            "Mốc dữ liệu đầu tiên</text>"
        )
    else:
        single_hint = ""

    area_markup = f'<path d="{area}" class="sale-history-area"/>' if area else ""
    return f"""<svg class="sale-history-svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="sale-history-svg-title sale-history-svg-desc">
      <title id="sale-history-svg-title">Lịch sử giá chào bán trung bình Lumi Hanoi</title>
      <desc id="sale-history-svg-desc">Đường giá bán trung bình theo mét vuông, tính từ các tin căn hộ bán đã duyệt và đang công khai.</desc>
      <defs>
        <linearGradient id="saleHistoryFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="currentColor" stop-opacity=".18"/>
          <stop offset="100%" stop-color="currentColor" stop-opacity=".015"/>
        </linearGradient>
      </defs>
      {''.join(grids)}
      {''.join(y_labels)}
      {''.join(x_labels)}
      {area_markup}
      <path d="{path}" class="sale-history-line"/>
      {''.join(dots)}
      {single_hint}
      <text x="18" y="{top+plot_h/2:.1f}" transform="rotate(-90 18 {top+plot_h/2:.1f})" text-anchor="middle" class="sale-history-unit">Triệu đồng/m²</text>
    </svg>"""


def render_sale_history(history: dict) -> str:
    series = [
        item for item in history.get("series", [])
        if isinstance(item, dict) and item.get("average_ppsm")
    ]
    if not series:
        body = """
        <div class="sale-history-empty">
          <strong>Đang chờ đủ dữ liệu bán để bắt đầu chuỗi lịch sử.</strong>
          <span>Hệ thống chỉ ghi nhận khi có ít nhất 3 tin căn hộ bán hợp lệ.</span>
        </div>"""
        latest = None
    else:
        latest = series[-1]
        body = history_chart_svg(series)

    if latest:
        latest_value = million_ppsm(latest["average_ppsm"])
        latest_count = int(latest.get("listing_count") or 0)
        start_label = month_label(str(series[0]["month"]))
        if len(series) >= 2:
            previous = float(series[-2]["average_ppsm"])
            current = float(latest["average_ppsm"])
            change = ((current - previous) / previous * 100) if previous else 0.0
            change_text = f"{change:+.1f}%".replace(".", ",")
            change_caption = f"so với {month_label(str(series[-2]['month']))}"
        else:
            change_text = "Đang tích lũy"
            change_caption = "cần thêm tháng để tính biến động"
    else:
        latest_value = "—"
        latest_count = 0
        start_label = "—"
        change_text = "—"
        change_caption = "chưa đủ dữ liệu"

    rows = "".join(
        "<tr>"
        f"<th>{gen.esc(month_label(str(item['month'])))}</th>"
        f"<td>{gen.esc(million_ppsm(item['average_ppsm']))}</td>"
        f"<td>{int(item.get('listing_count') or 0)} tin</td>"
        "</tr>"
        for item in reversed(series)
    )

    details = (
        f"""<details class="sale-history-data">
          <summary>Xem dữ liệu từng tháng</summary>
          <div class="market-table-scroll"><table>
            <thead><tr><th>Tháng</th><th>Giá bán TB/m²</th><th>Mẫu tin</th></tr></thead>
            <tbody>{rows}</tbody>
          </table></div>
        </details>"""
        if rows else ""
    )

    return f"""{SALE_HISTORY_START}
    <section class="sale-history-card" aria-labelledby="sale-history-title">
      <style>
        .sale-history-card{{margin:0 0 24px;padding:24px;border:1px solid rgba(18,24,36,.1);border-radius:24px;background:linear-gradient(180deg,#fff 0%,#fafafa 100%);box-shadow:0 18px 50px rgba(18,24,36,.06);overflow:hidden}}
        .sale-history-head{{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;margin-bottom:18px}}
        .sale-history-head .eyebrow{{margin:0 0 6px}}
        .sale-history-head h3{{margin:0;font-size:clamp(1.35rem,2.4vw,2rem);letter-spacing:-.035em}}
        .sale-history-head p:last-child{{max-width:620px;margin:8px 0 0;color:#667085;line-height:1.6}}
        .sale-history-badge{{flex:0 0 auto;padding:8px 12px;border:1px solid rgba(18,24,36,.1);border-radius:999px;background:#fff;font-size:.82rem;font-weight:700;color:#344054}}
        .sale-history-kpis{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:18px 0}}
        .sale-history-kpi{{padding:14px 16px;border:1px solid rgba(18,24,36,.08);border-radius:16px;background:#fff}}
        .sale-history-kpi span{{display:block;margin-bottom:5px;font-size:.76rem;color:#667085}}
        .sale-history-kpi strong{{display:block;font-size:1rem;letter-spacing:-.02em}}
        .sale-history-kpi small{{display:block;margin-top:4px;color:#98a2b3;font-size:.72rem}}
        .sale-history-plot{{min-height:250px;padding:8px 4px 0;border-radius:18px;background:radial-gradient(circle at 80% 10%,rgba(18,24,36,.04),transparent 38%)}}
        .sale-history-svg{{display:block;width:100%;height:auto;color:#111827;overflow:visible}}
        .sale-history-grid{{stroke:#e5e7eb;stroke-width:1;stroke-dasharray:4 7}}
        .sale-history-axis,.sale-history-unit{{fill:#98a2b3;font-size:11px;font-family:inherit}}
        .sale-history-line{{fill:none;stroke:currentColor;stroke-width:4;stroke-linecap:round;stroke-linejoin:round;filter:drop-shadow(0 5px 8px rgba(17,24,39,.12))}}
        .sale-history-area{{fill:url(#saleHistoryFill);stroke:none}}
        .sale-history-dot{{fill:#fff;stroke:#111827;stroke-width:3}}
        .sale-history-dot--latest{{fill:#111827;stroke:#fff;filter:drop-shadow(0 3px 6px rgba(17,24,39,.28))}}
        .sale-history-single{{fill:#667085;font-size:12px;font-family:inherit;font-weight:700}}
        .sale-history-note{{margin:10px 0 0;color:#667085;font-size:.82rem;line-height:1.55}}
        .sale-history-note strong{{color:#344054}}
        .sale-history-empty{{min-height:210px;display:grid;place-content:center;text-align:center;gap:6px;color:#667085}}
        .sale-history-empty strong{{color:#344054}}
        .sale-history-data{{margin-top:14px;border-top:1px solid rgba(18,24,36,.08);padding-top:12px}}
        .sale-history-data summary{{cursor:pointer;font-weight:700;color:#344054}}
        .sale-history-data .market-table-scroll{{margin-top:10px}}
        @media(max-width:760px){{
          .sale-history-card{{padding:18px 14px;border-radius:20px;margin-left:-2px;margin-right:-2px}}
          .sale-history-head{{display:block}}
          .sale-history-badge{{display:inline-flex;margin-top:12px}}
          .sale-history-kpis{{grid-template-columns:repeat(2,minmax(0,1fr))}}
          .sale-history-kpi{{padding:12px}}
          .sale-history-plot{{overflow-x:auto}}
          .sale-history-svg{{min-width:680px}}
        }}
      </style>
      <div class="sale-history-head">
        <div>
          <p class="eyebrow">Lịch sử giá bán</p>
          <h3 id="sale-history-title">Giá bán trung bình Lumi Hanoi theo thời gian</h3>
          <p>Biểu đồ theo dõi <strong>giá chào bán trung bình trên mỗi m²</strong> của căn hộ đã duyệt đang công khai. Đường cong được làm mượt để dễ nhìn nhưng mọi điểm dữ liệu đều là số ghi nhận thực tế.</p>
        </div>
        <span class="sale-history-badge">Chỉ giá bán · Không vẽ giá thuê</span>
      </div>
      <div class="sale-history-kpis">
        <div class="sale-history-kpi"><span>Giá bán TB hiện tại</span><strong>{gen.esc(latest_value)}</strong><small>trên mỗi m²</small></div>
        <div class="sale-history-kpi"><span>Biến động gần nhất</span><strong>{gen.esc(change_text)}</strong><small>{gen.esc(change_caption)}</small></div>
        <div class="sale-history-kpi"><span>Số tin trong mẫu</span><strong>{latest_count} tin</strong><small>căn bán hợp lệ</small></div>
        <div class="sale-history-kpi"><span>Bắt đầu ghi nhận</span><strong>{gen.esc(start_label)}</strong><small>tự cập nhật theo tháng</small></div>
      </div>
      <div class="sale-history-plot">{body}</div>
      <p class="sale-history-note"><strong>Cách tính:</strong> trung bình giá rao bán/m² từ các tin căn hộ bán đã duyệt có đủ giá và diện tích. Mỗi tháng lưu một snapshot; trong tháng hiện tại, snapshot được cập nhật theo quỹ tin mới nhất. Đây là giá chào tham khảo, không phải giá giao dịch công chứng.</p>
      {details}
    </section>
{SALE_HISTORY_END}"""


def upsert_sale_history(raw: str, block: str) -> str:
    if SALE_HISTORY_START in raw and SALE_HISTORY_END in raw:
        return re.sub(
            re.escape(SALE_HISTORY_START) + r".*?" + re.escape(SALE_HISTORY_END),
            lambda _: block,
            raw,
            count=1,
            flags=re.S,
        )
    anchor = gen.MARKET_PRICE_START
    position = raw.find(anchor)
    if position < 0:
        raise RuntimeError("Could not locate market price block on price page")
    position += len(anchor)
    return raw[:position] + "\n" + block + raw[position:]


def upsert_tower_index(raw: str, block: str) -> str:
    if TOWER_INDEX_START in raw and TOWER_INDEX_END in raw:
        return re.sub(
            re.escape(TOWER_INDEX_START) + r".*?" + re.escape(TOWER_INDEX_END),
            lambda _: block,
            raw,
            count=1,
            flags=re.S,
        )
    anchor = '<aside class="shop-market-box"'
    position = raw.find(anchor)
    if position < 0:
        raise RuntimeError("Could not locate shop market block on price page")
    return raw[:position] + block + "\n    " + raw[position:]


def main() -> None:
    if not gen.PRICE_PAGE.exists():
        raise RuntimeError(f"Price page does not exist: {gen.PRICE_PAGE}")
    listings = gen.fetch_approved()
    history = record_monthly_sale_snapshot(listings)
    raw = gen.PRICE_PAGE.read_text(encoding="utf-8")
    raw = raw.replace(
        '<p class="eyebrow">Snapshot thị trường</p><h2 id="market-snapshot-title">Dữ liệu căn hộ đang công khai</h2>',
        '<p class="eyebrow">Lumi Hanoi Market Index</p><h2 id="market-snapshot-title">Giá bán Lumi Hanoi và nguồn cung đang công khai</h2>',
        1,
    )
    raw = upsert_sale_history(raw, render_sale_history(history))
    raw = upsert_tower_index(raw, render_tower_index(listings))
    gen.PRICE_PAGE.write_text(raw, encoding="utf-8")
    print(
        "Market Index: added tower statistics and monthly sale-price history "
        "(rent remains table-only)"
    )


if __name__ == "__main__":
    main()
