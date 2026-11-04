"""공지 본문 → 구조화 정보. Claude가 있으면 AI로, 없으면 규칙 기반으로.

AI가 뽑은 마감일은 규칙 파서 결과와 교차검증해서 confidence 를 매긴다.
(마감일이 틀리면 앱 신뢰가 바로 깨지므로)
"""
import json
import os
import re
from datetime import date

from .dates import find_dates, parse_deadline

MODEL = os.getenv("EXTRACT_MODEL", "claude-haiku-5-5")

PROMPT = """너는 대학생 장학금·지원금 공지를 정리하는 도우미야.
아래 공지 본문을 읽고 JSON 하나만 출력해. 설명 문장 금지.

{{
  "is_opportunity": true/false,   // 학생이 '신청'할 수 있는 장학·지원 모집이면 true. 결과발표·수여식·단순안내는 false
  "deadline": "YYYY-MM-DD" 또는 null,   // 학생이 서류를 내야 하는 최종 마감일. 학과 내부 마감이 따로 있으면 더 빠른 쪽
  "amount": "금액이나 혜택 한 줄" 또는 null,
  "eligibility": "자격 조건을 쉬운 말 한두 문장으로",
  "docs": ["필요 서류", ...],
  "summary": "대학생 친구에게 말하듯 2문장 요약"
}}

오늘 날짜: {today}  (연도 없는 날짜는 오늘 기준으로 판단)
공지 제목: {title}
공지 본문:
\"\"\"
{body}
\"\"\"
"""


def _rule_based(title: str, body: str, today: date) -> dict:
    text = f"{title}\n{body}"
    # '마감', '까지', '기한' 근처 문장 우선
    hot = [ln for ln in text.splitlines() if re.search(r"마감|까지|기한|접수|신청\s*기간|제출", ln)]
    dl = None
    for ln in hot:
        dl = parse_deadline(ln, today)
        if dl:
            break
    dl = dl or parse_deadline(title, today)
    amt = re.search(r"(\d[\d,]*\s*만\s*원|\d[\d,]*\s*원|등록금\s*(전액|\d+\s*%))", text)
    return {
        "is_opportunity": not re.search(r"결과|합격자|명단|수여식", title),
        "deadline": dl.isoformat() if dl else None,
        "amount": amt.group(0) if amt else None,
        "eligibility": None,
        "docs": [],
        "summary": None,
    }


def _ai(title: str, body: str, today: date) -> dict:
    import anthropic  # 키가 있을 때만 필요

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": PROMPT.format(today=today.isoformat(), title=title, body=body[:6000])}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}


def extract(title: str, body: str, today: date | None = None) -> dict:
    today = today or date.today()
    rule = _rule_based(title, body, today)
    if not os.getenv("ANTHROPIC_API_KEY"):
        rule["confidence"] = "medium" if rule["deadline"] else "low"
        return rule

    try:
        ai = _ai(title, body, today)
    except Exception as e:  # AI 실패해도 수집은 계속
        print(f"  [AI 추출 실패 → 규칙 기반 사용] {e}")
        rule["confidence"] = "medium" if rule["deadline"] else "low"
        return rule

    # 교차검증: AI 마감일이 본문에 실제로 등장하는 날짜인지
    ai_dl = ai.get("deadline")
    in_text = {d.isoformat() for d in find_dates(f"{title}\n{body}", today.year)}
    if ai_dl and ai_dl == rule["deadline"]:
        conf = "high"
    elif ai_dl and ai_dl in in_text:
        conf = "medium"
    else:
        conf = "low"
    ai["confidence"] = conf
    return {**rule, **{k: v for k, v in ai.items() if v not in (None, "", [])}}
