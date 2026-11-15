-- 착한맛자랑 로그인 서버 (Supabase) — SQL Editor에 붙여 넣고 Run (여러 번 실행해도 안전)
-- 저장하는 것: 로그인 공급자·가입/접속 시각, 내 리스트(저장한 가게·코스·코스 식당 선택·메모·뽐내기 기록)
-- 저장하지 않는 것: 위치(GPS)·사진·맞춤 조건·지역 선택 (기기에만)
-- 각 회원은 자기 행만 읽고 쓸 수 있음 (행 단위 보안 규칙)

create table if not exists public.members (
  id            uuid primary key references auth.users(id) on delete cascade,
  provider      text,
  created_at    timestamptz not null default now(),
  last_seen_at  timestamptz not null default now()
);

create table if not exists public.user_lists (
  user_id     uuid primary key references auth.users(id) on delete cascade,
  doc         jsonb not null default '{"items":{},"tomb":{}}'::jsonb,
  updated_at  timestamptz not null default now(),
  constraint doc_size check (octet_length(doc::text) < 300000)   -- 1명당 약 300KB 상한
);

alter table public.members    enable row level security;
alter table public.user_lists enable row level security;

drop policy if exists "본인 읽기" on public.members;
create policy "본인 읽기" on public.members for select to authenticated using (auth.uid() = id);

drop policy if exists "본인 읽기" on public.user_lists;
drop policy if exists "본인 쓰기" on public.user_lists;
drop policy if exists "본인 수정" on public.user_lists;
create policy "본인 읽기" on public.user_lists for select to authenticated using (auth.uid() = user_id);
create policy "본인 쓰기" on public.user_lists for insert to authenticated with check (auth.uid() = user_id);
create policy "본인 수정" on public.user_lists for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- 로그인할 때마다 회원 기록(공급자·접속 시각) 갱신
create or replace function public.touch_member()
returns void language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  insert into public.members (id, provider)
    values (auth.uid(), (select raw_app_meta_data->>'provider' from auth.users where id = auth.uid()))
    on conflict (id) do update set last_seen_at = now();
end $$;

-- 회원 탈퇴: 계정 삭제 → members·user_lists 함께 삭제 (on delete cascade)
create or replace function public.delete_my_account()
returns void language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null then raise exception 'not signed in'; end if;
  delete from auth.users where id = auth.uid();
end $$;

revoke all on function public.touch_member() from public, anon;
revoke all on function public.delete_my_account() from public, anon;
grant execute on function public.touch_member() to authenticated;
grant execute on function public.delete_my_account() to authenticated;
