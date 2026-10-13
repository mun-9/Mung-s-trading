"""거래소 데이터 조회 + 손익 계산.

손익 계산 원칙
- 청산 손익(gross): Bitget 체결의 profit 값 (수수료 전)
- 수수료: 체결마다 낸 수수료. 진입 수수료는 바로 빼지 않고 보관했다가
  해당 포지션을 청산할 때 청산 수량 비율만큼 그 거래 손익에서 함께 뺀다 (FIFO).
- 펀딩비: 거래소 장부(account bill)의 contract_settle_fee, 발생한 날짜에 반영
- 페이백: USDT 입금 중 조건에 맞는 것, 입금된 날짜에 반영
- 순손익 = 청산 손익 - 수수료(청산 + 배분된 진입) + 펀딩비 + 페이백
"""
import random
from datetime import datetime, timedelta, timezone

import ccxt
import pandas as pd
import streamlit as st

KST = timezone(timedelta(hours=9))
UTC = timezone.utc

# 대시보드 기준 날짜 (이전 데이터는 표시하지 않음)
DASHBOARD_START_DATE = "2026-09-28"

# 원금으로 직접 넣은 입금액 (이 금액과 맞는 입금만 원금, 나머지 입금은 전부 페이백)
PRINCIPAL_DEPOSITS = [10520, 302, 250, 229.25]

# (예전 규칙, 원금 목록이 비어 있을 때만 사용) 이 날짜 이후, 이 금액 미만의 USDT 입금 = 페이백
PAYBACK_START = datetime(2026, 10, 1, tzinfo=KST)
PAYBACK_MAX = 10000

PRODUCT_TYPE = "USDT-FUTURES"

# 장부 조회가 실패했을 때만 쓰는 기본 종목 목록
BASE_SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT",
    "BNB/USDT", "ADA/USDT", "SUI/USDT", "1000PEPE/USDT", "WIF/USDT",
]

TRADE_BILL_TYPES = {
    "open_long", "open_short", "close_long", "close_short",
    "force_close_long", "force_close_short",
    "burst_long_loss_query", "burst_short_loss_query",
    "force_buy", "force_sell", "burst_buy", "burst_sell",
    "delivery_long", "delivery_short",
}
FUNDING_BILL_TYPE = "contract_settle_fee"

TRADE_COLS = [
    "order_id", "datetime", "date", "symbol", "side", "bucket", "has_pnl",
    "gross", "fee", "net", "amount", "price", "result",
]
EVENT_COLS = ["datetime", "date", "symbol", "kind", "amount"]


# -----------------------------------------------------------------------------
# 공통
# -----------------------------------------------------------------------------
def get_keys():
    try:
        return (st.secrets["API_KEY"], st.secrets["SECRET_KEY"], st.secrets["PASSPHRASE"])
    except Exception:
        return ("", "", "")


def principal_list():
    """원금 입금액 목록. Streamlit Secrets의 PRINCIPAL_DEPOSITS(쉼표 구분)가 있으면 그걸 우선."""
    try:
        raw = st.secrets["PRINCIPAL_DEPOSITS"]
        vals = raw if isinstance(raw, (list, tuple)) else str(raw).split(",")
        out = [float(v) for v in vals if str(v).strip()]
        if out:
            return out
    except Exception:
        pass
    return list(PRINCIPAL_DEPOSITS)


def match_principal(deps, amounts):
    """원금 금액마다 가장 가까운 입금 하나를 짝지음 (네트워크 수수료로 조금 덜 들어와도 2% 안이면 인정)."""
    used = set()
    for a in sorted(amounts, reverse=True):
        best, best_diff = None, None
        for d in deps:
            if id(d) in used:
                continue
            diff = abs(float(d.get("amount") or 0) - a)
            if diff <= max(1.0, a * 0.02) and (best_diff is None or diff < best_diff):
                best, best_diff = d, diff
        if best is not None:
            used.add(id(best))
    return used


def is_demo(keys):
    return not keys[0] or not keys[1]


def _exchange(keys=None):
    cfg = {"enableRateLimit": True, "options": {"defaultType": "swap"}}
    if keys:
        cfg.update({"apiKey": keys[0], "secret": keys[1], "password": keys[2]})
    return ccxt.bitget(cfg)


def _to_kst(ms):
    return datetime.fromtimestamp(int(ms) / 1000, tz=UTC).astimezone(KST)


def _plain_symbol(sym):
    return (sym or "").replace(":USDT", "")


def result_of(bucket, has_pnl, net):
    if bucket == "증가":
        return "진입"
    if not has_pnl:
        return "미확인"
    if net > 0:
        return "익절"
    if net < 0:
        return "손절"
    return "본전"


# -----------------------------------------------------------------------------
# 시세 (공개 API)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def fetch_usdt_krw():
    try:
        return float(ccxt.upbit({"enableRateLimit": True}).fetch_ticker("USDT/KRW").get("last") or 1350.0)
    except Exception:
        return 1350.0


@st.cache_data(ttl=30, show_spinner=False)
def fetch_live_ohlcv(symbol, timeframe, limit=120):
    try:
        bars = _exchange().fetch_ohlcv(symbol + ":USDT", timeframe, limit=limit)
    except Exception:
        return pd.DataFrame()
    df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["datetime"] = (pd.to_datetime(df["timestamp"], unit="ms")
                      .dt.tz_localize("UTC").dt.tz_convert("Asia/Seoul").dt.tz_localize(None))
    return df


