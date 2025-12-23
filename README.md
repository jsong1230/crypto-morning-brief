# Crypto Morning Brief

암호화폐 모닝 브리프 리포트를 생성하는 Python 기반 FastAPI 애플리케이션입니다.

## 기능

- **FastAPI 기반 REST API**: 건강 상태 확인 및 일일 리포트 생성
- **Markdown 리포트**: 구조화된 암호화폐 시장 리포트를 Markdown 형식으로 생성
- **실제 시장 데이터 통합**: CoinGecko (Spot), Binance Futures (파생상품), RSS 피드 (뉴스)
- **실제 데이터 기반 분석**: 시장 국면, 시그널, 시나리오 모두 실제 데이터로 생성
- **확장 가능한 Provider 구조**: 외부 API 연동을 위한 인터페이스 기반 설계
- **자동 Fallback**: API 실패 시 Mock 데이터로 자동 전환

## 요구사항

- Python 3.11 이상
- pip 또는 uv

## 설치

### 1. 가상 환경 생성 (권장)

```bash
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치

**프로덕션:**
```bash
pip install -r requirements.txt
```

**개발 환경:**
```bash
pip install -r requirements-dev.txt
```

또는 Makefile 사용:
```bash
make install-dev
```

### 3. 환경 변수 설정

`env.example`을 참고하여 `.env` 파일을 생성하세요:

```bash
cp env.example .env
```

## 환경 변수

**주요 환경 변수:**

| 변수 | 설명 | 기본값 | 필수 |
|------|------|--------|------|
| `PROVIDER` | 데이터 제공자 (`mock`, `public`, `real`) | `mock` | 아니오 |
| `SEND_TELEGRAM` | 텔레그램 전송 활성화 | `false` | 아니오 |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 | - | 텔레그램 사용 시 |
| `TELEGRAM_CHAT_ID` | 텔레그램 채팅 ID | - | 텔레그램 사용 시 |
| `LOG_LEVEL` | 로그 레벨 (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` | 아니오 |
| `HOST` | 서버 호스트 | `0.0.0.0` | 아니오 |
| `PORT` | 서버 포트 | `8000` | 아니오 |

**예시 `.env` 파일:**
```bash
# Provider 설정
PROVIDER=public  # 또는 mock

# 텔레그램 (선택사항)
SEND_TELEGRAM=false
# TELEGRAM_BOT_TOKEN=your_token_here
# TELEGRAM_CHAT_ID=your_chat_id_here

# 로깅
LOG_LEVEL=INFO
```

## 실행

### 개발 서버 실행

```bash
# Makefile 사용
make run

# 또는 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 Python 모듈로 실행
python -m app.main
```

서버가 실행되면 다음 URL에서 접근할 수 있습니다:
- API: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 대체 문서: http://localhost:8000/redoc

## API 엔드포인트

### GET `/api/v1/health`

서비스 건강 상태 확인

**응답:**
```json
{
  "status": "healthy",
  "service": "crypto-morning-brief"
}
```

### POST `/api/v1/report/daily`

일일 암호화폐 리포트 생성 (시그널 및 레짐 분석 포함)

**요청 본문:**
```json
{
  "symbols": ["BTC", "ETH"],
  "keywords": ["bitcoin", "ethereum"],
  "tz": "Asia/Seoul"
}
```

**파라미터:**
- `symbols` (선택): 암호화폐 심볼 목록 (기본값: `["BTC", "ETH"]`)
- `keywords` (선택): 뉴스 검색 키워드 목록 (기본값: `["bitcoin", "ethereum"]`)
- `tz` (선택): 타임존 (기본값: `"Asia/Seoul"`)

**응답:**
```json
{
  "date": "2024-01-15",
  "markdown": "# Crypto Morning Brief — 2024-01-15 (KST)\n...",
  "signals": [
    {
      "id": "BTC_funding_overheated",
      "level": "warn",
      "title": "BTC Funding Rate Overheated",
      "reason": "24h funding rate exceeds threshold",
      "metric": "funding_rate_24h",
      "threshold": 0.01,
      "value": 0.015
    }
  ],
  "regime": {
    "label": "neutral",
    "rationale": [
      "BTC: Funding rate elevated",
      "ETH: Low volatility"
    ]
  }
}
```

