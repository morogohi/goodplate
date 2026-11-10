// 앱 번들(www/) 만들기: 앱 화면(app.html)을 www/index.html 로, 데이터·아이콘·안내 페이지를 함께 복사한다.
// 앱은 실행 중 최신 데이터를 https://morogohi.github.io/goodplate/data/ 에서 받고, 실패하면 이 번들 데이터를 쓴다.
import { cpSync, mkdirSync, rmSync, readFileSync, writeFileSync } from 'node:fs';
const out = 'www';
rmSync(out, { recursive: true, force: true });
mkdirSync(out);
writeFileSync(`${out}/index.html`, readFileSync('app.html', 'utf8'));
for (const f of ['privacy.html', 'support.html', 'copyright.html', 'icon.svg', 'icon-192.png', 'icon-512.png', 'manifest.webmanifest']) cpSync(f, `${out}/${f}`);
cpSync('data', `${out}/data`, { recursive: true });
console.log('www/ 준비 완료');
