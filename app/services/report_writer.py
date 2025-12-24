"""Markdown report writer for crypto morning brief."""

from datetime import datetime
from typing import Any

from app.config import settings
from app.utils.exchange_rate import get_usd_to_krw


class ReportWriter:
    """Generate markdown reports from market data and signals."""

    def generate_report(
        self,
        date: str,  # KST date string (YYYY-MM-DD)
        spot_snapshot: dict[str, Any],
        derivatives_snapshot: dict[str, Any],
        signals: list[dict[str, Any]],
        regime: dict[str, Any],
        news_snapshot: list[dict[str, Any]],
        korea_stocks: dict[str, Any] | None = None,
        us_stocks: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate markdown report.

        Args:
            date: Date string in KST format (YYYY-MM-DD).
            spot_snapshot: Spot market data.
            derivatives_snapshot: Derivatives market data.
            signals: List of signal dictionaries.
            regime: Regime dictionary with label and rationale.
            news_snapshot: List of news dictionaries.

        Returns:
            Markdown formatted string.
        """
        lines = []

        # 1. Title
        lines.append(f"# 암호화폐 모닝 브리프 — {date} (KST)")
        lines.append("")

        # 2. Market One-liner Summary
        lines.append("## 📊 시장 요약")
        lines.append("")
        summary = self._generate_market_summary(spot_snapshot)
        lines.append(summary)
        lines.append("")

        # 3. Regime
        lines.append("## 🎯 시장 국면")
        lines.append("")
        regime_section = self._generate_regime_section(regime)
        lines.append(regime_section)
        lines.append("")

        # 4. Signals Top 5
        lines.append("## ⚠️ 주요 시그널")
        lines.append("")
        signals_section = self._generate_signals_section(signals)
        lines.append(signals_section)
        lines.append("")

        # 5. Key Metrics Table
        lines.append("## 📈 주요 지표")
        lines.append("")
        metrics_section = self._generate_metrics_section(spot_snapshot, derivatives_snapshot)
        lines.append(metrics_section)
        lines.append("")

        # 6. News/Events Summary
        lines.append("## 📰 뉴스 & 이벤트")
        lines.append("")
        news_section = self._generate_news_section(news_snapshot)
        lines.append(news_section)
        lines.append("")

        # 7. Scenarios
        lines.append("## 🔮 시장 시나리오")
        lines.append("")
        scenarios_section = self._generate_scenarios_section(
            spot_snapshot, derivatives_snapshot, signals
        )
        lines.append(scenarios_section)
        lines.append("")

        # 9. Disclaimer
        lines.append("## ⚠️ 면책 조항")
        lines.append("")
        lines.append(
            "본 리포트는 리서치 목적으로만 제공되며 투자 조언을 구성하지 않습니다. "
            "제공된 정보는 시장 데이터 및 기술적 분석을 기반으로 하며, "
            "투자 결정의 유일한 근거로 사용되어서는 안 됩니다. "
            "항상 자체적인 리서치를 수행하고, 투자 결정을 내리기 전에 "
            "자격을 갖춘 재무 고문과 상담하시기 바랍니다."
        )
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*리포트 생성 시간: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*")

        return "\n".join(lines)

    def _generate_market_summary(self, spot_snapshot: dict[str, Any]) -> str:
        """Generate one-line market summary."""
        btc_data = spot_snapshot.get("BTC", {})
        eth_data = spot_snapshot.get("ETH", {})

        btc_price = btc_data.get("price", 0)
        btc_change = btc_data.get("change_24h", 0)
        eth_price = eth_data.get("price", 0)
        eth_change = eth_data.get("change_24h", 0)

        btc_emoji = "📈" if btc_change >= 0 else "📉"
        eth_emoji = "📈" if eth_change >= 0 else "📉"

        # Get current USD to KRW exchange rate
        usd_to_krw = get_usd_to_krw()

        # Convert to KRW
        btc_price_krw = btc_price * usd_to_krw
        eth_price_krw = eth_price * usd_to_krw

        summary = (
            f"**BTC** {btc_emoji} ₩{btc_price_krw:,.0f} ({btc_change:+.2f}%) | "
            f"**ETH** {eth_emoji} ₩{eth_price_krw:,.0f} ({eth_change:+.2f}%)"
        )

        # Add market sentiment
        if btc_change > 0 and eth_change > 0:
            summary += " — 시장이 상승 모멘텀을 보이고 있음"
        elif btc_change < 0 and eth_change < 0:
            summary += " — 시장이 매도 압력을 받고 있음"
        else:
            summary += " — 시장에 혼재된 신호"

        return summary

    def _generate_regime_section(self, regime: dict[str, Any]) -> str:
        """Generate regime section."""
        label = regime.get("label", "neutral")
        rationale = regime.get("rationale", [])

        # Regime emoji and description
        regime_map = {
            "risk_on": ("🟢", "리스크 온", "시장 참여자들이 위험 선호 성향을 보이고 있음"),
            "neutral": ("🟡", "중립", "시장이 균형 상태에 있음"),
            "risk_off": ("🔴", "리스크 오프", "시장 참여자들이 위험 회피 성향을 보이고 있음"),
        }

        emoji, name, desc = regime_map.get(label, ("🟡", "중립", "알 수 없음"))

        lines = [f"**{emoji} {name}** — {desc}", ""]

        if rationale:
            lines.append("**주요 요인:**")
            for item in rationale[:5]:  # Limit to 5 items
                lines.append(f"- {item}")
        else:
            lines.append("중요한 요인이 확인되지 않았습니다.")

        return "\n".join(lines)

    def _generate_signals_section(self, signals: list[dict[str, Any]]) -> str:
        """Generate signals section (Top 5, critical/warn prioritized)."""
        if not signals:
            return "현재 시점에서 중요한 시그널이 감지되지 않았습니다."

        # Sort signals: critical > warn > info
        level_priority = {"critical": 0, "warn": 1, "info": 2}
        sorted_signals = sorted(
            signals, key=lambda s: level_priority.get(s.get("level", "info"), 2)
        )[:5]  # Top 5

        lines = []
        for signal in sorted_signals:
            level = signal.get("level", "info")
            title = signal.get("title", "Unknown Signal")
            reason = signal.get("reason", "")

            # Level emoji
            level_emoji = {
                "critical": "🔴",
                "warn": "🟡",
                "info": "🔵",
            }.get(level, "⚪")

            lines.append(f"**{level_emoji} {title}**")
            lines.append(f"- {reason}")
            lines.append("")

        return "\n".join(lines)

    def _generate_metrics_section(
        self,
        spot_snapshot: dict[str, Any],
        derivatives_snapshot: dict[str, Any],
    ) -> str:
        """Generate key metrics table for BTC and ETH."""
        lines = []

        # BTC Metrics
        btc_spot = spot_snapshot.get("BTC", {})
        btc_deriv = derivatives_snapshot.get("BTC", {})

        if btc_spot:
            lines.append("### BTC")
            lines.append("")
            # Get current USD to KRW exchange rate
            usd_to_krw = get_usd_to_krw()

            # Convert USD to KRW
            btc_price_usd = btc_spot.get("price", 0)
            btc_price_krw = btc_price_usd * usd_to_krw
            btc_volume_krw = btc_spot.get("volume_24h", 0) * usd_to_krw
            btc_market_cap_krw = btc_spot.get("market_cap", 0) * usd_to_krw
            btc_high_krw = btc_spot.get("high_24h", 0) * usd_to_krw
            btc_low_krw = btc_spot.get("low_24h", 0) * usd_to_krw

            lines.append("| 지표 | 값 |")
            lines.append("|------|-----|")
            lines.append(f"| 가격 | ₩{btc_price_krw:,.0f} |")
            lines.append(f"| 24시간 변동 | {btc_spot.get('change_24h', 0):+.2f}% |")
            lines.append(f"| 24시간 거래량 | ₩{btc_volume_krw:,.0f} |")
            lines.append(f"| 시가총액 | ₩{btc_market_cap_krw:,.0f} |")
            lines.append(f"| 24시간 고가 | ₩{btc_high_krw:,.0f} |")
            lines.append(f"| 24시간 저가 | ₩{btc_low_krw:,.0f} |")

            if btc_deriv:
                lines.append(
                    f"| 펀딩 레이트 (8h) | {btc_deriv.get('funding_rate', 0) * 100:.4f}% |"
                )
                lines.append(
                    f"| 펀딩 레이트 (24h) | {btc_deriv.get('funding_rate_24h', 0) * 100:.4f}% |"
                )
                oi_krw = btc_deriv.get("open_interest_usd", 0) * usd_to_krw
                lines.append(f"| 미결제약정 | ₩{oi_krw:,.0f} |")
                lines.append(f"| 롱/숏 비율 | {btc_deriv.get('long_short_ratio', 0):.3f} |")
                long_liq_krw = btc_deriv.get("long_liquidation_24h", 0) * usd_to_krw
                short_liq_krw = btc_deriv.get("short_liquidation_24h", 0) * usd_to_krw
                lines.append(f"| 롱 청산 (24h) | ₩{long_liq_krw:,.0f} |")
                lines.append(f"| 숏 청산 (24h) | ₩{short_liq_krw:,.0f} |")

            lines.append("")

        # ETH Metrics
        eth_spot = spot_snapshot.get("ETH", {})
        eth_deriv = derivatives_snapshot.get("ETH", {})

        if eth_spot:
            lines.append("### ETH")
            lines.append("")
            # Get current USD to KRW exchange rate
            usd_to_krw = get_usd_to_krw()

            # Convert USD to KRW
            eth_price_usd = eth_spot.get("price", 0)
            eth_price_krw = eth_price_usd * usd_to_krw
            eth_volume_krw = eth_spot.get("volume_24h", 0) * usd_to_krw
            eth_market_cap_krw = eth_spot.get("market_cap", 0) * usd_to_krw
            eth_high_krw = eth_spot.get("high_24h", 0) * usd_to_krw
            eth_low_krw = eth_spot.get("low_24h", 0) * usd_to_krw

            lines.append("| 지표 | 값 |")
            lines.append("|------|-----|")
            lines.append(f"| 가격 | ₩{eth_price_krw:,.0f} |")
            lines.append(f"| 24시간 변동 | {eth_spot.get('change_24h', 0):+.2f}% |")
            lines.append(f"| 24시간 거래량 | ₩{eth_volume_krw:,.0f} |")
            lines.append(f"| 시가총액 | ₩{eth_market_cap_krw:,.0f} |")
            lines.append(f"| 24시간 고가 | ₩{eth_high_krw:,.0f} |")
            lines.append(f"| 24시간 저가 | ₩{eth_low_krw:,.0f} |")

            if eth_deriv:
                lines.append(
                    f"| 펀딩 레이트 (8h) | {eth_deriv.get('funding_rate', 0) * 100:.4f}% |"
                )
                lines.append(
                    f"| 펀딩 레이트 (24h) | {eth_deriv.get('funding_rate_24h', 0) * 100:.4f}% |"
                )
                oi_krw = eth_deriv.get("open_interest_usd", 0) * usd_to_krw
                lines.append(f"| 미결제약정 | ₩{oi_krw:,.0f} |")
                lines.append(f"| 롱/숏 비율 | {eth_deriv.get('long_short_ratio', 0):.3f} |")
                long_liq_krw = eth_deriv.get("long_liquidation_24h", 0) * usd_to_krw
                short_liq_krw = eth_deriv.get("short_liquidation_24h", 0) * usd_to_krw
                lines.append(f"| 롱 청산 (24h) | ₩{long_liq_krw:,.0f} |")
                lines.append(f"| 숏 청산 (24h) | ₩{short_liq_krw:,.0f} |")

        return "\n".join(lines)

    def _generate_news_section(self, news_snapshot: list[dict[str, Any]]) -> str:
        """Generate news section (max 5 items)."""
        if not news_snapshot:
            return "현재 시점에서 중요한 뉴스나 이벤트가 없습니다."

        lines = []
        for news in news_snapshot[:5]:  # Max 5 items
            title = news.get("title", "Untitled")
            source = news.get("source", "Unknown")
            published_at = news.get("published_at", "")
            sentiment = news.get("sentiment", "neutral")
            url = news.get("url", "")

            # Sentiment emoji
            sentiment_emoji = {
                "positive": "🟢",
                "neutral": "🟡",
                "negative": "🔴",
            }.get(sentiment, "⚪")

            # Format date
            date_str = ""
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    date_str = dt.strftime("%Y-%m-%d %H:%M UTC")
                except Exception:
                    date_str = published_at

            lines.append(f"**{sentiment_emoji} {title}**")
            lines.append(f"- 출처: {source}")
            if date_str:
                lines.append(f"- 발행일: {date_str}")
            if url:
                lines.append(f"- [자세히 보기]({url})")
            lines.append("")

        return "\n".join(lines)

    def _generate_stock_section(
        self,
        korea_stocks: dict[str, Any] | None,
        us_stocks: dict[str, Any] | None,
    ) -> str:
        """Generate stock market section."""
        lines = []

        if korea_stocks:
            lines.append("### 🇰🇷 한국 주식시장")
            lines.append("")
            lines.append("| 지수 | 현재가 | 24h 변화 | 거래량 |")
            lines.append("|------|--------|----------|--------|")

            for symbol, data in korea_stocks.items():
                price = data.get("price", 0)
                change_24h = data.get("change_24h", 0)
                volume = data.get("volume_24h", 0)

                change_str = f"{change_24h:+.2f}%"
                change_emoji = "🟢" if change_24h > 0 else "🔴" if change_24h < 0 else "⚪"
                volume_str = f"{volume:,.0f}" if volume > 0 else "-"

                lines.append(f"| {symbol} | {price:,.2f} | {change_emoji} {change_str} | {volume_str} |")

            lines.append("")
            lines.append("")

        if us_stocks:
            lines.append("### 🇺🇸 미국 주식시장")
            lines.append("")
            lines.append("| 지수 | 현재가 | 24h 변화 | 거래량 |")
            lines.append("|------|--------|----------|--------|")

            for symbol, data in us_stocks.items():
                price = data.get("price", 0)
                change_24h = data.get("change_24h", 0)
                volume = data.get("volume_24h", 0)

                change_str = f"{change_24h:+.2f}%"
                change_emoji = "🟢" if change_24h > 0 else "🔴" if change_24h < 0 else "⚪"
                volume_str = f"{volume:,.0f}" if volume > 0 else "-"

                lines.append(f"| {symbol} | {price:,.2f} | {change_emoji} {change_str} | {volume_str} |")

            lines.append("")

        if not korea_stocks and not us_stocks:
            return "주식시장 데이터를 사용할 수 없습니다."

        return "\n".join(lines)

    def _generate_scenarios_section(
        self,
        spot_snapshot: dict[str, Any],
        derivatives_snapshot: dict[str, Any],
        signals: list[dict[str, Any]],
    ) -> str:
        """Generate market scenarios (upside/sideways/downside) with trigger conditions only."""
        btc_spot = spot_snapshot.get("BTC", {})
        btc_deriv = derivatives_snapshot.get("BTC", {})
        eth_spot = spot_snapshot.get("ETH", {})

        btc_spot.get("price", 0)
        btc_change = btc_spot.get("change_24h", 0)
        eth_change = eth_spot.get("change_24h", 0)

        # Count signal levels
        critical_count = sum(1 for s in signals if s.get("level") == "critical")
        warn_count = sum(1 for s in signals if s.get("level") == "warn")

        lines = []

        # Upside Scenario
        lines.append("### 📈 상승 시나리오")
        triggers = []
        if btc_change > 0 and eth_change > 0:
            triggers.append("BTC와 ETH 모두 지속적인 상승 모멘텀")
        if btc_deriv.get("funding_rate", 0) < 0.001:
            triggers.append("펀딩 레이트가 낮게 유지 (롱 스퀴즈 리스크 없음)")
        if btc_deriv.get("long_short_ratio", 1.0) < 1.2:
            triggers.append("롱/숏 비율이 과도하게 확대되지 않음")
        if warn_count == 0 and critical_count == 0:
            triggers.append("중요한 경고 시그널 없음")
        if not triggers:
            triggers.append("거래량 확인과 함께 주요 저항선 돌파")

        for trigger in triggers[:3]:  # Max 3 triggers
            lines.append(f"- {trigger}")
        lines.append("")

        # Sideways Scenario
        lines.append("### ➡️ 횡보 시나리오")
        triggers = []
        if abs(btc_change) < 3 and abs(eth_change) < 3:
            triggers.append("낮은 변동성과 범위 내 가격 움직임")
        if btc_deriv.get("funding_rate", 0) > -0.001 and btc_deriv.get("funding_rate", 0) < 0.001:
            triggers.append("펀딩 레이트가 중립 수준 근처 (균형 상태)")
        if warn_count > 0 and critical_count == 0:
            triggers.append("일부 경고 시그널 있으나 중요한 문제 없음")
        if not triggers:
            triggers.append("지지선과 저항선 사이에서 가격 정체")

        for trigger in triggers[:3]:
            lines.append(f"- {trigger}")
        lines.append("")

        # Downside Scenario
        lines.append("### 📉 하락 시나리오")
        triggers = []
        if critical_count >= 1:
            triggers.append("중요 시그널 감지 (예: 극단적 펀딩 레이트, 청산 리스크)")
        if btc_change < -5 or eth_change < -5:
            triggers.append("급격한 가격 하락과 매도 압력 증가")
        if btc_deriv.get("funding_rate", 0) > 0.01:
            triggers.append("높은 펀딩 레이트는 롱 스퀴즈 리스크를 시사")
        if btc_deriv.get("long_short_ratio", 1.0) > 1.5:
            triggers.append("극단적인 롱/숏 비율은 과도한 레버리지 롱 포지션을 시사")
        if not triggers:
            triggers.append("거래량 확인과 함께 주요 지지선 이탈")

        for trigger in triggers[:3]:
            lines.append(f"- {trigger}")

        return "\n".join(lines)