**cURL 예시:**
```bash
# 기본 파라미터로 리포트 생성
curl -X POST "http://localhost:8000/api/v1/report/daily" \
  -H "Content-Type: application/json" \
  -d '{}'

# 커스텀 파라미터로 리포트 생성
curl -X POST "http://localhost:8000/api/v1/report/daily" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["BTC", "ETH"],
    "keywords": ["bitcoin", "ethereum"],
    "tz": "Asia/Seoul"
  }'

# UTC 타임존으로 리포트 생성
curl -X POST "http://localhost:8000/api/v1/report/daily" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["BTC"],
    "keywords": ["bitcoin"],
    "tz": "UTC"
  }'
```

**에러 응답:**
- `400`: 잘못된 요청 형식
- `502`: Provider 데이터 수집 실패
- `500`: 리포트 생성 실패

**텔레그램 알림:**
리포트 생성 시 텔레그램으로 자동 전송할 수 있습니다 (옵션).

1. `.env` 파일에 설정 추가:
```bash
SEND_TELEGRAM=true
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

2. 텔레그램 봇 생성:
   - [@BotFather](https://t.me/botfather)에게 `/newbot` 명령어로 봇 생성
   - 받은 토큰을 `TELEGRAM_BOT_TOKEN`에 설정

3. 채팅 ID 확인:
   - [@userinfobot](https://t.me/userinfobot)에게 메시지 전송하여 ID 확인
   - 또는 그룹 채팅의 경우 봇을 추가한 후 메시지 전송하여 확인

**참고:**
- 텔레그램 전송 실패 시에도 리포트 생성은 성공합니다 (경고 로그만 기록)
- 긴 리포트는 자동으로 요약되거나 분할 전송됩니다 (4096자 제한)

### GET `/api/v1/market/spot`

스팟 시장 스냅샷 조회

**쿼리 파라미터:**
- `symbols`: 쉼표로 구분된 심볼 목록 (예: "BTC,ETH")

**응답:**
```json
{
  "data": {
    "BTC": {
      "price": 45000.0,
      "change_24h": 2.5,
      "volume_24h": 18000000000.0,
      "market_cap": 900000000000.0,
      "high_24h": 46000.0,
      "low_24h": 44000.0,
      "timestamp": "2024-01-15T12:00:00"
    }
  },
  "symbols": ["BTC", "ETH"]
}
```

### GET `/api/v1/market/derivatives`

파생상품 시장 스냅샷 조회

**쿼리 파라미터:**
- `symbols`: 쉼표로 구분된 심볼 목록 (예: "BTC,ETH")

**응답:**
```json
{
  "data": {
    "BTC": {
      "funding_rate": 0.0001,
      "funding_rate_24h": 0.0003,
      "open_interest": 120000000000.0,
      "open_interest_usd": 120000000000.0,
      "long_short_ratio": 1.15,
      "long_liquidation_24h": 50000000.0,
      "short_liquidation_24h": 45000000.0,
      "timestamp": "2024-01-15T12:00:00"
    }
  },
  "symbols": ["BTC", "ETH"]
}
```

### GET `/api/v1/market/news`

뉴스 스냅샷 조회

**쿼리 파라미터:**
- `keywords`: 쉼표로 구분된 키워드 목록 (예: "Bitcoin,Ethereum")

**응답:**
```json
{
  "data": [
    {
      "title": "Bitcoin Price Surges Amid Institutional Adoption",
      "source": "CryptoNews",
      "published_at": "2024-01-15T10:00:00",
      "url": "https://example.com/news/bitcoin-1234",
      "sentiment": "positive",
      "keywords": ["Bitcoin"],
      "summary": "Latest developments regarding Bitcoin..."
    }
  ],
  "keywords": ["Bitcoin", "Ethereum"],
  "count": 5
}
```

### GET `/api/v1/signals/analyze`

시그널 분석 (룰 기반 엔진)

**쿼리 파라미터:**
- `symbols`: 쉼표로 구분된 심볼 목록 (예: "BTC,ETH", 기본값: "BTC,ETH")

**응답:**
```json
{
  "symbols": ["BTC", "ETH"],
  "signals": [
    {
      "id": "BTC_funding_overheated",
      "level": "warn",
      "title": "BTC Funding Rate Overheated (long bias)",
      "reason": "24h funding rate 1.500% exceeds threshold",
      "metric": "funding_rate_24h",
      "threshold": 0.01,
      "value": 0.015
    }
  ],
  "regime": {
    "label": "risk_off",
    "rationale": [
      "BTC: Funding rate elevated",
      "BTC: High volatility"
    ]
  },
  "timestamp": "2024-01-15T12:00:00",
  "signals_count": 5
}
```

**시그널 레벨:**
- `info`: 정보성 시그널
- `warn`: 경고 시그널
- `critical`: 심각한 시그널

**레짐 (Regime):**
- `risk_on`: 위험 선호 시장
- `neutral`: 중립 시장
- `risk_off`: 위험 회피 시장

### GET `/api/v1/report/morning-brief`

모닝 브리프 리포트 생성 (Markdown)

**쿼리 파라미터:**
- `date`: KST 날짜 (YYYY-MM-DD 형식, 기본값: 오늘)
- `symbols`: 쉼표로 구분된 심볼 목록 (예: "BTC,ETH", 기본값: "BTC,ETH")
- `keywords`: 쉼표로 구분된 키워드 목록 (예: "Bitcoin,Ethereum", 기본값: "Bitcoin,Ethereum")

**응답:**
```json
{
  "date": "2024-01-15",
  "markdown": "# Crypto Morning Brief — 2024-01-15 (KST)\n...",
  "metadata": {
    "symbols": ["BTC", "ETH"],
    "keywords": ["Bitcoin", "Ethereum"],
    "signals_count": 5,
    "regime": "neutral",
    "generated_at": "2024-01-15T12:00:00"
  }
}
```

**리포트 구성:**
1. 제목: "암호화폐 모닝 브리프 — YYYY-MM-DD (KST)"
2. 시장 한줄 요약 (BTC/ETH 변화 포함) - **실제 데이터**
3. Market Regime (risk_on/neutral/risk_off) + 근거 - **실제 데이터 기반 분석**
4. Key Signals Top 5 (critical/warn 우선) - **실제 데이터 기반 시그널**
5. Key Metrics 테이블 (BTC/ETH 각각) - **실제 Spot 및 파생상품 데이터**
6. News & Events 요약 (최대 5개) - **실제 뉴스 (RSS 피드)**
7. Market Scenarios 3개 (상방/횡보/하방) - **실제 데이터 기반 트리거 조건**
8. Disclaimer (리서치용, 투자 조언 아님)

> **참고**: `PROVIDER=public` 설정 시 모든 섹션이 실제 데이터를 사용합니다.

## 프로젝트 구조

```
crypto-morning-brief/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 애플리케이션 진입점
│   ├── config.py            # 설정 관리 (pydantic-settings)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API 라우트 정의
│   ├── services/
│   │   ├── __init__.py
│   │   ├── report_service.py  # 리포트 생성 비즈니스 로직
│   │   ├── signal_engine.py   # 룰 기반 시그널 엔진
│   │   └── report_writer.py    # 마크다운 리포트 작성기
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py          # Provider 인터페이스
│   │   ├── factory.py       # Provider 팩토리
│   │   ├── dummy.py         # 더미 데이터 Provider
│   │   └── mock_provider.py # Mock MarketProvider
│   ├── models/
│   │   ├── __init__.py
│   │   └── report.py        # Pydantic 모델
│   └── utils/
│       ├── __init__.py
│       └── logger.py         # 로깅 설정
├── tests/
│   ├── __init__.py
│   ├── test_api.py          # API 테스트
│   ├── test_services.py     # 서비스 테스트
│   ├── test_market_provider.py  # MarketProvider 테스트
│   ├── test_signal_engine.py    # SignalEngine 테스트
│   ├── test_signal_api.py       # Signal API 테스트
│   ├── test_report_writer.py   # ReportWriter 테스트
│   └── test_report_api.py       # Report API 테스트
├── .env.example              # 환경 변수 예제
├── .gitignore
├── Makefile                  # 개발 편의 명령어
├── pyproject.toml           # 프로젝트 설정
├── requirements.txt         # 프로덕션 의존성
├── requirements-dev.txt     # 개발 의존성
└── README.md
```

## 개발

### 테스트 실행

```bash
# Makefile 사용
make test

