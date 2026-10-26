"""InsForge client and database operations for investigations."""

import json
from datetime import datetime

from app.core.config import get_settings
from app.models.schemas import InvestigationHistoryEntry


import json
import os
from datetime import datetime
from typing import List

from app.core.config import get_settings
from app.models.schemas import InvestigationHistoryEntry
from app.services import progress


class InForgeClient:
    """Client for InsForge operations (auth, database, realtime).

    This implementation provides two modes:
    - If INSFORGE_URL and INSFORGE_API_KEY are present, it will attempt to use them
      (left as TODO for full SDK calls).
    - Otherwise, it falls back to a local JSON file persistence so the app remains functional
      in development without external credentials.
    """

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.INSFORGE_URL
        self.api_key = self.settings.INSFORGE_API_KEY

        # Determine storage location for fallback history persistence
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.history_file = os.path.join(self.data_dir, "investigations.json")

        # If no credentials provided, continue with fallback but do not raise.
        if not self.base_url or not self.api_key:
            # warn at runtime but keep the service usable
            try:
                import logging

                logging.getLogger(__name__).warning(
                    "InsForge credentials missing: falling back to local history persistence"
                )
            except Exception:
                pass

    def _read_history(self) -> List[dict]:
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return []

    def _write_history(self, rows: List[dict]) -> None:
        with open(self.history_file, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, default=str, indent=2)

    def save_investigation(
        self,
        user_id: str,
        namespace: str | None,
        root_cause: str,
        explanation: str,
        confidence: int,
        status: str,
        diagnosis_data: dict,
    ) -> dict:
        """Save investigation to InsForge database or local fallback file.

        Returns the saved record.
        """
        investigation_id = f"inv_{int(datetime.now().timestamp() * 1000)}"
        record = {
            "id": investigation_id,
            "user_id": user_id,
            "namespace": namespace,
            "root_cause": root_cause,
            "explanation": explanation,
            "confidence": confidence,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "diagnosis_data": diagnosis_data,
        }

        # If InsForge credentials present, TODO: insert via SDK
        if self.base_url and self.api_key:
            # TODO: implement real InsForge insert using official SDK or HTTP API
            # For now still persist locally as well for reliability
            pass

        rows = self._read_history()
        rows.insert(0, record)
        # Keep only the most recent 100 entries
        rows = rows[:100]
        self._write_history(rows)

        return record

    def get_investigation_history(self, user_id: str) -> List[InvestigationHistoryEntry]:
        """Fetch investigation history for a user.

        If InsForge is configured, this should query the remote DB. For now, uses local file.
        """
        rows = self._read_history()
        # filter by user_id
        user_rows = [r for r in rows if r.get("user_id") == user_id]
        # Convert created_at to datetime in the Pydantic model
        results = []
        for r in user_rows:
            try:
                r_copy = r.copy()
                r_copy["created_at"] = r_copy.get("created_at")
                results.append(InvestigationHistoryEntry(**r_copy))
            except Exception:
                continue
        return results

    def publish_progress(self, channel: str, message: dict) -> bool:
        """Publish progress update to realtime channel.

        This implementation pushes progress messages into the local in-memory
        progress queue so connected clients can stream updates via SSE.
        """
        # channel will be the investigation id for our local pub/sub
        try:
            # schedule the publish into the queue
            asyncio.get_event_loop().create_task(progress.publish(channel, message))
            return True
        except Exception:
            # If event loop not running in this thread, try running in a new loop
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(progress.publish(channel, message))
                loop.close()
                return True
            except Exception:
                return False


# Singleton instance
_client: InForgeClient | None = None


def get_insforge_client() -> InForgeClient:
    """Get or create the InsForge client instance."""
    global _client
    if _client is None:
        _client = InForgeClient()
    return _client


# Singleton instance
_client: InForgeClient | None = None


def get_insforge_client() -> InForgeClient:
    """Get or create the InsForge client instance."""
    global _client
    if _client is None:
        _client = InForgeClient()
    return _client
