import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Cache-Control": "no-store",
};

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { ...cors, "Content-Type": "application/json; charset=utf-8" },
  });

const text = (value: unknown, max: number) => String(value ?? "").trim().slice(0, max);
const tokenPattern = /^[A-Za-z0-9_-]{43,90}$/;
const phases = new Set(["Signature", "Prestige", "Elite"]);
const towersByPhase: Record<string, Set<string>> = {
  Signature: new Set(["S1", "S2", "S3", "S5", "S6"]),
  Prestige: new Set(["P1", "P2"]),
  Elite: new Set(["E1", "E2"]),
};
const unitTypes = new Set(["1PN", "2PN", "3PN", "4PN", "Duplex", "Penthouse", "Shop chân đế"]);
const floorLabels = new Set(["Thấp", "Trung", "Cao"]);

const hashToken = async (token: string) => {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(token));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
};

const serviceHeaders = (serviceRole: string, extra: Record<string, string> = {}) => ({
  Authorization: `Bearer ${serviceRole}`,
  apikey: serviceRole,
  "Content-Type": "application/json",
  ...extra,
});

const safeListing = (row: Record<string, unknown>) => {
  const { edit_token_hash: _secret, ...safe } = row;
  return safe;
};

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);

  const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
  const serviceRole = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
  if (!supabaseUrl || !serviceRole) return json({ error: "Server configuration missing" }, 500);

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return json({ error: "Dữ liệu gửi lên không hợp lệ." }, 400);
  }

  const action = text(body.action, 30);
  const token = String(body.token || "");
  if (!tokenPattern.test(token)) return json({ error: "Link quản lý không hợp lệ hoặc đã mất quyền truy cập." }, 404);

  const tokenHash = await hashToken(token);
  const select = [
    "id", "listing_code", "slug", "listing_type", "status", "title", "description",
    "phase", "tower", "unit_type", "area_sqm", "floor_label", "price_vnd", "furnishing",
    "available_from", "legal_status", "poster_name", "contact_phone", "approved_at",
    "expires_at", "created_at", "updated_at", "edit_token_hash",
    "listing_images(id,storage_path,sort_order,alt_text)"
  ].join(",");

  const loadListing = async () => {
    const url = `${supabaseUrl}/rest/v1/listings?select=${encodeURIComponent(select)}&edit_token_hash=eq.${encodeURIComponent(tokenHash)}&limit=1`;
    const response = await fetch(url, {
      headers: serviceHeaders(serviceRole, { Accept: "application/json" }),
    });
    if (!response.ok) throw new Error("lookup_failed");
    const rows = await response.json();
    return Array.isArray(rows) && rows.length ? rows[0] : null;
  };

  let listing: Record<string, unknown> | null;
  try {
    listing = await loadListing();
  } catch {
    return json({ error: "Không đọc được tin lúc này." }, 502);
  }
  if (!listing) return json({ error: "Link quản lý không hợp lệ hoặc tin không còn tồn tại." }, 404);

  if (action === "get") return json({ ok: true, listing: safeListing(listing) });

  if (action === "hide" || action === "done") {
    const nextStatus = action === "hide"
      ? "expired"
      : (listing.listing_type === "rent" ? "rented" : "sold");
    const patch: Record<string, unknown> = {
      status: nextStatus,
      is_featured: false,
      sort_priority: 0,
    };
    if (action === "hide") patch.expires_at = new Date().toISOString();

    const url = `${supabaseUrl}/rest/v1/listings?id=eq.${encodeURIComponent(String(listing.id))}&edit_token_hash=eq.${encodeURIComponent(tokenHash)}`;
    const response = await fetch(url, {
      method: "PATCH",
      headers: serviceHeaders(serviceRole, { Prefer: "return=minimal" }),
      body: JSON.stringify(patch),
    });
    if (!response.ok) return json({ error: "Chưa cập nhật được trạng thái tin." }, 502);
    const refreshed = await loadListing();
    return json({ ok: true, listing: safeListing(refreshed || { ...listing, ...patch }) });
  }

  if (action !== "update") return json({ error: "Thao tác không được hỗ trợ." }, 400);

  const source = body.patch && typeof body.patch === "object" ? body.patch as Record<string, unknown> : {};
  const patch: Record<string, unknown> = {};

  if ("listing_type" in source) {
    const value = text(source.listing_type, 10);
    if (!["sale", "rent"].includes(value)) return json({ error: "Loại giao dịch không hợp lệ." }, 400);
    patch.listing_type = value;
  }
  if ("title" in source) {
    const value = text(source.title, 180);
    if (value.length < 10) return json({ error: "Tiêu đề cần ít nhất 10 ký tự." }, 400);
    patch.title = value;
  }
  if ("description" in source) {
    const value = text(source.description, 3000);
    if (!value) return json({ error: "Vui lòng nhập mô tả tin." }, 400);
    patch.description = value;
  }
  if ("phase" in source) {
    const value = text(source.phase, 30);
    if (!phases.has(value)) return json({ error: "Phân khu không hợp lệ." }, 400);
    patch.phase = value;
  }
  if ("tower" in source) patch.tower = text(source.tower, 10);
  if ("unit_type" in source) {
    const value = text(source.unit_type, 40);
    if (!unitTypes.has(value)) return json({ error: "Loại căn không hợp lệ." }, 400);
    patch.unit_type = value;
  }
  if ("area_sqm" in source) {
    const value = Number(source.area_sqm);
    if (!Number.isFinite(value) || value < 20 || value > 1000) return json({ error: "Diện tích không hợp lệ." }, 400);
    patch.area_sqm = Math.round(value * 100) / 100;
  }
  if ("price_vnd" in source) {
    const value = Math.round(Number(source.price_vnd));
    if (!Number.isFinite(value) || value < 1_000_000 || value > 1_000_000_000_000_000) {
      return json({ error: "Mức giá không hợp lệ." }, 400);
    }
    patch.price_vnd = value;
  }
  if ("floor_label" in source) {
    const value = text(source.floor_label, 20);
    if (value && !floorLabels.has(value)) return json({ error: "Khoảng tầng không hợp lệ." }, 400);
    patch.floor_label = value || null;
  }
  if ("furnishing" in source) patch.furnishing = text(source.furnishing, 80) || null;
  if ("available_from" in source) {
    const value = text(source.available_from, 10);
    if (value && !/^\d{4}-\d{2}-\d{2}$/.test(value)) return json({ error: "Ngày có thể vào ở không hợp lệ." }, 400);
    patch.available_from = value || null;
  }
  if ("legal_status" in source) patch.legal_status = text(source.legal_status, 120) || null;
  if ("poster_name" in source) {
    const value = text(source.poster_name, 120);
    if (value.length < 2) return json({ error: "Tên người đăng chưa hợp lệ." }, 400);
    patch.poster_name = value;
  }
  if ("contact_phone" in source) {
    const value = text(source.contact_phone, 30);
    if (value.length < 8) return json({ error: "Số điện thoại chưa hợp lệ." }, 400);
    patch.contact_phone = value;
  }

  const nextPhase = String(patch.phase ?? listing.phase ?? "");
  const nextTower = String(patch.tower ?? listing.tower ?? "");
  if (!phases.has(nextPhase) || !towersByPhase[nextPhase]?.has(nextTower)) {
    return json({ error: "Tòa không thuộc phân khu đã chọn." }, 400);
  }

  if (!Object.keys(patch).length) return json({ error: "Không có thay đổi để lưu." }, 400);

  patch.status = "pending";
  patch.approved_at = null;
  patch.expires_at = null;
  patch.is_featured = false;
  patch.sort_priority = 0;

  const updateUrl = `${supabaseUrl}/rest/v1/listings?id=eq.${encodeURIComponent(String(listing.id))}&edit_token_hash=eq.${encodeURIComponent(tokenHash)}`;
  const response = await fetch(updateUrl, {
    method: "PATCH",
    headers: serviceHeaders(serviceRole, { Prefer: "return=minimal" }),
    body: JSON.stringify(patch),
  });

  if (!response.ok) {
    const detail = (await response.text()).slice(0, 300);
    console.error("manage-listing update failed", response.status, detail);
    return json({ error: "Chưa lưu được thay đổi. Vui lòng thử lại." }, 502);
  }

  const refreshed = await loadListing();
  return json({
    ok: true,
    listing: safeListing(refreshed || { ...listing, ...patch }),
    message: "Đã lưu thay đổi và chuyển tin về chờ duyệt.",
  });
});
