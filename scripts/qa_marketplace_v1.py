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
assert 'select:"id,slug,listing_code,listing_type,title,description' in api, "Public detail must use an explicit safe column list"
assert "service-role" in config.lower() and "supabaseAnonKey" in config
assert "service_role" not in config

print("Marketplace V1 QA passed: public lists, submission, detail, admin and RLS schema verified.")
