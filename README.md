# 장학금·지원금 마감 캘린더 — 데이터 수집기 (1단계)

대학생이 받을 수 있는 **청년정책 · 정부 보조금 · 학교 장학 공지**를 한곳에 모아
**마감 임박 순**으로 정리한 `data/feed.json` 을 만듭니다. 앱 화면은 이 파일만 읽으면 됩니다.

```
1층 (전국 공통)  온통청년 API ─┐
                 보조금24 API ─┼─▶ SQLite(data/items.db) ─▶ data/feed.json (마감순)
2층 (학교별)     장학 공지 목록 ─┘   ↑ AI가 본문에서 마감일·금액·자격·서류 추출
```

## 1. 설치

```bash
pip install -r requirements.txt
python tests/test_offline.py     # 4개 ✓ 나오면 정상
```

## 2. API 키 (전부 무료)

| 환경변수 | 어디서 | 비고 |
|---|---|---|
| `YOUTH_API_KEY` | 온통청년 > 이용안내 > 오픈 API 이용방법 | 청년정책 |
| `GOV24_API_KEY` | 공공데이터포털 > "행정안전부_대한민국 공공서비스(혜택) 정보" 활용신청 | 자동승인, **일반 인증키(Decoding)** 사용 |
| `ANTHROPIC_API_KEY` | console.anthropic.com | 없어도 돌아감 (규칙 기반 추출로 대체) |

```bash
# Mac/Linux
export YOUTH_API_KEY=...  GOV24_API_KEY=...  ANTHROPIC_API_KEY=...
# Windows PowerShell
$env:YOUTH_API_KEY="..."
```

## 3. 처음 한 번: 실제 응답 확인

공공 API는 개편 때 필드명이 바뀌는 일이 많아서, 코드가 여러 후보 이름을 자동으로 찾게 해뒀습니다.
그래도 첫 실행 전에 실제 필드명을 눈으로 확인하세요.

```bash
python run.py probe youth
python run.py probe gov24
```

출력된 필드명이 `sc/youth.py`, `sc/gov24.py` 맨 위의 `F_TITLE`, `F_PERIOD` 같은 후보 목록에 없으면 거기에 추가하면 됩니다.
온통청년 주소가 바뀌었으면 코드 수정 없이 `YOUTH_API_URL` 환경변수로 덮어쓰세요.

## 4. 실행

```bash
python run.py all           # 전체 수집 → data/feed.json
python run.py school ajou   # 학교 하나만 테스트
python run.py feed          # 수집 없이 feed.json만 다시 생성
```

하루 1~2번 돌리면 충분합니다. 이미 읽은 학교 공지는 다시 열지 않아서 AI 비용이 거의 안 듭니다.

## 5. 학교 추가하는 법

`config/schools.yaml` 에서 학교 블록의 `notice_url` 에 **장학 공지 목록 페이지 주소**를 넣고
`verified: true`, `enabled: true` 로 바꾸면 끝. 코드는 안 건드립니다.

- 확인된 주소: 아주대, 성균관대
- 비워둔 학교: 단국대, 한양대, 중앙대, 경희대, 건국대, 국민대, 동국대, 홍익대 → 브라우저로 장학 공지 탭을 열고 주소창 URL 복사

**주의:** 목록이 자바스크립트로만 그려지는 사이트(링크가 `javascript:` 로 시작)는 지금 방식으로 못 읽습니다.
`python run.py school <id>` 에서 "새 공지 0건"이 계속 나오면 그 경우일 가능성이 높아요.

## 6. 마감일 신뢰도 (`confidence`)

마감일이 틀리면 앱 신뢰가 바로 깨지므로 항목마다 신뢰도를 붙입니다.

- `high` — AI 추출 결과와 규칙 파서 결과가 일치 (또는 API가 준 날짜)
- `medium` — 날짜가 본문에 실제로 있음, 한쪽 방식만 찾음
- `low` — 확인 안 됨 → 앱에서 "원문 확인 필요" 배지 표시 권장

어떤 경우든 앱에는 **원문 링크(`url`)를 항상 함께 보여주세요.**

## 7. feed.json 형식

```json
{
  "generated": "2026-11-04",
  "items": [
    {
      "source": "school", "school": "ajou",
      "title": "[교외장학] 2026학년도 2학기 이인길 장학생 모집 공고",
      "url": "https://...", "deadline": "2026-11-28",
      "amount": "1인당 200만원",
      "eligibility": "직전학기 평점 3.0 이상, 소득 8구간 이하 재학생",
      "docs": ["신청서", "성적증명서", "가족관계증명서"],
      "summary": "...", "confidence": "high", "region": "경기 수원시"
    }
  ]
}
```

## 크롤링 매너 (지키고 있는 것)

- robots.txt 가 막으면 건너뜀
- 같은 사이트 요청 사이 최소 1.5초
- 본문은 요약만 저장·표시하고 원문 링크로 연결

## 파일 구조

```
run.py               실행 진입점
config/schools.yaml  학교 목록 + 장학 키워드
sc/youth.py          온통청년 수집
sc/gov24.py          보조금24 수집 (청년·대학생 관련만 필터)
sc/school.py         범용 학교 공지 수집 (목록 → 상세 → 추출)
sc/extract.py        AI/규칙 기반 정보 추출 + 교차검증
sc/dates.py          한국어 날짜 표기 → 마감일
sc/store.py          SQLite 저장 + 마감순 피드
tests/               네트워크 없이 도는 테스트
```
