from pathlib import Path

from railway_pipeline.ingestion.rstgcn_adapter import read_rstgcn_events


def test_rstgcn_adapter_joins_route_sequence(tmp_path: Path) -> None:
    delays = tmp_path / "delays.csv"
    routes = tmp_path / "routes.csv"
    delays.write_text(
        "train,date,station,sch_arr,act_arr,arr_delay,sch_dep,act_dep,dep_delay\n12303,2024-09-02,HWH,08:00 AM,08:01 AM,1,08:00 AM,08:01 AM,1\n"
    )
    routes.write_text(
        "stnSerialNumber,trainNumber,station_code\n1,12303,HWH\n"
    )
    event = list(read_rstgcn_events(delays, routes))[0]
    assert event["station_sequence"] == 1
    assert event["arrival_delay_minutes"] == 1.0


def test_rstgcn_adapter_marks_unmatched_stops_for_quarantine(tmp_path: Path) -> None:
    delays = tmp_path / "delays.csv"
    routes = tmp_path / "routes.csv"
    delays.write_text(
        "train,date,station,sch_arr,act_arr,arr_delay,sch_dep,act_dep,dep_delay\n12303,2024-09-02,HWH,,,,,,\n"
    )
    routes.write_text("stnSerialNumber,trainNumber,station_code\n")
    event = list(read_rstgcn_events(delays, routes))[0]
    assert event["station_sequence"] == 0
