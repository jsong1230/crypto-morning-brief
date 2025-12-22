"""Markdown report writer for crypto morning brief."""

from datetime import datetime
from typing import Any


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
        lines.append(f"# Crypto Morning Brief — {date} (KST)")
        lines.append("")

        # 2. Market One-liner Summary
        lines.append("## 📊 Market Summary")
        lines.append("")
        summary = self._generate_market_summary(spot_snapshot)
        lines.append(summary)
        lines.append("")

        # 3. Regime
        lines.append("## 🎯 Market Regime")
        lines.append("")
        regime_section = self._generate_regime_section(regime)
        lines.append(regime_section)
        lines.append("")

        # 4. Signals Top 5
        lines.append("## ⚠️ Key Signals")
        lines.append("")
        signals_section = self._generate_signals_section(signals)
        lines.append(signals_section)
        lines.append("")

        # 5. Key Metrics Table
        lines.append("## 📈 Key Metrics")
        lines.append("")
        metrics_section = self._generate_metrics_section(spot_snapshot, derivatives_snapshot)
        lines.append(metrics_section)
        lines.append("")

        # 6. News/Events Summary
        lines.append("## 📰 News & Events")
        lines.append("")
        news_section = self._generate_news_section(news_snapshot)
        lines.append(news_section)
        lines.append("")

        # 7. Scenarios
        lines.append("## 🔮 Market Scenarios")
        lines.append("")
        scenarios_section = self._generate_scenarios_section(
            spot_snapshot, derivatives_snapshot, signals
        )
        lines.append(scenarios_section)
        lines.append("")

        # 8. Disclaimer
        lines.append("## ⚠️ Disclaimer")
        lines.append("")
        lines.append(
            "This report is for research purposes only and does not constitute "
            "investment advice. The information provided is based on market data "
            "and technical analysis, and should not be used as the sole basis "
            "for investment decisions. Always conduct your own research and "
            "consult with a qualified financial advisor before making any "
            "investment decisions."
        )
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*Report generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*")

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

        summary = (
            f"**BTC** {btc_emoji} ${btc_price:,.0f} ({btc_change:+.2f}%) | "
            f"**ETH** {eth_emoji} ${eth_price:,.0f} ({eth_change:+.2f}%)"
        )

        # Add market sentiment
        if btc_change > 0 and eth_change > 0:
            summary += " — Market showing bullish momentum"
        elif btc_change < 0 and eth_change < 0:
            summary += " — Market under selling pressure"
        else:
            summary += " — Mixed signals in the market"

        return summary

    def _generate_regime_section(self, regime: dict[str, Any]) -> str:
        """Generate regime section."""
        label = regime.get("label", "neutral")
        rationale = regime.get("rationale", [])

        # Regime emoji and description
        regime_map = {
            "risk_on": ("🟢", "Risk-On", "Market participants are showing risk appetite"),
            "neutral": ("🟡", "Neutral", "Market is in a balanced state"),
            "risk_off": ("🔴", "Risk-Off", "Market participants are risk-averse"),
        }

        emoji, name, desc = regime_map.get(label, ("🟡", "Neutral", "Unknown"))

        lines = [f"**{emoji} {name}** — {desc}", ""]

        if rationale:
            lines.append("**Key Factors:**")
            for item in rationale[:5]:  # Limit to 5 items
                lines.append(f"- {item}")
        else:
            lines.append("No significant factors identified.")

        return "\n".join(lines)

    def _generate_signals_section(self, signals: list[dict[str, Any]]) -> str:
        """Generate signals section (Top 5, critical/warn prioritized)."""
        if not signals:
            return "No significant signals detected at this time."

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
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Price | ${btc_spot.get('price', 0):,.2f} |")
            lines.append(f"| 24h Change | {btc_spot.get('change_24h', 0):+.2f}% |")
            lines.append(f"| 24h Volume | ${btc_spot.get('volume_24h', 0):,.0f} |")
            lines.append(f"| Market Cap | ${btc_spot.get('market_cap', 0):,.0f} |")
            lines.append(f"| 24h High | ${btc_spot.get('high_24h', 0):,.2f} |")
            lines.append(f"| 24h Low | ${btc_spot.get('low_24h', 0):,.2f} |")

            if btc_deriv:
                lines.append(
                    f"| Funding Rate (8h) | {btc_deriv.get('funding_rate', 0) * 100:.4f}% |"
                )
                lines.append(
                    f"| Funding Rate (24h) | {btc_deriv.get('funding_rate_24h', 0) * 100:.4f}% |"
                )
                lines.append(f"| Open Interest | ${btc_deriv.get('open_interest_usd', 0):,.0f} |")
                lines.append(f"| Long/Short Ratio | {btc_deriv.get('long_short_ratio', 0):.3f} |")
                lines.append(
                    f"| Long Liquidation (24h) | ${btc_deriv.get('long_liquidation_24h', 0):,.0f} |"
                )
                lines.append(
                    f"| Short Liquidation (24h) | ${btc_deriv.get('short_liquidation_24h', 0):,.0f} |"
                )

            lines.append("")

        # ETH Metrics
        eth_spot = spot_snapshot.get("ETH", {})
        eth_deriv = derivatives_snapshot.get("ETH", {})

        if eth_spot:
            lines.append("### ETH")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Price | ${eth_spot.get('price', 0):,.2f} |")
            lines.append(f"| 24h Change | {eth_spot.get('change_24h', 0):+.2f}% |")
            lines.append(f"| 24h Volume | ${eth_spot.get('volume_24h', 0):,.0f} |")
            lines.append(f"| Market Cap | ${eth_spot.get('market_cap', 0):,.0f} |")
            lines.append(f"| 24h High | ${eth_spot.get('high_24h', 0):,.2f} |")
            lines.append(f"| 24h Low | ${eth_spot.get('low_24h', 0):,.2f} |")

            if eth_deriv:
                lines.append(
                    f"| Funding Rate (8h) | {eth_deriv.get('funding_rate', 0) * 100:.4f}% |"
                )
                lines.append(
                    f"| Funding Rate (24h) | {eth_deriv.get('funding_rate_24h', 0) * 100:.4f}% |"
                )
                lines.append(f"| Open Interest | ${eth_deriv.get('open_interest_usd', 0):,.0f} |")
                lines.append(f"| Long/Short Ratio | {eth_deriv.get('long_short_ratio', 0):.3f} |")
                lines.append(
                    f"| Long Liquidation (24h) | ${eth_deriv.get('long_liquidation_24h', 0):,.0f} |"
                )
                lines.append(
                    f"| Short Liquidation (24h) | ${eth_deriv.get('short_liquidation_24h', 0):,.0f} |"
                )

        return "\n".join(lines)

    def _generate_news_section(self, news_snapshot: list[dict[str, Any]]) -> str:
        """Generate news section (max 5 items)."""
        if not news_snapshot:
            return "No significant news or events at this time."

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
            lines.append(f"- Source: {source}")
            if date_str:
                lines.append(f"- Published: {date_str}")
            if url:
                lines.append(f"- [Read more]({url})")
            lines.append("")

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
        lines.append("### 📈 Upside Scenario")
        triggers = []
        if btc_change > 0 and eth_change > 0:
            triggers.append("Sustained positive momentum in both BTC and ETH")
        if btc_deriv.get("funding_rate", 0) < 0.001:
            triggers.append("Funding rate remains low (no long squeeze risk)")
        if btc_deriv.get("long_short_ratio", 1.0) < 1.2:
            triggers.append("Long/short ratio not overly extended")
        if warn_count == 0 and critical_count == 0:
            triggers.append("No critical warning signals present")
        if not triggers:
            triggers.append("Break above key resistance levels with volume confirmation")

        for trigger in triggers[:3]:  # Max 3 triggers
            lines.append(f"- {trigger}")
        lines.append("")

        # Sideways Scenario
        lines.append("### ➡️ Sideways Scenario")
        triggers = []
        if abs(btc_change) < 3 and abs(eth_change) < 3:
            triggers.append("Low volatility and range-bound price action")
        if btc_deriv.get("funding_rate", 0) > -0.001 and btc_deriv.get("funding_rate", 0) < 0.001:
            triggers.append("Funding rate near neutral (equilibrium)")
        if warn_count > 0 and critical_count == 0:
            triggers.append("Some warning signals but no critical issues")
        if not triggers:
            triggers.append("Price consolidates between support and resistance levels")

        for trigger in triggers[:3]:
            lines.append(f"- {trigger}")
        lines.append("")

        # Downside Scenario
        lines.append("### 📉 Downside Scenario")
        triggers = []
        if critical_count >= 1:
            triggers.append("Critical signals detected (e.g., extreme funding, liquidation risk)")
        if btc_change < -5 or eth_change < -5:
            triggers.append("Sharp price decline with increased selling pressure")
        if btc_deriv.get("funding_rate", 0) > 0.01:
            triggers.append("High funding rate indicates long squeeze risk")
        if btc_deriv.get("long_short_ratio", 1.0) > 1.5:
            triggers.append("Extreme long/short ratio suggests over-leveraged longs")
        if not triggers:
            triggers.append("Break below key support levels with volume confirmation")

        for trigger in triggers[:3]:
            lines.append(f"- {trigger}")

        return "\n".join(lines)