# 또는 직접 실행
pytest -v

# 커버리지 포함
pytest --cov=app --cov-report=html
```

### 코드 포맷팅 및 린팅

```bash
# 포맷팅
make format

# 또는 개별 실행
black app tests
ruff check --fix app tests

# 린팅만
make lint
```

### Provider 교체

프로젝트는 두 가지 Provider 인터페이스를 제공합니다:

1. **CryptoDataProvider**: 기존 리포트 생성용 (하위 호환성 유지)
2. **MarketProvider**: 새로운 시장 데이터 제공용 (스팟, 파생상품, 뉴스)

#### MarketProvider 사용

`MarketProvider`는 FastAPI 의존성 주입을 통해 자동으로 선택됩니다:

1. `.env` 파일에서 `PROVIDER` 설정:
   ```bash
   PROVIDER=mock    # Mock 데이터 (기본값)
   PROVIDER=public  # CoinGecko 공개 API (실제 가격 데이터)
   PROVIDER=real    # 실제 Provider (향후 구현)
   ```

2. 새로운 Provider 구현:
   - `app/providers/base.py`의 `MarketProvider` 인터페이스를 구현
   - `app/providers/factory.py`의 `get_market_provider()` 함수에 추가

#### PublicProvider (CoinGecko API + Binance Futures API + RSS Feeds)

`PROVIDER=public`으로 설정하면 CoinGecko 공개 API, Binance Futures API, RSS 피드를 사용하여 **모든 실제 시장 데이터**를 가져옵니다.

**특징:**
- ✅ API 키 불필요 (무료 공개 API)
- ✅ BTC/ETH 등 주요 암호화폐 실제 가격 제공 (CoinGecko API)
- ✅ 24h 변화율, 거래량, 시가총액 등 실제 데이터
- ✅ **실제 파생상품 데이터** (Binance Futures API)
  - 펀딩 레이트 (8h, 24h 평균)
  - 미결제약정 (Open Interest)
  - 롱/숏 비율
  - 청산 데이터 (24h)
- ✅ 실제 암호화폐 뉴스 (CoinTelegraph, Decrypt, CoinDesk RSS 피드)
- ⚠️ API 실패 시 자동으로 Mock으로 fallback

**데이터 소스:**
- **Spot 가격**: CoinGecko API
- **파생상품**: Binance Futures API
- **뉴스**: CoinTelegraph RSS, Decrypt RSS, CoinDesk RSS

뉴스는 키워드 필터링을 통해 관련 기사만 수집하며, 최대 10개의 최신 뉴스를 반환합니다.

**시장 시나리오 및 시장 국면:**
- 모든 시나리오 분석은 실제 데이터 기반으로 생성됩니다
- Spot 가격, 파생상품 데이터, 시그널 모두 실제 데이터를 사용합니다

**사용 예시:**
```bash
# .env 파일
PROVIDER=public

