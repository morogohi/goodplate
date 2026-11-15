#!/usr/bin/env bash
# 에뮬레이터 점검: 설치 → 위치(종로) 지정 → 실행 → 탭 이동 → 딥링크 → 오류 로그 확인
set -u
APK="$1"; PKG=io.github.morogohi.goodplate; OUT=smoke; mkdir -p $OUT; FAIL=0
shot(){ adb exec-out screencap -p > "$OUT/$1.png"; echo "📸 $1"; }
alive(){ adb shell pidof $PKG >/dev/null; }
adb install -r "$APK" || { echo "설치 실패"; exit 1; }
adb shell pm grant $PKG android.permission.ACCESS_FINE_LOCATION || true
adb shell pm grant $PKG android.permission.ACCESS_COARSE_LOCATION || true
adb emu geo fix 126.9831 37.5702 || true          # 종로 종각
adb logcat -c
adb shell monkey -p $PKG -c android.intent.category.LAUNCHER 1 >/dev/null
sleep 25; shot 01-home
alive && echo "✅ 실행 유지" || { echo "❌ 앱이 종료됨"; FAIL=1; }
W=$(adb shell wm size | grep -o '[0-9]*x[0-9]*' | tail -1); WX=${W%x*}; WY=${W#*x}
NAVY=$((WY*93/100))
for t in "2:02-map:32" "3:03-course:50" "4:04-list:68"; do
  IFS=: read n name px <<< "$t"; adb shell input tap $((WX*px/100)) $NAVY; sleep 6; shot $name
done
adb shell input tap $((WX*14/100)) $NAVY; sleep 3
# 로그인 딥링크(취소) — 인텐트 필터가 앱을 여는지
adb shell am start -W -a android.intent.action.VIEW -d "io.github.morogohi.goodplate://auth?error=access_denied" $PKG > $OUT/deeplink.txt 2>&1
cat $OUT/deeplink.txt; sleep 2; shot 05-deeplink
grep -q "Status: ok" $OUT/deeplink.txt && echo "✅ 딥링크로 앱 열림" || { echo "❌ 딥링크 실패"; FAIL=1; }
alive && echo "✅ 끝까지 실행 유지" || { echo "❌ 앱이 종료됨"; FAIL=1; }
adb logcat -d > $OUT/logcat.txt
grep -E "FATAL EXCEPTION|AndroidRuntime: " $OUT/logcat.txt | head -20 && { echo "❌ 네이티브 오류"; FAIL=1; }
grep -E "Capacitor/Console.*(Uncaught|TypeError|ReferenceError|SyntaxError)" $OUT/logcat.txt | head -20 && { echo "❌ 화면 스크립트 오류"; FAIL=1; }
grep -E "Capacitor/Console" $OUT/logcat.txt | tail -30 > $OUT/console.txt
echo "결과: FAIL=$FAIL"; exit $FAIL
