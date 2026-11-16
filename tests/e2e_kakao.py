"""카카오맵 경로 테스트 — 가짜 카카오 지도 SDK로 키·도메인 없이 검증, 실패 시 기본 지도 대체 확인
  python -m http.server 8765 &  python tests/e2e_kakao.py [BASE_URL]"""
import sys, base64
from playwright.sync_api import sync_playwright
BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8765').rstrip('/')
R=[]
def ok(n,c,i=''): R.append(('PASS' if c else 'FAIL',n,i))
KEY="Object.defineProperty(window,'MAP_CONFIG',{value:{kakaoJsKey:'test-js-key'},writable:false});"
FAKE=r"""
(function(){const SC=60000;   // 위경도 → 화면 좌표 (레벨이 낮을수록 확대)
function LatLng(a,b){this.a=a;this.b=b}LatLng.prototype.getLat=function(){return this.a};LatLng.prototype.getLng=function(){return this.b};
function LatLngBounds(){this.p=[]}LatLngBounds.prototype.extend=function(l){this.p.push(l)};
function Map(el,o){this.el=el;this.c=o.center;this.lv=o.level;this.ov=[];this.ls={};el.dataset.fake='kakao';window.__kmap=this}
Map.prototype.getProjection=function(){const m=this;const k=SC/Math.pow(2,m.lv-1);return{containerPointFromCoords:l=>({x:(l.b-m.c.b)*k,y:(m.c.a-l.a)*k})}};
Map.prototype.getLevel=function(){return this.lv};Map.prototype.setLevel=function(v){this.lv=v;(this.ls.zoom_changed||[]).forEach(f=>f())};
Map.prototype.setBounds=function(){this.lv=Math.max(1,this.lv-1);(this.ls.zoom_changed||[]).forEach(f=>f())};
Map.prototype.addControl=function(){};
function Circle(o){this.o=o}Circle.prototype.setMap=function(){};Circle.prototype.getBounds=function(){return new LatLngBounds()};
function CustomOverlay(o){this.o=o;this.w=null}
CustomOverlay.prototype.setMap=function(m){if(this.w){this.w.remove();this.w=null}if(!m)return;const w=document.createElement('div');w.className='kov';
 if(typeof this.o.content==='string')w.innerHTML=this.o.content;else w.appendChild(this.o.content);m.el.appendChild(w);this.w=w};
window.kakao={maps:{load:cb=>setTimeout(cb,10),LatLng,LatLngBounds,Map,Circle,CustomOverlay,ZoomControl:function(){},ControlPosition:{RIGHT:1},
 event:{addListener:(m,ev,f)=>{(m.ls[ev]=m.ls[ev]||[]).push(f)}}}};})();
"""
tile=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
with sync_playwright() as p:
    b=p.chromium.launch(); errs=[]
    ctx=b.new_context(viewport={'width':390,'height':844}); ctx.add_init_script(KEY)
    ctx.route('**/dapi.kakao.com/**',lambda r:r.fulfill(status=200,content_type='application/javascript',body=FAKE))
    pg=ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(BASE+'/app.html'); pg.evaluate('localStorage.clear()'); pg.goto(BASE+'/app.html#map'); pg.wait_for_timeout(2000)
    ok('카카오 지도로 표시', pg.evaluate('S.mapEngine')=='kakao' and pg.locator('#kmap[data-fake="kakao"]').count()==1, pg.evaluate('S.mapEngine'))
    n=pg.evaluate("[...document.querySelectorAll('#kmap .lpin')].length+[...document.querySelectorAll('#kmap .lclu')].reduce((a,e)=>a+ +e.textContent,0)")
    ok('핀 수(묶음 포함) = 목록 수', n==pg.locator('.list .store').count(), f'{n} vs {pg.locator(".list .store").count()}')
    ok('내 위치 표시', pg.locator('#kmap .lme').count()==1)
    pg.locator('#kmap .lpin').first.click(); pg.wait_for_timeout(400)
    ok('핀 누르면 가게 상세', pg.evaluate("document.querySelector('#sheet').classList.contains('open')"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    if pg.locator('#kmap .lclu').count():
        lv=pg.evaluate('__kmap.getLevel()'); pg.locator('#kmap .lclu').first.click(); pg.wait_for_timeout(300)
        ok('묶음 누르면 확대 또는 목록', pg.evaluate('__kmap.getLevel()')<lv or pg.evaluate("document.querySelector('#sheet').classList.contains('open')"))
    pg.click('[data-r="3000"]') if pg.locator('[data-r="3000"]').count() else None; pg.wait_for_timeout(800)
    ok('반경 바꿔도 카카오 지도 유지', pg.evaluate('S.mapEngine')=='kakao' and pg.locator('#kmap').count()==1)
    # 키는 있지만 도메인 미등록(401) → 기본 지도로 대체
    ctx2=b.new_context(viewport={'width':390,'height':844}); ctx2.add_init_script(KEY)
    ctx2.route('**/dapi.kakao.com/**',lambda r:r.fulfill(status=401,body='unauthorized'))
    ctx2.route('**/tile.openstreetmap.org/**',lambda r:r.fulfill(status=200,content_type='image/png',body=tile))
    q=ctx2.new_page(); q.on('pageerror',lambda e:errs.append('Q '+str(e)))
    q.goto(BASE+'/app.html#map'); q.wait_for_timeout(2500)
    ok('카카오 실패 시 기본 지도로 대체', q.evaluate('S.mapEngine')=='leaflet' and q.locator('#lmap').count()==1, q.evaluate('S.mapEngine'))
    # 키 없음 → 바로 기본 지도, 카카오 요청 안 함
    ctx3=b.new_context(viewport={'width':390,'height':844}); hits=[]
    ctx3.route('**/dapi.kakao.com/**',lambda r:(hits.append(1),r.abort()))
    ctx3.route('**/tile.openstreetmap.org/**',lambda r:r.fulfill(status=200,content_type='image/png',body=tile))
    z=ctx3.new_page(); z.goto(BASE+'/app.html#map'); z.wait_for_timeout(1500)
    ok('키 없으면 기본 지도·카카오 요청 없음', z.evaluate('S.mapEngine')=='leaflet' and not hits)
    ok('JS 오류 없음', not errs, errs[:3])
    b.close()
for r in R: print(' | '.join(map(str,r)))
f=sum(r[0]=='FAIL' for r in R); print('FAILS:',f); sys.exit(1 if f else 0)