# -----------------------------------------------------------------------------
# 포지션 & 잔고 (10초 캐시)
# -----------------------------------------------------------------------------
DEMO_POSITIONS = [
    {"symbol": "BTC/USDT", "side": "LONG", "leverage": 20, "entry_price": 63200.0, "mark_price": 64800.0,
     "size": 0.3, "margin": 948.0, "liq_price": 60100.0, "unrealized_pnl": 480.0, "roe": 50.6},
    {"symbol": "BTC/USDT", "side": "SHORT", "leverage": 20, "entry_price": 65100.0, "mark_price": 64800.0,
     "size": 0.5, "margin": 1581.25, "liq_price": 68200.0, "unrealized_pnl": 150.0, "roe": 9.4},
]


@st.cache_data(ttl=10, show_spinner=False)
def fetch_positions(keys):
    """(포지션 목록, 지갑 잔고, 오류 메시지 or None)"""
    if is_demo(keys):
        return DEMO_POSITIONS, 10000.0, None
    try:
        ex = _exchange(keys)
        bal = ex.fetch_balance({"type": "swap"})
        total_balance = float((bal.get("USDT") or {}).get("total") or 0)
        out = []
        for p in ex.fetch_positions():
            size = float(p.get("contracts") or 0)
            if size <= 0:
                continue
            side = (p.get("side") or "long").upper()
            entry, mark = float(p.get("entryPrice") or 0), float(p.get("markPrice") or 0)
            margin = float(p.get("initialMargin") or 0)
            upnl = p.get("unrealizedPnl")
            upnl = float(upnl) if upnl is not None else ((mark - entry) * size if side == "LONG" else (entry - mark) * size)
            out.append({
                "symbol": _plain_symbol(p.get("symbol")), "side": side, "leverage": int(float(p.get("leverage") or 1)),
                "entry_price": entry, "mark_price": mark, "size": size, "margin": margin,
                "liq_price": float(p.get("liquidationPrice") or 0), "unrealized_pnl": upnl,
                "roe": (upnl / margin * 100) if margin > 0 else 0.0,
            })
        return out, total_balance, None
    except Exception as e:
        return [], 0.0, f"{type(e).__name__}: {e}"


# -----------------------------------------------------------------------------
# 체결 → 거래(주문) 단위 + 수수료 배분
# -----------------------------------------------------------------------------
def parse_fill(t):
    info = t.get("info") or {}
    ts = str(info.get("tradeSide", "")).lower()
    ro = info.get("reduceOnly", t.get("reduceOnly"))
    raw = info.get("profit", info.get("realizedPnl"))
    has_pnl = raw not in (None, "")
    gross = float(raw or 0)

    if "open" in ts:
        is_close = False
    elif "close" in ts:
        is_close = True
    elif ro in (True, "true", "YES", "yes"):
        is_close = True
    elif ro in (False, "false", "NO", "no"):
        is_close = False
    else:
        is_close = has_pnl and gross != 0

    buy = str(info.get("side") or t.get("side", "")).lower() == "buy"
    hedge = str(info.get("posMode", "")).lower() == "hedge_mode" or ts in ("open", "close")
    if "long" in ts:
        side = "LONG"
    elif "short" in ts:
        side = "SHORT"
    elif hedge:
        # Bitget 양방향(헤지) 모드: 롱 포지션은 진입·청산 모두 side=buy, 숏은 모두 sell
        side = "LONG" if buy else "SHORT"
    else:
        # 단방향 모드: 청산 체결은 반대 방향 주문이므로 뒤집어서 판단
        side = ("LONG" if buy else "SHORT") if not is_close else ("SHORT" if buy else "LONG")

    fee = 0.0
    fee_obj = t.get("fee") or {}
    if fee_obj.get("cost") is not None and str(fee_obj.get("currency", "USDT")).upper() in ("USDT", ""):
        fee = abs(float(fee_obj["cost"]))

    dt = _to_kst(t["timestamp"])
    return {
        "trade_id": str(t.get("id") or f"{t.get('order')}_{t['timestamp']}"),
        "order_id": str(t.get("order") or t["timestamp"]),
        "datetime": dt.replace(tzinfo=None), "date": dt.strftime("%Y-%m-%d"),
        "symbol": _plain_symbol(t.get("symbol")), "side": side, "is_close": bool(is_close),
        "has_pnl": has_pnl, "gross": gross, "fee": fee,
        "amount": float(t.get("amount") or 0), "price": float(t.get("price") or t.get("average") or 0),
    }


