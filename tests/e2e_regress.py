"""브라우저 회귀 테스트 (2026-11-11 실브라우저 점검 지적 사항 재현)
  python -m http.server 8765 &  python tests/e2e_regress.py [BASE_URL]
"""
import re, sys
from playwright.sync_api import sync_playwright
BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8765').rstrip('/')
R=[]
def ok(name,cond,info=''): R.append(('PASS' if cond else 'FAIL',name,info))
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':390,'height':844}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(BASE+'/app.html'); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(1200)
    # 1) 필터 집계 일치: 데이트 + 1만원 미만
    pg.click('[data-pur="date"]'); pg.wait_for_timeout(200); pg.click('[data-fopen]'); pg.wait_for_timeout(200); pg.click('[data-fbud="b1"]'); pg.wait_for_timeout(200)
    btn=pg.inner_text('[data-fapply]'); n=int(re.search(r'(\d+)곳',btn).group(1))
    pg.click('[data-fapply]'); pg.wait_for_timeout(300)
    h2=pg.inner_text('.sec-h h2'); m=int(re.search(r'(\d+)곳',h2).group(1))
    ds=pg.eval_on_selector_all('.list .store .ds','els=>els.map(e=>e.textContent)')
    far=[d for d in ds if d.endswith('km') and float(d[:-2])>3]
    ok('필터 버튼 수 = 홈 결과 수',n==m,f'버튼 "{btn}" / 결과 "{h2}"'); ok('결과가 모두 3km 안',not far,str(ds))
    wide=pg.locator('[data-wide]')
    if wide.count():
        t=wide.first.inner_text(); more=int(re.search(r'\+(\d+)',t).group(1)); wide.first.click(); pg.wait_for_timeout(300)
        m2=int(re.search(r'(\d+)곳',pg.inner_text('.sec-h h2')).group(1)); ok('넓혀 보기 = 기존+추가',m2==m+more,f'{m}+{more}→{m2}')
        pg.click('[data-fopen]'); pg.wait_for_timeout(200); ok('넓혀 보기 상태에서도 시트 수 일치',str(m2)+'곳' in pg.inner_text('[data-fapply]'),pg.inner_text('[data-fapply]'))
        pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    pg.click('[data-fclear]') if pg.locator('[data-fclear]').count() else None; pg.wait_for_timeout(200)
    # 지도 탭 시트 수 = 지도 목록 수
    pg.click('nav [data-tab="map"]'); pg.click('[data-radius="500"]'); pg.click('[data-fopen]'); pg.click('[data-pur="solo"]'); pg.wait_for_timeout(300)
    bt=pg.inner_text('[data-fapply]'); pg.click('[data-fapply]'); pg.wait_for_timeout(300)
    ok('지도: 시트 수 = 목록 수', bt.startswith('반경 500m') and str(pg.locator('.list .store').count())+'곳' in bt, f'{bt} / {pg.locator(".list .store").count()}')
    pg.click('[data-fclear]'); pg.wait_for_timeout(200)
    # 2) 바꾼 식당 저장 유지
    pg.goto(BASE+'/app.html#course-seoul-palace'); pg.wait_for_timeout(1000)
    first=pg.inner_text('#page .scard:has([data-swap="seoul-palace:1"]) .pick .nm')
    pg.evaluate("document.querySelector('[data-swap=\"seoul-palace:1\"]').click()"); pg.wait_for_timeout(500)
    swapped=pg.inner_text('#page .scard:has([data-swap="seoul-palace:1"]) .pick .nm')
    pg.evaluate("document.querySelector('[data-savecourse]').click()"); pg.wait_for_timeout(200)
    pg.reload(); pg.wait_for_timeout(1200)
    after=pg.inner_text('#page .scard:has([data-swap="seoul-palace:1"]) .pick .nm')
    ok('식당 교체 후 새로고침해도 유지', first!=swapped and after==swapped, f'{first} → {swapped} → 새로고침 {after}')
    summ=pg.inner_text('.sumrow'); ok('코스 상세: 착한가게 수와 슬롯 수 분리', '추천 중 착한가게' in summ and '/' in summ, summ.replace('\n',' '))
    # 5) 접근성: Esc, 닫기 버튼, inert
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300); ok('Esc로 코스 페이지 닫힘', not pg.evaluate("document.querySelector('#page').classList.contains('open')"))
    ok('닫힌 코스 페이지 inert', pg.evaluate("document.querySelector('#page').hasAttribute('inert')"))
    pg.click('nav [data-tab="home"]'); pg.wait_for_timeout(200); pg.click('.mcard'); pg.wait_for_timeout(400)
    ok('가게 상세 닫기 버튼', pg.locator('#sheet .xbtn').is_visible()); ok('열릴 때 닫기 버튼에 포커스', pg.evaluate("document.activeElement.classList.contains('xbtn')"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    ok('Esc로 상세창 닫힘 + inert/aria-hidden', pg.evaluate("(s=>!s.classList.contains('open')&&s.hasAttribute('inert')&&s.getAttribute('aria-hidden')==='true')(document.querySelector('#sheet'))"))
    pg.click('.mcard'); pg.wait_for_timeout(300); pg.click('#sheet .xbtn'); pg.wait_for_timeout(300); ok('닫기 버튼으로 닫힘', not pg.evaluate("document.querySelector('#sheet').classList.contains('open')"))
    # 3) 샘플 표현
    ok('앱 수집 바: 샘플 명시', '샘플 데이터' in pg.inner_text('.collect') and '자동 수집은 준비 중' in pg.inner_text('.collect'), pg.inner_text('.collect').replace('\n',' '))
    pg.click('.mcard'); pg.wait_for_timeout(300); ok('가게 상세: 가상 샘플 안내', '가상의 샘플 가게' in pg.inner_text('#sheet')); pg.keyboard.press('Escape')
    # 4a) 코스 카드 문구
    card=pg.inner_text('.ccard .cmeta'); ok('코스 카드: 식사·쉼 분리', '식사' in card and '착한 한 끼' not in card, [l for l in card.split('\n') if '식사' in l])
    # 6) 응원 배지 즉시 반영
    pg.click('nav [data-tab="brag"]'); pg.wait_for_timeout(300); n0=int(pg.inner_text('#bragN'))
    pg.click('[data-reason="맛있어요"]'); pg.click('#mkCard'); pg.wait_for_timeout(1000)
    ok('응원 배지 즉시 +1', int(pg.inner_text('#bragN'))==n0+1, f'{n0}→{pg.inner_text("#bragN")}')
    # 대표 페이지 샘플 문구 일관성
    lp=b.new_page(viewport={'width':1366,'height':860}); lp.goto(BASE+'/index.html'); lp.wait_for_timeout(2500)
    body=lp.inner_text('body')
    ok('대표: 샘플일 때 "새벽 업데이트" 문구 없음', '새벽 업데이트' not in body and '매일 새벽 자동 업데이트' not in body)
    ok('대표: 통계 라벨 (샘플)', '소개하는 가게 (샘플)' in body)
    ok('대표: 코스 카드 식사 표기', '착한 한 끼 ' not in lp.inner_text('#cgrid'))
    ok('JS 오류 없음', not errs, str(errs))
    b.close()
for r in R: print(*r, sep=' | ')
print('FAILS:', sum(r[0]=='FAIL' for r in R))

sys.exit(1 if any(r[0]=='FAIL' for r in R) else 0)
