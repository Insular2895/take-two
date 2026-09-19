"""Local durable journal used to reconcile a bridge restart."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from pathlib import Path
from typing import Any

from .contracts import GatewayEvent, PaperCommand, RecoveryIdentity


class JournalConflict(RuntimeError):
    """The same intent identity was observed with different immutable content."""


class BridgeJournal:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS intents (
              intent_id TEXT PRIMARY KEY,
              order_ref TEXT NOT NULL UNIQUE,
              command_hash TEXT NOT NULL,
              command_json TEXT NOT NULL,
              state TEXT NOT NULL,
              claimed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              dispatch_started_at TEXT,
              terminal_at TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
              broker_event_key TEXT PRIMARY KEY,
              intent_id TEXT NOT NULL REFERENCES intents(intent_id),
              event_type TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              posted_at TEXT
            );
            CREATE TABLE IF NOT EXISTS broker_identities (
              intent_id TEXT PRIMARY KEY REFERENCES intents(intent_id),
              broker_order_id INTEGER,
              broker_perm_id INTEGER
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_journal_perm_id
              ON broker_identities(broker_perm_id)
              WHERE broker_perm_id IS NOT NULL AND broker_perm_id > 0;
            CREATE TABLE IF NOT EXISTS broker_executions (
              exec_id TEXT PRIMARY KEY,
              intent_id TEXT NOT NULL REFERENCES intents(intent_id)
            );
            """
        )
        self._connection.commit()

    @staticmethod
    def _canonical_command(command: Mapping[str, Any]) -> tuple[str, str]:
        encoded = json.dumps(command, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return encoded, hashlib.sha256(encoded.encode()).hexdigest()

    def remember_claim(self, command: PaperCommand, raw_command: Mapping[str, Any]) -> None:
        encoded, digest = self._canonical_command(raw_command)
        with self._connection:
            existing = self._connection.execute(
                "SELECT command_hash FROM intents WHERE intent_id=?", (command.intent_id,)
            ).fetchone()
            if existing and existing["command_hash"] != digest:
                raise JournalConflict("immutable command content changed")
            self._connection.execute(
                """INSERT OR IGNORE INTO intents(
                     intent_id,order_ref,command_hash,command_json,state
                   ) VALUES(?,?,?,?,'CLAIMED')""",
                (command.intent_id, command.order_ref, digest, encoded),
            )

    def mark_dispatch_started(self, intent_id: str) -> None:
        with self._connection:
            self._connection.execute(
                """UPDATE intents SET state='DISPATCH_STARTED',dispatch_started_at=CURRENT_TIMESTAMP
                   WHERE intent_id=? AND dispatch_started_at IS NULL""",
                (intent_id,),
            )

    def remember_event(self, intent_id: str, event: GatewayEvent) -> None:
        payload = json.dumps(event.as_payload(), sort_keys=True, separators=(",", ":"))
        terminal = event.event_type in {
            "LOCAL_NOT_TRANSMITTED",
            "FILLED",
            "REJECTED",
            "CANCELLED",
            "EXPIRED",
        }
        with self._connection:
            self._connection.execute(
                """INSERT OR IGNORE INTO events(
                     broker_event_key,intent_id,event_type,payload_json
                   ) VALUES(?,?,?,?)""",
                (event.broker_event_key, intent_id, event.event_type, payload),
            )
            if event.broker_order_id is not None or event.broker_perm_id is not None:
                self._connection.execute(
                    """INSERT INTO broker_identities(intent_id,broker_order_id,broker_perm_id)
                       VALUES(?,?,?)
                       ON CONFLICT(intent_id) DO UPDATE SET
                         broker_order_id=coalesce(excluded.broker_order_id,broker_order_id),
                         broker_perm_id=coalesce(excluded.broker_perm_id,broker_perm_id)""",
                    (intent_id, event.broker_order_id, event.broker_perm_id),
                )
            if event.broker_exec_id:
                self._connection.execute(
                    "INSERT OR IGNORE INTO broker_executions(exec_id,intent_id) VALUES(?,?)",
                    (event.broker_exec_id, intent_id),
                )
            self._connection.execute(
                """UPDATE intents SET state=?,
                   terminal_at=CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE terminal_at END
                   WHERE intent_id=?""",
                (event.event_type, terminal, intent_id),
            )

    def mark_event_posted(self, event_key: str) -> None:
        with self._connection:
            self._connection.execute(
                "UPDATE events SET posted_at=CURRENT_TIMESTAMP WHERE broker_event_key=?",
                (event_key,),
            )

    def unposted_events(self) -> list[tuple[str, str, dict[str, Any]]]:
        query = """SELECT intent_id,broker_event_key,payload_json
                   FROM events WHERE posted_at IS NULL ORDER BY rowid"""
        with closing(self._connection.execute(query)) as cursor:
            return [
                (row["intent_id"], row["broker_event_key"], json.loads(row["payload_json"]))
                for row in cursor.fetchall()
            ]

    def unresolved_order_refs(self) -> list[tuple[str, str]]:
        return [(item.intent_id, item.order_ref) for item in self.unresolved_orders()]

    def unresolved_orders(self) -> list[RecoveryIdentity]:
        with closing(
            self._connection.execute(
                """SELECT i.intent_id,i.order_ref,b.broker_order_id,b.broker_perm_id
                   FROM intents i LEFT JOIN broker_identities b ON b.intent_id=i.intent_id
                   WHERE i.terminal_at IS NULL AND i.dispatch_started_at IS NOT NULL
                   ORDER BY i.claimed_at"""
            )
        ) as cursor:
            rows = cursor.fetchall()
        recovered: list[RecoveryIdentity] = []
        for row in rows:
            exec_rows = self._connection.execute(
                "SELECT exec_id FROM broker_executions WHERE intent_id=? ORDER BY exec_id",
                (row["intent_id"],),
            ).fetchall()
            recovered.append(
                RecoveryIdentity(
                    intent_id=row["intent_id"],
                    order_ref=row["order_ref"],
                    broker_order_id=row["broker_order_id"],
                    broker_perm_id=row["broker_perm_id"],
                    broker_exec_ids=tuple(item["exec_id"] for item in exec_rows),
                )
            )
        return recovered

    def close(self) -> None:
        self._connection.close()