def build_trades(fills):
    """체결 목록 → 주문 단위 거래 DataFrame + 아직 청산되지 않은 진입 수수료.

    진입 체결의 수수료는 (종목, 방향)별로 보관하고, 청산 체결이 나올 때
    청산 수량 / 보유 수량 비율만큼 꺼내서 그 청산 거래의 수수료로 함께 계산한다.
    """
    if not fills:
        return pd.DataFrame(columns=TRADE_COLS), {}
    df = pd.DataFrame(fills).drop_duplicates(subset=["trade_id"]).sort_values("datetime", kind="stable")

    book = {}  # (symbol, side) -> [보유 수량, 보관 중인 진입 수수료]
    fee_total, nets = [], []
    for r in df.itertuples(index=False):
        key = (r.symbol, r.side)
        qty, pool = book.get(key, [0.0, 0.0])
        if not r.is_close:
            book[key] = [qty + r.amount, pool + r.fee]
            fee_total.append(r.fee)
            nets.append(0.0)
            continue
        alloc = 0.0
        if qty > 0 and pool > 0:
            if r.amount >= qty - 1e-12:
                alloc = pool
            else:
                alloc = pool * (r.amount / qty)
        book[key] = [max(qty - r.amount, 0.0), pool - alloc]
        fee_total.append(r.fee + alloc)
        nets.append(r.gross - r.fee - alloc)

    df["fee_all"] = fee_total
    df["net"] = nets
    df["bucket"] = df["is_close"].map({True: "축소", False: "증가"})
    df["notional"] = df["amount"] * df["price"]

    g = df.groupby(["order_id", "symbol", "side"], as_index=False).agg(
        datetime=("datetime", "last"), date=("date", "last"),
        bucket=("bucket", lambda s: s.mode().iat[0]), has_pnl=("has_pnl", "max"),
        gross=("gross", "sum"), fee=("fee_all", "sum"), net=("net", "sum"),
        amount=("amount", "sum"), notional=("notional", "sum"),
    )
    g["price"] = (g["notional"] / g["amount"]).where(g["amount"] > 0, 0.0)
    # 진입 주문은 손익이 없으므로 net=0, 수수료는 청산 때 반영되므로 0으로 표기
    is_open = g["bucket"] == "증가"
    g.loc[is_open, "fee"] = 0.0
    g["result"] = [result_of(b, h, n) for b, h, n in zip(g["bucket"], g["has_pnl"], g["net"])]
    g = g.drop(columns=["notional"]).sort_values("datetime", ascending=False)

    # 아직 청산되지 않은 진입 수수료: {"종목|방향": [남은 수량, 보관 중인 수수료]}
    pending = {f"{k[0]}|{k[1]}": [v[0], v[1]] for k, v in book.items() if v[0] > 1e-12 and v[1] > 0}
    return g[TRADE_COLS].reset_index(drop=True), pending


# -----------------------------------------------------------------------------
# 거래소 장부 (펀딩비, 거래한 종목 목록, 검증용 합계)
# -----------------------------------------------------------------------------
def fetch_bills(ex, since_ms, now_ms):
    bills, window = [], 7 * 24 * 60 * 60 * 1000
    start = since_ms
    while start < now_ms:
        end = min(start + window, now_ms)
        id_less = None
        for _ in range(100):
            req = {"productType": PRODUCT_TYPE, "startTime": str(start), "endTime": str(end), "limit": "100"}
            if id_less:
                req["idLessThan"] = id_less
            data = (ex.privateMixGetV2MixAccountBill(req) or {}).get("data") or {}
            page = data.get("bills") or []
            bills.extend(page)
            if len(page) < 100:
                break
            next_id = data.get("endId") or page[-1].get("billId")
            if not next_id or next_id == id_less:
                break
            id_less = next_id
        start = end
    uniq = {b.get("billId"): b for b in bills}
    return list(uniq.values())


def parse_bills(ex, bills):
    """→ (펀딩비 이벤트, 장부 일별 순손익 DataFrame, 거래한 종목 set)"""
    events, ledger, symbols = [], [], set()
    for b in bills:
        bt = str(b.get("businessType", ""))
        if str(b.get("coin", "USDT")).upper() != "USDT":
            continue
        dt = _to_kst(b.get("cTime") or 0)
        amount = float(b.get("amount") or 0)
        fee = float(b.get("fee") or 0)
        sym = _plain_symbol(ex.safe_symbol(b.get("symbol"), None, None, "swap")) if b.get("symbol") else ""
        if bt == FUNDING_BILL_TYPE:
            events.append({"datetime": dt.replace(tzinfo=None), "date": dt.strftime("%Y-%m-%d"),
                           "symbol": sym, "kind": "funding", "amount": amount + fee})
            ledger.append({"date": dt.strftime("%Y-%m-%d"), "net": amount + fee})
        elif bt in TRADE_BILL_TYPES:
            if sym:
                symbols.add(sym)
            ledger.append({"date": dt.strftime("%Y-%m-%d"), "net": amount + fee})
    ledger_df = (pd.DataFrame(ledger).groupby("date", as_index=False)["net"].sum()
                 if ledger else pd.DataFrame(columns=["date", "net"]))
    return events, ledger_df, symbols


# -----------------------------------------------------------------------------
# 전체 거래 데이터 (캐시)
# -----------------------------------------------------------------------------
def _empty_result(errors=None, demo=False):
    return {"trades": pd.DataFrame(columns=TRADE_COLS), "events": pd.DataFrame(columns=EVENT_COLS),
            "ledger": pd.DataFrame(columns=["date", "net"]), "pending_fees": {}, "fills": [],
            "errors": errors or [], "demo": demo, "loaded_at": datetime.now(KST)}


