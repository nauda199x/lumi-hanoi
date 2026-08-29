#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required_files = [
    "assets/css/marketplace.css",
    "assets/js/marketplace-config.js",
    "assets/js/marketplace-api.js",
    "assets/js/marketplace-list.js",
    "assets/js/marketplace-form.js",
    "assets/js/marketplace-detail.js",
    "assets/js/marketplace-admin.js",
    "giao-dich-lumi-hanoi/index.html",
    "dang-tin-lumi-hanoi/index.html",
    "tin-dang-lumi-hanoi/index.html",
    "admin/index.html",
    "supabase/marketplace-schema.sql",
]
for relative in required_files:
    assert (ROOT / relative).is_file(), f"Missing {relative}"

sale = (ROOT / "mua-ban-lumi-hanoi/index.html").read_text(encoding="utf-8")
rent = (ROOT / "cho-thue-lumi-hanoi/index.html").read_text(encoding="utf-8")
submit = (ROOT / "dang-tin-lumi-hanoi/index.html").read_text(encoding="utf-8")
admin = (ROOT / "admin/index.html").read_text(encoding="utf-8")
detail = (ROOT / "tin-dang-lumi-hanoi/index.html").read_text(encoding="utf-8")
schema = (ROOT / "supabase/marketplace-schema.sql").read_text(encoding="utf-8")
config = (ROOT / "assets/js/marketplace-config.js").read_text(encoding="utf-8")
api = (ROOT / "assets/js/marketplace-api.js").read_text(encoding="utf-8")
home = (ROOT / "index.html").read_text(encoding="utf-8")
transaction_hub = (ROOT / "giao-dich-lumi-hanoi/index.html").read_text(encoding="utf-8")
site_js = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")

assert 'data-listing-type="sale"' in sale and 'marketplace-list.js' in sale
assert 'data-listing-type="rent"' in rent and 'marketplace-list.js' in rent
assert 'data-marketplace-submit' in submit and 'name="contact_public"' in submit
assert 'name="website"' in submit, "Submission form needs a honeypot"
assert 'data-marketplace-admin' in admin and 'noindex,nofollow' in admin
assert 'data-listing-detail' in detail and 'noindex,follow' in detail
assert "enable row level security" in schema.lower()
assert "listings_anon_submit_pending" in schema and "listings_admin_manage" in schema
assert "can_upload_pending_image" in schema, "Storage uploads must belong to a pending listing"
assert "revoke all on public.admin_users,public.listings" in schema
assert "create or replace function private.is_admin" in schema
assert "create or replace function public.is_admin" not in schema, "SECURITY DEFINER helpers must not live in an exposed schema"
assert "grant all on public.admin_users" not in schema, "Authenticated access must use least privilege"
assert "alter table public.listings set schema archive" in schema, "Existing empty scaffold must be preserved, not deleted"
assert "drop table" not in schema.lower(), "Marketplace setup must not destructively drop project tables"
assert "notify pgrst, 'reload schema'" in schema
assert 'select:"id,slug,listing_code,listing_type,title,description' in api, "Public detail must use an explicit safe column list"
assert "service-role" in config.lower() and "supabasePublishableKey" in config
assert "service_role" not in config
assert home.index('href="/tong-quan-lumi-hanoi/">Tổng quan</a>') < home.index("<summary>Giao dịch</summary>") < home.index('href="/mat-bang-lumi-hanoi/">Mặt bằng</a>')
assert '<a class="btn" href="/giao-dich-lumi-hanoi/">Giao dịch</a>' in home
assert 'href="/mua-ban-lumi-hanoi/"' in transaction_hub
assert 'href="/cho-thue-lumi-hanoi/"' in transaction_hub
assert 'href="/dang-tin-lumi-hanoi/"' in transaction_hub
assert "Cẩm nang giao dịch" not in home
assert "overviewLink.after(transactionDropdown)" in site_js, "Every legacy page must prioritize the transaction dropdown after Overview"

print("Marketplace V1 QA passed: public lists, submission, detail, admin and RLS schema verified.")
