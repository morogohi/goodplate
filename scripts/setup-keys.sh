#!/usr/bin/env bash
# 착한맛자랑 — API 키 등록 + 첫 수집 한 번에 (macOS·Linux)
# 준비: GitHub CLI 로그인 (gh auth login) · 실행: bash scripts/setup-keys.sh
set -euo pipefail
REPO=morogohi/goodplate
echo -e "\n착한맛자랑 키 등록 — 입력한 키는 화면에 보이지 않고 GitHub Secrets 에만 저장됩니다.\n"
gh auth status >/dev/null
ask() { local name=$1 label=$2 opt=${3:-}; local v
  read -rsp "$label${opt:+ (없으면 Enter)}: " v; echo
  if [ -z "$v" ]; then [ -n "$opt" ] && return 0; echo "$label 이(가) 필요합니다."; exit 1; fi
  printf '%s' "$v" | gh secret set "$name" -R "$REPO" && echo "  ✓ $name 등록"; }
ask KAKAO_REST_KEY "카카오 REST API 키"
ask NAVER_CLIENT_ID "네이버 Client ID" opt
ask NAVER_CLIENT_SECRET "네이버 Client Secret" opt
ask YOUTUBE_API_KEY "YouTube Data API 키" opt
ask GOODPRICE_CSV_URL "착한가격업소 CSV 내려받기 주소" opt
gh workflow run daily-collect -R "$REPO"
gh workflow run verify-courses -R "$REPO" -f fix=true
echo -e "\n완료. 진행 상황: https://github.com/$REPO/actions"