def _finish(fills, events, ledger, errors, demo):
    trades, pending = build_trades(fills)
    trades = trades[trades["date"] >= DASHBOARD_START_DATE] if not trades.empty else trades
    ev = pd.DataFrame(events, columns=EVENT_COLS) if events else pd.DataFrame(columns=EVENT_COLS)
    if not ev.empty:
        ev = ev[ev["date"] >= DASHBOARD_START_DATE].sort_values("datetime", ascending=False)
    return {"trades": trades.reset_index(drop=True), "events": ev.reset_index(drop=True), "ledger": ledger,
            "pending_fees": pending, "errors": errors, "demo": demo, "loaded_at": datetime.now(KST)}


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_history(keys, _format=3):
    if is_demo(keys):
        return _demo_history()

    errors = []
    try:
        ex = _exchange(keys)
        ex.load_markets()
    except Exception as e:
        return _empty_result([f"거래소 연결 실패: {type(e).__name__}: {e}"])

    since_ms = int(datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").replace(tzinfo=KST).timestamp() * 1000)
    now_ms = int(datetime.now(UTC).timestamp() * 1000)

    # 1) 장부: 펀딩비 + 실제로 거래한 종목 찾기
    events, ledger, traded = [], pd.DataFrame(columns=["date", "net"]), set()
    try:
        events, ledger, traded = parse_bills(ex, fetch_bills(ex, since_ms, now_ms))
    except Exception as e:
        errors.append(f"장부(펀딩비) 조회 실패 — 펀딩비 미반영: {type(e).__name__}: {e}")

    # 2) 체결: 장부에서 찾은 종목 + 현재 보유 종목 (장부 실패 시 기본 목록)
    symbols = set(traded)
    if not symbols:
        symbols = set(BASE_SYMBOLS)
    try:
        pos, _, _ = fetch_positions(keys)
        symbols |= {p["symbol"] for p in pos}
    except Exception:
        pass

    fills = []
    chunk = 2 * 24 * 60 * 60 * 1000
    for sym in sorted(symbols):
        mkt = f"{sym}:USDT"
        if mkt not in ex.markets:
            continue
        cur = since_ms
        while cur < now_ms:
            until = min(cur + chunk, now_ms)
            end = until
            # 한 번에 최대 100건 → 100건이 꽉 차면 가장 오래된 체결 이전 구간을 다시 조회
            for _ in range(50):
                try:
                    trades = ex.fetch_my_trades(symbol=mkt, since=cur, limit=100, params={"until": end})
                except Exception as e:
                    errors.append(f"{sym} 체결 조회 실패: {type(e).__name__}: {e}")
                    break
                fills.extend(parse_fill(t) for t in trades)
                if len(trades) < 100:
                    break
                oldest = min(t["timestamp"] for t in trades)
                if oldest <= cur or oldest >= end:
                    break
                end = oldest
            cur = until

    # 3) 입출금: 원금·페이백 구분 (현물 계좌로 들어오는 USDT 입금)
    transfers = []
    try:
        look_from_w = int((datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").replace(tzinfo=KST)
                           - timedelta(days=90)).timestamp() * 1000)
        cur = look_from_w
        wds = {}
        while cur < now_ms:
            until = min(cur + 30 * 24 * 60 * 60 * 1000, now_ms)
            for w in ex.fetch_withdrawals(code="USDT", since=cur, limit=100, params={"until": until}):
                if str(w.get("status", "")).lower() in ("ok", "success", "completed", "1") and w.get("timestamp"):
                    wds[str(w.get("id") or w["timestamp"])] = w
            cur = until
        for w in wds.values():
            dt = _to_kst(w["timestamp"])
            transfers.append({"datetime": dt.replace(tzinfo=None), "date": dt.strftime("%Y-%m-%d"),
                              "kind": "withdraw", "amount": float(w.get("amount") or 0)})
    except Exception as e:
        errors.append(f"출금 내역 조회 실패: {type(e).__name__}: {e}")

    #    PAYBACK_MAX 이상 입금 = 원금. 마지막 원금 입금 이후의 입금은 전부 페이백.
    try:
        look_from = int((datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").replace(tzinfo=KST)
                         - timedelta(days=90)).timestamp() * 1000)
        deps = []
        cur = look_from
        while cur < now_ms:
            until = min(cur + 30 * 24 * 60 * 60 * 1000, now_ms)
            deps.extend(ex.fetch_deposits(code="USDT", since=cur, limit=100, params={"until": until}))
            cur = until
        ok = {}
        for d in deps:
            if str(d.get("status", "")).lower() in ("ok", "success", "completed", "1") and d.get("timestamp"):
                ok[str(d.get("id") or d["timestamp"])] = d
        deps = sorted(ok.values(), key=lambda d: d["timestamp"])
        principal_ids = match_principal(deps, principal_list())
        for d in deps:
            amount = float(d.get("amount") or 0)
            dt = _to_kst(d["timestamp"])
            is_principal = id(d) in principal_ids
            # 원금이 아닌 입금 중 대시보드 시작일 이후 것 = 페이백
            is_payback = not is_principal and d["timestamp"] >= since_ms and amount > 0
            if not is_principal and not is_payback:
                continue  # 시작일 이전 페이백은 표시·계산 안 함
            transfers.append({"datetime": dt.replace(tzinfo=None), "date": dt.strftime("%Y-%m-%d"),
                              "kind": "payback" if is_payback else "principal", "amount": amount})
            if is_payback:
                events.append({"datetime": dt.replace(tzinfo=None), "date": dt.strftime("%Y-%m-%d"),
                               "symbol": "", "kind": "payback", "amount": amount})
    except Exception as e:
        errors.append(f"입금(페이백) 조회 실패: {type(e).__name__}: {e}")

    out = _finish(fills, events, ledger, errors, demo=False)
    out["transfers"] = sorted(transfers, key=lambda x: x["datetime"], reverse=True)
    return out


# -----------------------------------------------------------------------------
# 데모 데이터 (API 키가 없을 때)
# -----------------------------------------------------------------------------
def _demo_history():
    rnd = random.Random(7)
    start = datetime.strptime(DASHBOARD_START_DATE, "%Y-%m-%d").replace(tzinfo=KST)
    now = datetime.now(KST)
    fee_rate = 0.0006
    base = {"BTC/USDT": 63000.0, "ETH/USDT": 2500.0, "SOL/USDT": 150.0}
    size = {"BTC/USDT": 0.2, "ETH/USDT": 3.0, "SOL/USDT": 40.0}
    fills, events, ledger = [], [], {}
    n = 0

    def add_fill(t, sym, side, is_close, qty, price, gross):
        nonlocal n
        n += 1
        fee = qty * price * fee_rate
        fills.append({"trade_id": f"D{n}", "order_id": f"DO{n}",
                      "datetime": t.replace(tzinfo=None), "date": t.strftime("%Y-%m-%d"),
                      "symbol": sym, "side": side, "is_close": is_close, "has_pnl": is_close,
                      "gross": round(gross, 4), "fee": round(fee, 4), "amount": qty, "price": round(price, 2)})
        d = t.strftime("%Y-%m-%d")
        ledger[d] = ledger.get(d, 0.0) + gross - fee

    t = start + timedelta(hours=2)
    while t < now - timedelta(hours=6):
        sym = rnd.choice(list(base))
        side = rnd.choice(["LONG", "SHORT"])
        entry = base[sym] * (1 + rnd.uniform(-0.03, 0.03))
        qty = size[sym] * rnd.choice([0.5, 1, 1.5])
        parts = rnd.choice([1, 1, 2])
        for _ in range(parts):
            add_fill(t, sym, side, False, qty / parts, entry, 0.0)
            t += timedelta(minutes=rnd.randint(1, 20))
        move = rnd.choice([1, 1, -1]) * rnd.uniform(0.001, 0.012)
        exit_p = entry * (1 + move) if side == "LONG" else entry * (1 - move)
        t += timedelta(minutes=rnd.randint(10, 300))
        closes = rnd.choice([1, 2])
        for _ in range(closes):
            q = qty / closes
            gross = (exit_p - entry) * q if side == "LONG" else (entry - exit_p) * q
            add_fill(t, sym, side, True, q, exit_p, gross)
            t += timedelta(minutes=rnd.randint(1, 30))
        t += timedelta(hours=rnd.uniform(1, 9))

    # 지금 보유 중인 데모 포지션의 진입 체결 (청산 전이라 수수료 보관)
    for p in DEMO_POSITIONS:
        add_fill(now - timedelta(hours=3), p["symbol"], p["side"], False, p["size"], p["entry_price"], 0.0)

    # 펀딩비 (8시간마다) & 페이백 (전날 수수료의 50%)
    day = start
    while day < now:
        for h in (1, 9, 17):
            ft = day.replace(hour=h)
            if ft < now and rnd.random() < 0.7:
                amt = round(rnd.uniform(-4, 1.5), 4)
                events.append({"datetime": ft.replace(tzinfo=None), "date": ft.strftime("%Y-%m-%d"),
                               "symbol": "BTC/USDT", "kind": "funding", "amount": amt})
                ledger[ft.strftime("%Y-%m-%d")] = ledger.get(ft.strftime("%Y-%m-%d"), 0.0) + amt
        prev = (day - timedelta(days=1)).strftime("%Y-%m-%d")
        prev_fee = sum(f["fee"] for f in fills if f["date"] == prev)
        if day >= PAYBACK_START and prev_fee > 0:
            pt = day.replace(hour=11)
            if pt < now:
                events.append({"datetime": pt.replace(tzinfo=None), "date": pt.strftime("%Y-%m-%d"),
                               "symbol": "", "kind": "payback", "amount": round(prev_fee * 0.5, 2)})
        day += timedelta(days=1)

    ledger_df = pd.DataFrame([{"date": k, "net": v} for k, v in ledger.items()])
    out = _finish(fills, events, ledger_df, [], demo=True)
    principal_dt = (start - timedelta(days=3)).replace(tzinfo=None)
    out["transfers"] = sorted(
        [{"datetime": principal_dt, "date": principal_dt.strftime("%Y-%m-%d"), "kind": "principal", "amount": 10000.0}]
        + [{"datetime": e["datetime"], "date": e["date"], "kind": "payback", "amount": e["amount"]} for e in events if e["kind"] == "payback"],
        key=lambda x: x["datetime"], reverse=True)
    out["demo_equity"] = 10000.0 + sum(ledger.values()) + sum(e["amount"] for e in events if e["kind"] == "payback")
    return out


# -----------------------------------------------------------------------------
# 집계 헬퍼
# -----------------------------------------------------------------------------
def period_slice(hist, start_str, end_str):
    t, ev, lg = hist["trades"], hist["events"], hist["ledger"]
    t = t[(t["date"] >= start_str) & (t["date"] <= end_str)] if not t.empty else t
    ev = ev[(ev["date"] >= start_str) & (ev["date"] <= end_str)] if not ev.empty else ev
    lg = lg[(lg["date"] >= start_str) & (lg["date"] <= end_str)] if not lg.empty else lg
    return t, ev, lg


def breakdown(trades, events):
    closes = trades[trades["bucket"] == "축소"] if not trades.empty else trades
    gross = float(closes["gross"].sum()) if not closes.empty else 0.0
    fee = float(closes["fee"].sum()) if not closes.empty else 0.0
    funding = float(events.loc[events["kind"] == "funding", "amount"].sum()) if not events.empty else 0.0
    payback = float(events.loc[events["kind"] == "payback", "amount"].sum()) if not events.empty else 0.0
    return {"gross": gross, "fee": fee, "funding": funding, "payback": payback,
            "net": gross - fee + funding + payback}


def daily_net(trades, events, start_str, end_str):
    dates = [d.strftime("%Y-%m-%d") for d in pd.date_range(start=start_str, end=end_str)]
    out = pd.DataFrame({"date": dates})
    closes = trades[trades["bucket"] == "축소"] if not trades.empty else trades
    t = closes.groupby("date")["net"].sum() if not closes.empty else pd.Series(dtype=float)
    e = events.groupby("date")["amount"].sum() if not events.empty else pd.Series(dtype=float)
    out["pnl"] = out["date"].map(t).fillna(0.0) + out["date"].map(e).fillna(0.0)
    out["cum"] = out["pnl"].cumsum()
    return out


def performance(trades):
    closes = trades[(trades["bucket"] == "축소") & trades["has_pnl"]] if not trades.empty else trades
    if closes.empty:
        return None
    c = closes.sort_values("datetime")
    wins, losses = c[c["net"] > 0]["net"], c[c["net"] < 0]["net"]
    gw, gl = float(wins.sum()), float(-losses.sum())
    streak = worst = 0
    for v in c["net"]:
        streak = streak + 1 if v < 0 else 0
        worst = max(worst, streak)
    eq = c["net"].cumsum()
    mdd = float((eq - eq.cummax()).min())
    avg_w = float(wins.mean()) if len(wins) else 0.0
    avg_l = float(-losses.mean()) if len(losses) else 0.0
    return {
        "count": len(c), "profit_factor": (gw / gl) if gl > 0 else None,
        "avg_win": avg_w, "avg_loss": avg_l, "rr": (avg_w / avg_l) if avg_l > 0 else None,
        "expectancy": float(c["net"].mean()), "max_loss_streak": worst, "mdd": mdd,
        "best": float(c["net"].max()), "worst": float(c["net"].min()),
        "dd": (eq - eq.cummax()).round(2).tolist(),
    }


# -----------------------------------------------------------------------------
# 관심 종목 시세 (차트 페이지 초기값, 15초 캐시)
# -----------------------------------------------------------------------------
WATCH_SYMBOLS = BASE_SYMBOLS + [
    "LINK/USDT", "AVAX/USDT", "TRX/USDT", "LTC/USDT", "DOT/USDT", "TON/USDT",
    "HYPE/USDT", "ENA/USDT", "TAO/USDT", "APT/USDT", "NEAR/USDT", "ARB/USDT",
]


@st.cache_data(ttl=15, show_spinner=False)
def fetch_tickers():
    try:
        raw = _exchange().fetch_tickers(params={"productType": PRODUCT_TYPE})
    except Exception:
        return {}
    out = {}
    for k, v in raw.items():
        if not k.endswith(":USDT"):
            continue
        info = v.get("info") or {}

        def f(x):
            try:
                return float(x)
            except (TypeError, ValueError):
                return None
        out[_plain_symbol(k)] = {
            "last": f(v.get("last")), "pct": f(v.get("percentage")), "high": f(v.get("high")),
            "low": f(v.get("low")), "qv": f(v.get("quoteVolume")), "funding": f(info.get("fundingRate")),
        }
    return out


@st.cache_data(ttl=60, show_spinner=False)
def fetch_upbit_krw():
    """업비트 원화 시세 {코인: {"last": 원, "pct": 변동%}} — 김프·하단 원화 시세용."""
    try:
        ex = ccxt.upbit({"enableRateLimit": True})
        ex.load_markets()
        syms = [s for s in ex.symbols if s.endswith("/KRW")]
        out = {}
        for i in range(0, len(syms), 100):
            for k, v in ex.fetch_tickers(syms[i:i + 100]).items():
                out[k.split("/")[0]] = {"last": v.get("last"), "pct": v.get("percentage")}
        return out
    except Exception:
        return {}


_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def _http_json(url, timeout=5):
    import json as _json
    import urllib.request
    with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=timeout) as r:
        return _json.loads(r.read().decode("utf-8"))


