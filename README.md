# Mung-s-trading
트레이딩을 기록합니다

- `app.py` — 진입점 (상단 메뉴: 매매 히스토리 / 차트)
- `views/history.py` — 보유 포지션, 손익 카드, 손익 구성, 성과 지표, 매매 내역
- `views/chart.py` — TradingView 3분할 차트
- `lib/data.py` — Bitget 데이터 조회와 손익 계산 (수수료·펀딩비·페이백)
- `lib/ui.py` — 색상, CSS, 공통 컴포넌트

API 키는 Streamlit Secrets에 `API_KEY`, `SECRET_KEY`, `PASSPHRASE`로 넣습니다. 키가 없으면 데모 데이터로 표시됩니다.
