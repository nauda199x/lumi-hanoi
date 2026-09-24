-- Lumi Hanoi marketplace moderation reasons
alter table public.listings
  add column if not exists moderation_reason text,
  add column if not exists moderation_note text,
  add column if not exists rejected_at timestamptz;

alter table public.listings drop constraint if exists listings_moderation_reason_check;
alter table public.listings add constraint listings_moderation_reason_check
check (
  moderation_reason is null or moderation_reason in (
    'price_bait','wrong_images','multiple_listings','inconsistent_info',
    'duplicate','unavailable','unverifiable','other'
  )
) not valid;
alter table public.listings validate constraint listings_moderation_reason_check;

alter table public.listings drop constraint if exists listings_moderation_note_check;
alter table public.listings add constraint listings_moderation_note_check
check (moderation_note is null or char_length(moderation_note) <= 500) not valid;
alter table public.listings validate constraint listings_moderation_note_check;
