"""네트워크 없이 핵심 로직 검증. 실행: python -m pytest tests -q  (또는 python tests/test_offline.py)"""
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sc import gov24, youth  # noqa: E402
from sc.dates import parse_deadline  # noqa: E402
from sc.extract import extract  # noqa: E402
from sc.records import extract_records  # noqa: E402
from sc.school import find_notice_links, main_text  # noqa: E402
from sc.store import Store  # noqa: E402

TODAY = date(2026, 11, 4)

LIST_HTML = """
<table><tbody>
<tr><td>1031</td><td><a href="?mode=view&articleNo=111">[교외장학] 2026학년도 2학기 이인길 장학생 모집 공고(~11.28.(금)까지) NEW</a></td></tr>
<tr><td>1030</td><td><a href="?mode=view&articleNo=110">[교외장학] 2026년 하반기 인재육성장학생 선발계획 공고</a></td></tr>
<tr><td>1029</td><td><a href="?mode=view&articleNo=109">2026학년도 2학기 성적우수장학생 선발 결과 안내</a></td></tr>
<tr><td>1028</td><td><a href="?mode=view&articleNo=108">도서관 휴관 안내</a></td></tr>
<tr><td>1027</td><td><a href="javascript:void(0)">[장학] 자바스크립트 링크 장학공지</a></td></tr>
</tbody></table>"""

DETAIL_HTML = """
<html><head><script>var x=1;</script></head><body>
<nav>메뉴 메뉴 메뉴</nav>
<div class="board-view-con">
 1. 지원자격: 재학생 중 직전학기 평점 3.0 이상, 소득 8구간 이하
 2. 장학금액: 1인당 200만원
 3. 제출기한: 2026. 11. 28.(금) 17:00까지 학생지원팀 방문 제출
 4. 제출서류: 신청서, 성적증명서, 가족관계증명서
</div>
<footer>주소 경기도 수원시</footer>
</body></html>"""


def test_dates():
    assert parse_deadline("2026.11.03 ~ 2026.11.20", TODAY) == date(2026, 11, 20)
    assert parse_deadline("~11.28.(금)까지", TODAY) == date(2026, 11, 28)
    assert parse_deadline("20261101 ~ 20261215", TODAY) == date(2026, 12, 15)
    assert parse_deadline("~ 1/10", TODAY) == date(2027, 1, 10)  # 연도 넘김
    assert parse_deadline("상시 신청", TODAY) is None
    assert parse_deadline("2026년 12월 5일까지", TODAY) == date(2026, 12, 5)


def test_school_links_and_body():
    links = find_notice_links(LIST_HTML, "https://www.ajou.ac.kr/kr/ajou/notice_scholarship.do",
                              ["장학", "장학생"], ["결과", "합격자"])
    titles = [t for t, _ in links]
    assert len(links) == 2, titles  # 결과발표·도서관·javascript 링크 제외
    assert links[0][1] == "https://www.ajou.ac.kr/kr/ajou/notice_scholarship.do?mode=view&articleNo=111"
    assert not titles[0].endswith("NEW")
    body = main_text(DETAIL_HTML)
    assert "200만원" in body and "메뉴" not in body and "var x" not in body


def test_rule_extract():
    body = main_text(DETAIL_HTML)
    info = extract("이인길 장학생 모집 공고", body, TODAY)
    assert info["deadline"] == "2026-11-28"
    assert "200만원" in info["amount"]
    assert info["is_opportunity"] is True
    assert info["confidence"] == "medium"


def test_api_records_and_feed():
    youth_json = json.dumps({"result": {"pagging": {"totCount": 2}, "youthPolicyList": [
        {"plcyNo": "R1", "plcyNm": "경기도 청년 월세 지원", "aplyYmd": "20261101 ~ 20261130",
         "aplyUrlAddr": "https://example.go.kr/a", "plcySprtCn": "월 20만원 최대 12개월"},
        {"plcyNo": "R2", "plcyNm": "청년 마음건강 바우처", "aplyYmd": "", "plcySprtCn": "상담 지원"},
    ]}})
    youth_xml = """<youthPolicyList><pageIndex>1</pageIndex>
      <youthPolicy><bizId>X1</bizId><polyBizSjnm>용인시 청년 교통비</polyBizSjnm><rqutPrdCn>2026.10.01~2026.11.10</rqutPrdCn></youthPolicy>
      <youthPolicy><bizId>X2</bizId><polyBizSjnm>지난 정책</polyBizSjnm><rqutPrdCn>2026.01.01~2026.02.01</rqutPrdCn></youthPolicy>
    </youthPolicyList>"""
    gov_json = json.dumps({"page": 1, "data": [
        {"서비스ID": "G1", "서비스명": "대학생 근로장학금", "신청기한": "2026.11.03 ~ 2026.11.20", "지원대상": "대학생"},
        {"서비스ID": "G2", "서비스명": "노인 일자리", "신청기한": "상시", "지원대상": "만 65세 이상"},
    ]})

    with tempfile.TemporaryDirectory() as d:
        store = Store(Path(d) / "t.db")
        for raw in (youth_json, youth_xml):
            for rec in extract_records(raw):
                store.upsert(youth.to_item(rec, TODAY))
        for rec in extract_records(gov_json):
            if gov24.is_relevant(rec):
                store.upsert(gov24.to_item(rec, TODAY))
        feed = store.feed(TODAY)
        titles = [i["title"] for i in feed]
        assert titles[0] == "용인시 청년 교통비"          # 11/10 가장 임박
        assert titles[1] == "대학생 근로장학금"           # 11/20
        assert titles[2] == "경기도 청년 월세 지원"       # 11/30
        assert "지난 정책" not in titles                 # 마감 지남 제외
        assert "노인 일자리" not in titles               # 관련 없음 필터
        assert titles[-1] == "청년 마음건강 바우처"       # 마감일 모름 → 맨 뒤


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("✓", name)
