from __future__ import annotations

from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.services.threshold_selection_service import ThresholdSelectionService


def test_default_threshold_created_when_no_specific_match(session) -> None:
    """When no category or geography threshold is configured, a default is created for that scope."""
    repository = ThresholdConfigurationRepository(session)
    service = ThresholdSelectionService(repository)
    selected = service.resolve(service_category="Roads", geography_value=None, forecast_window_type="hourly")

    assert selected is not None
    assert selected.service_category == "Roads"
    assert selected.forecast_window_type == "hourly"
    assert float(selected.threshold_value) == 100.0  # default
