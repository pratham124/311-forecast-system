from __future__ import annotations


class OperationalStatusService:
    def blocked_summary(self, outcome: str, detail: str) -> str:
        return f"{outcome}: {detail}"
