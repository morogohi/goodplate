"""제보·의견·익명 이용 집계 테스트 — 서버 없이(메일 앱) / 가짜 Supabase(익명 접수·집계)
  python -m http.server 8765 &  python tests/e2e_feedback.py [BASE_URL]"""
import sys, json
from playwright.sync_api import sync_playwright
BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8765').rstrip('/')
R=[]
def ok(n,c,i=''): R.append(('PASS' if c else 'FAIL',n,i))
MOCK=r"""
Object.defineProperty(window,'AUTH_CONFIG',{value:{supabaseUrl:'https://x.supabase.co',supabaseAnonKey:'anon',providers:['kakao','google']},writable:false});
window.__ins=[];window.__bumps=[];
window.supabase={createClient(){return{auth:{onAuthStateChange(){},async getSession(){return{data:{session:null}}}},
  async rpc(n,a){if(n==='bump_many')window.__bumps.push(...a.keys);return{error:null}},
  from(t){return{insert:async r=>{window.__ins.push([t,r]);return{error:null}}}}}}};
"""
with sync_playwright() as p:
    b=p.chromium.launch(); errs=[]
    # 1) 서버 설정 없음 → 메일 앱
    pg=b.new_page(viewport={'width':390,'height':844}); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(BASE+'/app.html'); pg.evaluate('localStorage.clear()'); pg.reload(); pg.wait_for_timeout(1200)
    pg.evaluate("window.__mail=null;window.__mailHook=u=>{window.__mail=u}")
    sid=pg.evaluate('S.stores[0].id'); pg.evaluate(f"storeSheet('{sid}',S.sido)"); pg.wait_for_timeout(300)
    ok('가게 상세에 수정 요청 버튼', pg.locator('[data-report]').count()==1)
    pg.click('[data-report]'); pg.wait_for_timeout(300)
    pg.click('[data-repsend]'); pg.wait_for_timeout(200)
    ok('종류 안 고르면 안내', '골라' in pg.inner_text('#toast'))
    pg.click('[data-rk="price"]'); pg.fill('#repTxt','김치찌개 9,000원으로 올랐어요'); pg.click('[data-repsend]'); pg.wait_for_timeout(300)
    m=pg.evaluate('window.__mail') or ''
    from urllib.parse import unquote
    ok('메일 앱으로: 받는 곳·가게·내용', m.startswith('mailto:support.um09@gmail.com') and '9,000' in unquote(m) and '가격' in unquote(m), unquote(m)[:80])
    pg.evaluate("location.hash='#list'"); pg.wait_for_timeout(400)
    pg.click('#view [data-suggest]'); pg.wait_for_timeout(300)
    pg.click('[data-repsend]'); pg.wait_for_timeout(200); ok('제보: 이름 없으면 안내', '이름' in pg.inner_text('#toast'))
    pg.fill('#repName','종로 착한분식'); pg.click('[data-repsend]'); pg.wait_for_timeout(300)
    ok('제보 메일', '착한분식' in unquote(pg.evaluate('window.__mail') or ''))
    pg.evaluate("location.hash='#home'"); pg.wait_for_timeout(400)
    t=pg.inner_text('#view'); ok('홈에 공공데이터 출처·문의', '공공누리' in t and 'support.um09@gmail.com' in t)
    # 2) 가짜 Supabase → 익명 접수·집계
    ctx=b.new_context(viewport={'width':390,'height':844}); ctx.add_init_script(MOCK)
    q=ctx.new_page(); q.on('pageerror',lambda e:errs.append('Q '+str(e)))
    q.goto(BASE+'/app.html'); q.evaluate('localStorage.clear()'); q.reload(); q.wait_for_timeout(4000)
    bm=q.evaluate('window.__bumps'); ok('첫 방문: new·dau 집계', 'new' in bm and 'dau' in bm, bm)
    st=q.evaluate("localStorage.getItem('cmj_stat')"); ok('기기에 저장되는 건 날짜뿐', set(json.loads(st))<= {'first','last','off'}, st)
    q.reload(); q.wait_for_timeout(3500); ok('같은 날 다시 와도 dau 중복 없음', 'dau' not in q.evaluate('window.__bumps'))
    # 어제 처음 왔던 기기 → d1
    q.evaluate("localStorage.setItem('cmj_stat',JSON.stringify({first:new Date(Date.now()-864e5).toISOString().slice(0,10),last:'2000-01-01'}))"); q.reload(); q.wait_for_timeout(3500)
    bm=q.evaluate('window.__bumps'); ok('다음 날 재방문: d1 집계', 'd1' in bm and 'dau' in bm and 'new' not in bm, bm)
    cid=q.evaluate('IDX.courses[0].id'); q.evaluate(f"location.hash='#course-{cid}'"); q.wait_for_timeout(1200)
    q.click('[data-helpful="yes"]'); q.wait_for_timeout(3500)
    bm=q.evaluate('window.__bumps'); ok('코스 열람·도움돼요 집계', 'course_open' in bm and 'course_yes' in bm, bm)
    q.evaluate("history.back()"); q.wait_for_timeout(300)
    s2=q.evaluate('S.stores[1].id'); q.evaluate(f"storeSheet('{s2}',S.sido)"); q.wait_for_timeout(300)
    q.click('[data-report]'); q.wait_for_timeout(200); q.click('[data-rk="closed"]'); q.click('[data-repsend]'); q.wait_for_timeout(800)
    ins=q.evaluate('window.__ins'); ok('익명 접수(reports)', ins and ins[-1][0]=='reports' and ins[-1][1]['kind']=='closed' and 'user' not in json.dumps(ins), ins[-1:] )
    # 끄기
    q.evaluate("closeSheet();document.getElementById('acctBtn').click()"); q.wait_for_timeout(300)
    q.click('[data-statset]'); q.wait_for_timeout(200)
    q.evaluate("window.__bumps=[]"); q.evaluate(f"storeSheet('{s2}',S.sido)"); q.wait_for_timeout(3500)
    ok('통계 끄면 안 보냄', q.evaluate('window.__bumps')==[])
    # 추적 거부(GPC)
    ctx2=b.new_context(viewport={'width':390,'height':844}); ctx2.add_init_script(MOCK+"Object.defineProperty(navigator,'globalPrivacyControl',{value:true});")
    z=ctx2.new_page(); z.goto(BASE+'/app.html'); z.wait_for_timeout(3500)
    ok('추적 거부 설정이면 안 보냄', z.evaluate('window.__bumps')==[])
    ok('JS 오류 없음', not errs, errs[:3])
    b.close()
for r in R: print(' | '.join(map(str,r)))
f=sum(r[0]=='FAIL' for r in R); print('FAILS:',f); sys.exit(1 if f else 0)
