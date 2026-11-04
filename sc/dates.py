"""한국어 공지에 흔한 날짜 표기에서 '마감일'을 뽑는 규칙 기반 파서.

AI 키가 없을 때의 대체 수단이자, AI 결과를 교차검증하는 용도.
예: "2026.11.20(금)까지", "~ 11/28", "2026-11-03 ~ 2026-11-20", "11. 20.(목) 18:00"
"""
import re
from datetime import date

_FULL = re.compile(r"(20\d{2})\s*[.\-/년]\s*(\d{1,2})\s*[.\-/월]\s*(\d{1,2})")
_SHORT = re.compile(r"(?<![\d.])(\d{1,2})\s*[./월]\s*(\d{1,2})(?:\s*일)?(?![\d])")
_COMPACT = re.compile(r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)")  # 20261120 (API에 흔함)


def _valid(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None


def find_dates(text: str, ref_year: int) -> list[date]:
    """텍스트 속 모든 날짜를 등장 순서대로."""
    if not text:
        return []
    found: list[tuple[int, date]] = []
    taken: list[tuple[int, int]] = []

    def overlaps(span):
        return any(not (span[1] <= a or span[0] >= b) for a, b in taken)

    for rx, kind in ((_COMPACT, "c"), (_FULL, "f"), (_SHORT, "s")):
        for m in rx.finditer(text):
            if overlaps(m.span()):
                continue
            if kind in ("c", "f"):
                dt = _valid(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            else:
                dt = _valid(ref_year, int(m.group(1)), int(m.group(2)))
            if dt:
                found.append((m.start(), dt))
                taken.append(m.span())
    return [d for _, d in sorted(found)]


def parse_deadline(text: str, today: date | None = None) -> date | None:
    """신청기간 문자열에서 마감일 추정.

    규칙: '~' 뒤에 오는 날짜가 있으면 그것, 없으면 등장한 날짜 중 가장 늦은 것.
    연도 없는 날짜(11/20)는 올해로 보되, 오늘보다 4개월 이상 과거면 내년으로 넘김.
    """
    today = today or date.today()
    if not text:
        return None
    if any(k in text for k in ("상시", "수시", "예산 소진")) and not find_dates(text, today.year):
        return None

    tail = text.split("~")[-1] if "~" in text else text
    dates = find_dates(tail, today.year) or find_dates(text, today.year)
    if not dates:
        return None
    dl = max(dates)
    # 연도 생략 표기 보정 (12월 공지에 '~1/10' 같은 경우)
    if (today - dl).days > 120 and not _FULL.search(text) and not _COMPACT.search(text):
        dl = _valid(dl.year + 1, dl.month, dl.day) or dl
    return dl