@st.cache_data(ttl=15, show_spinner=False)
def fetch_usdt_live():
    """업비트 테더(USDT/KRW) 실시간 가격 + 전일 대비 %. 실패하면 None."""
    try:
        t = _http_json("https://api.upbit.com/v1/ticker?markets=KRW-USDT")[0]
        return {"p": float(t["trade_price"]), "pct": float(t.get("signed_change_rate") or 0) * 100}
    except Exception:
        try:
            return {"p": float(fetch_usdt_krw()), "pct": None}
        except Exception:
            return None


def _yahoo(sym):
    for host in ("query1", "query2"):
        try:
            j = _http_json(f"https://{host}.finance.yahoo.com/v8/finance/chart/{sym}?range=1d&interval=1d")
            m = j["chart"]["result"][0]["meta"]
            p, prev = float(m["regularMarketPrice"]), float(m.get("chartPreviousClose") or m.get("previousClose") or 0)
            return {"p": p, "pct": (p / prev - 1) * 100 if prev else None}
        except Exception:
            continue
    return None


def _naver_index(code):
    try:
        j = _http_json(f"https://m.stock.naver.com/api/index/{code}/basic")
        num = lambda v: float(str(v).replace(",", ""))
        return {"p": num(j["closePrice"]), "pct": num(j["fluctuationsRatio"])}
    except Exception:
        return None


