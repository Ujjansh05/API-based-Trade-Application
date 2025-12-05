"""
Core logic for Notify + Auto-Buy trading feature.

Focus: correctness, safety, clarity.

Key principles:
- Notifications monitor ALL tokens that meet strategy conditions but never place trades.
- Auto-Buy applies ONLY to explicitly enabled tokens with sufficient margin.
- Runtime-configurable token selection with per-token enable flag.
- Clear, logged decision flow for debugging.

This module is designed to be language-agnostic in structure but implemented in Python.
It does not depend on FastAPI; you can wire it into the backend or run as a standalone service.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional, Tuple
import time


# -----------------------------
# Data Models & Config
# -----------------------------

@dataclass
class MarketTick:
    """Represents a single market tick for a token/instrument."""
    token: str            # e.g., "NSE:INFY" or option symbol like "NFO:NIFTY25DEC24500CE"
    ltp: float            # last traded price
    open: float
    high: float
    low: float
    volume: int
    timestamp: float      # epoch seconds


@dataclass
class TokenAutoBuyConfig:
    """Runtime-configurable token selection for auto-buy."""
    token: str
    autobuy: bool = False
    quantity: int = 1     # default order quantity (lots or shares depending on instrument)


@dataclass
class StrategySignal:
    """Represents a strategy evaluation result for a token."""
    token: str
    signal: str           # e.g., "BUY", "SELL", "NONE"
    score: float = 0.0    # optional score/confidence
    reason: str = ""      # human-readable reason


@dataclass
class MarginSnapshot:
    """Represents user's margin state at a point in time."""
    available: float
    utilized: float = 0.0


