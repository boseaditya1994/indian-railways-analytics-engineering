from railway_pipeline.dashboard.service import UnavailableDashboardMartRepository


def test_unavailable_dashboard_never_invents_metrics() -> None:
    overview = UnavailableDashboardMartRepository().network_overview()
    assert overview.data_status.state == "awaiting_approved_source"
    assert overview.journeys_analysed is None
    assert overview.average_arrival_delay_minutes is None