MACRO = [("kospi", "코스피", "KOSPI", "^KS11"), ("spx", "S&P500", None, "^GSPC"), ("soxl", "SOXL", None, "SOXL"),
         ("vix", "VIX", None, "^VIX"), ("gold", "금", None, "GC=F"), ("usdkrw", "달러/원", None, "KRW=X")]


@st.cache_data(ttl=60, show_spinner=False)
def fetch_macro():
    """시장 화면 맨 위 줄: 코스피 · S&P500 · SOXL · VIX · 금 · 달러/원 (1분마다 새로)."""
    from concurrent.futures import ThreadPoolExecutor

    def one(row):
        k, name, naver, yh = row
        q = (_naver_index(naver) if naver else None) or _yahoo(yh)
        return {"k": k, "name": name, **(q or {"p": None, "pct": None})}

    with ThreadPoolExecutor(max_workers=6) as ex:
        return list(ex.map(one, MACRO))


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_usdkrw():
    """달러-원 환율 (김프 계산용). 실패하면 None."""
    import json as _json
    import urllib.request
    try:
        with urllib.request.urlopen("https://open.er-api.com/v6/latest/USD", timeout=6) as r:
            return float(_json.loads(r.read().decode())["rates"]["KRW"])
    except Exception:
        return None


@st.cache_data(ttl=15, show_spinner=False)
def fetch_bybit_tickers():
    """Bybit USDT 무기한 시세 (차트 페이지 기준 거래소). 실패하면 {}."""
    try:
        raw = ccxt.bybit({"enableRateLimit": True}).fetch_tickers(params={"category": "linear"})
    except Exception:
        return {}
    out = {}
    for k, v in raw.items():
        if not k.endswith("/USDT:USDT"):
            continue
        info = v.get("info") or {}

        def f(x):
            try:
                return float(x)
            except (TypeError, ValueError):
                return None
        out[_plain_symbol(k)] = {
            "last": f(info.get("lastPrice")) or f(v.get("last")),
            "pct": (f(info.get("price24hPcnt")) * 100) if f(info.get("price24hPcnt")) is not None else f(v.get("percentage")),
            "high": f(info.get("highPrice24h")), "low": f(info.get("lowPrice24h")),
            "qv": f(info.get("turnover24h")), "funding": f(info.get("fundingRate")),
            "nft": f(info.get("nextFundingTime")),
        }
    return out