@dataclass
class ExecutionLog:
    """Accumulates decision logs for debugging and audit."""
    entries: List[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        self.entries.append(f"[{ts}] {message}")


# -----------------------------
# Strategy & Validation Hooks
# -----------------------------

def simple_breakout_strategy(tick: MarketTick) -> StrategySignal:
    """
    Example strategy: BUY on breakout above recent high threshold.
    Replace with your actual strategy logic.
    """
    if tick.ltp > tick.high * 0.995:  # near high
        return StrategySignal(token=tick.token, signal="BUY", score=0.7, reason="Near session high breakout")
    return StrategySignal(token=tick.token, signal="NONE", score=0.0, reason="No breakout")


def estimate_order_cost(token: str, ltp: float, quantity: int) -> float:
    """
    Estimate notional cost for margin validation.
    Extend to include fees, span exposure, instrument multipliers.
    """
    return max(ltp, 0.0) * max(quantity, 1)


def has_sufficient_margin(margin: MarginSnapshot, cost: float) -> bool:
    return margin.available >= cost


# -----------------------------
# Notification & Auto-Buy Engine
# -----------------------------

class NotifyAutoBuyEngine:
    """
    Engine to:
    - Continuously evaluate strategy against market ticks
    - Send notifications for ALL qualifying tokens
    - Execute auto-buy ONLY for user-enabled tokens with sufficient margin
    """

    def __init__(
        self,
        token_config: List[TokenAutoBuyConfig],
        get_latest_ticks: Callable[[], List[MarketTick]],
        get_margin: Callable[[], MarginSnapshot],
        send_notification: Callable[[str, Dict], None],
        place_buy_order: Callable[[str, int], Tuple[bool, str]],
        strategy_fn: Callable[[MarketTick], StrategySignal] = simple_breakout_strategy,
        log: Optional[ExecutionLog] = None,
    ) -> None:
        self.token_config_map: Dict[str, TokenAutoBuyConfig] = {c.token: c for c in token_config}
        self.get_latest_ticks = get_latest_ticks
        self.get_margin = get_margin
        self.send_notification = send_notification
        self.place_buy_order = place_buy_order
        self.strategy_fn = strategy_fn
        self.log = log or ExecutionLog()

    def update_token_config(self, config: List[TokenAutoBuyConfig]) -> None:
        """Runtime update of token selection and flags."""
        self.token_config_map = {c.token: c for c in config}
        self.log.add(f"Token config updated: {self.token_config_map}")

    def _notify(self, signal: StrategySignal, tick: MarketTick) -> None:
        payload = {
            "token": signal.token,
            "signal": signal.signal,
            "ltp": tick.ltp,
            "reason": signal.reason,
            "score": signal.score,
            "timestamp": tick.timestamp,
        }
        # Notification must never place trades by itself
        self.send_notification("signal_detected", payload)
        self.log.add(f"Notification sent for {signal.token}: {payload}")

    def _try_autobuy(self, signal: StrategySignal, tick: MarketTick, margin: MarginSnapshot) -> None:
        # Enforce explicit selection: no auto-buy without enabled flag
        cfg = self.token_config_map.get(signal.token)
        if not cfg or not cfg.autobuy:
            self.log.add(f"Auto-Buy skipped: {signal.token} not enabled.")
            return

        if signal.signal != "BUY":
            self.log.add(f"Auto-Buy skipped: signal is {signal.signal} for {signal.token}.")
            return

        # Margin validation
        est_cost = estimate_order_cost(signal.token, tick.ltp, cfg.quantity)
        if not has_sufficient_margin(margin, est_cost):
            self.log.add(
                f"Auto-Buy blocked: insufficient margin. Needed={est_cost:.2f}, Available={margin.available:.2f}"
            )
            self.send_notification(
                "insufficient_margin",
                {
                    "token": signal.token,
                    "needed": est_cost,
                    "available": margin.available,
                    "quantity": cfg.quantity,
                },
            )
            return

        # Place order (safe: only BUY path, quantity from config)
        ok, order_id = self.place_buy_order(signal.token, cfg.quantity)
        if ok:
            self.log.add(f"Auto-Buy executed for {signal.token}, qty={cfg.quantity}, order_id={order_id}")
            self.send_notification(
                "order_placed",
                {"token": signal.token, "quantity": cfg.quantity, "order_id": order_id},
            )
        else:
            self.log.add(f"Auto-Buy failed for {signal.token}: {order_id}")
            self.send_notification("order_failed", {"token": signal.token, "error": order_id})

    def step(self) -> ExecutionLog:
        """
        Process one evaluation step:
        - Pull latest ticks
        - Evaluate strategy
        - Send notifications for all qualifying tokens
        - Attempt auto-buy where enabled and margin allows
        Returns the execution log for inspection.
        """
        ticks = self.get_latest_ticks()
        margin = self.get_margin()
        self.log.add(f"Fetched {len(ticks)} ticks; margin available={margin.available:.2f}")

        for tick in ticks:
            sig = self.strategy_fn(tick)
            # Notify for any non-NONE signals (or notify all if desired)
            if sig.signal != "NONE":
                self._notify(sig, tick)
            # Auto-Buy path (BUY only, strict controls)
            self._try_autobuy(sig, tick, margin)

        return self.log


# -----------------------------
# Example Usage / Test Harness
# -----------------------------

def _example():
    """Minimal harness demonstrating the engine with sample data structures."""
    # Sample token selection structure
    selection = [
        TokenAutoBuyConfig(token="NSE:INFY", autobuy=True, quantity=10),
        TokenAutoBuyConfig(token="NSE:TCS", autobuy=False, quantity=5),
        TokenAutoBuyConfig(token="NFO:NIFTY25DEC24500CE", autobuy=True, quantity=1),
    ]

    # Mock data providers
    def get_ticks() -> List[MarketTick]:
        now = time.time()
        return [
            MarketTick(token="NSE:INFY", ltp=1440.0, open=1430.0, high=1441.0, low=1420.0, volume=1_000_000, timestamp=now),
            MarketTick(token="NSE:TCS", ltp=3750.0, open=3700.0, high=3800.0, low=3690.0, volume=800_000, timestamp=now),
            MarketTick(token="NFO:NIFTY25DEC24500CE", ltp=120.0, open=110.0, high=121.0, low=105.0, volume=50_000, timestamp=now),
        ]

    def get_margin() -> MarginSnapshot:
        return MarginSnapshot(available=10_000.0, utilized=2_000.0)

    def notify(kind: str, payload: Dict) -> None:
        print(f"NOTIFY[{kind}] {payload}")

    def place_buy(token: str, qty: int) -> Tuple[bool, str]:
        # In production, call broker API here and return (True, order_id) or (False, error)
        return True, f"SIM-{int(time.time())}"

    engine = NotifyAutoBuyEngine(
        token_config=selection,
        get_latest_ticks=get_ticks,
        get_margin=get_margin,
        send_notification=notify,
        place_buy_order=place_buy,
    )

    log = engine.step()
    print("\n--- Decision Log ---")
    for line in log.entries:
        print(line)


if __name__ == "__main__":
    _example()
