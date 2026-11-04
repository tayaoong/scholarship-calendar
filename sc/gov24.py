"""1층 · 보조금24(행정안전부_대한민국 공공서비스(혜택) 정보) 수집기.

키 발급: 공공데이터포털(data.go.kr)에서 '행정안전부_대한민국 공공서비스(혜택) 정보' 활용신청(자동승인).
1만 개가 넘는 혜택이 들어 있어서, 대학생·청년·자취생과 관련된 것만 키워드로 거른다.
"""
import os
from datetime import date

from . import http
from .dates import parse_deadline
from .records import extract_records, pick
from .store import make_id

API_URL = os.getenv("GOV24_API_URL", "https://api.odcloud.kr/api/gov24/v3/serviceList")

RELEVANT = ["청년", "대학생", "대학원생", "장학", "학자금", "1인가구", "자취", "월세", "주거", "취업", "구직"]

F_ID = ["서비스ID", "serviceId", "SVC_ID"]
F_TITLE = ["서비스명", "serviceName", "SVC_NM"]
F_PERIOD = ["신청기한", "applyPeriod"]
F_URL = ["상세조회URL", "detailUrl"]
F_TARGET = ["지원대상", "선정기준"]
F_SUPPORT = ["지원내용", "지원유형"]
F_DESC = ["서비스목적요약", "서비스목적"]
F_ORG = ["소관기관명", "부서명"]


def fetch_raw(page: int = 1, size: int = 500) -> str:
    params = {"page": page, "perPage": size, "serviceKey": os.environ["GOV24_API_KEY"].strip()}  # 줄바꿈·공백 제거
    return http.get(API_URL, params=params).text


def is_relevant(rec: dict) -> bool:
    blob = " ".join(str(v) for v in rec.values())
    return any(k in blob for k in RELEVANT)


def to_item(rec: dict, today: date) -> dict | None:
    title = pick(rec, F_TITLE)
    if not title:
        return None
    period = pick(rec, F_PERIOD, "")
    dl = parse_deadline(period, today)
    return {
        "id": make_id("gov24", pick(rec, F_ID) or title),
        "source": "gov24",
        "title": title,
        "url": pick(rec, F_URL),
        "period_raw": period,
        "deadline": dl.isoformat() if dl else None,
        "region": pick(rec, F_ORG),
        "amount": pick(rec, F_SUPPORT),
        "eligibility": pick(rec, F_TARGET),
        "summary": (pick(rec, F_DESC) or "")[:300],
        "confidence": "high" if dl else "low",
    }


def collect(store, max_pages: int = 30, today: date | None = None) -> int:
    today = today or date.today()
    n = 0
    for page in range(1, max_pages + 1):
        recs = extract_records(fetch_raw(page))
        if not recs:
            break
        for rec in recs:
            if not is_relevant(rec):
                continue
            item = to_item(rec, today)
            if item:
                store.upsert(item)
                n += 1
    return n
"""1층 · 보조금24(행정안전부_대한민국 공공서비스(혜택) 정보) 수집기.

키 발급: 공공데이터포털(data.go.kr)에서 '행정안전부_대한민국 공공서비스(혜택) 정보' 활용신청(자동승인).
1만 개가 넘는 혜택이 들어 있어서, 대학생·청년·자취생과 관련된 것만 키워드로 거른다.
"""
import os
from datetime import date

from . import http
from .dates import parse_deadline
from .records import extract_records, pick
from .store import make_id

API_URL = os.getenv("GOV24_API_URL", "https://api.odcloud.kr/api/gov24/v3/serviceList")

RELEVANT = ["청년", "대학생", "대학원생", "장학", "학자금", "1인가구", "자취", "월세", "주거", "취업", "구직"]

F_ID = ["서비스ID", "serviceId", "SVC_ID"]
F_TITLE = ["서비스명", "serviceName", "SVC_NM"]
F_PERIOD = ["신청기한", "applyPeriod"]
F_URL = ["상세조회URL", "detailUrl"]
F_TARGET = ["지원대상", "선정기준"]
F_SUPPORT = ["지원내용", "지원유형"]
F_DESC = ["서비스목적요약", "서비스목적"]
F_ORG = ["소관기관명", "부서명"]


def fetch_raw(page: int = 1, size: int = 500) -> str:
    params = {"page": page, "perPage": size, "serviceKey": os.environ["GOV24_API_KEY"]}
    return http.get(API_URL, params=params).text


def is_relevant(rec: dict) -> bool:
    blob = " ".join(str(v) for v in rec.values())
    return any(k in blob for k in RELEVANT)


def to_item(rec: dict, today: date) -> dict | None:
    title = pick(rec, F_TITLE)
    if not title:
        return None
    period = pick(rec, F_PERIOD, "")
    dl = parse_deadline(period, today)
    return {
        "id": make_id("gov24", pick(rec, F_ID) or title),
        "source": "gov24",
        "title": title,
        "url": pick(rec, F_URL),
        "period_raw": period,
        "deadline": dl.isoformat() if dl else None,
        "region": pick(rec, F_ORG),
        "amount": pick(rec, F_SUPPORT),
        "eligibility": pick(rec, F_TARGET),
        "summary": (pick(rec, F_DESC) or "")[:300],
        "confidence": "high" if dl else "low",
    }


def collect(store, max_pages: int = 30, today: date | None = None) -> int:
    today = today or date.today()
    n = 0
    for page in range(1, max_pages + 1):
        recs = extract_records(fetch_raw(page))
        if not recs:
            break
        for rec in recs:
            if not is_relevant(rec):
                continue
            item = to_item(rec, today)
            if item:
                store.upsert(item)
                n += 1
    return n