# -----------------------------------------------------------------------------
# 롱숏 비율 (브라우저에서 못 가져오는 Binance·OKX는 서버에서 조회)
# -----------------------------------------------------------------------------
def _get_json(url, timeout=4):
    import json as _json
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return _json.loads(r.read().decode())


def _ls_binance(sym):
    d = _get_json(f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={sym}&period=1h&limit=1")[-1]
    oi = float(_get_json(f"https://fapi.binance.com/futures/data/openInterestHist?symbol={sym}&period=5m&limit=1")[-1]["sumOpenInterestValue"])
    return {"long": float(d["longAccount"]), "short": float(d["shortAccount"]), "oi": oi}


def _ls_okx(sym):
    inst = sym.replace("USDT", "-USDT-SWAP")
    d = _get_json(f"https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio-contract?instId={inst}&period=1H&limit=1")["data"][0]
    r = float(d[1])
    oi = float(_get_json(f"https://www.okx.com/api/v5/public/open-interest?instId={inst}")["data"][0]["oiUsd"])
    return {"long": r / (1 + r), "short": 1 / (1 + r), "oi": oi}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ls_external(symbols):
    """{심볼: {"binance": {...} or None, "okx": {...} or None}} — 실패한 거래소는 None."""
    from concurrent.futures import ThreadPoolExecutor
    jobs = {(s, ex): fn for s in symbols for ex, fn in (("binance", _ls_binance), ("okx", _ls_okx))}
    out = {s: {"binance": None, "okx": None} for s in symbols}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(fn, s): (s, ex) for (s, ex), fn in jobs.items()}
        for f, (s, ex) in futs.items():
            try:
                out[s][ex] = f.result(timeout=8)
            except Exception:
                out[s][ex] = None
    return out


def pending_fee_for(pending, symbol, side, size):
    """현재 보유 수량만큼의 진입 수수료 (기록상 수량이 더 크면 비율로 줄임)."""
    try:
        v = (pending or {}).get(f"{symbol}|{side}")
        if not v:
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        qty, fee = float(v[0]), float(v[1])
        if qty <= 0:
            return 0.0
        return fee * min(1.0, float(size or 0) / qty)
    except Exception:
        return 0.0


