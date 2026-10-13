"""거래 기록 백업 (GitHub 비공개 저장소).

Bitget은 체결·장부 기록을 최근 90일 정도까지만 내줌 → 그보다 오래된 기록이 사라지지 않게
불러온 원본 기록(체결 · 선물/현물 장부 · 입금 · 출금)을 '비공개' GitHub 저장소에 월별 파일로 쌓아 둠.

- Streamlit Secrets
    ARCHIVE_TOKEN = "github_pat_..."   (그 저장소 하나만 Contents 읽기/쓰기 권한)
    ARCHIVE_REPO  = "mun-9/mung-trading-data"   (생략하면 이 이름)
- 토큰이 없으면 백업 없이 지금처럼 동작.
- 안전장치: 저장소가 '비공개'가 아니면 절대 쓰지 않음 (거래 기록이 공개되지 않게).
"""
import base64
import gzip
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import streamlit as st

KST = timezone(timedelta(hours=9))
DEFAULT_REPO = "mun-9/mung-trading-data"
BRANCH = "main"
DIR = "archive"
KINDS = ("fills", "bills", "spot_bills", "deposits", "withdrawals")


def _cfg():
    try:
        tok = str(st.secrets.get("ARCHIVE_TOKEN", "") or "")
        repo = str(st.secrets.get("ARCHIVE_REPO", "") or DEFAULT_REPO)
    except Exception:
        return None, None
    return (tok, repo) if tok else (None, None)


def enabled():
    return _cfg()[0] is not None


def _req(method, url, body=None, raw=False):
    tok, _ = _cfg()
    h = {"Authorization": f"Bearer {tok}", "X-GitHub-Api-Version": "2022-11-28",
         "Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json", "User-Agent": "mung9-journal"}
    data = json.dumps(body).encode() if body is not None else None
    if data:
        h["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h, method=method), timeout=15) as r:
        b = r.read()
        return b if raw else (json.loads(b.decode()) if b else {})


def _is_private():
    _, repo = _cfg()
    return bool(_req("GET", f"https://api.github.com/repos/{repo}").get("private"))


def _month_of_ms(ms):
    return datetime.fromtimestamp(int(ms) / 1000, tz=KST).strftime("%Y-%m")


def _ts(kind, rec):
    if kind == "fills":
        return rec["ts"]
    if kind in ("bills", "spot_bills"):
        return int(rec.get("cTime") or 0)
    return int(rec.get("timestamp") or 0)


def load():
    """→ ({kind: {key: record}}, {파일명: sha})  · 실패하면 예외."""
    _, repo = _cfg()
    out = {k: {} for k in KINDS}
    shas = {}
    try:
        files = _req("GET", f"https://api.github.com/repos/{repo}/contents/{DIR}?ref={BRANCH}")
    except urllib.error.HTTPError as e:
        if e.code == 404:  # 아직 백업이 하나도 없음
            return out, shas
        raise
    for f in files if isinstance(files, list) else []:
        name = f.get("name", "")
        if not name.endswith(".json.gz"):
            continue
        shas[name] = f.get("sha")
        blob = _req("GET", f"https://api.github.com/repos/{repo}/contents/{DIR}/{name}?ref={BRANCH}", raw=True)
        part = json.loads(gzip.decompress(blob).decode("utf-8"))
        for k in KINDS:
            out[k].update(part.get(k) or {})
    return out, shas


def save(store, shas, changed_months):
    """바뀐 달의 파일만 다시 씀. 저장소가 비공개가 아니면 아무것도 안 함."""
    if not changed_months:
        return 0
    if not _is_private():
        raise RuntimeError("백업 저장소가 비공개(Private)가 아니라서 저장하지 않았어요")
    _, repo = _cfg()
    n = 0
    for m in sorted(changed_months):
        part = {k: {key: rec for key, rec in store[k].items() if _month_of_ms(_ts(k, rec)) == m} for k in KINDS}
        name = f"{m}.json.gz"
        body = {"message": f"backup {m} ({datetime.now(KST):%Y-%m-%d %H:%M} KST)", "branch": BRANCH,
                "content": base64.b64encode(gzip.compress(json.dumps(part, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))).decode()}
        if shas.get(name):
            body["sha"] = shas[name]
        res = _req("PUT", f"https://api.github.com/repos/{repo}/contents/{DIR}/{name}", body)
        shas[name] = (res.get("content") or {}).get("sha", shas.get(name))
        n += 1
    return n


def merge(store, kind, items, key_fn):
    """새로 받은 기록을 합치고, 새로 생긴 기록이 있는 달 set을 돌려줌."""
    months = set()
    for it in items:
        k = key_fn(it)
        if not k:
            continue
        if k not in store[kind]:
            months.add(_month_of_ms(_ts(kind, it)))
        store[kind][k] = it
    return months
