-- Guest listing management links
-- Safe to apply to the existing production database. Existing listings remain valid
-- but only new listings created by the updated form receive a management token.

begin;

alter table public.listings
  add column if not exists edit_token_hash text;

alter table public.listings
  drop constraint if exists listings_edit_token_hash_format;

alter table public.listings
  add constraint listings_edit_token_hash_format
  check (edit_token_hash is null or edit_token_hash ~ '^[0-9a-f]{64}$') not valid;

alter table public.listings
  validate constraint listings_edit_token_hash_format;

create unique index if not exists listings_edit_token_hash_uidx
  on public.listings(edit_token_hash)
  where edit_token_hash is not null;

grant insert (edit_token_hash) on public.listings to anon;

notify pgrst, 'reload schema';

commit;
