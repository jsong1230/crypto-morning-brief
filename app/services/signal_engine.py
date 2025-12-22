"""Rule-based signal engine for research briefing."""

from datetime import datetime
from typing import Any


class SignalEngine:
    """Rule-based signal engine that analyzes market data and generates signals."""

    # Thresholds for various rules
    THRESHOLDS = {
        "funding_rate_overheated": 0.01,  # 1% per 8h
        "funding_rate_extreme": 0.05,  # 5% per 8h
        "oi_increase_critical": 0.3,  # 30% increase
        "oi_increase_warning": 0.15,  # 15% increase
        "volatility_extreme": 0.15,  # 15% daily change
        "volatility_high": 0.10,  # 10% daily change
        "volume_surge_zscore": 2.0,  # 2 standard deviations
        "price_oi_surge_price": 0.05,  # 5% price increase
        "price_oi_surge_oi": 0.20,  # 20% OI increase
        "price_drop_volume_price": -0.05,  # -5% price drop
        "price_drop_volume_volume": 0.5,  # 50% volume increase
        "long_short_ratio_extreme": 1.5,  # 1.5:1 or 0.67:1
        "long_short_ratio_warning": 1.3,  # 1.3:1 or 0.77:1
        "liquidation_risk_ratio": 0.1,  # 10% of OI
    }

    def __init__(self):
        """Initialize signal engine."""
        self._historical_data: dict[str, list[dict[str, Any]]] = {}

    def analyze(
        self,
        spot_snapshot: dict[str, Any],
        derivatives_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze market data and generate signals.

        Args:
            spot_snapshot: Spot market data from provider.
            derivatives_snapshot: Derivatives market data from provider.

        Returns:
            Dictionary with 'signals' and 'regime' keys.
        """
        signals: list[dict[str, Any]] = []
        regime_rationale: list[str] = []

        # Process each symbol
        symbols = set(spot_snapshot.keys()) & set(derivatives_snapshot.keys())

        for symbol in symbols:
            spot_data = spot_snapshot[symbol]
            deriv_data = derivatives_snapshot[symbol]

            # Rule 1: Funding Rate Overheated
            signal = self._check_funding_overheated(symbol, deriv_data)
            if signal:
                signals.append(signal)
                regime_rationale.append(f"{symbol}: Funding rate elevated")

            # Rule 2: Open Interest Surge
            signal = self._check_oi_surge(symbol, deriv_data)
            if signal:
                signals.append(signal)
                regime_rationale.append(f"{symbol}: Open interest surge")

            # Rule 3: Volatility Spike
            signal = self._check_volatility_spike(symbol, spot_data)
            if signal:
                signals.append(signal)
                regime_rationale.append(f"{symbol}: High volatility")

            # Rule 4: Volume Surge
            signal = self._check_volume_surge(symbol, spot_data)
            if signal:
                signals.append(signal)
                regime_rationale.append(f"{symbol}: Volume surge")

            # Rule 5: Long/Short Ratio Extreme
            signal = self._check_long_short_ratio(symbol, deriv_data)
            if signal:
                signals.append(signal)
                regime_rationale.append(f"{symbol}: Long/short imbalance")

            # Rule 6: Price Surge + OI Surge (Liquidation Risk)
            signal = self._check_price_oi_surge(symbol, spot_data, deriv_data)
            if signal:
                signals.append(signal)
                regime_rationale.append(f"{symbol}: Liquidation risk alert")

            # Rule 7: Price Drop + Volume Surge (Panic Selling)
            signal = self._check_price_drop_volume(symbol, spot_data)
            if signal:
                signals.append(signal)
                regime_rationale.append(f"{symbol}: Potential panic selling")

            # Rule 8: Extreme Funding Rate
            signal = self._check_extreme_funding(symbol, deriv_data)
            if signal:
                signals.append(signal)
                regime_rationale.append(f"{symbol}: Extreme funding rate")

            # Rule 9: Liquidation Risk
            signal = self._check_liquidation_risk(symbol, deriv_data)
            if signal:
                signals.append(signal)
                regime_rationale.append(f"{symbol}: High liquidation risk")

            # Rule 10: Price Momentum + Derivatives Divergence
            signal = self._check_momentum_divergence(symbol, spot_data, deriv_data)
            if signal:
                signals.append(signal)
                regime_rationale.append(f"{symbol}: Momentum divergence")

            # Rule 11: BTC Dominance Change (if BTC is in data)
            if symbol == "BTC" and len(spot_snapshot) > 1:
                signal = self._check_btc_dominance_change(spot_snapshot)
                if signal:
                    signals.append(signal)
                    regime_rationale.append("BTC dominance shift")

        # Determine market regime
        regime = self._determine_regime(signals, regime_rationale)

        return {
            "signals": signals,
            "regime": regime,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _check_funding_overheated(
        self, symbol: str, deriv_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Rule 1: Check if funding rate is overheated."""
        deriv_data.get("funding_rate", 0)
        funding_rate_24h = deriv_data.get("funding_rate_24h", 0)

        if abs(funding_rate_24h) >= self.THRESHOLDS["funding_rate_overheated"]:
            level = (
                "critical"
                if abs(funding_rate_24h) >= self.THRESHOLDS["funding_rate_extreme"]
                else "warn"
            )
            direction = "long" if funding_rate_24h > 0 else "short"
            return {
                "id": f"{symbol}_funding_overheated",
                "level": level,
                "title": f"{symbol} Funding Rate Overheated ({direction} bias)",
                "reason": f"24h funding rate {funding_rate_24h * 100:.3f}% exceeds threshold",
                "metric": "funding_rate_24h",
                "threshold": self.THRESHOLDS["funding_rate_overheated"],
                "value": funding_rate_24h,
            }
        return None

    def _check_oi_surge(self, symbol: str, deriv_data: dict[str, Any]) -> dict[str, Any] | None:
        """Rule 2: Check if open interest has surged."""
        oi = deriv_data.get("open_interest", 0)
        oi_usd = deriv_data.get("open_interest_usd", oi)

        # Store historical data for comparison
        if symbol not in self._historical_data:
            self._historical_data[symbol] = []

        hist = self._historical_data[symbol]
        if len(hist) > 0:
            prev_oi = hist[-1].get("open_interest_usd", oi_usd)
            if prev_oi > 0:
                oi_change = (oi_usd - prev_oi) / prev_oi

                if oi_change >= self.THRESHOLDS["oi_increase_critical"]:
                    level = "critical"
                    threshold = self.THRESHOLDS["oi_increase_critical"]
                elif oi_change >= self.THRESHOLDS["oi_increase_warning"]:
                    level = "warn"
                    threshold = self.THRESHOLDS["oi_increase_warning"]
                else:
                    return None

                return {
                    "id": f"{symbol}_oi_surge",
                    "level": level,
                    "title": f"{symbol} Open Interest Surge",
                    "reason": f"OI increased {oi_change * 100:.1f}% in 24h",
                    "metric": "open_interest_change_24h",
                    "threshold": threshold,
                    "value": oi_change,
                }

        # Store current data
        hist.append(
            {
                "open_interest_usd": oi_usd,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        # Keep only last 10 entries
        if len(hist) > 10:
            self._historical_data[symbol] = hist[-10:]

        return None

    def _check_volatility_spike(
        self, symbol: str, spot_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Rule 3: Check if volatility has spiked."""
        change_24h = abs(spot_data.get("change_24h", 0)) / 100  # Convert to decimal

        if change_24h >= self.THRESHOLDS["volatility_extreme"]:
            level = "critical"
            threshold = self.THRESHOLDS["volatility_extreme"]
        elif change_24h >= self.THRESHOLDS["volatility_high"]:
            level = "warn"
            threshold = self.THRESHOLDS["volatility_high"]
        else:
            return None

        direction = "up" if spot_data.get("change_24h", 0) > 0 else "down"
        return {
            "id": f"{symbol}_volatility_spike",
            "level": level,
            "title": f"{symbol} Volatility Spike ({direction})",
            "reason": f"24h price change {abs(spot_data.get('change_24h', 0)):.2f}% exceeds threshold",
            "metric": "change_24h_abs",
            "threshold": threshold * 100,
            "value": abs(spot_data.get("change_24h", 0)),
        }

    def _check_volume_surge(self, symbol: str, spot_data: dict[str, Any]) -> dict[str, Any] | None:
        """Rule 4: Check if volume has surged (simplified z-score approximation)."""
        volume_24h = spot_data.get("volume_24h", 0)
        market_cap = spot_data.get("market_cap", 1)

        # Simple approximation: volume/market_cap ratio
        volume_ratio = volume_24h / market_cap if market_cap > 0 else 0

        # Store historical for comparison
        if symbol not in self._historical_data:
            self._historical_data[symbol] = []

        hist = self._historical_data[symbol]
        if len(hist) > 0:
            prev_ratios = [h.get("volume_ratio", volume_ratio) for h in hist[-5:]]
            if prev_ratios:
                mean_ratio = sum(prev_ratios) / len(prev_ratios)
                std_ratio = (
                    (sum((r - mean_ratio) ** 2 for r in prev_ratios) / len(prev_ratios)) ** 0.5
                    if len(prev_ratios) > 1
                    else mean_ratio * 0.1
                )

                if std_ratio > 0:
                    zscore = (volume_ratio - mean_ratio) / std_ratio
                    if zscore >= self.THRESHOLDS["volume_surge_zscore"]:
                        return {
                            "id": f"{symbol}_volume_surge",
                            "level": "warn",
                            "title": f"{symbol} Volume Surge",
                            "reason": f"Volume z-score {zscore:.2f} indicates unusual activity",
                            "metric": "volume_zscore",
                            "threshold": self.THRESHOLDS["volume_surge_zscore"],
                            "value": zscore,
                        }

        # Store current data
        if hist:
            hist[-1]["volume_ratio"] = volume_ratio
        else:
            hist.append({"volume_ratio": volume_ratio})

        return None

    def _check_long_short_ratio(
        self, symbol: str, deriv_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Rule 5: Check if long/short ratio is extreme."""
        ratio = deriv_data.get("long_short_ratio", 1.0)

        if ratio >= self.THRESHOLDS["long_short_ratio_extreme"]:
            level = "warn"
            threshold = self.THRESHOLDS["long_short_ratio_extreme"]
            direction = "long"
        elif ratio <= 1 / self.THRESHOLDS["long_short_ratio_extreme"]:
            level = "warn"
            threshold = 1 / self.THRESHOLDS["long_short_ratio_extreme"]
            direction = "short"
        elif ratio >= self.THRESHOLDS["long_short_ratio_warning"]:
            level = "info"
            threshold = self.THRESHOLDS["long_short_ratio_warning"]
            direction = "long"
        elif ratio <= 1 / self.THRESHOLDS["long_short_ratio_warning"]:
            level = "info"
            threshold = 1 / self.THRESHOLDS["long_short_ratio_warning"]
            direction = "short"
        else:
            return None

        return {
            "id": f"{symbol}_long_short_imbalance",
            "level": level,
            "title": f"{symbol} Long/Short Imbalance ({direction} bias)",
            "reason": f"Long/short ratio {ratio:.3f} indicates {direction} bias",
            "metric": "long_short_ratio",
            "threshold": threshold,
            "value": ratio,
        }

    def _check_price_oi_surge(
        self,
        symbol: str,
        spot_data: dict[str, Any],
        deriv_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Rule 6: Check for price surge + OI surge (liquidation risk)."""
        change_24h = spot_data.get("change_24h", 0) / 100
        oi = deriv_data.get("open_interest_usd", 0)

        # Check OI change
        if symbol not in self._historical_data:
            self._historical_data[symbol] = []
        hist = self._historical_data[symbol]
        oi_change = 0
        if len(hist) > 0:
            prev_oi = hist[-1].get("open_interest_usd", oi)
            if prev_oi > 0:
                oi_change = (oi - prev_oi) / prev_oi

        if (
            change_24h >= self.THRESHOLDS["price_oi_surge_price"]
            and oi_change >= self.THRESHOLDS["price_oi_surge_oi"]
        ):
            return {
                "id": f"{symbol}_liquidation_risk_alert",
                "level": "critical",
                "title": f"{symbol} Liquidation Risk Alert",
                "reason": f"Price surge {change_24h * 100:.1f}% + OI surge {oi_change * 100:.1f}% indicates liquidation risk",
                "metric": "price_oi_surge_combo",
                "threshold": f"{self.THRESHOLDS['price_oi_surge_price'] * 100:.1f}% price, {self.THRESHOLDS['price_oi_surge_oi'] * 100:.1f}% OI",
                "value": f"{change_24h * 100:.1f}% price, {oi_change * 100:.1f}% OI",
            }
        return None

    def _check_price_drop_volume(
        self, symbol: str, spot_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Rule 7: Check for price drop + volume surge (panic selling)."""
        change_24h = spot_data.get("change_24h", 0) / 100
        volume_24h = spot_data.get("volume_24h", 0)
        market_cap = spot_data.get("market_cap", 1)
        volume_ratio = volume_24h / market_cap if market_cap > 0 else 0

        # Check volume change
        if symbol not in self._historical_data:
            self._historical_data[symbol] = []
        hist = self._historical_data[symbol]
        volume_change = 0
        if len(hist) > 0:
            prev_ratio = hist[-1].get("volume_ratio", volume_ratio)
            if prev_ratio > 0:
                volume_change = (volume_ratio - prev_ratio) / prev_ratio

        if (
            change_24h <= self.THRESHOLDS["price_drop_volume_price"]
            and volume_change >= self.THRESHOLDS["price_drop_volume_volume"]
        ):
            return {
                "id": f"{symbol}_panic_selling_risk",
                "level": "warn",
                "title": f"{symbol} Potential Panic Selling",
                "reason": f"Price drop {change_24h * 100:.1f}% + volume surge {volume_change * 100:.1f}% indicates panic selling",
                "metric": "price_drop_volume_combo",
                "threshold": f"{self.THRESHOLDS['price_drop_volume_price'] * 100:.1f}% price, {self.THRESHOLDS['price_drop_volume_volume'] * 100:.1f}% volume",
                "value": f"{change_24h * 100:.1f}% price, {volume_change * 100:.1f}% volume",
            }
        return None

    def _check_extreme_funding(
        self, symbol: str, deriv_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Rule 8: Check for extreme funding rate."""
        funding_rate = deriv_data.get("funding_rate", 0)

        if abs(funding_rate) >= self.THRESHOLDS["funding_rate_extreme"]:
            direction = "long" if funding_rate > 0 else "short"
            return {
                "id": f"{symbol}_extreme_funding",
                "level": "critical",
                "title": f"{symbol} Extreme Funding Rate ({direction})",
                "reason": f"Funding rate {funding_rate * 100:.3f}% per 8h is extremely high",
                "metric": "funding_rate",
                "threshold": self.THRESHOLDS["funding_rate_extreme"],
                "value": funding_rate,
            }
        return None

    def _check_liquidation_risk(
        self, symbol: str, deriv_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Rule 9: Check for high liquidation risk."""
        long_liq = deriv_data.get("long_liquidation_24h", 0)
        short_liq = deriv_data.get("short_liquidation_24h", 0)
        oi = deriv_data.get("open_interest_usd", 0)

        if oi > 0:
            total_liq = long_liq + short_liq
            liq_ratio = total_liq / oi

            if liq_ratio >= self.THRESHOLDS["liquidation_risk_ratio"]:
                return {
                    "id": f"{symbol}_high_liquidation_risk",
                    "level": "warn",
                    "title": f"{symbol} High Liquidation Risk",
                    "reason": f"24h liquidation {liq_ratio * 100:.1f}% of OI indicates high risk",
                    "metric": "liquidation_ratio",
                    "threshold": self.THRESHOLDS["liquidation_risk_ratio"],
                    "value": liq_ratio,
                }
        return None

    def _check_momentum_divergence(
        self,
        symbol: str,
        spot_data: dict[str, Any],
        deriv_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Rule 10: Check for price momentum vs derivatives divergence."""
        change_24h = spot_data.get("change_24h", 0)
        funding_rate = deriv_data.get("funding_rate", 0)
        oi_change = 0

        # Get OI change
        if symbol in self._historical_data and len(self._historical_data[symbol]) > 0:
            hist = self._historical_data[symbol]
            oi = deriv_data.get("open_interest_usd", 0)
            if len(hist) > 0:
                prev_oi = hist[-1].get("open_interest_usd", oi)
                if prev_oi > 0:
                    oi_change = (oi - prev_oi) / prev_oi

        # Price up but funding negative or OI decreasing = divergence
        if change_24h > 5 and (funding_rate < -0.0005 or oi_change < -0.1):
            return {
                "id": f"{symbol}_momentum_divergence",
                "level": "info",
                "title": f"{symbol} Momentum Divergence",
                "reason": f"Price up {change_24h:.1f}% but derivatives show bearish signals",
                "metric": "momentum_divergence",
                "threshold": "Price up >5% with negative funding or OI decrease",
                "value": f"{change_24h:.1f}% price, {funding_rate * 100:.3f}% funding, {oi_change * 100:.1f}% OI",
            }
        # Price down but funding positive or OI increasing = divergence
        elif change_24h < -5 and (funding_rate > 0.0005 or oi_change > 0.1):
            return {
                "id": f"{symbol}_momentum_divergence",
                "level": "info",
                "title": f"{symbol} Momentum Divergence",
                "reason": f"Price down {change_24h:.1f}% but derivatives show bullish signals",
                "metric": "momentum_divergence",
                "threshold": "Price down >5% with positive funding or OI increase",
                "value": f"{change_24h:.1f}% price, {funding_rate * 100:.3f}% funding, {oi_change * 100:.1f}% OI",
            }

        return None

    def _check_btc_dominance_change(self, spot_snapshot: dict[str, Any]) -> dict[str, Any] | None:
        """Rule 11: Check for BTC dominance change."""
        if "BTC" not in spot_snapshot:
            return None

        btc_mcap = spot_snapshot["BTC"].get("market_cap", 0)
        total_mcap = sum(data.get("market_cap", 0) for data in spot_snapshot.values())

        if total_mcap == 0:
            return None

        btc_dominance = btc_mcap / total_mcap

        # Store historical
        if "BTC" not in self._historical_data:
            self._historical_data["BTC"] = []

        hist = self._historical_data["BTC"]
        if len(hist) > 0:
            prev_dom = hist[-1].get("btc_dominance", btc_dominance)
            dom_change = btc_dominance - prev_dom

            # Significant change (>2%)
            if abs(dom_change) >= 0.02:
                direction = "increasing" if dom_change > 0 else "decreasing"
                return {
                    "id": "btc_dominance_change",
                    "level": "info",
                    "title": f"BTC Dominance {direction.capitalize()}",
                    "reason": f"BTC dominance changed {dom_change * 100:.2f}% to {btc_dominance * 100:.2f}%",
                    "metric": "btc_dominance_change",
                    "threshold": 0.02,
                    "value": dom_change,
                }

        # Store current
        if hist:
            hist[-1]["btc_dominance"] = btc_dominance
        else:
            hist.append({"btc_dominance": btc_dominance})

        return None

    def _determine_regime(
        self, signals: list[dict[str, Any]], rationale: list[str]
    ) -> dict[str, Any]:
        """
        Determine market regime based on signals.

        Args:
            signals: List of generated signals.
            rationale: List of rationale strings.

        Returns:
            Regime dictionary with label and rationale.
        """
        if not signals:
            return {
                "label": "neutral",
                "rationale": ["No significant signals detected"],
            }

        # Count signals by level
        critical_count = sum(1 for s in signals if s["level"] == "critical")
        warn_count = sum(1 for s in signals if s["level"] == "warn")
        sum(1 for s in signals if s["level"] == "info")

        # Determine regime
        if critical_count >= 2:
            label = "risk_off"
        elif critical_count >= 1 or warn_count >= 3:
            label = "risk_off"
        elif warn_count >= 1:
            label = "neutral"
        else:
            label = "risk_on"

        return {
            "label": label,
            "rationale": rationale[:10],  # Limit to 10 items
        }