# 또는 환경 변수로
export PROVIDER=public
python scripts/run_daily_report.py
```

예시:
```python
from app.providers.base import MarketProvider

class YourMarketProvider(MarketProvider):
    async def get_spot_snapshot(self, symbols: list[str]) -> dict[str, Any]:
        # 구현
        pass
    
    async def get_derivatives_snapshot(self, symbols: list[str]) -> dict[str, Any]:
        # 구현
        pass
    
    async def get_news_snapshot(self, keywords: list[str]) -> list[dict[str, Any]]:
        # 구현
        pass
    
    def is_available(self) -> bool:
        return True
```

그리고 `app/providers/factory.py`에서:
```python
def get_market_provider() -> MarketProvider:
    provider_type = settings.provider.lower()
    if provider_type == "your_provider":
        return YourMarketProvider()
    # ...
```

## Makefile 명령어

- `make install` - 프로덕션 의존성 설치
- `make install-dev` - 개발 의존성 설치
- `make run` - 개발 서버 실행
- `make test` - 테스트 실행
- `make test-cov` - 커버리지 포함 테스트
- `make lint` - 코드 린팅
- `make format` - 코드 포맷팅
- `make clean` - 캐시 및 빌드 파일 정리

## 시그널 엔진

프로젝트는 리서치 브리핑용 룰 기반 시그널 엔진을 포함합니다. 시그널 엔진은 스팟 및 파생상품 시장 데이터를 분석하여 위험 신호와 시장 국면을 판단합니다.

### 구현된 룰 (11개)

1. **Funding Rate Overheated**: Funding rate가 임계치 초과 시 과열 신호
2. **Open Interest Surge**: OI 24h 증가율이 임계치 초과 시 급증 신호
3. **Volatility Spike**: 24h 변동폭이 임계치 초과 시 변동성 급등
4. **Volume Surge**: 거래량 z-score 기반 급증 감지
5. **Long/Short Ratio Extreme**: 롱/숏 비율 편향 감지
6. **Price Surge + OI Surge**: 가격 급등과 OI 급증 조합 (청산 리스크 경보)
7. **Price Drop + Volume Surge**: 가격 급락과 거래량 급증 (패닉 가능성)
8. **Extreme Funding Rate**: 극단적인 funding rate 감지
9. **Liquidation Risk**: 청산 비율이 높을 때 위험 신호
10. **Momentum Divergence**: 가격 모멘텀과 파생상품 지표의 괴리 감지
11. **BTC Dominance Change**: BTC 도미넌스 급변 감지

### 사용 예시

```python
from app.services.signal_engine import SignalEngine
from app.providers.mock_provider import MockMarketProvider

