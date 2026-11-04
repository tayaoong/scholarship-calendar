# 내돈내찾 — 이어서 작업하기 (2026-11-04 기준)

이 파일은 다른 Claude 대화에서 작업을 그대로 이어가기 위한 인수인계 문서예요.
사용자(융)는 개발 완전 초보라, 설명은 쉽게 하고 가능한 건 Claude가 직접 해주는 걸 원해요.

## 한 줄 요약
대학생·청년이 받을 수 있는 장학금·청년정책·정부지원금을 마감순으로 보여주는 **토스 앱인토스 미니앱 "내돈내찾"**.
데이터 수집·앱 빌드·배포는 끝났고, **토스 콘솔에서 검토 요청 직전** 단계예요.

## 어디에 뭐가 있나
| 항목 | 위치 |
|---|---|
| 코드 저장소 (공개) | https://github.com/tayaoong/scholarship-calendar (main 브랜치) |
| 공고 데이터 (매일 갱신) | https://tayaoong.github.io/scholarship-calendar/feed.json |
| 토스 앱 파일 (.ait, 매일 같이 빌드) | https://tayaoong.github.io/scholarship-calendar/naedon-naechat.ait |
| 토스 콘솔 앱 등록 화면 | https://apps-in-toss.toss.im/workspace/105897/mini-app/naedon-naechat/meta/edit |
| 앱 아이콘 원본 (10번 "내돈!" 말풍선) | `assets/icon.svg` |

## 구조
- `run.py`, `sc/` — 파이썬 수집기. 보조금24(gov24), 온통청년(youth), 학교 장학 공지(school) → SQLite → `data/feed.json`
  - `sc/gov24.py`: 청년·대학생 관련만 거르는 INCLUDE/EXCLUDE 정규식 + 나이 범위 검사. 출처별로 `store.replace_source()`로 통째 교체.
- `.github/workflows/collect.yml` — 매일 06:17(KST) 수집 → feed.json 검사(0건이면 배포 안 함) → `toss-app` 빌드해서 .ait 생성 → GitHub Pages 배포.
- `.github/workflows/build-app.yml` — .ait만 수동 빌드.
- `web/index.html` — 앱 화면 전체(한 파일). 토스/애플 스타일. 주요 기능:
  - 프로필(대학생/휴학생/청년, 학교, 시·도/시·군·구) — 전국 17개 시·도 시·군·구 목록 내장
  - 지역 필터 `scopeOf()`: 공고 제목·기관명에서 지역을 찾아, 내 지역이거나 전국 대상인 것만 표시 (재단 이름 앞 지역명도 인식: 목포인재육성재단 → 전남 목포)
  - 공고 검색창, 분류 칩(전체/장학금/청년정책/정부지원/찜), 이번 주 달력, 받을 수 있는 금액 합계, 상세 시트(서류 체크리스트·공유)
  - 줄바꿈: 문장 단위 우선(`bySentence()` + `.s{display:inline-block}`), 안 되면 단어 단위(`word-break:keep-all`). 사용자가 줄바꿈 품질에 민감함.
- `toss-app/` — 앱인토스 WebView 래퍼 (`@apps-in-toss/web-framework@3.9.0`). appName `naedon-naechat`.
  - `scripts/sync.mjs`가 `web/index.html`에 설정(SC_CONFIG: feedUrl, sample:false, onboarding:true)과 `src/bridge.js`를 끼워 넣음.
  - `src/bridge.js`: 공유 링크, 외부 링크 열기, 토스 배너 광고(`#adSlot`, 광고 ID는 저장소 변수 `AD_GROUP_ID`, 없으면 테스트 ID).

## 비밀 키 (GitHub 저장소 Settings → Secrets → Actions)
- `GOV24_API_KEY` ✅ 들어가 있음 (공공데이터포털 "행정안전부_대한민국 공공서비스(혜택) 정보", 일반 인증키 Decoding)
- `YOUTH_API_KEY` ❌ **아직 없음** → 온통청년 공고 0건. 온통청년(youthcenter.go.kr) 오픈API 키 발급받아 넣으면 됨.
- `ANTHROPIC_API_KEY` 선택 (학교 공지 본문에서 마감일 추출용)
- 키 값은 절대 Claude가 직접 입력하지 않고 사용자가 넣음.

## 현재 숫자
- 공고 961건 (보조금24 954 + 성균관대 공지 7), 마감일 확인된 것 63건
- 경기 용인으로 설정 시 151건 보임 (지역 필터 개선 전 201건 → 다른 지역 재단 장학금 50건 제외)

## 토스 콘솔 진행 상황 (워크스페이스 105897, 앱 naedon-naechat, 비게임)
✅ 완료(임시저장됨)
- 앱 번들 업로드: 최신 버전 **20261104-2** (지역 필터·검색창 들어간 버전)
- 한국어 이름 `내돈내찾`, 영어 이름 `Naedon Naechat`, 부제 `놓친 장학금·지원금 마감 전에 찾기`
- 상세 설명, 출시 노트, 메모, 사용 연령(만 19세 이상)
- 고객문의 이메일 `kohyung101@gmail.com`
- 앱 로고 + 다크모드 로고: 10번 "내돈!" 말풍선 아이콘

⏳ 남은 일 (순서대로)
1. **토스앱 테스트** — 콘솔의 "토스앱 테스트" 버튼 → 사용자가 폰으로 열어 확인 (20261104-2가 아직 `isTested:false`). 확인할 것: 용인 설정 시 타지역 공고 안 뜨는지, 검색창 동작.
2. **카테고리 및 노출** 단계 — 카테고리 선택, 스크린샷(콘솔의 "AI로 스크린샷 자동으로 채우기" 또는 직접 업로드), 앱 검색 키워드(예: 장학금, 지원금, 청년정책, 대학생, 마감, 국가장학금, 청년지원금, 월세지원).
3. **검토 요청** — 반드시 사용자에게 먼저 물어보고 누를 것.
4. (출시 후) 토스 광고 그룹 ID 받으면 저장소 Variables에 `AD_GROUP_ID` 추가.
5. (개선) 온통청년 키 넣기, 학교 공지 소스 늘리기(`config/schools.yaml`, 지금은 성균관대만 실제 수집됨).

## 작업 요령 (이전 대화에서 알아낸 것)
- 이전 환경에서는 Claude의 git push/GitHub API 쓰기가 막혀 있었음(403). 그래서 **사용자 데스크톱 Claude 앱의 내장 브라우저**로 GitHub 웹 편집기를 열어 수정·커밋했음:
  `https://github.com/tayaoong/scholarship-calendar/edit/main/<파일경로>` → 편집기(`.cm-content`)에 포커스 → Ctrl+A, Delete → 붙여넣기 이벤트로 새 내용 넣기 → "Commit changes..." → 대화상자의 "Commit changes".
  새 환경에서 GitHub 연결이 되면 그냥 git push 하면 됨.
- 수집·빌드 다시 돌리기: Actions → collect → Run workflow. 끝나면 Pages의 .ait가 새 버전이 됨.
- 콘솔에 .ait 올리기: 콘솔 페이지에서 JS로 위 .ait 주소를 fetch → File로 만들어 `input[type=file][accept=".ait"]`에 넣고 change 이벤트. 아이콘(png)도 같은 방식.
- 토스 비즈니스 로그인은 사용자가 직접 함. 비밀번호·키는 Claude가 입력하지 않음.
