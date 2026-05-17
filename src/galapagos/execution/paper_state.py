from __future__ import annotations

from galapagos.execution.paper_broker import PaperBroker
from galapagos.execution.position_manager import Position
from galapagos.journal.sqlite_store import SQLiteStore


class PaperState:
    def __init__(self, store: SQLiteStore, initial_capital: float, profile: str) -> None:
        self.store = store
        self.initial_capital = initial_capital
        self.profile = profile

    def load_broker(self) -> PaperBroker:
        cash = self.store.get_account_cash(default=self.initial_capital, profile=self.profile)
        positions = {
            payload["id"]: Position.from_dict(payload)
            for payload in self.store.load_open_positions(profile=self.profile)
        }
        return PaperBroker(
            initial_capital=self.initial_capital,
            cash=cash,
            positions=positions,
        )

    def save_broker(self, broker: PaperBroker) -> None:
        self.store.set_account_cash(broker.cash, profile=self.profile)
        self.store.replace_open_positions(
            [position for position in broker.positions.values()],
            profile=self.profile,
        )
