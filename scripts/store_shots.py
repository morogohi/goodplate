"""스토어 스크린샷 자동 생성 — 실데이터일 때만 (샘플이면 건너뜀, --force 로 강제)
  python -m http.server 8766 --directory www &   python scripts/store_shots.py [--force]
"""
import base64, json, sys, datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent
BASE='http://localhost:8766'
idx=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))
mark=ROOT/'store/.source'
if '--force' not in sys.argv:
    if idx.get('sample'):
        print('샘플 데이터라 스크린샷을 다시 만들지 않습니다'); sys.exit(0)
    if mark.exists() and mark.read_text().startswith('real'):
        print('이미 실데이터로 만든 스크린샷이 있습니다 (--force 로 다시 생성)'); sys.exit(0)
SC=[('01','home',None,'오늘, 착한 한 끼와\n산책 어때요','내 위치에서 착한가게·맛집을 바로'),
    ('02','fit','parents','누구랑, 얼마로,\n뭐 먹을지 고르면','부모님·데이트·회식… 맞는 가게만 쏙'),
    ('03','course','seoul-palace','여행코스 사이엔\n착한 한 끼','관광지 근처 착한가게를 자동 추천'),
    ('04','map',None,'지도로 한눈에,\n가까운 순서대로','착한가격업소·나눔가게를 색으로 구분'),
    ('05','brag',None,'사진 한 장으로\n가게를 응원해요','좋아하는 이유를 담은 공유 카드')]
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':390,'height':844},device_scale_factor=3); pg=ctx.new_page()
    for no,kind,arg,_,_ in SC:
        pg.goto(BASE+'/index.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1500)
        if kind=='fit': pg.click('[data-pur="parents"]'); pg.wait_for_timeout(400); pg.evaluate("scrollTo(0,250)")
        if kind=='course': pg.evaluate(f"location.hash='course-{arg}'"); pg.wait_for_timeout(900); pg.evaluate("document.querySelector('#page').scrollTop=360")
        if kind=='map': pg.click('nav [data-tab="map"]')
        if kind=='brag':
            pg.click('nav [data-tab="brag"]'); pg.wait_for_timeout(300); pg.click('[data-reason="가성비 최고"]'); pg.click('[data-reason="사장님 친절"]')
            pg.fill('#bText','점심마다 줄 서는 이유가 있어요. 국물이 진하고 사장님이 정말 친절해요!'); pg.click('#mkCard'); pg.wait_for_timeout(1200); pg.evaluate("scrollTo(0,520)")
        pg.wait_for_timeout(500); pg.screenshot(path=str(ROOT/f'.shots_raw_{no}.png'))
    ctx.close()
    for plat,(W,H) in {'ios':(1290,2796),'android':(1080,1920)}.items():
        for no,kind,arg,title,sub in SC:
            img=base64.b64encode(open(str(ROOT/f'.shots_raw_{no}.png'),'rb').read()).decode()
            sw=int(W*0.74); fs=int(W*0.072)
            html=f"""<html><body style="margin:0;width:{W}px;height:{H}px;background:linear-gradient(170deg,#1F6F5C,#174F42);font-family:'Noto Sans KR',sans-serif;color:#fff;overflow:hidden;text-align:center">
            <div style="padding-top:{int(H*0.06)}px;font-size:{fs}px;font-weight:800;line-height:1.25;letter-spacing:-2px;white-space:pre-line">{title}</div>
            <div style="font-size:{int(fs*0.46)}px;opacity:.85;margin-top:{int(H*0.015)}px">{sub}</div>
            <img src="data:image/png;base64,{img}" style="width:{sw}px;margin-top:{int(H*0.04)}px;border-radius:{int(W*0.06)}px;border:{int(W*0.012)}px solid #111;box-shadow:0 40px 80px rgba(0,0,0,.35)"></body></html>"""
            pg=b.new_page(viewport={'width':W,'height':H}); pg.set_content(html); pg.wait_for_timeout(300)
            pg.screenshot(path=str(ROOT/f'store/screenshots/{plat}/{no}-{kind}.png')); pg.close()
    # Google Play 그래픽 이미지 1024x500
    pg=b.new_page(viewport={'width':1024,'height':500})
    pg.set_content("""<html><body style="margin:0;width:1024px;height:500px;background:#F6F4F0;font-family:'Noto Sans KR',sans-serif;display:flex;align-items:center;gap:40px;padding:0 70px;box-sizing:border-box">
    <svg width="150" height="150" viewBox="0 0 32 32"><rect width="32" height="32" rx="9" fill="#1F6F5C"/><path d="M9 23c0-8 5.5-13.5 14.5-13.5C22.5 18.5 17 23 9 23z" fill="#fff"/><path d="M9 23l8-8" stroke="#1F6F5C" stroke-width="1.6" stroke-linecap="round"/></svg>
    <div><div style="font-size:64px;font-weight:800;letter-spacing:-3px;color:#16181D">착한맛자랑</div><div style="font-size:30px;color:#1F6F5C;font-weight:700;margin-top:6px">착한 한 끼로 떠나는 우리 동네 여행</div><div style="font-size:22px;color:#7E818A;margin-top:10px">전국 착한가게 · 맛집 · 여행코스 | 무료 공익 서비스</div></div></body></html>""")
    pg.screenshot(path=str(ROOT/'store/feature-graphic.png'))
    b.close()
for f in ROOT.glob('.shots_raw_*.png'): f.unlink()
mark.write_text(('sample' if idx.get('sample') else 'real')+' '+datetime.date.today().isoformat()+'\n')
print('스크린샷 생성 완료')
