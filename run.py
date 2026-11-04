"""장학금·지원금 마감 캘린더 수집기 실행 파일.

  python run.py all              # 전부 수집 → data/feed.json 생성
  python run.py youth            # 온통청년만
  python run.py gov24            # 보조금24만
  python run.py schools          # 학교 공지만 (schools.yaml 에서 enabled 인 학교)
  python run.py school ajou      # 특정 학교만
  python run.py probe youth      # API 응답의 실제 필드명 확인 (처음 1회 필수)
  python run.py probe gov24
  python run.py feed             # 저장된 데이터로 feed.json 만 다시 만들기
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from sc import gov24, school, youth  # noqa: E402
from sc.records import extract_records  # noqa: E402
from sc.store import Store  # noqa: E402

DB = ROOT / "data" / "items.db"
FEED = ROOT / "data" / "feed.json"


def load_cfg():
    return yaml.safe_load((ROOT / "config" / "schools.yaml").read_text(encoding="utf-8"))


def need(env: str) -> bool:
    if os.getenv(env):
        return True
    print(f"  {env} 환경변수가 없어서 건너뜀 (README의 'API 키' 참고)")
    return False


def run_youth(store):
    if need("YOUTH_API_KEY"):
        print(f"  온통청년: {youth.collect(store)}건")


def run_gov24(store):
    if need("GOV24_API_KEY"):
        print(f"  보조금24(청년·대학생 관련): {gov24.collect(store)}건")


def run_schools(store, only: str | None = None):
    cfg = load_cfg()
    for s in cfg["schools"]:
        if only and s["id"] != only:
            continue
        if not only and not s.get("enabled"):
            continue
        if not s.get("notice_url"):
            print(f"  [{s['name']}] notice_url 비어 있음 → schools.yaml 채우기")
            continue
        try:
            n = school.collect_school(store, s, cfg["include_keywords"], cfg["exclude_keywords"])
            print(f"  [{s['name']}] 새 공지 {n}건")
        except Exception as e:
            print(f"  [{s['name']}] 실패: {e}")


def probe(which: str):
    raw = youth.fetch_raw(1, 3) if which == "youth" else gov24.fetch_raw(1, 3)
    recs = extract_records(raw)
    print(f"레코드 {len(recs)}개 발견")
    if recs:
        print("필드명:", list(recs[0].keys()))
        print(json.dumps(recs[0], ensure_ascii=False, indent=2)[:2000])
    else:
        print(raw[:1500])


def write_feed(store):
    items = store.feed(date.today())
    schools = [{"id": s["id"], "name": s["name"]}
               for s in load_cfg()["schools"] if s.get("enabled") and s.get("notice_url")]
    payload = json.dumps({"generated": date.today().isoformat(), "schools": schools, "items": items},
                         ensure_ascii=False, indent=2)
    FEED.write_text(payload, encoding="utf-8")
    (ROOT / "web" / "feed.json").write_text(payload, encoding="utf-8")  # 웹 화면이 읽는 사본
    dated = sum(1 for i in items if i["deadline"])
    print(f"feed.json: {len(items)}건 (마감일 확인 {dated}건) → {FEED}")


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "all"
    if cmd == "probe":
        return probe(argv[2])
    store = Store(DB)
    if cmd in ("all", "youth"):
        run_youth(store)
    if cmd in ("all", "gov24"):
        run_gov24(store)
    if cmd in ("all", "schools"):
        run_schools(store)
    if cmd == "school":
        run_schools(store, only=argv[2])
    write_feed(store)


if __name__ == "__main__":
    main(sys.argv)
