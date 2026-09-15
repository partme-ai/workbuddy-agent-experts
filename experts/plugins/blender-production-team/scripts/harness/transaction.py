"""Transaction snapshots, rollback, and recovery metadata."""

from __future__ import annotations

import json
import os
import secrets
from copy import deepcopy
from pathlib import Path
from collections.abc import Callable

from .errors import HarnessError


class TransactionManager:
    def __init__(self, *, capture: Callable[[], object], restore: Callable[[object], None], journal_path: Path | None = None):
        self._capture = capture
        self._restore = restore
        self._journal_path = Path(journal_path) if journal_path else None
        self._transactions: dict[str, dict] = {}

    def begin(self, transaction_id: str, *, scene_revision: int) -> dict:
        if transaction_id in self._transactions:
            raise HarnessError("TRANSACTION_EXISTS", f"transaction already exists: {transaction_id}")
        snapshot_id = "snapshot-" + secrets.token_hex(12)
        self._transactions[transaction_id] = {
            "transactionId": transaction_id,
            "snapshotId": snapshot_id,
            "beginRevision": scene_revision,
            "sceneRevision": scene_revision,
            "state": "active",
            "restoration": "unknown",
            "snapshot": deepcopy(self._capture()),
        }
        self._write_journal()
        return {"transactionId": transaction_id, "snapshotId": snapshot_id, "sceneRevision": scene_revision}

    def execute(self, transaction_id: str, callback):
        transaction = self._require_active(transaction_id)
        try:
            return callback()
        except BaseException:
            self._rollback_transaction(transaction)
            raise

    def rollback(self, transaction_id: str) -> dict:
        transaction = self._require_active(transaction_id)
        self._rollback_transaction(transaction)
        return self.status(transaction_id)

    def commit(self, transaction_id: str, *, scene_revision: int) -> dict:
        transaction = self._require_active(transaction_id)
        transaction["state"] = "committed"
        transaction["sceneRevision"] = scene_revision
        transaction["restoration"] = "not_required"
        transaction.pop("snapshot", None)
        self._write_journal()
        return {"transactionId": transaction_id, "snapshotId": transaction["snapshotId"], "sceneRevision": scene_revision}

    def status(self, transaction_id: str) -> dict:
        transaction = self._transactions.get(transaction_id)
        if transaction is None:
            raise HarnessError("TRANSACTION_NOT_FOUND", f"transaction not found: {transaction_id}")
        return {key: value for key, value in transaction.items() if key != "snapshot"}

    def _require_active(self, transaction_id: str) -> dict:
        transaction = self._transactions.get(transaction_id)
        if transaction is None:
            raise HarnessError("TRANSACTION_NOT_FOUND", f"transaction not found: {transaction_id}")
        if transaction["state"] != "active":
            raise HarnessError("TRANSACTION_NOT_ACTIVE", f"transaction is {transaction['state']}: {transaction_id}")
        return transaction

    def _rollback_transaction(self, transaction: dict) -> None:
        try:
            restore_result = self._restore(deepcopy(transaction["snapshot"]))
            restored = restore_result if isinstance(restore_result, bool) else self._capture() == transaction["snapshot"]
            transaction["restoration"] = "confirmed" if restored else "failed"
        except Exception:
            transaction["restoration"] = "failed"
        transaction["state"] = "rolled_back"
        transaction.pop("snapshot", None)
        self._write_journal()

    def _write_journal(self) -> None:
        if self._journal_path is None:
            return
        self._journal_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "transactions": [
                {key: value for key, value in transaction.items() if key != "snapshot"}
                for transaction in self._transactions.values()
            ]
        }
        temporary = self._journal_path.with_suffix(self._journal_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True, indent=2))
        os.replace(temporary, self._journal_path)
