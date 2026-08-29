# Lumi Hanoi Marketplace — Supabase

This directory contains the production schema for public submissions, admin moderation and listing images.

## Required setup

1. Apply `marketplace-schema.sql` to a dedicated Supabase project.
2. Create one admin in Supabase Authentication.
3. Insert that user's id into `public.admin_users` using the statement at the end of the schema.
4. Put only the project URL and **publishable** key in `assets/js/marketplace-config.js`.

Never put the service-role key, database password or admin password in this repository.

## Security model

- Anonymous visitors can insert only `pending` listings.
- Pending/rejected listings cannot be selected by public visitors.
- Only users listed in `admin_users` can approve, edit, feature or close listings.
- Public visitors can read only approved, unexpired listings whose contact disclosure was accepted.
- Images are limited by the bucket to JPG/PNG/WebP and 5 MB per object.

The browser configuration is intentionally public; authorization is enforced by PostgreSQL Row Level Security, not by hiding the publishable key.
