-- Lumi Hanoi marketplace: allow concise listing descriptions.
-- Keep description required and reject whitespace-only values, while preserving
-- the existing 3000-character maximum.

begin;

alter table public.listings
  drop constraint if exists listings_description_check;

alter table public.listings
  add constraint listings_description_check
  check (char_length(btrim(description)) between 1 and 3000);

notify pgrst, 'reload schema';

commit;
