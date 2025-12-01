from typing import Optional, List
from ib_insync import IB, Contract, Stock, Index, Future, Option, Forex, util

class IBClient:
    """Thin wrapper around ib_insync to manage connection and simple calls."""
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib: IB = IB()

    def connect(self) -> None:
        if not self.ib.isConnected():
            self.ib.connect(self.host, self.port, clientId=self.client_id)

    def disconnect(self) -> None:
        if self.ib.isConnected():
            self.ib.disconnect()

    def qualify(self, contract: Contract) -> Contract:
        self.connect()
        qualified = self.ib.qualifyContracts(contract)
        if not qualified:
            raise RuntimeError("Failed to qualify contract")
        return qualified[0]

    def get_bars(self, contract: Contract, duration: str, bar_size: str, what_to_show: str = "TRADES", use_rth: bool = True):
        """
        Fetch historical bars using IB API.
        duration e.g. "1200 S" (seconds) or "2 D"
        bar_size e.g. "10 mins", "5 mins", "1 hour"
        """
        self.connect()
        qualified = self.qualify(contract)
        bars = self.ib.reqHistoricalData(
            qualified,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=use_rth,
            formatDate=1
        )
        return util.df(bars)

    def place_market_order(self, contract: Contract, action: str, quantity: float):
        from ib_insync import MarketOrder
        self.connect()
        qualified = self.qualify(contract)
        order = MarketOrder(action, quantity)
        trade = self.ib.placeOrder(qualified, order)
        return trade

    def place_limit_order(self, contract: Contract, action: str, quantity: float, limit_price: float):
        from ib_insync import LimitOrder
        self.connect()
        qualified = self.qualify(contract)
        order = LimitOrder(action, quantity, limit_price)
        trade = self.ib.placeOrder(qualified, order)
        return trade

