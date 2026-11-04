# 내돈내찾 · 토스 미니앱 출시 가이드

화면 원본은 `web/index.html` 하나예요. `toss-app/` 은 그걸 토스용으로 감싸서 `.ait` 번들을 만드는 곳이고,
공고 데이터는 GitHub가 매일 아침 수집해서 `feed.json` 으로 올려요.

```
GitHub Actions (매일 06:17)          토스 미니앱 (.ait)
  run.py all → feed.json  ──Pages──▶  화면이 feed.json 을 읽음
```

---

## 1단계 · API 키 (융 님이 직접, 무료)

| 키 | 어디서 |
|---|---|
| `YOUTH_API_KEY` | 온통청년 > 이용안내 > 오픈 API 이용방법 |
| `GOV24_API_KEY` | 공공데이터포털 > "행정안전부_대한민국 공공서비스(혜택) 정보" 활용신청 (일반 인증키 Decoding) |
| `ANTHROPIC_API_KEY` | console.anthropic.com (학교 공지 AI 추출용, 없어도 동작) |

받으면 PC에서 먼저 한 번 확인:

```bash
pip install -r requirements.txt
python run.py probe youth     # 필드명이 잘 잡히는지
python run.py probe gov24
python run.py all             # data/feed.json 생성
```

## 2단계 · GitHub에 올리고 매일 자동 수집 켜기

1. GitHub에 새 저장소 `scholarship-calendar` 를 **Public** 으로 만들고 이 폴더 전체를 올리기
   (`.gitignore` 가 data/, node_modules 등은 알아서 빼요)
2. 저장소 **Settings > Secrets and variables > Actions** 에 위 키 3개를 같은 이름으로 등록
3. **Settings > Pages > Source** 를 **GitHub Actions** 로 선택
4. **Actions 탭 > collect > Run workflow** 로 한 번 수동 실행
5. 성공하면 `https://<깃허브아이디>.github.io/scholarship-calendar/feed.json` 이 열려요. 이 주소가 공고 데이터 주소

수집이 0건으로 끝나면 배포를 안 해서, 어제 데이터가 그대로 유지돼요.

## 3단계 · 미니앱 번들 만들기

```bash
cd toss-app
cp .env.example .env          # VITE_FEED_URL 에 2단계 주소 넣기
npm install
npm run build                 # → naedon-naechat.ait 생성
```

`npm run dev` 로 PC 브라우저에서 미리 볼 수 있어요 (토스 기능은 꺼진 상태로 동작).

## 4단계 · 콘솔 등록과 검수

1. 앱인토스 콘솔에서 새 미니앱 만들기. **앱 이름(영문)을 `naedon-naechat` 로** (한글 표시 이름은 "내돈내찾 · 장학금 지원금 마감") 하거나,
   다르게 정했다면 `toss-app/apps-in-toss.config.ts` 의 `appName` 과 `.env` 의 `VITE_APP_NAME` 을 똑같이 바꾸기
2. 앱 정보 입력: 한글 이름, 아이콘, 스크린샷, 설명
3. `naedon-naechat.ait` 업로드 → 콘솔 QR로 내 폰 토스에서 테스트
   - 공유하기 → 토스 공유 시트가 뜨는지
   - "원문 보고 신청하기" → 브라우저로 열리는지
   - 맨 아래 테스트 배너 광고가 뜨는지
4. 콘솔에서 광고 그룹을 만들고, **출시 직전에만** `.env` 의 `VITE_AD_GROUP_ID` 에 실제 ID를 넣고 다시 빌드
5. 앱 출시 메뉴에서 앱 정보 + 번들 함께 검수 요청

광고 수익만 쓰면 사업자 등록 없이 출시돼요. 누적 예상수익이 5천 원이 되면 그때 사업자·정산정보를 등록하면 돼요.

## 검수 전에 스스로 확인할 것

- [ ] 예시 공고가 하나도 안 보이는지 (`.env` 의 `SC_SAMPLE` 비어 있어야 함)
- [ ] 모든 공고에 원문 링크가 있는지
- [ ] 마감일 신뢰도 낮은 공고에 "원문 확인" 표시가 뜨는지
- [ ] 화면 문구에 "확정", "무조건 받는" 같은 단정 표현이 없는지
- [ ] 광고가 버튼 바로 옆에 붙어 있지 않은지 (지금은 목록 맨 아래, 푸터 위)

## 나중에 붙일 것

- 마감 알림 (토스 푸시 / 알림 동의) — 반응 보고 2차에
- 학교 추가 — `config/schools.yaml` 에 URL만 넣으면 다음 날 아침 자동 반영
- 중복 수혜 불가 표시