# 데이터 수집
provider = MockMarketProvider()
spot = await provider.get_spot_snapshot(["BTC", "ETH"])
deriv = await provider.get_derivatives_snapshot(["BTC", "ETH"])

# 시그널 분석
engine = SignalEngine()
result = engine.analyze(spot, deriv)

# 결과 확인
for signal in result["signals"]:
    print(f"{signal['level']}: {signal['title']}")
    print(f"  {signal['reason']}")

print(f"Market Regime: {result['regime']['label']}")
```

### API 사용

```bash
# 시그널 분석
curl "http://localhost:8000/api/v1/signals/analyze?symbols=BTC,ETH"

# 모닝 브리프 리포트 생성
curl "http://localhost:8000/api/v1/report/morning-brief?date=2024-01-15"
```

## 스케줄러 실행

일일 리포트를 자동으로 생성하는 방법은 두 가지가 있습니다.

### 1. 로컬 실행 (Cron)

로컬에서 cron을 사용하여 매일 리포트를 생성할 수 있습니다.

#### 스크립트 실행

```bash
# 기본 설정으로 실행 (출력은 stdout)
python scripts/run_daily_report.py

# 파일로 저장
python scripts/run_daily_report.py --output reports/daily_report_$(date +%Y%m%d).md

# 커스텀 심볼 및 키워드
python scripts/run_daily_report.py --symbols BTC ETH SOL --keywords bitcoin ethereum solana

# 다른 타임존 사용
python scripts/run_daily_report.py --tz UTC
```

#### Crontab 설정

매일 KST 08:30에 실행하려면:

```bash
# crontab 편집
crontab -e

