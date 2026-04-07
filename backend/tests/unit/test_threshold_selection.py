from __future__ import annotations

from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.services.threshold_selection_service import ThresholdSelectionService


def test_global_threshold_is_used_for_any_category_scope(session) -> None:
    repository = ThresholdConfigurationRepository(session)
    repository.set_global_threshold(threshold_value=80, operational_manager_id="mgr-1")
    session.commit()

    service = ThresholdSelectionService(repository)
    selected = service.resolve(service_category="Roads", geography_value="Ward 1", forecast_window_type="hourly")

    assert selected is not None
    assert selected.service_category == "__GLOBAL__"
    assert selected.forecast_window_type == "global"
    assert float(selected.threshold_value) == 80
