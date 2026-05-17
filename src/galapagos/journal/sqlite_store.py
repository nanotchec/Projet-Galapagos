from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any

from galapagos.execution.position_manager import Position


class SQLiteStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.migrate()

    def migrate(self) -> None:
        cur = self.connection.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS market_snapshots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              timestamp_utc TEXT NOT NULL,
              profile TEXT NOT NULL,
              asset TEXT NOT NULL,
              timeframe TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              data_quality_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS agent_decisions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              timestamp_utc TEXT NOT NULL,
              profile TEXT NOT NULL,
              asset TEXT NOT NULL,
              timeframe TEXT NOT NULL,
              input_context_hash TEXT NOT NULL,
              market_snapshot_id INTEGER,
              raw_llm_response TEXT NOT NULL,
              parsed_decision TEXT NOT NULL,
              decision_validity TEXT NOT NULL,
              risk_engine_result TEXT,
              final_action TEXT,
              reasoning_summary TEXT,
              critical_data_used TEXT
            );
            CREATE TABLE IF NOT EXISTS risk_decisions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              timestamp_utc TEXT NOT NULL,
              agent_decision_id INTEGER,
              approved INTEGER NOT NULL,
              final_action TEXT NOT NULL,
              reasons_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS paper_trades (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              entry_timestamp TEXT,
              exit_timestamp TEXT,
              side TEXT,
              entry_price REAL,
              exit_price REAL,
              stop_loss REAL,
              take_profit REAL,
              size REAL,
              fees REAL,
              slippage REAL,
              pnl REAL,
              pnl_percent REAL,
              strategy TEXT,
              profile TEXT,
              status TEXT,
              close_reason TEXT,
              payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS positions (
              id TEXT PRIMARY KEY,
              payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS performance_snapshots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              timestamp_utc TEXT NOT NULL,
              profile TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS system_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              timestamp_utc TEXT NOT NULL,
              level TEXT NOT NULL,
              message TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );
            """
        )
        self._migrate_paper_account(cur)
        self.connection.commit()

    def _migrate_paper_account(self, cur: sqlite3.Cursor) -> None:
        columns = cur.execute("PRAGMA table_info(paper_account)").fetchall()
        if not columns:
            cur.execute(
                """
                CREATE TABLE paper_account (
                  profile TEXT PRIMARY KEY,
                  cash REAL NOT NULL
                );
                """
            )
            return
        column_names = {column[1] for column in columns}
        if "profile" in column_names:
            return
        legacy = cur.execute("SELECT cash FROM paper_account WHERE id = 1").fetchone()
        legacy_cash = float(legacy[0]) if legacy else None
        cur.execute("ALTER TABLE paper_account RENAME TO paper_account_legacy_v11")
        cur.execute(
            """
            CREATE TABLE paper_account (
              profile TEXT PRIMARY KEY,
              cash REAL NOT NULL
            );
            """
        )
        if legacy_cash is not None:
            cur.execute(
                "INSERT INTO paper_account (profile, cash) VALUES (?, ?)",
                ("galapagos_30m", legacy_cash),
            )

    def insert_market_snapshot(self, payload: dict[str, Any]) -> int:
        cur = self.connection.execute(
            """
            INSERT INTO market_snapshots
            (timestamp_utc, profile, asset, timeframe, payload_json, data_quality_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload["timestamp_utc"],
                payload["profile"],
                payload["asset"],
                payload["timeframe"],
                json.dumps(payload),
                json.dumps(payload.get("data_quality", {})),
            ),
        )
        self.connection.commit()
        return int(cur.lastrowid)

    def insert_agent_decision(self, payload: dict[str, Any]) -> int:
        cur = self.connection.execute(
            """
            INSERT INTO agent_decisions
            (timestamp_utc, profile, asset, timeframe, input_context_hash, market_snapshot_id,
             raw_llm_response, parsed_decision, decision_validity, risk_engine_result,
             final_action, reasoning_summary, critical_data_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["timestamp_utc"],
                payload["profile"],
                payload["asset"],
                payload["timeframe"],
                payload["input_context_hash"],
                payload.get("market_snapshot_id"),
                payload["raw_llm_response"],
                json.dumps(payload["parsed_decision"]),
                payload["decision_validity"],
                json.dumps(payload.get("risk_engine_result")),
                payload.get("final_action"),
                payload.get("reasoning_summary"),
                json.dumps(payload.get("critical_data_used", [])),
            ),
        )
        self.connection.commit()
        return int(cur.lastrowid)

    def insert_risk_decision(self, payload: dict[str, Any]) -> int:
        cur = self.connection.execute(
            """
            INSERT INTO risk_decisions
            (timestamp_utc, agent_decision_id, approved, final_action, reasons_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload["timestamp_utc"],
                payload.get("agent_decision_id"),
                int(payload["approved"]),
                payload["final_action"],
                json.dumps(payload.get("reasons", [])),
            ),
        )
        self.connection.commit()
        return int(cur.lastrowid)

    def insert_paper_trade(self, payload: dict[str, Any]) -> int:
        cur = self.connection.execute(
            """
            INSERT INTO paper_trades
            (entry_timestamp, exit_timestamp, side, entry_price, exit_price, stop_loss,
             take_profit, size, fees, slippage, pnl, pnl_percent, strategy, profile,
             status, close_reason, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("entry_timestamp"),
                payload.get("exit_timestamp"),
                payload.get("side"),
                payload.get("entry_price"),
                payload.get("exit_price"),
                payload.get("stop_loss"),
                payload.get("take_profit"),
                payload.get("size"),
                payload.get("fees", payload.get("entry_fee")),
                payload.get("slippage", payload.get("entry_slippage")),
                payload.get("pnl"),
                payload.get("pnl_percent"),
                payload.get("strategy"),
                payload.get("profile"),
                payload.get("status"),
                payload.get("close_reason"),
                json.dumps(payload),
            ),
        )
        self.connection.commit()
        return int(cur.lastrowid)

    def load_open_positions(self, profile: str | None = None) -> list[dict[str, Any]]:
        rows = self.query("SELECT payload_json FROM positions")
        positions = [json.loads(row["payload_json"]) for row in rows]
        if profile is not None:
            return [position for position in positions if position.get("profile") == profile]
        return positions

    def replace_open_positions(
        self,
        positions: list[Position],
        *,
        profile: str | None = None,
    ) -> None:
        with self.connection:
            if profile is None:
                self.connection.execute("DELETE FROM positions")
            else:
                self.connection.execute(
                    """
                    DELETE FROM positions
                    WHERE json_extract(payload_json, '$.profile') = ?
                    """,
                    (profile,),
                )
            self.connection.executemany(
                "INSERT INTO positions (id, payload_json) VALUES (?, ?)",
                [(position.id, json.dumps(asdict(position))) for position in positions],
            )

    def get_account_cash(self, default: float, profile: str = "galapagos_30m") -> float:
        rows = self.query("SELECT cash FROM paper_account WHERE profile = ?", (profile,))
        if not rows:
            self.set_account_cash(default, profile=profile)
            return default
        return float(rows[0]["cash"])

    def set_account_cash(self, cash: float, profile: str = "galapagos_30m") -> None:
        self.connection.execute(
            """
            INSERT INTO paper_account (profile, cash)
            VALUES (?, ?)
            ON CONFLICT(profile) DO UPDATE SET cash = excluded.cash
            """,
            (profile, cash),
        )
        self.connection.commit()

    def insert_system_event(self, payload: dict[str, Any]) -> int:
        cur = self.connection.execute(
            """
            INSERT INTO system_events (timestamp_utc, level, message, payload_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                payload["timestamp_utc"],
                payload["level"],
                payload["message"],
                json.dumps(payload.get("payload", {})),
            ),
        )
        self.connection.commit()
        return int(cur.lastrowid)

    def insert_performance_snapshot(self, payload: dict[str, Any]) -> int:
        cur = self.connection.execute(
            """
            INSERT INTO performance_snapshots (timestamp_utc, profile, payload_json)
            VALUES (?, ?, ?)
            """,
            (
                payload["timestamp_utc"],
                payload["profile"],
                json.dumps(payload),
            ),
        )
        self.connection.commit()
        return int(cur.lastrowid)

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return list(self.connection.execute(sql, params))
