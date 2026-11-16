export const units = ["1PN", "2PN", "3PN", "4PN", "Duplex", "Penthouse", "any"];
export const furnishings = ["any", "Đồ cơ bản", "Full nội thất"];
export const clean = (value, limit) => typeof value === "string" ? value.trim().slice(0, limit) : "";
export const localDate = (stamp = Date.now()) => new Intl.DateTimeFormat("en-CA", {
  year: "numeric", month: "2-digit", day: "2-digit", timeZone: "Asia/Ho_Chi_Minh",
}).format(stamp);

const normalized = (s) => s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase().replaceAll("đ", "d");
const validBudget = (value) => Number.isInteger(value) && value >= 1e6 && value <= 2e8 ? value : null;
const validDate = (value) => /^\d{4}-\d{2}-\d{2}$/.test(value) &&
  Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;

export function hasParking(text) {
  return normalized(text).split(/[.\n;!?]+/).some((line) =>
    /\b(?:slot (?:xe ham|xe o to|o to|oto)|cho (?:(?:do|gui) )?(?:o to|oto|xe hoi)|car parking)\b/.test(line) &&
    !/\b(?:khong|ko co|chua|het|xac minh|xac nhan|tuy|neu can|uu tien|can hoi|can kiem tra)\b/.test(line));
}

export function parseNeeds(note, today = localDate()) {
  const text = normalized(clean(note, 500));
  const rooms = text.match(/\b([1-4])\s*(?:p\s*n|n(?:gu)?|phong ngu|bedrooms?|br)\b/);
  const amounts = Array.from(text.matchAll(/\b(\d{1,3}(?:[.,]\d{1,2})?)\s*(?:trieu|million|tr|m)(?![a-z0-9²])/g),
    (match) => Number(match[1].replace(",", ".")));
  const iso = text.match(/\b\d{4}-\d{2}-\d{2}\b/)?.[0];
  const local = text.match(/\b(\d{1,2})\/(\d{1,2})(?:\/(20\d{2}))?\b/);
  let move = iso || "";
  if (!iso && local) {
    const suffix = "-" + local[2].padStart(2, "0") + "-" + local[1].padStart(2, "0");
    const year = Number(today.slice(0, 4));
    move = (local[3] || year) + suffix;
    if (!local[3] && move < today) move = (year + 1) + suffix;
  } else if (!move && /\b(?:vao (?:o )?ngay|don (?:vao )?ngay|asap)\b/.test(text)) move = today;
  return {
    unit_type: rooms ? rooms[1] + "PN" : /\bpenthouse\b/.test(text) ? "Penthouse" : /\bduplex\b/.test(text) ? "Duplex" : "any",
    budget_vnd: validBudget(Math.round(Math.max(...amounts) * 1e6)),
    furnishing: /\b(?:co ban|unfurnished)\b/.test(text) ? "Đồ cơ bản" :
      /\b(?:full|day du noi that|fully furnished)\b/.test(text) ? "Full nội thất" : "any",
    parking: /\b(?:slot xe|slot o to|cho (?:(?:do|gui) )?(?:o to|oto|xe hoi)|parking)\b/.test(text) &&
      !/\b(?:khong can|ko can|k can|no need|no parking)\b/.test(text),
    move_in: move >= today && validDate(move) ? move : "",
  };
}

export function validateSearch(data, today = localDate()) {
  return {
    unit_type: units.includes(data.unit_type) ? data.unit_type : "any",
    budget_vnd: validBudget(data.budget_vnd),
    furnishing: furnishings.includes(data.furnishing) ? data.furnishing : "any",
    parking: data.parking === true,
    move_in: typeof data.move_in === "string" && data.move_in >= today && validDate(data.move_in) ? data.move_in : "",
  };
}

export function matchListings(rows, needs) {
  return rows.filter((row) => !needs.parking || hasParking(row.title + "\n" + row.description))
    .sort((a, b) => {
      if (needs.move_in && Boolean(a.available_from) !== Boolean(b.available_from)) return a.available_from ? -1 : 1;
      return Number(a.price_vnd) - Number(b.price_vnd) || String(b.approved_at).localeCompare(String(a.approved_at));
    }).slice(0, 3).map((row) => ({
      slug: row.slug, unit_type: row.unit_type, tower: row.tower, price_vnd: Number(row.price_vnd),
      area_sqm: Number(row.area_sqm), furnishing: row.furnishing, available_from: row.available_from,
      parking_mentioned: hasParking(row.title + "\n" + row.description),
      image_path: row.listing_images?.[0]?.storage_path || "",
    }));
}

export function validateLead(data, today = localDate()) {
  const needs = validateSearch(data, today);
  const phone = clean(data.phone, 45).replace(/[ ().-]/g, "").replace(/^0084/, "+84").replace(/^\+84(?=\d{9}$)/, "0");
  if (!/^(?:\d{8,15}|\+[1-9]\d{7,14})$/.test(phone)) throw new Error("Vui lòng nhập số điện thoại/Zalo hợp lệ.");
  const id = clean(data.id, 40);
  if (!/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(id)) throw new Error("Vui lòng tải lại trang.");
  if (data.consent !== true) throw new Error("Vui lòng đồng ý để Đức liên hệ.");
  if (!needs.budget_vnd) throw new Error("Vui lòng nhập ngân sách tối đa.");
  if (data.move_in && !needs.move_in) throw new Error("Chọn ngày nhận nhà từ hôm nay trở đi.");
  const viewing = clean(data.viewing_date, 12);
  const period = ["morning", "afternoon", "evening"].includes(data.viewing_period) ? data.viewing_period : null;
  if ((viewing && (!validDate(viewing) || viewing < today || !period)) || (!viewing && period)) throw new Error("Chọn cả ngày xem và buổi muốn xem.");
  const preferred = clean(data.preferred_listing, 120);
  const attribution = {};
  for (const key of ["utm_source", "utm_medium", "utm_campaign", "utm_content", "gclid", "gbraid", "wbraid", "landing_page"]) {
    const value = clean(data.attribution?.[key], 150);
    if (/^[\p{L}0-9_./~ -]+$/u.test(value)) attribution[key] = value;
  }
  const nextWeek = localDate(Date.parse(today + "T12:00:00+07:00") + 7 * 86400000);
  return {
    ...needs, id, phone, attribution,
    move_in: needs.move_in || null, viewing_date: viewing || null, viewing_period: period,
    preferred_listing: /^[a-z0-9-]{8,120}$/.test(preferred) ? preferred : null,
    note: clean(data.note, 500) || null,
    priority: viewing || (needs.move_in && needs.move_in <= nextWeek) ? "hot" : "normal",
  };
}
