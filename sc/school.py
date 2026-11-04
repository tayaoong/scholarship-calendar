"""2층 · 학교별 장학 공지 범용 수집기.

학교마다 크롤러를 따로 짜지 않는다. 목록 페이지에서
  1) 제목에 장학 키워드가 있는 링크를 찾고
  2) 처음 보는 글만 상세 페이지를 열어 본문을 뽑고
  3) extract.py 가 마감일·자격·금액을 정리
하는 방식이라 schools.yaml 에 URL 한 줄만 추가하면 새 학교가 붙는다.
"""
import re
from datetime import date
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from . import http
from .extract import extract
from .store import make_id

NOISE = ["script", "style", "nav", "header", "footer", "aside", "form", "noscript", "iframe"]
BODY_HINTS = ["board-view", "bbs_view", "view-con", "view_cont", "fr-view", "article", "content", "view"]


def find_notice_links(html: str, base_url: str, include: list[str], exclude: list[str]) -> list[tuple[str, str]]:
    """목록 HTML → [(제목, 상세URL)] (중복 제거, 등장 순)."""
    soup = BeautifulSoup(html, "html.parser")
    seen, out = set(), []
    for a in soup.select("a[href]"):
        title = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
        title = re.sub(r"\s*NEW\s*$", "", title)
        href = a["href"].strip()
        if len(title) < 6 or href.startswith(("javascript:", "#", "mailto:")):
            continue
        if not any(k in title for k in include) or any(k in title for k in exclude):
            continue
        url = urljoin(base_url, href)
        if url in seen:
            continue
        seen.add(url)
        out.append((title, url))
    return out


def main_text(html: str) -> str:
    """상세 페이지에서 본문만. 알려진 본문 클래스 → 없으면 텍스트가 가장 긴 블록."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(NOISE):
        tag.decompose()
    for hint in BODY_HINTS:
        el = soup.select_one(f'[class*="{hint}"]')
        if el and len(el.get_text(strip=True)) > 80:
            return _clean(el.get_text("\n"))
    blocks = soup.find_all(["div", "section", "td", "article"])
    best = max(blocks, key=lambda b: len(b.get_text(strip=True)), default=soup)
    return _clean(best.get_text("\n"))


def _clean(t: str) -> str:
    lines = [re.sub(r"[ \t ]+", " ", ln).strip() for ln in t.splitlines()]
    return "\n".join(ln for ln in lines if ln)[:8000]


def collect_school(store, school: dict, include: list[str], exclude: list[str],
                   max_new: int = 20, today: date | None = None) -> int:
    today = today or date.today()
    list_url = school["notice_url"]
    if not http.allowed(list_url):
        print(f"  [{school['name']}] robots.txt 가 수집을 막고 있어 건너뜀")
        return 0
    links = find_notice_links(http.get(list_url).text, list_url, include, exclude)
    n = 0
    for title, url in links:
        item_id = make_id("school", url)
        if store.has(item_id):
            continue  # 이미 처리한 공지는 다시 안 읽음 (AI 비용 절약)
        if n >= max_new:
            break
        body = main_text(http.get(url).text) if http.allowed(url) else ""
        info = extract(title, body, today)
        if not info.get("is_opportunity", True):
            continue
        store.upsert({
            "id": item_id, "source": "school", "school": school["id"],
            "title": title, "url": url, "region": school.get("region"),
            "deadline": info.get("deadline"), "period_raw": None,
            "amount": info.get("amount"), "eligibility": info.get("eligibility"),
            "docs": info.get("docs") or [], "summary": info.get("summary"),
            "confidence": info.get("confidence"),
        })
        n += 1
    return n
