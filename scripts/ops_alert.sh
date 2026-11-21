#!/usr/bin/env bash
# 운영 경고를 GitHub 이슈로 — 열린 경고 이슈가 있으면 댓글, 없으면 새로 만듦 (저장소 소유자에게 메일 알림)
#   ops_alert.sh open "제목" 본문파일   |   ops_alert.sh close "정상화 메시지"
set -u
MODE="$1"; LABEL=ops-alert
num=$(gh issue list --label "$LABEL" --state open --json number -q '.[0].number' 2>/dev/null)
if [ "$MODE" = open ]; then
  TITLE="$2"; BODY="$3"
  gh label create "$LABEL" --color D93F0B --description "자동 운영 경고 (수집 실패·데이터 지연)" 2>/dev/null || true
  if [ -n "$num" ]; then gh issue comment "$num" --body-file "$BODY"
  else gh issue create --title "$TITLE" --label "$LABEL" --body-file "$BODY"; fi
else
  [ -n "$num" ] && gh issue close "$num" --comment "$2" || echo "열린 경고 없음"
fi
