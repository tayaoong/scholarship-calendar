"""예의 바른 HTTP: robots.txt 확인, 요청 간 간격, 일반 UA."""
import time
import urllib.robotparser
from urllib.parse import urlparse

import requests

UA = "ScholarshipCalendarBot/0.1 (+student project; respects robots.txt)"
_session = requests.Session()
_session.headers.update({"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9"})
_robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
_last_hit: dict[str, float] = {}
MIN_INTERVAL = 1.5  # 같은 사이트에 최소 1.5초 간격


def allowed(url: str) -> bool:
    host = urlparse(url)
    base = f"{host.scheme}://{host.netloc}"
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(base + "/robots.txt")
        try:
            r = _session.get(base + "/robots.txt", timeout=10)
            rp.parse(r.text.splitlines() if r.status_code == 200 else [])
        except requests.RequestException:
            rp.parse([])
        _robots[base] = rp
    rp = _robots[base]
    return rp.can_fetch(UA, url) if rp else True


def get(url: str, **kw) -> requests.Response:
    netloc = urlparse(url).netloc
    wait = MIN_INTERVAL - (time.time() - _last_hit.get(netloc, 0))
    if wait > 0:
        time.sleep(wait)
    kw.setdefault("timeout", 20)
    r = _session.get(url, **kw)
    _last_hit[netloc] = time.time()
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() == "iso-8859-1":
        r.encoding = r.apparent_encoding  # 한국 사이트 EUC-KR 대응
    return r
