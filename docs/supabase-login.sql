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

-- ─────────────────────────────────────────────────────────────
-- 제보·익명 이용 집계 (로그인 없이도 동작, 개인 식별 정보 없음)
-- ─────────────────────────────────────────────────────────────
-- 가게 정보 수정 요청·가게 제보 (익명 접수, 읽기는 운영자만: 대시보드/서비스 키)
create table if not exists public.reports (
  id          bigint generated always as identity primary key,
  created_at  timestamptz not null default now(),
  kind        text not null check (kind in ('price','closed','place','good','other','suggest')),
  store_id    text check (char_length(store_id) <= 40),
  store_name  text not null check (char_length(store_name) between 1 and 60),
  sido        text check (char_length(sido) <= 20),
  body        text not null default '' check (char_length(body) <= 300),
  status      text not null default 'new' check (status in ('new','done','rejected'))
);
alter table public.reports enable row level security;
drop policy if exists "누구나 접수" on public.reports;
create policy "누구나 접수" on public.reports for insert to anon, authenticated
  with check (status = 'new');
-- (select 정책 없음 → 앱에서는 읽을 수 없고, 운영자는 Supabase 대시보드에서 확인)

-- 날짜별 횟수만 저장 (사용자 ID·IP·위치 없음)
create table if not exists public.daily_stats (
  day  date not null default (now() at time zone 'Asia/Seoul')::date,
  k    text not null,
  n    integer not null default 0,
  primary key (day, k)
);
alter table public.daily_stats enable row level security;   -- 직접 읽기·쓰기 불가, 아래 함수로만

create or replace function public.bump_many(keys text[])
returns void language plpgsql security definer set search_path = '' as $$
declare k text; d date := (now() at time zone 'Asia/Seoul')::date;
begin
  if array_length(keys, 1) > 30 then return; end if;          -- 한 번에 30개까지
  foreach k in array keys loop
    if k = any (array['dau','new','d1','d7','d30','store_open','course_open','course_yes','course_no','share','filter','gps','report','suggest']) then
      insert into public.daily_stats (day, k, n) values (d, k, 1)
        on conflict (day, k) do update set n = public.daily_stats.n + 1;
    end if;
  end loop;
end $$;

-- 공개 운영 지표 페이지용: 최근 N일 합계 (집계값만)
create or replace function public.get_stats(days integer default 30)
returns table (day date, k text, n integer) language sql security definer set search_path = '' stable as $$
  select day, k, n from public.daily_stats
  where day >= (now() at time zone 'Asia/Seoul')::date - least(greatest(days, 1), 366)
  order by day, k;
$$;

revoke all on function public.bump_many(text[]) from public;
revoke all on function public.get_stats(integer) from public;
grant execute on function public.bump_many(text[]) to anon, authenticated;
grant execute on function public.get_stats(integer) to anon, authenticated;
