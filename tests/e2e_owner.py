"""가게 바로가기 링크·공유·사장님 포스터(QR)·새로 소개된 가게 테스트
  python -m http.server 8765 &  python tests/e2e_owner.py [BASE_URL]"""
import sys, json, re
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8765').rstrip('/')
ROOT=Path(__file__).resolve().parent.parent
R=[]
def ok(n,c,i=''): R.append(('PASS' if c else 'FAIL',n,i))
idx=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))
sk=[k for k in idx['regions'] if k!='seoul'][0]
st=json.loads((ROOT/f'data/r/{sk}.json').read_text(encoding='utf-8'))['stores'][0]
with sync_playwright() as p:
    b=p.chromium.launch(); errs=[]
    pg=b.new_page(viewport={'width':390,'height':844}); pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(BASE+'/app.html'); pg.evaluate('localStorage.clear()')
    pg.goto(f"{BASE}/app.html#store-{sk}-{st['id']}"); pg.wait_for_timeout(1800)
    ok('가게 링크로 다른 시도 가게 상세 열기', pg.evaluate("document.querySelector('#sheet').classList.contains('open')") and st['name'] in pg.inner_text('#sheet'))
    ok('열고 나면 주소 정리(새로고침 시 다시 안 열림)', '#store-' not in pg.url, pg.url)
    pg.evaluate("navigator.share=undefined;navigator.clipboard.writeText=async t=>{window.__clip=t}")
    pg.click('[data-sshare]'); pg.wait_for_timeout(300)
    clip=pg.evaluate('window.__clip') or ''
    ok('가게 공유: 이름 + 바로가기 링크', st['name'] in clip and f"#store-{sk}-{st['id']}" in clip, clip[:90])
    href=pg.get_attribute('#sheet a.owner','href') or ''
    ok('사장님 포스터 링크', href.startswith('poster.html?s=') and st['id'] in href, href)
    pg.goto(f"{BASE}/app.html#store-{sk}-없는가게"); pg.wait_for_timeout(1500)
    ok('없는 가게 링크 안내', '찾지 못했' in pg.inner_text('#toast'))
    # 포스터
    q=b.new_page(viewport={'width':800,'height':1100}); q.on('pageerror',lambda e:errs.append('P '+str(e)))
    q.goto(f"{BASE}/{href}"); q.wait_for_timeout(1200)
    t=q.inner_text('.paper')
    ok('포스터: 가게 이름·QR', st['name'] in t and q.locator('.qr svg').count()==1)
    ok('포스터: 착한가격업소 표시는 실제 지정일 때만', ('착한가격업소' in q.inner_text('.badge') if q.locator('.badge').count() else True) and (q.locator('.badge').count()>0)==bool(st.get('good')))
    q.select_option('#size','a4'); q.wait_for_timeout(200)
    ok('포스터: A4 전환·인쇄 크기', 'a4' in (q.get_attribute('.paper','class') or '') and 'A4' in q.inner_text('#pageSize'))
    try:
        import cv2, numpy as np
        img=cv2.imdecode(np.frombuffer(q.locator('.qr').screenshot(),np.uint8),cv2.IMREAD_COLOR)
        v,_,_=cv2.QRCodeDetector().detectAndDecode(cv2.copyMakeBorder(img,40,40,40,40,cv2.BORDER_CONSTANT,value=(255,255,255)))
        ok('QR이 가게 링크로 읽힘', v.endswith(f"#store-{sk}-{st['id']}"), v)
    except ImportError:
        ok('QR 해독(opencv 없음, 건너뜀)', True)
    q.goto(f"{BASE}/poster.html?s={sk}&id=none"); q.wait_for_timeout(800)
    ok('포스터: 없는 가게 안내', '찾지 못했어요' in q.inner_text('body'))
    # 새로 소개된 가게 (가짜 날짜로 확인)
    h=b.new_page(viewport={'width':390,'height':844}); h.on('pageerror',lambda e:errs.append('H '+str(e)))
    h.goto(BASE+'/app.html'); h.wait_for_timeout(1200)
    h.evaluate("const t=new Date().toISOString().slice(0,10);S.stores.forEach((s,i)=>s.first_seen=i<3?t:'2026-11-14');IDX.new_base='2026-11-18';render()"); h.wait_for_timeout(300)
    ok('새로 소개된 가게: 최근 것만', h.locator('#freshSec .mcard').count()==3, h.locator('#freshSec .mcard').count())
    h.evaluate("S.stores.forEach(s=>s.first_seen='2026-11-14');render()"); h.wait_for_timeout(200)
    ok('새 가게 없으면 섹션 숨김', h.locator('#freshSec').count()==0)
    ok('JS 오류 없음', not errs, errs[:3])
    b.close()
for r in R: print(' | '.join(map(str,r)))
f=sum(r[0]=='FAIL' for r in R); print('FAILS:',f); sys.exit(1 if f else 0)