# 다음 줄 추가
# KST 08:30 = UTC 23:30 (previous day)
# 예: KST 2024-01-15 08:30 = UTC 2024-01-14 23:30
30 23 * * * cd /path/to/crypto-morning-brief && /usr/bin/python3 scripts/run_daily_report.py --output reports/daily_report_$(date +\%Y\%m\%d).md >> logs/cron.log 2>&1
```

**시간 변환 참고:**
- KST (한국 표준시) = UTC + 9시간
- KST 08:30 = UTC 23:30 (전날)
- Cron 표현식: `30 23 * * *` (매일 UTC 23:30 = KST 다음날 08:30)

**참고:**
- `%` 문자는 crontab에서 이스케이프 필요 (`\%`)
- Python 경로는 `which python3`로 확인
- 프로젝트 경로를 절대 경로로 지정
- `.env` 파일이 프로젝트 루트에 있어야 함

#### 로그 확인

```bash
# cron 로그 확인
tail -f logs/cron.log

# 또는 시스템 로그 확인 (macOS/Linux)
grep CRON /var/log/syslog  # Linux
grep cron /var/log/system.log  # macOS
```

### 2. GitHub Actions

GitHub Actions를 사용하여 자동으로 리포트를 생성하고 텔레그램으로 전송할 수 있습니다.

#### 설정 방법

1. **Secrets 설정 (필수):**
   - GitHub 저장소 → Settings → Secrets and variables → Actions
   - "New repository secret" 버튼 클릭
   - 다음 Secrets를 각각 추가:
     - **Name**: `TELEGRAM_BOT_TOKEN`
       - **Value**: `8328907437:AAE4VD-l_F6HRtdipMrskFNrEmSHcNuI-AY`
     - **Name**: `TELEGRAM_CHAT_ID`
       - **Value**: `57364261`
   - 각 Secret을 추가한 후 "Add secret" 버튼 클릭
   - 두 개의 Secret이 모두 추가되었는지 확인

2. **Workflow 확인:**
   - `.github/workflows/daily.yml` 파일이 이미 포함되어 있습니다
   - 매일 UTC 23:30 (KST 08:30 다음날)에 자동 실행됩니다
   - `SEND_TELEGRAM=true`로 자동 설정되어 리포트가 텔레그램으로 전송됩니다

3. **수동 실행:**
   - GitHub 저장소 → Actions → "Daily Morning Brief" → "Run workflow"

#### 실행 시간

- **스케줄:** 매일 UTC 23:30 (KST 다음날 08:30)
- **Cron 표현식:** `30 23 * * *`
- **시간 변환:** KST 08:30 = UTC 23:30 (전날)
  - 예: UTC 2024-01-14 23:30 실행 → KST 2024-01-15 08:30 리포트 생성
- **수동 실행:** 언제든지 가능 (workflow_dispatch)

#### Workflow 동작

1. 코드 체크아웃
2. Python 3.11 환경 설정
3. 의존성 설치 (`requirements.txt`)
4. 리포트 생성 및 텔레그램 전송 (`scripts/run_daily_report.py`)
5. 리포트 파일이 생성된 경우 Artifact로 업로드 (7일간 보관)

#### 결과 확인

- **Actions 탭:** 실행 로그 확인
- **텔레그램:** 리포트가 자동으로 전송됨
- **Artifacts:** 리포트 파일 다운로드 가능 (7일간 보관)

## 예시 결과

### 리포트 생성 예시

```bash
# 스크립트로 리포트 생성
$ python scripts/run_daily_report.py

================================================================================
DAILY REPORT
================================================================================

# Crypto Morning Brief — 2024-01-15 (KST)

## 📊 Market Summary

**BTC** 📈 $45,320 (+2.38%) | **ETH** 📈 $2,480 (+4.50%) — Market showing bullish momentum

## 🎯 Market Regime

**🟡 Neutral** — Market is in a balanced state

**Key Factors:**
- BTC: Funding rate elevated
- ETH: Low volatility