@st.cache_data(ttl=30, show_spinner=False)
def fetch_equity(keys):
    """(선물 계정 자산(미실현 포함), 현물 USDT, 오류) — 계좌 기준 손익 계산용."""
    if is_demo(keys):
        return None, None, None
    try:
        ex = _exchange(keys)
        fut = float((ex.fetch_balance({"type": "swap"}).get("USDT") or {}).get("total") or 0)
        spot = float((ex.fetch_balance({"type": "spot"}).get("USDT") or {}).get("total") or 0)
        return fut, spot, None
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"


@st.cache_data(ttl=15, show_spinner=False)
def fetch_okx_tickers():
    """OKX USDT 무기한 시세 (차트 페이지 기준 거래소). 실패하면 {}."""
    try:
        raw = _get_json("https://www.okx.com/api/v5/market/tickers?instType=SWAP", timeout=6)["data"]
    except Exception:
        return {}
    out = {}
    for t in raw:
        iid = t.get("instId", "")
        if not iid.endswith("-USDT-SWAP"):
            continue
        try:
            last, open24 = float(t["last"]), float(t["open24h"])
            out[iid.replace("-USDT-SWAP", "/USDT")] = {
                "last": last, "pct": (last / open24 - 1) * 100 if open24 else None,
                "high": float(t["high24h"]), "low": float(t["low24h"]),
                "qv": float(t.get("volCcy24h") or 0) * last, "funding": None,
            }
        except (KeyError, ValueError, TypeError):
            continue
    return out


# -----------------------------------------------------------------------------
# 코인 페이지: 시가총액 순위 · 트렌딩 · 뉴스
# -----------------------------------------------------------------------------
@st.cache_data(ttl=180, show_spinner=False)
def fetch_cg_markets(n=200):
    """CoinGecko 시가총액 상위 코인 (7일 미니차트 포함). 실패하면 [] → 브라우저가 직접 다시 시도."""
    try:
        rows = _get_json("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc"
                         f"&per_page={n}&page=1&sparkline=true&price_change_percentage=1h,24h,7d", timeout=8)
    except Exception:
        return []
    out = []
    for c in rows:
        sp = ((c.get("sparkline_in_7d") or {}).get("price") or [])
        step = max(1, len(sp) // 42)
        out.append({
            "id": c.get("id"), "sym": (c.get("symbol") or "").upper(), "name": c.get("name"), "img": c.get("image"),
            "rank": c.get("market_cap_rank"), "price": c.get("current_price"), "mcap": c.get("market_cap"),
            "fdv": c.get("fully_diluted_valuation"), "vol": c.get("total_volume"),
            "h1": c.get("price_change_percentage_1h_in_currency"), "h24": c.get("price_change_percentage_24h_in_currency"),
            "d7": c.get("price_change_percentage_7d_in_currency"), "high24": c.get("high_24h"), "low24": c.get("low_24h"),
            "ath": c.get("ath"), "athc": c.get("ath_change_percentage"), "athd": (c.get("ath_date") or "")[:10],
            "circ": c.get("circulating_supply"), "total": c.get("total_supply"), "max": c.get("max_supply"),
            "spark": [round(v, 8) for v in sp[::step]][-42:],
        })
    return out


@st.cache_data(ttl=600, show_spinner=False)
def fetch_cg_trending():
    """CoinGecko 검색 트렌딩 코인 (지금 사람들이 많이 찾는 코인)."""
    try:
        j = _get_json("https://api.coingecko.com/api/v3/search/trending", timeout=6)
    except Exception:
        return []
    out = []
    for it in (j.get("coins") or [])[:10]:
        c = it.get("item") or {}
        d = c.get("data") or {}
        pc = (d.get("price_change_percentage_24h") or {}).get("usd")
        out.append({"id": c.get("id"), "sym": (c.get("symbol") or "").upper(), "name": c.get("name"),
                    "img": c.get("small") or c.get("thumb"), "rank": c.get("market_cap_rank"), "h24": pc})
    return out


NEWS_FEEDS = [("블록미디어", "https://www.blockmedia.co.kr/feed"), ("토큰포스트", "https://www.tokenpost.kr/rss")]


@st.cache_data(ttl=120, show_spinner=False)
def fetch_news(limit=30):
    """국내 코인 뉴스 RSS (최신순)."""
    import re as _re
    import urllib.request
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    items = []
    for src, url in NEWS_FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as r:
                root = ET.fromstring(r.read())
            for it in root.iter("item"):
                title = (it.findtext("title") or "").strip()
                link = (it.findtext("link") or "").strip()
                try:
                    ts = parsedate_to_datetime(it.findtext("pubDate") or "").timestamp()
                except Exception:
                    ts = 0
                desc = _re.sub(r"<[^>]+>", "", it.findtext("description") or "")
                desc = _re.sub(r"\s+", " ", desc).strip()[:140]
                if title and link.startswith("http"):
                    items.append({"src": src, "title": title, "link": link, "ts": ts, "desc": desc})
        except Exception:
            continue
    items.sort(key=lambda x: x["ts"], reverse=True)
    return items[:limit]
