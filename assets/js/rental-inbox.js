(async () => {
  "use strict";
  const $ = (selector) => document.querySelector(selector);
  const api = window.LumiMarketplace;
  if (!api) return;
  const root = api.config.supabaseUrl.replace(/\/$/, "") + "/rest/v1/lumi_rental_leads";
  const rows = $("#inbox-list"), filter = $("#filter"), hot = $("#hot"), message = $("#message"), more = $("#more"), reload = $("#reload");
  const labels = { new: "Mới", contacted: "Đã liên hệ", scheduled: "Đã hẹn", viewed: "Đã xem", signed: "Đã thuê", closed: "Đã đóng" };
  const periods = { morning: "Sáng", afternoon: "Chiều", evening: "Tối" };
  const zone = "Asia/Ho_Chi_Minh";
  const dayFormat = new Intl.DateTimeFormat("en-CA", { timeZone: zone, year: "numeric", month: "2-digit", day: "2-digit" });
  const datetime = new Intl.DateTimeFormat("vi-VN", { timeZone: zone, dateStyle: "short", timeStyle: "short" });
  const price = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 });
  const dateLabel = (date) => date.split("-").reverse().join("/");
  let cursor = null, busy = false, changing = 0, timer;

  function signInRequired() {
    clearInterval(timer);
    rows.replaceChildren();
    $("#inbox").hidden = true;
    $("#auth").hidden = false;
    const link = document.createElement("a");
    link.href = "/admin/";
    link.textContent = "Đăng nhập trang quản trị";
    $("#auth").replaceChildren(link, " để xem khách thuê.");
  }
  async function request(query, options = {}) {
    const session = await api.requireAdmin();
    if (!session) {
      signInRequired();
      throw new Error("Phiên quản trị đã hết hạn.");
    }
    const response = await fetch(root + "?" + query, {
      ...options, cache: "no-store", signal: AbortSignal.timeout(15000),
      headers: {
        apikey: api.config.supabasePublishableKey || api.config.supabaseAnonKey,
        Authorization: "Bearer " + session.access_token,
        "Content-Type": "application/json", ...options.headers,
      },
    });
    if (response.status === 401 || response.status === 403) signInRequired();
    if (!response.ok && !(options.method === "HEAD" && response.status === 416)) throw new Error("Không tải được khách thuê. Vui lòng thử lại.");
    return response;
  }
  async function refreshCounts() {
    const today = dayFormat.format() + "T00:00:00+07:00";
    const requests = [{ created_at: "gte." + today }, { status: "eq.new", priority: "eq.hot" }];
    const responses = await Promise.all(requests.map((parameters) =>
      request(new URLSearchParams({ select: "id", limit: "1", ...parameters }), { method: "HEAD", headers: { Prefer: "count=exact" } })));
    const [count, urgent] = responses.map((response) => response.headers.get("content-range")?.split("/")[1] || "—");
    $("#counts").textContent = count + " yêu cầu hôm nay · " + urgent + " khách ưu tiên chưa liên hệ";
    document.title = Number(urgent) > 0 ? "(" + urgent + ") Khách thuê Lumi Hà Nội" : "Khách thuê Lumi Hà Nội | Quản trị";
  }
  function paragraph(text, className = "") {
    const element = document.createElement("p");
    element.className = className;
    element.textContent = text;
    return element;
  }
  function link(href, label) {
    const element = document.createElement("a");
    element.href = href;
    element.textContent = label;
    return element;
  }
  function card(lead) {
    const wrapper = document.createElement("article"), headline = document.createElement("h2");
    wrapper.className = "lead";
    headline.textContent = (lead.unit_type === "any" ? "Loại căn linh hoạt" : lead.unit_type) + " · " + price.format(lead.budget_vnd / 1e6) + " triệu/tháng";
    wrapper.append(headline, paragraph(datetime.format(new Date(lead.created_at)) + " · " +
      (lead.attribution?.utm_source || "Nguồn trực tiếp/không rõ") +
      (lead.attribution?.utm_campaign ? " / " + lead.attribution.utm_campaign : "")));
    if (lead.priority === "hot" && lead.status === "new") wrapper.append(paragraph("Ưu tiên liên hệ", "hot"));
    const facts = [
      lead.furnishing === "any" ? "" : lead.furnishing, lead.parking ? "Cần chỗ ô tô" : "",
      lead.move_in ? "Nhận nhà " + dateLabel(lead.move_in) : "",
      lead.viewing_date ? "Muốn xem " + periods[lead.viewing_period] + " " + dateLabel(lead.viewing_date) : "",
    ].filter(Boolean);
    if (facts.length) wrapper.append(paragraph(facts.join(" · ")));
    if (lead.note) wrapper.append(paragraph(lead.note));
    if (lead.preferred_listing) wrapper.append(link("/cho-thue-lumi-hanoi/" + encodeURIComponent(lead.preferred_listing) + "/", "Mở căn khách quan tâm"));

    const actions = document.createElement("div"), select = document.createElement("select");
    actions.className = "actions";
    select.setAttribute("aria-label", "Trạng thái khách thuê");
    for (const [value, label] of Object.entries(labels)) select.add(new Option(label, value));
    select.value = lead.status;
    select.addEventListener("change", async () => {
      select.disabled = true;
      changing++;
      try {
        const response = await request(new URLSearchParams({ id: "eq." + lead.id, updated_at: "eq." + lead.updated_at, select: "id,status,updated_at" }), {
          method: "PATCH", body: JSON.stringify({ status: select.value }), headers: { Prefer: "return=representation" },
        });
        const [updated] = await response.json();
        if (!updated) throw new Error("Yêu cầu vừa thay đổi. Hãy tải lại danh sách.");
        Object.assign(lead, updated);
        if (filter.value && filter.value !== lead.status) wrapper.remove();
        else wrapper.replaceWith(card(lead));
        message.textContent = "Đã lưu trạng thái.";
        refreshCounts().catch(() => {});
      } catch (error) {
        select.value = lead.status;
        message.textContent = error.message;
      } finally {
        select.disabled = false;
        changing--;
      }
    });
    actions.append(link("tel:" + lead.phone, "Gọi " + lead.phone), select);
    if (/^0\d{9}$/.test(lead.phone)) actions.append(link("https://zalo.me/" + lead.phone, "Mở Zalo"));
    wrapper.append(actions);
    return wrapper;
  }
  async function load(append = false, background = false) {
    if (busy || changing) return;
    busy = true;
    filter.disabled = hot.disabled = more.disabled = reload.disabled = true;
    if (!background) message.textContent = "Đang tải…";
    try {
      const query = new URLSearchParams({ select: "*", order: "created_at.desc,id.desc", limit: "31" });
      if (filter.value) query.set("status", "eq." + filter.value);
      if (hot.checked) query.set("priority", "eq.hot");
      if (append && cursor) query.set("or", "(created_at.lt." + cursor.created_at + ",and(created_at.eq." + cursor.created_at + ",id.lt." + cursor.id + "))");
      const response = await request(query), data = await response.json();
      if (changing) return;
      const page = data.slice(0, 30), cards = page.map(card);
      if (append) rows.append(...cards);
      else rows.replaceChildren(...cards);
      cursor = page.at(-1) || null;
      more.hidden = data.length <= 30;
      if (!background) message.textContent = rows.children.length ? "" : "Chưa có khách thuê theo bộ lọc này.";
      refreshCounts().catch(() => {});
    } catch (error) {
      if (!background) message.textContent = error.message;
    } finally {
      filter.disabled = hot.disabled = more.disabled = reload.disabled = false;
      busy = false;
    }
  }
  if (!await api.requireAdmin()) return signInRequired();
  $("#auth").hidden = true;
  $("#inbox").hidden = false;
  filter.addEventListener("change", () => load());
  hot.addEventListener("change", () => load());
  reload.addEventListener("click", () => load());
  more.addEventListener("click", () => load(true));
  await load();
  if ($("#inbox").hidden) return;
  timer = setInterval(() => {
    if (document.visibilityState !== "visible") return;
    if (rows.children.length <= 30 && !rows.contains(document.activeElement)) load(false, true);
    else refreshCounts().catch(() => {});
  }, 60000);
})();
