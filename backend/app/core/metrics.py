from __future__ import annotations

from collections import Counter


_support_signals: Counter[str] = Counter()


def record_user_guide_support_signal(signal: str) -> None:
    _support_signals[signal] += 1


def get_user_guide_support_metrics() -> dict[str, int]:
    return dict(_support_signals)


def reset_user_guide_support_metrics() -> None:
    _support_signals.clear()
