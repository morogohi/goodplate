"""실제 지도(Leaflet) 테스트 — 타일은 가짜 이미지로 대체해 네트워크 없이 확인
  python -m http.server 8765 &  python tests/e2e_map.py [BASE_URL]"""
import sys, base64
from playwright.sync_api import sync_playwright
BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8765').rstrip('/')
tile=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP89+7dfwAJbwPXy7uOIgAAAABJRU5ErkJggg==')
FAIL=[]
def chk(name,cond):
    print('PASS' if cond else 'FAIL',name); cond or FAIL.append(name)
with sync_playwright() as p:
    b=p.chromium.launch()
    # 1) 타일 정상
    pg=b.new_page(viewport={'width':390,'height':844}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('**/*basemaps.cartocdn.com/**',lambda r:r.fulfill(status=200,content_type='image/png',body=tile))
    pg.goto(BASE+'/app.html#map'); pg.wait_for_timeout(2000)
    n_list=pg.locator('.list .store').count(); n_pin=pg.locator('.leaflet-marker-icon .lpin').count()
    chk('실제 지도 표시', pg.locator('#lmap.leaflet-container').count()==1); chk('핀 수 = 목록 수', n_pin==n_list); chk('지도 출처 표기', 'OpenStreetMap' in pg.inner_text('.leaflet-control-attribution'))
    pg.click('[data-radius="3000"]'); pg.wait_for_timeout(1200)
    chk('3km 핀 수 = 목록 수', pg.locator('.leaflet-marker-icon .lpin').count()==pg.locator('.list .store').count())
    pg.locator('.leaflet-marker-icon').last.dispatch_event('click'); pg.wait_for_timeout(500)
    chk('핀 누르면 가게 상세', pg.evaluate("document.querySelector('#sheet').classList.contains('open')"))
    chk('정보 수정 요청 링크', bool(pg.get_attribute('#sheet a.mini[href*="issues/new"]','href')))
    pg.keyboard.press('Escape'); chk('JS 오류 없음', not errs)
    # 2) 타일 차단 → 모식도
    pg2=b.new_page(viewport={'width':390,'height':844})
    pg2.route('**/*basemaps.cartocdn.com/**',lambda r:r.abort())
    pg2.goto(BASE+'/app.html#map'); pg2.wait_for_timeout(2500)
    chk('타일 차단 시 모식도 대체', pg2.locator('#mapBox svg').count()==1 and pg2.locator('#lmap').count()==0)
    b.close()
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844})
    pg.route('**/*basemaps.cartocdn.com/**',lambda r:r.fulfill(status=200,content_type='image/png',body=tile))
    pg.goto(BASE+'/app.html#map'); pg.wait_for_timeout(1500)
    pg.click('[data-fopen]'); pg.wait_for_timeout(400)
    top=pg.evaluate("(()=>{const b=document.querySelector('#sheet [data-pur=\"solo\"]').getBoundingClientRect();const el=document.elementFromPoint(b.x+b.width/2,b.y+b.height/2);return el.closest('#sheet')?'sheet':el.className})()")
    chk('시트가 지도 위', top=='sheet'); pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    nav=pg.evaluate("(()=>{const b=document.querySelector('nav [data-tab=\"home\"]').getBoundingClientRect();window.scrollTo(0,200);const el=document.elementFromPoint(b.x+b.width/2,b.y+b.height/2);return !!el.closest('nav')})()")
    chk('내비가 지도 위', nav); b.close()
sys.exit(1 if FAIL else 0)
