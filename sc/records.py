"""API 응답(JSON이든 XML이든)에서 '레코드 목록'을 찾아내고, 필드명을 후보 목록으로 매핑.

공공 API는 버전이 바뀔 때 필드명이 자주 바뀌어서, 필드명을 하드코딩하지 않고
후보 이름 중 처음 있는 것을 쓰는 방식으로 만들었다.
"""
import json
import xml.etree.ElementTree as ET


def _largest_dict_list(node):
    best = []
    if isinstance(node, list):
        if node and all(isinstance(x, dict) for x in node) and len(node) > len(best):
            best = node
        for x in node:
            cand = _largest_dict_list(x)
            if len(cand) > len(best):
                best = cand
    elif isinstance(node, dict):
        for v in node.values():
            cand = _largest_dict_list(v)
            if len(cand) > len(best):
                best = cand
    return best


def _xml_records(root: ET.Element) -> list[dict]:
    """같은 태그가 반복되는 가장 큰 묶음을 레코드로 본다."""
    best: list[dict] = []
    for parent in root.iter():
        children = list(parent)
        if len(children) < 1:
            continue
        tags = [c.tag for c in children]
        tag = max(set(tags), key=tags.count)
        group = [c for c in children if c.tag == tag and len(list(c)) > 0]
        if len(group) > len(best):
            best = [{g.tag: (g.text or "").strip() for g in rec} for rec in group]
    return best


def extract_records(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith("{") or text.startswith("["):
        return _largest_dict_list(json.loads(text))
    return _xml_records(ET.fromstring(text))


def pick(rec: dict, candidates: list[str], default=None):
    for c in candidates:
        v = rec.get(c)
        if v not in (None, "", "null"):
            return str(v).strip()
    return default
