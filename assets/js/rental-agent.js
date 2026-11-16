(() => {
  "use strict";
  const $ = (selector) => document.querySelector(selector);
  const search = $("#search"), request = $("#request"), config = window.LUMI_MARKETPLACE_CONFIG;
  if (!search || !request || !config?.supabaseUrl) return;
  const base = config.supabaseUrl.replace(/\/$/, "");
  const endpoint = base + "/functions/v1/lumi-rental-agent";
  const params = new URLSearchParams(location.search), attribution = {};
  const results = $("#results"), picked = $("#picked");
  const fmt = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 });
  const today = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh", year: "numeric", month: "2-digit", day: "2-digit" }).format();
  const fields = search.elements, contact = request.elements;
  let id = crypto.randomUUID(), preferred = "", searchVersion = 0;

  const track = (name, data = {}) => window.gtag?.("event", name, { page_path: location.pathname, ...data });
  function status(selector, message, error = false) {
    const node = $(selector);
    node.textContent = message;
    node.toggleAttribute("data-error", error);
  }
  function choose(slug, title, focus = true) {
    preferred = slug;
    picked.hidden = !slug;
    picked.querySelector("span").textContent = title;
    if (focus && slug) contact.phone.focus();
  }
  function needs() {
    return {
      unit_type: fields.unit_type.value,
      budget_vnd: Math.round(Number(fields.budget.value) * 1e6) || null,
      furnishing: fields.furnishing.value,
      move_in: fields.move_in.value,
      parking: fields.parking.checked,
    };
  }
  async function action(actionName, data) {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: config.supabasePublishableKey || config.supabaseAnonKey },
      body: JSON.stringify({ action: actionName, ...data }), signal: AbortSignal.timeout(18000),
    });
    const output = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(output.error || "Hệ thống đang bận. Anh/chị có thể nhắn Zalo cho Đức.");
    return output;
  }
  function card(row) {
    const wrapper = document.createElement("article");
    wrapper.className = "match";
    if (row.image_path) {
      const img = document.createElement("img");
      img.alt = "";
      img.loading = "lazy";
      img.src = base + "/storage/v1/object/public/listing-images/" + row.image_path.split("/").map(encodeURIComponent).join("/");
      img.addEventListener("error", () => img.remove(), { once: true });
      wrapper.append(img);
    }
    const body = document.createElement("div"), heading = document.createElement("h3"), link = document.createElement("a");
    link.href = "/cho-thue-lumi-hanoi/" + encodeURIComponent(row.slug) + "/";
    link.textContent = row.unit_type + " · " + row.tower + " · " + row.area_sqm + " m²";
    heading.append(link);
    const price = document.createElement("p");
    price.textContent = fmt.format(row.price_vnd / 1e6) + " triệu/tháng" + (row.furnishing ? " · " + row.furnishing : "");
    const timing = document.createElement("p");
    timing.textContent = (row.available_from ? "Ngày nhận theo tin: " + row.available_from.split("-").reverse().join("/") : "Hỏi lại ngày nhận nhà") +
      (row.parking_mentioned ? " · Tin có ghi chỗ ô tô" : "");
    const view = document.createElement("button");
    view.type = "button";
    view.className = "link";
    view.textContent = "Hỏi xem căn này";
    view.addEventListener("click", () => choose(row.slug, "Đã chọn " + link.textContent));
    body.append(heading, price, timing, view);
    wrapper.append(body);
    return wrapper;
  }

  for (const key of ["utm_source", "utm_medium", "utm_campaign", "utm_content", "gclid", "gbraid", "wbraid"]) {
    const value = params.get(key);
    if (value && /^[\p{L}0-9_./~ -]{1,130}$/u.test(value)) attribution[key] = value;
  }
  try {
    const from = new URL(document.referrer);
    if (from.origin === location.origin) attribution.landing_page = from.pathname;
    else if (!attribution.utm_source && /(^|\.)google\./i.test(from.hostname)) {
      attribution.utm_source = "google";
      attribution.utm_medium = "organic";
    }
  } catch {}
  attribution.landing_page ||= location.pathname;
  if (attribution.gclid || attribution.gbraid || attribution.wbraid) {
    attribution.utm_source ||= "google";
    if (!params.has("utm_medium")) attribution.utm_medium = "cpc";
  }
  if (Array.from(fields.unit_type.options).some((option) => option.value === params.get("loai"))) fields.unit_type.value = params.get("loai");
  const budget = Number(params.get("ngan_sach"));
  if (budget >= 1 && budget <= 200) fields.budget.value = budget;
  const slug = params.get("can");
  if (slug && /^[a-z0-9-]{8,120}$/.test(slug)) choose(slug, "Căn từ tin anh/chị đang xem", false);
  fields.move_in.min = today;
  contact.viewing_date.min = today;
  picked.querySelector("button").addEventListener("click", () => choose("", ""));

  $("#interpret").addEventListener("click", async (event) => {
    const button = event.currentTarget, note = fields.note.value.trim(), snapshot = JSON.stringify(needs()), version = searchVersion;
    if (note.length < 3) {
      status("#interpret-status", "Anh/chị nhập vài từ về căn đang tìm.", true);
      fields.note.focus();
      return;
    }
    button.disabled = true;
    status("#interpret-status", "Đang đọc mô tả…");
    try {
      const { needs: parsed } = await action("interpret", { note });
      if (snapshot !== JSON.stringify(needs()) || version !== searchVersion || fields.note.value.trim() !== note) {
        status("#interpret-status", "Tiêu chí vừa thay đổi. Anh/chị có thể chạy lại từ mô tả.");
        return;
      }
      for (const key of ["unit_type", "furnishing", "move_in"]) {
        if (parsed[key] && parsed[key] !== "any") fields[key].value = parsed[key];
      }
      if (parsed.budget_vnd) fields.budget.value = parsed.budget_vnd / 1e6;
      fields.parking.checked = parsed.parking;
      status("#interpret-status", "Anh/chị kiểm tra lại tiêu chí trước khi tìm căn.");
      track("rental_agent_interpreted");
    } catch (error) {
      status("#interpret-status", error.message, true);
    } finally { button.disabled = false; }
  });
  search.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = $("#find"), version = ++searchVersion, criteria = needs();
    button.disabled = true;
    results.replaceChildren();
    status("#search-status", "Đang tìm trong quỹ căn của Đức…");
    try {
      const { listings } = await action("search", criteria);
      if (version !== searchVersion || JSON.stringify(criteria) !== JSON.stringify(needs())) {
        status("#search-status", "Tiêu chí vừa thay đổi. Anh/chị có thể tìm lại.");
        return;
      }
      results.replaceChildren(...listings.map(card));
      status("#search-status", listings.length ? "Đức sẽ xác nhận lại giá, tình trạng và giờ xem." :
        "Chưa có căn khớp trên web. Anh/chị có thể gửi nhu cầu để Đức kiểm tra quỹ mới.");
      track("rental_agent_search", { result_count: listings.length });
    } catch (error) {
      status("#search-status", error.message, true);
    } finally { button.disabled = false; }
  });

  request.addEventListener("submit", async (event) => {
    event.preventDefault();
    const criteria = needs(), valid = search.reportValidity(), button = $("#send");
    if (!criteria.budget_vnd || !valid) {
      status("#request-status", "Anh/chị kiểm tra tiêu chí và nhập ngân sách tối đa.", true);
      if (!criteria.budget_vnd) fields.budget.focus();
      return;
    }
    button.disabled = true;
    status("#request-status", "Đang gửi…");
    try {
      const result = await action("submit", {
        ...criteria, id, attribution, preferred_listing: preferred, note: fields.note.value,
        phone: contact.phone.value, viewing_date: contact.viewing_date.value, viewing_period: contact.viewing_period.value,
        consent: contact.consent.checked, website: contact.website.value,
      });
      if (!result.ok) throw new Error("Chưa lưu được yêu cầu.");
      if (result.created) track("generate_lead", { lead_surface: "lumi_rental_agent", viewing_requested: Boolean(contact.viewing_date.value) });
      request.reset();
      choose("", "");
      id = crypto.randomUUID();
      status("#request-status", "Đã gửi yêu cầu. Đức sẽ liên hệ để xác nhận căn và giờ xem.");
    } catch (error) {
      status("#request-status", error.message, true);
    } finally { button.disabled = false; }
  });

  $("#zalo").addEventListener("click", () => track("rental_agent_zalo_click"));
  window.dataLayer ||= [];
  window.gtag ||= function () { window.dataLayer.push(arguments); };
  window.gtag("js", new Date());
  window.gtag("config", "G-EG08S7QJWG", { page_location: location.origin + location.pathname });
  const analytics = document.createElement("script");
  analytics.async = true;
  analytics.src = "https://www.googletagmanager.com/gtag/js?id=G-EG08S7QJWG";
  document.head.append(analytics);
})();
