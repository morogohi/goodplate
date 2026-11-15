"""로그인·동기화·탈퇴 테스트 — 가짜 Supabase(window.supabase 모의 객체)로 실제 서버 없이 검증
  python -m http.server 8765 &  python tests/e2e_auth.py [BASE_URL]
"""
import sys, json
from playwright.sync_api import sync_playwright
BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8765').rstrip('/')
R=[]
def ok(n,c,i=''): R.append(('PASS' if c else 'FAIL',n,i))

# 서버 대신 window.__srv (테스트가 주입) 에 저장. 세션은 localStorage 'cmj_auth' 존재 여부로 흉내
MOCK = r"""
Object.defineProperty(window,'AUTH_CONFIG',{value:{supabaseUrl:'https://x.supabase.co',supabaseAnonKey:'anon',providers:['kakao','google']},writable:false});  // 실제 설정 파일보다 우선
window.__srv = JSON.parse(sessionStorage.getItem('__srv')||'{"row":null,"rpc":[],"deleted":false}');
const save=()=>sessionStorage.setItem('__srv',JSON.stringify(window.__srv));
const U={id:'u1',app_metadata:{provider:'kakao'},user_metadata:{nickname:'테스터'}};
window.supabase={createClient(){
  const subs=[];const sess=()=>localStorage.getItem('cmj_auth')?{user:U}:null;
  return{auth:{
    onAuthStateChange(f){subs.push(f)},
    async getSession(){return{data:{session:sess()}}},
    async exchangeCodeForSession(code){window.__srv.rpc.push('exchange:'+code);save();localStorage.setItem('cmj_auth','1');subs.forEach(f=>f('SIGNED_IN',{user:U}));return{error:null}},
    async signInWithOAuth({provider,options}){if(options&&options.skipBrowserRedirect){window.__srv.rpc.push('url:'+provider+':'+options.redirectTo);save();return{data:{url:'https://x.supabase.co/auth/v1/authorize?provider='+provider},error:null}}window.__srv.rpc.push('oauth:'+provider);save();localStorage.setItem('cmj_auth','1');subs.forEach(f=>f('SIGNED_IN',{user:U}));return{error:null}},
    async signOut(){localStorage.removeItem('cmj_auth');subs.forEach(f=>f('SIGNED_OUT',null));return{error:null}}},
   async rpc(n){window.__srv.rpc.push(n);if(n==='delete_my_account'){window.__srv.deleted=true;window.__srv.row=null}save();return{error:null}},
   from(){const q={select(){return q},eq(){return q},async maybeSingle(){return{data:window.__srv.row,error:null}},
     async upsert(r){window.__srv.row={doc:r.doc};save();return{error:null}}};return q}};
}};
"""
with sync_playwright() as p:
    b=p.chromium.launch(); errs=[]
    # --- 설정이 비어 있으면 '준비 중'
    pg=b.new_page(viewport={'width':390,'height':844}); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(BASE+'/app.html'); pg.evaluate('localStorage.clear()'); pg.reload(); pg.wait_for_timeout(1000)
    pg.click('#acctBtn'); pg.wait_for_timeout(300)
    ok('설정 없음 → 준비 중 안내', '준비하고 있어요' in pg.inner_text('#sheet') and pg.locator('[data-login]').count()==0)
    pg.keyboard.press('Escape'); pg.close()

    # --- 기기 A: 로그인 전 저장 → 로그인 → 서버로 올라감
    ctxA=b.new_context(viewport={'width':390,'height':844}); ctxA.add_init_script(MOCK)
    A=ctxA.new_page(); A.on('pageerror',lambda e:errs.append('A '+str(e)))
    A.goto(BASE+'/app.html'); A.evaluate('localStorage.clear();sessionStorage.clear()'); A.reload(); A.wait_for_timeout(1000)
    sid=A.evaluate("S.stores[0].id"); sid2=A.evaluate("S.stores[1].id")
    A.evaluate(f"S.saved['{sid}']={{list:'가고 싶은 곳',snap:{{name:'A가게'}}}};S.memos['{sid}']='A 메모';persist()")
    A.evaluate("closeSheet();document.getElementById('acctBtn').click()"); A.wait_for_timeout(300)
    ok('로그인 버튼 2개(카카오·구글)', A.locator('[data-login]').count()==2)
    ok('로그인 전 안내: 위치는 안 보냄','위치' in A.inner_text('#sheet'))
    A.click('[data-login="kakao"]'); A.wait_for_timeout(2500)
    srv=A.evaluate('window.__srv')
    ok('카카오 로그인 호출', 'oauth:kakao' in srv['rpc'])
    ok('회원 기록 touch_member 호출', 'touch_member' in srv['rpc'])
    items=(srv['row'] or {}).get('doc',{}).get('items',{})
    ok('서버에 저장 가게·메모 업로드', f'saved:{sid}' in items and f'memo:{sid}' in items, list(items)[:5])
    ok('위치·조건은 업로드 안 함', not any(k.split(':')[0] in('sido','area','f','useGps','radius') for k in items) and 'lat' not in json.dumps(items))
    ok('계정 버튼 로그인 표시', 'on' in A.get_attribute('#acctBtn','class') and '테스터' in A.get_attribute('#acctBtn','aria-label'))
    A.evaluate("closeSheet();document.getElementById('acctBtn').click()"); A.wait_for_timeout(300)
    ok('계정 시트: 이름·동기화 정보', '테스터' in A.inner_text('#sheet') and '저장한 가게 1곳' in A.inner_text('#sheet'), A.inner_text('#sheet')[:120])

    # --- 기기 B: 다른 기기에서 다른 가게 저장, 서버 내용과 병합
    srvjson=json.dumps(srv)
    ctxB=b.new_context(viewport={'width':390,'height':844}); ctxB.add_init_script(MOCK)
    B=ctxB.new_page(); B.on('pageerror',lambda e:errs.append('B '+str(e)))
    B.goto(BASE+'/app.html'); B.evaluate(f"localStorage.clear();sessionStorage.setItem('__srv',{json.dumps(srvjson)})"); B.reload(); B.wait_for_timeout(1000)
    B.evaluate(f"S.saved['{sid2}']={{list:'단골',snap:{{name:'B가게'}}}};persist()")
    B.evaluate("localStorage.setItem('cmj_auth','1')"); B.reload(); B.wait_for_timeout(2500)
    ok('B: 서버 가게 + B 가게 병합', B.evaluate(f"!!S.saved['{sid}']&&!!S.saved['{sid2}']"), B.evaluate("Object.keys(S.saved)"))
    ok('B: 메모도 내려옴', B.evaluate(f"S.memos['{sid}']")=='A 메모')
    # B에서 A가게 삭제 → 서버에 지움 표시
    B.evaluate(f"delete S.saved['{sid}'];persist()"); B.wait_for_timeout(2500)
    srv2=B.evaluate('window.__srv'); it2=srv2['row']['doc']
    ok('B 삭제가 서버에 반영(tomb)', f'saved:{sid}' not in it2['items'] and f'saved:{sid}' in it2['tomb'])
    # A가 다시 동기화하면 삭제가 반영되고 B 가게가 들어옴 (A는 오래된 사본을 가지고 있음)
    A.evaluate(f"sessionStorage.setItem('__srv',{json.dumps(json.dumps(srv2))});window.__srv=JSON.parse(sessionStorage.getItem('__srv'))")
    A.evaluate("Sync.run()"); A.wait_for_timeout(1500)
    ok('A: 다른 기기 삭제 반영 + 새 가게 수신', A.evaluate(f"!S.saved['{sid}']&&!!S.saved['{sid2}']"), A.evaluate("Object.keys(S.saved)"))

    # 병합 규칙 단위 검사
    m=A.evaluate("""(()=>{const n=Date.now();return Sync._merge({items:{a:{v:1,t:n+10},b:{v:1,t:n+5}},tomb:{c:n+20}},{items:{a:{v:2,t:n+20},c:{v:3,t:n+10},b:{v:9,t:n+1}},tomb:{b:n+3}})})()""")
    ok('병합: 최신 값이 이김', m['items']['a']['v']==2 and m['items']['b']['v']==1)
    ok('병합: 더 늦은 삭제가 이김', 'c' not in m['items'] and m['tomb'].get('c',0)>0)

    # --- 로그아웃: 기기 리스트는 남음
    A.evaluate("closeSheet();document.getElementById('acctBtn').click()"); A.wait_for_timeout(300); A.click('[data-logout]'); A.wait_for_timeout(800)
    ok('로그아웃 후 계정 버튼 기본', 'on' not in (A.get_attribute('#acctBtn','class') or '') )
    ok('로그아웃해도 기기 리스트 유지', A.evaluate(f"!!S.saved['{sid2}']"))

    # --- 탈퇴: 2단계 확인
    B.evaluate("closeSheet();document.getElementById('acctBtn').click()"); B.wait_for_timeout(300); B.click('[data-delask]'); B.wait_for_timeout(200)
    ok('탈퇴 확인 단계 표시', '정말 탈퇴' in B.inner_text('#sheet'))
    B.click('[data-delcancel]'); B.wait_for_timeout(200)
    ok('취소하면 확인 단계 닫힘', '정말 탈퇴' not in B.inner_text('#sheet') and not B.evaluate('window.__srv.deleted'))
    B.click('[data-delask]'); B.wait_for_timeout(200); B.click('[data-delconfirm]'); B.wait_for_timeout(1000)
    ok('탈퇴: delete_my_account 호출 + 로그아웃', B.evaluate('window.__srv.deleted') and 'on' not in (B.get_attribute('#acctBtn','class') or ''))

    # --- 로그인 취소로 돌아온 경우 안내
    C=ctxA.new_page(); C.goto(BASE+'/app.html?error=access_denied'); C.wait_for_timeout(1500)
    ok('로그인 취소 안내 + 주소 정리', '취소' in C.inner_text('#toast') and 'error' not in C.url, C.url)
    # --- 앱(안드로이드): 시스템 브라우저 + 딥링크
    def native(plat):
        return MOCK+"window.Capacitor={isNativePlatform:()=>true,getPlatform:()=>'%s',Plugins:{Browser:{open:async o=>{window.__opened=o.url},close:async()=>{window.__closed=1}},App:{addListener:(n,f)=>{window.__url=f}}}};"%plat
    ctxN=b.new_context(viewport={'width':390,'height':844}); ctxN.add_init_script(native('android'))
    N=ctxN.new_page(); N.on('pageerror',lambda e:errs.append('N '+str(e)))
    N.goto(BASE+'/app.html'); N.evaluate('localStorage.clear();sessionStorage.clear()'); N.reload(); N.wait_for_timeout(1200)
    N.evaluate("document.getElementById('acctBtn').click()"); N.wait_for_timeout(300)
    ok('앱(안드로이드): 카카오·구글 버튼', N.locator('[data-login]').count()==2, N.inner_text('#sheet')[:80])
    N.click('[data-login="google"]'); N.wait_for_timeout(800)
    ok('앱: 시스템 브라우저로 열기 + 딥링크 주소', 'provider=google' in (N.evaluate('window.__opened') or '') and any('io.github.morogohi.goodplate://auth' in r for r in N.evaluate('window.__srv.rpc')))
    N.evaluate("window.__url({url:'io.github.morogohi.goodplate://auth?code=abc123'})"); N.wait_for_timeout(2000)
    ok('앱: 딥링크로 돌아오면 코드 교환·로그인', 'exchange:abc123' in N.evaluate('window.__srv.rpc') and N.evaluate('window.__closed')==1 and 'on' in (N.get_attribute('#acctBtn','class') or ''))
    N.evaluate("closeSheet();window.__url({url:'io.github.morogohi.goodplate://auth?error=access_denied'})"); N.wait_for_timeout(500)
    ok('앱: 취소하고 돌아오면 안내', '취소' in N.inner_text('#toast'))
    # --- iOS: apple 미설정이면 로그인 숨김(지침 4.8), 설정되면 Apple 버튼
    ctxI=b.new_context(viewport={'width':390,'height':844}); ctxI.add_init_script(native('ios'))
    I=ctxI.new_page(); I.goto(BASE+'/app.html'); I.wait_for_timeout(1200)
    I.evaluate("document.getElementById('acctBtn').click()"); I.wait_for_timeout(300)
    ok('iOS: Apple 미설정이면 다음 업데이트 안내', I.locator('[data-login]').count()==0 and '다음 업데이트' in I.inner_text('#sheet'))
    ctxI2=b.new_context(viewport={'width':390,'height':844}); ctxI2.add_init_script(native('ios').replace("providers:['kakao','google']","providers:['kakao','google','apple']"))
    I2=ctxI2.new_page(); I2.goto(BASE+'/app.html'); I2.wait_for_timeout(1200)
    I2.evaluate("document.getElementById('acctBtn').click()"); I2.wait_for_timeout(300)
    ok('iOS: Apple 설정 시 Apple 버튼 맨 위', I2.locator('[data-login]').count()==3 and I2.locator('[data-login]').first.get_attribute('data-login')=='apple')
    ok('JS 오류 없음', not errs, errs[:3])
    b.close()
for r in R: print(' | '.join(map(str,r)))
f=sum(r[0]=='FAIL' for r in R); print('FAILS:',f); sys.exit(1 if f else 0)
