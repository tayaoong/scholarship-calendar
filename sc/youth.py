"""1층 · 온통청년 청년정책 API 수집기.

키 발급: 온통청년(youthcenter.go.kr) > 이용안내 > 오픈 API 이용방법 에서 신청.
요청 URL/파라미터명은 온통청년 문서 기준이며, API 개편으로 바뀌면
환경변수 YOUTH_API_URL, YOUTH_KEY_PARAM 으로 덮어쓰면 된다.
처음 돌릴 때는 `python run.py probe youth` 로 실제 응답 필드명을 꼭 확인할 것.
"""
import os
from datetime import date

from . import http
from .dates import parse_deadline
from .records import extract_records, pick
from .store import make_id

# 2025년 개편된 주소를 먼저 시도하고, 응답이 비면 예전 주소로 한 번 더 시도
API_URLS = [u for u in [os.getenv("YOUTH_API_URL"),
                        "https://www.youthcenter.go.kr/go/ythip/getPlcy",
                        "https://www.youthcenter.go.kr/opi/youthPlcyList.do"] if u]
KEY_PARAM = os.getenv("YOUTH_KEY_PARAM", "openApiVlak")

# 필드명 후보 (신·구 버전 모두 커버)
F_ID = ["plcyNo", "bizId", "polyBizSecd"]
F_TITLE = ["plcyNm", "polyBizSjnm"]
F_PERIOD = ["aplyYmd", "rqutPrdCn", "bizPrdBgngYmd"]
F_URL = ["aplyUrlAddr", "rqutUrla", "refUrlAddr1", "rfcSiteUrla1"]
F_DESC = ["plcyExplnCn", "polyItcnCn"]
F_SUPPORT = ["plcySprtCn", "sporCn"]
F_TARGET = ["addAplyQlfcCndCn", "sprtTrgtCn", "ageInfo", "splzRlmRqisCn"]
F_REGION = ["rgtrUpInstCdNm", "rgtrInstCdNm", "zipCd", "polyBizSecd"]


def fetch_raw(page: int = 1, size: int = 100, query: str = "") -> str:
    key = os.environ["YOUTH_API_KEY"].strip()  # 붙여넣을 때 딸려온 줄바꿈·공백 제거
    params = {KEY_PARAM: key, "apiKeyNm": key, "pageIndex": page, "pageNum": page,
              "display": size, "pageSize": size, "rtnType": "json"}
    if query:
        params["query"] = query
    last = ""
    for url in API_URLS:
        try:
            last = http.get(url, params=params).text
            if extract_records(last):
                return last
        except Exception as e:  # 주소가 바뀌었으면 다음 후보로
            print(f"  온통청년 {url} 실패: {e}")
    return last


def to_item(rec: dict, today: date) -> dict | None:
    title = pick(rec, F_TITLE)
    if not title:
        return None
    period = pick(rec, F_PERIOD, "")
    dl = parse_deadline(period, today)
    return {
        "id": make_id("youth", pick(rec, F_ID) or title),
        "source": "youth",
        "title": title,
        "url": pick(rec, F_URL),
        "period_raw": period,
        "deadline": dl.isoformat() if dl else None,
        "region": pick(rec, F_REGION),
        "amount": pick(rec, F_SUPPORT),
        "eligibility": pick(rec, F_TARGET),
        "summary": (pick(rec, F_DESC) or "")[:300],
        "confidence": "high" if dl else "low",
    }


def collect(store, max_pages: int = 10, today: date | None = None) -> int:
    today = today or date.today()
    found = []
    for page in range(1, max_pages + 1):
        recs = extract_records(fetch_raw(page))
        if not recs:
            break
        found += [it for it in (to_item(r, today) for r in recs) if it]
    if found:
        store.replace_source("youth", found)
    return len(found)
