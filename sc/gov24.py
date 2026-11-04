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

import re

# 제목이나 지원대상에 이런 말이 있어야 대학생·청년 공고로 봄 (예전엔 공고 전체 글에서 찾아서 엉뚱한 게 많이 섞였음)
INCLUDE = re.compile(r"청년|대학생|대학원생|재학생|장학|학자금|휴학|졸업예정|사회초년|1인\s*가구|자취|취업준비|구직")
# 제목에 이런 말이 있으면 대상이 다른 공고라 뺌
EXCLUDE = re.compile(r"노인|어르신|65세|60세 이상|영유아|임산부|산모|출산|초등|중학생|고등학생|청소년|농업인|농업경영|"
                     r"어업인|축산|소상공인|사업자|법인|중소기업|장애인|국가유공|보훈|참전|다문화|한부모|기초생활|위기가구|공무원")
AGE = re.compile(r"(\d{2})\s*세\s*(?:이상)?\s*[~∼\-]\s*(?:만\s*)?(\d{2})\s*세")

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


def _age_fits(text: str) -> bool:
    """'만 19세~34세' 같은 나이 범위에 20대 중반이 들어가면 청년 대상으로 봄"""
    m = AGE.search(text or "")
    return bool(m) and int(m.group(1)) <= 24 <= int(m.group(2)) <= 45


def is_relevant(rec: dict) -> bool:
    title = pick(rec, F_TITLE, "")
    target = (pick(rec, F_TARGET, "") or "")[:200]
    if EXCLUDE.search(title):
        return False
    return bool(INCLUDE.search(title) or INCLUDE.search(target) or _age_fits(target))


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
        "amount": (pick(rec, F_SUPPORT) or "")[:200],
        "eligibility": (pick(rec, F_TARGET) or "")[:300],
        "summary": (pick(rec, F_DESC) or "")[:300],
        "confidence": "high" if dl else "low",
    }


def collect(store, max_pages: int = 30, today: date | None = None) -> int:
    today = today or date.today()
    found = []
    for page in range(1, max_pages + 1):
        recs = extract_records(fetch_raw(page))
        if not recs:
            break
        for rec in recs:
            if is_relevant(rec):
                item = to_item(rec, today)
                if item:
                    found.append(item)
    if found:  # 새로 받아온 게 있을 때만 예전 목록을 통째로 바꿈 (끝난 공고·기준 바뀐 공고 정리)
        store.replace_source("gov24", found)
    return len(found)
