from __future__ import annotations

from datetime import datetime, timezone

from app.repositories.threshold_configuration_repository import ThresholdConfigurationRepository
from app.services.threshold_selection_service import ThresholdSelectionService


def test_geography_threshold_precedence_for_matching_region(session) -> None:
    repo = ThresholdConfigurationRepository(session)
    now = datetime.now(timezone.utc)
    default = repo.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=30,
        operational_manager_id="mgr-1",
        notification_channels=["email"],
        effective_from=now,
    )
    specific = repo.create_configuration(
        service_category="Roads",
        forecast_window_type="hourly",
        threshold_value=60,
        operational_manager_id="mgr-1",
        notification_channels=["email"],
        geography_type="ward",
        geography_value="Ward 1",
        effective_from=now,
    )
    session.commit()

    service = ThresholdSelectionService(repo)

    selected_for_ward_1 = service.resolve(service_category="Roads", geography_value="Ward 1", forecast_window_type="hourly")
    selected_for_ward_2 = service.resolve(service_category="Roads", geography_value="Ward 2", forecast_window_type="hourly")

    assert selected_for_ward_1 is not None
    assert selected_for_ward_1.threshold_configuration_id == specific.threshold_configuration_id
    assert selected_for_ward_2 is not None
    assert selected_for_ward_2.threshold_configuration_id == default.threshold_configuration_id
