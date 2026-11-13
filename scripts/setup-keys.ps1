# 착한맛자랑 — API 키 등록 + 첫 수집 한 번에 (Windows PowerShell)
# 준비: GitHub CLI 설치 후 로그인 (winget install GitHub.cli ; gh auth login)
# 실행: 저장소 폴더에서  powershell -ExecutionPolicy Bypass -File scripts\setup-keys.ps1
$ErrorActionPreference = "Stop"
$repo = "morogohi/goodplate"
Write-Host "`n착한맛자랑 키 등록 — 입력한 키는 화면에 보이지 않고 GitHub Secrets 에만 저장됩니다.`n" -ForegroundColor Green
Write-Host "발급처: 카카오 https://developers.kakao.com  / 네이버 https://developers.naver.com  / YouTube https://console.cloud.google.com`n"
function Ask($name, $label, $optional=$false) {
  $s = Read-Host -AsSecureString "$label$(if($optional){' (없으면 Enter)'})"
  $v = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
  if ([string]::IsNullOrWhiteSpace($v)) { if ($optional) { return }; throw "$label 이(가) 필요합니다." }
  $v | gh secret set $name -R $repo
  Write-Host "  ✓ $name 등록" -ForegroundColor Green
}
gh auth status | Out-Null
Ask "KAKAO_REST_KEY" "카카오 REST API 키"
Ask "NAVER_CLIENT_ID" "네이버 Client ID" $true
Ask "NAVER_CLIENT_SECRET" "네이버 Client Secret" $true
Ask "YOUTUBE_API_KEY" "YouTube Data API 키" $true
Ask "GOODPRICE_CSV_URL" "착한가격업소 CSV 내려받기 주소" $true
Write-Host "`n첫 수집과 코스 좌표 검증을 시작합니다..." -ForegroundColor Green
gh workflow run daily-collect -R $repo
gh workflow run verify-courses -R $repo -f fix=true
Write-Host "완료. 진행 상황: https://github.com/$repo/actions  (수집이 끝나면 스토어 스크린샷도 자동으로 다시 만들어집니다)`n"
