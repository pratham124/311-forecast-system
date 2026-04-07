from __future__ import annotations

from app.core.metrics import get_user_guide_support_metrics, record_user_guide_support_signal, reset_user_guide_support_metrics


def test_user_guide_support_metrics_record_get_and_reset():
    reset_user_guide_support_metrics()
    assert get_user_guide_support_metrics() == {}

    record_user_guide_support_signal("guide_unavailable")
    assert get_user_guide_support_metrics() == {"guide_unavailable": 1}

    reset_user_guide_support_metrics()
    assert get_user_guide_support_metrics() == {}
