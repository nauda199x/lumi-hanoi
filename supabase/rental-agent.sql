begin;
create table public.lumi_rental_leads (
  id uuid primary key,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  phone text not null check (char_length(phone) between 8 and 16),
  unit_type text not null check (unit_type in ('1PN','2PN','3PN','4PN','Duplex','Penthouse','any')),
  budget_vnd integer not null check (budget_vnd between 1000000 and 200000000),
  furnishing text not null check (furnishing in ('any','Đồ cơ bản','Full nội thất')),
  move_in date,
  parking boolean not null default false,
  viewing_date date,
  viewing_period text check (viewing_period in ('morning','afternoon','evening')),
  preferred_listing text check (preferred_listing ~ '^[a-z0-9-]{8,120}$'),
  note text check (char_length(note) <= 500),
  attribution jsonb not null default '{}'::jsonb,
  consent_at timestamptz not null default now(),
  status text not null default 'new' check (status in ('new','contacted','scheduled','viewed','signed','closed')),
  priority text not null check (priority in ('hot','normal'))
);
create index lumi_rental_leads_created_idx on public.lumi_rental_leads (created_at desc, id desc);
alter table public.lumi_rental_leads enable row level security;
revoke all on public.lumi_rental_leads from public, anon, authenticated;
grant select, update (status), delete on public.lumi_rental_leads to authenticated;
grant select, insert on public.lumi_rental_leads to service_role;
create policy lumi_leads_admin_read on public.lumi_rental_leads for select to authenticated using ((select private.is_admin()));
create policy lumi_leads_admin_update on public.lumi_rental_leads for update to authenticated using ((select private.is_admin())) with check ((select private.is_admin()));
create policy lumi_leads_admin_delete on public.lumi_rental_leads for delete to authenticated using ((select private.is_admin()));
create trigger lumi_rental_leads_set_updated_at before update on public.lumi_rental_leads for each row execute function private.set_updated_at();
create table public.lumi_rental_rate (
  bucket text not null,
  win bigint not null,
  hits integer not null,
  primary key (bucket, win)
);
alter table public.lumi_rental_rate enable row level security;
revoke all on public.lumi_rental_rate from public, anon, authenticated;
grant select, insert, update, delete on public.lumi_rental_rate to service_role;
create function public.lumi_rental_rate_allow(p_bucket text, p_window integer, p_limit integer)
returns boolean language sql volatile security invoker set search_path = ''
as $$
  with current_window as (select floor(extract(epoch from now()) / p_window)::bigint as win),
  counter as (
    insert into public.lumi_rental_rate as rate (bucket, win, hits)
    select p_bucket, win, 1 from current_window
    on conflict (bucket, win) do update set hits = rate.hits + 1
      where rate.hits < p_limit
    returning hits
  )
  select exists(select 1 from counter);
$$;
revoke all on function public.lumi_rental_rate_allow(text, integer, integer) from public, anon, authenticated;
grant execute on function public.lumi_rental_rate_allow(text, integer, integer) to service_role;
commit;

-- Production retention schedule.
create extension if not exists pg_cron with schema pg_catalog;
select cron.schedule('lumi-rental-retention','10 19 * * *',$job$
  delete from public.lumi_rental_leads where created_at < now() - interval '90 days';
  delete from public.lumi_rental_rate where win * case when bucket = 'ai' then 86400 else 900 end < extract(epoch from now() - interval '2 days');
$job$);
