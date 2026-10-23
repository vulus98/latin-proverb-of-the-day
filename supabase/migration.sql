create table public.allowed_emails (
  email text primary key,
  created_at timestamptz not null default now()
);

insert into public.allowed_emails (email) values
  ('bozic.vukasin@gmail.com'),
  ('janajokanovic99@gmail.com')
on conflict (email) do nothing;

create table public.feedback (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  feedback_date date not null default (timezone('Europe/Belgrade', now())::date),
  choice text not null check (choice in ('delightful', 'wise', 'thoughtful', 'cute', 'honest')),
  response text not null,
  proverb_date text not null,
  proverb_latin text not null,
  created_at timestamptz not null default now(),
  notified_at timestamptz
);

create unique index one_feedback_per_user_per_day
  on public.feedback (user_id, feedback_date);

alter table public.allowed_emails enable row level security;
alter table public.feedback enable row level security;

create policy "Users can read their own allowlist entry"
  on public.allowed_emails for select
  to authenticated
  using (lower(email) = lower((select auth.jwt()->>'email')));

create policy "Allowed users can submit feedback"
  on public.feedback for insert
  to authenticated
  with check (
    user_id = (select auth.uid())
    and exists (
      select 1 from public.allowed_emails
      where lower(email) = lower((select auth.jwt()->>'email'))
    )
  );

create policy "Users can read their own feedback"
  on public.feedback for select
  to authenticated
  using (user_id = (select auth.uid()));

create or replace function public.reject_unknown_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if not exists (
    select 1 from public.allowed_emails
    where lower(email) = lower(new.email)
  ) then
    raise exception 'This email is not allowed to access the proverb page';
  end if;
  return new;
end;
$$;

drop trigger if exists validate_allowed_auth_user on auth.users;
create trigger validate_allowed_auth_user
  before insert on auth.users
  for each row execute function public.reject_unknown_auth_user();
