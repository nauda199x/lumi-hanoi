-- Apply after marketplace-schema.sql. Public inventory uses feed_at for its
-- newest sort while the original publication date stays available for display.
alter table public.listings
  add column if not exists bumped_at timestamptz,
  add column if not exists feed_at timestamptz
  generated always as (greatest(coalesce(approved_at, created_at), bumped_at)) stored;

grant select (feed_at) on public.listings to anon;

create index if not exists listings_public_newest_idx
  on public.listings (listing_type, feed_at desc, created_at desc, id desc)
  where status = 'approved';

-- A generated value has not been computed yet in a BEFORE trigger.
-- Skip it in the comparison, including when just a view count changed.
create or replace function private.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if (to_jsonb(new) - 'updated_at' - 'view_count' - 'feed_at') is distinct from
     (to_jsonb(old) - 'updated_at' - 'view_count' - 'feed_at') then
    new.updated_at = now();
  else
    new.updated_at = old.updated_at;
  end if;
  return new;
end;
$$;

-- The existing admin-only listings RLS policy also applies inside this RPC.
create or replace function public.bump_marketplace_listing(
  target_listing_id uuid,
  expected_updated_at timestamptz
)
returns uuid
language sql
security invoker
set search_path = ''
as $$
  update public.listings
    set bumped_at = clock_timestamp()
    where id = target_listing_id
      and updated_at = expected_updated_at
      and status = 'approved'
      and contact_public
      and (expires_at is null or expires_at > clock_timestamp())
    returning id;
$$;

revoke all on function public.bump_marketplace_listing(uuid, timestamptz) from public, anon;
grant execute on function public.bump_marketplace_listing(uuid, timestamptz) to authenticated;

notify pgrst, 'reload schema';