## ⚠️ Key Signals

**🟡 BTC Funding Rate Overheated (long bias)**
- 24h funding rate 1.500% exceeds threshold

**🔵 BTC Volatility Spike (up)**
- 24h price change 12.00% exceeds threshold

## 📈 Key Metrics

### BTC

| Metric | Value |
|--------|-------|
| Price | $45,320.15 |
| 24h Change | +2.38% |
| 24h Volume | $18,453,881,737 |
| Market Cap | $921,380,176,458 |
| Funding Rate (8h) | 0.0203% |
| Open Interest | $185,910,013,016 |
| Long/Short Ratio | 1.193 |

### ETH

| Metric | Value |
|--------|-------|
| Price | $2,479.96 |
| 24h Change | +4.50% |
| 24h Volume | $12,777,444,784 |
| Market Cap | $292,247,071,148 |
| Funding Rate (8h) | 0.0416% |
| Open Interest | $36,218,617,811 |
| Long/Short Ratio | 1.104 |

## 📰 News & Events

**실제 뉴스 데이터:**
- `PROVIDER=public` 설정 시 CoinTelegraph, Decrypt, CoinDesk의 RSS 피드에서 실제 뉴스를 가져옵니다
- 키워드 기반 필터링으로 관련 뉴스만 수집
- 감정 분석 (positive/neutral/negative) 포함

**🟢 Bitcoin Price Surges Amid Institutional Adoption**
- Source: CryptoNews
- Published: 2024-01-15 10:00 UTC

**🟡 Ethereum Network Upgrade Scheduled**
- Source: TechCrypto
- Published: 2024-01-15 08:00 UTC

## 🔮 Market Scenarios

### 📈 Upside Scenario
- Funding rate remains low (no long squeeze risk)
- Long/short ratio not overly extended
- No critical warning signals present

### ➡️ Sideways Scenario
- Low volatility and range-bound price action
- Funding rate near neutral (equilibrium)

### 📉 Downside Scenario
- Break below key support levels with volume confirmation

## ⚠️ Disclaimer

This report is for research purposes only and does not constitute investment advice...
```

### API 응답 예시

```bash
# Health check
$ curl http://localhost:8000/api/v1/health
{
  "status": "healthy",
  "service": "crypto-morning-brief"
}

# 리포트 생성
$ curl -X POST http://localhost:8000/api/v1/report/daily \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTC", "ETH"]}'

{
  "date": "2024-01-15",
  "markdown": "# Crypto Morning Brief — 2024-01-15 (KST)\n...",
  "signals": [
    {
      "id": "BTC_funding_overheated",
      "level": "warn",
      "title": "BTC Funding Rate Overheated",
      "reason": "24h funding rate exceeds threshold",
      "metric": "funding_rate_24h",
      "threshold": 0.01,
      "value": 0.015
    }
  ],
  "regime": {
    "label": "neutral",
    "rationale": ["BTC: Funding rate elevated"]
  }
}
```

## 코드 품질

### 포맷팅 및 린팅

프로젝트는 `ruff`를 사용하여 코드 포맷팅과 린팅을 관리합니다.

```bash
# 코드 포맷팅
ruff format app/ tests/

# 린팅 검사
ruff check app/ tests/

# 자동 수정 가능한 문제 수정
ruff check app/ tests/ --fix
```

### 타입 힌트

모든 함수와 메서드에 타입 힌트가 포함되어 있습니다:

```python
def analyze(
    self,
    spot_snapshot: dict[str, Any],
    derivatives_snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Analyze market data and generate signals."""
    ...
```

### 예외 처리

일관된 예외 처리 패턴을 사용합니다:
- Provider 실패: `502 Bad Gateway`
- 비즈니스 로직 오류: `500 Internal Server Error`
- 잘못된 요청: `400 Bad Request`
- 텔레그램 전송 실패: 경고 로그만 기록 (요청은 성공)

## 라이선스

이 프로젝트는 개인 학습 및 개발 목적으로 사용됩니다.

