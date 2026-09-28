import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Metric = { label: string; value: string; detail: string };

type DataStatus = { state: string; message: string; last_successful_pipeline_at?: string | null };
type NetworkOverview = {
  data_status: DataStatus; journeys_analysed?: number | null; stations?: number | null;
  average_arrival_delay_minutes?: number | null; median_arrival_delay_minutes?: number | null;
  on_time_or_early_percent?: number | null;
  station_stop_observations?: number | null; coverage_start_date?: string | null; coverage_end_date?: string | null;
};
type PipelineHealth = {
  data_status: DataStatus; last_run_status?: string | null; records_received?: number | null;
  records_rejected?: number | null;
};
type LiveTrainStatus = {
  data_status: DataStatus; train_number?: string | null; train_name?: string | null;
  journey_date?: string | null; status?: string | null; delay_minutes?: number | null;
  current_station_code?: string | null; next_station_code?: string | null;
  next_station_name?: string | null; provider_updated_at?: string | null; cached?: boolean;
};
type PredictionSummary = {
  data_status: DataStatus; model_name?: string | null; evaluation_rows?: number | null;
  mae_minutes?: number | null; rmse_minutes?: number | null; global_mean_mae_minutes?: number | null;
  accepted_for_prediction?: boolean | null;
};
type DelayDistribution = { data_status: DataStatus; bands: { label: string; observations: number }[] };
type StationHotspots = { data_status: DataStatus; stations: { station_code: string; observations: number; average_delay_minutes: number; median_delay_minutes: number; on_time_percent: number }[] };
type DailyTrend = { data_status: DataStatus; days: { journey_date: string; observations: number; average_delay_minutes: number; median_delay_minutes: number }[] };
type TrainProfile = { data_status: DataStatus; train_number?: string; journeys?: number; observations?: number; average_delay_minutes?: number; median_delay_minutes?: number; on_time_percent?: number };
type ProspectiveArchive = { data_status: DataStatus; snapshots?: number; trains?: number; first_retrieved_at?: string | null; latest_retrieved_at?: string | null; average_delay_minutes?: number | null };
const apiBase = import.meta.env.VITE_DASHBOARD_API_BASE_URL ?? "";
const liveLookupEnabled = import.meta.env.VITE_ENABLE_LIVE_LOOKUP !== "false";
const number = (value?: number | null, digits = 0) => value == null ? "—" : value.toLocaleString(undefined, { maximumFractionDigits: digits });
const dateTime = (value?: string | null) => value ? new Date(value).toLocaleString() : "Not available";

function App() {
  const [overview, setOverview] = useState<NetworkOverview | null>(null);
  const [health, setHealth] = useState<PipelineHealth | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [liveTrainNumber, setLiveTrainNumber] = useState("12919");
  const [liveStatus, setLiveStatus] = useState<LiveTrainStatus | null>(null);
  const [liveLoading, setLiveLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictionSummary | null>(null);
  const [distribution, setDistribution] = useState<DelayDistribution | null>(null);
  const [hotspots, setHotspots] = useState<StationHotspots | null>(null);
  const [trend, setTrend] = useState<DailyTrend | null>(null);
  const [archive, setArchive] = useState<ProspectiveArchive | null>(null);
  const [profileNumber, setProfileNumber] = useState("12919");
  const [profile, setProfile] = useState<TrainProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [staticMode, setStaticMode] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(`${apiBase}/v1/dashboard/network-overview`).then((response) => response.ok ? response.json() : Promise.reject()),
      fetch(`${apiBase}/v1/dashboard/pipeline-health`).then((response) => response.ok ? response.json() : Promise.reject()),
      fetch(`${apiBase}/v1/dashboard/prediction-summary`).then((response) => response.ok ? response.json() : Promise.reject()),
      fetch(`${apiBase}/v1/dashboard/delay-distribution`).then((response) => response.ok ? response.json() : Promise.reject()),
      fetch(`${apiBase}/v1/dashboard/station-hotspots`).then((response) => response.ok ? response.json() : Promise.reject()),
      fetch(`${apiBase}/v1/dashboard/daily-trend`).then((response) => response.ok ? response.json() : Promise.reject()),
      fetch(`${apiBase}/v1/dashboard/prospective-archive`).then((response) => response.ok ? response.json() : Promise.reject())
    ]).then(([network, pipeline, evaluatedPrediction, delayBands, stationRanks, daily, prospective]) => {
      setOverview(network as NetworkOverview);
      setHealth(pipeline as PipelineHealth);
      setPrediction(evaluatedPrediction as PredictionSummary);
      setDistribution(delayBands as DelayDistribution); setHotspots(stationRanks as StationHotspots);
      setTrend(daily as DailyTrend); setArchive(prospective as ProspectiveArchive);
    }).catch(() => fetch(`${import.meta.env.BASE_URL}dashboard_snapshot.json`).then((response) => response.json()).then((snapshot) => {
      setOverview(snapshot.overview as NetworkOverview); setHealth(snapshot.health as PipelineHealth);
      setPrediction(snapshot.prediction as PredictionSummary); setStaticMode(true);
    }).catch(() => setError("The dashboard API and static portfolio snapshot are unavailable.")));
  }, []);

  const status = overview?.data_status;
  const metrics: Metric[] = [
    { label: "Journeys analysed", value: number(overview?.journeys_analysed), detail: "Unique train-day journeys" },
    { label: "Stations", value: number(overview?.stations), detail: "Observed route stations" },
    { label: "Average arrival delay", value: overview?.average_arrival_delay_minutes == null ? "—" : `${number(overview.average_arrival_delay_minutes, 1)} min`, detail: "Across observed station stops" },
    { label: "On time or early", value: overview?.on_time_or_early_percent == null ? "—" : `${number(overview.on_time_or_early_percent, 1)}%`, detail: "Arrival delay at or below zero" }
  ];
  const loadLiveStatus = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLiveLoading(true);
    try {
      const response = await fetch(`${apiBase}/v1/live/trains/${encodeURIComponent(liveTrainNumber)}`);
      setLiveStatus(await response.json() as LiveTrainStatus);
    } catch {
      setLiveStatus({ data_status: { state: "provider_unavailable", message: "Live status could not be retrieved." } });
    } finally {
      setLiveLoading(false);
    }
  };
  const loadTrainProfile = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setProfileLoading(true);
    try {
      const response = await fetch(`${apiBase}/v1/dashboard/trains/${encodeURIComponent(profileNumber)}`);
      setProfile(await response.json() as TrainProfile);
    } catch {
      setProfile({ data_status: { state: "unavailable", message: "Historical train profile could not be retrieved." } });
    } finally { setProfileLoading(false); }
  };
  return (
    <main>
      <header>
        <div>
          <p className="eyebrow">INDEPENDENT PORTFOLIO PROJECT</p>
          <h1>Rail Delay Analytics</h1>
          <p className="subtitle">Historical delay analytics and time-safe arrival-delay prediction.</p>
        </div>
        <span className="status">Data status: {status?.state ?? "loading"}</span>
      </header>

      <section className="notice" aria-label="Data limitation notice">
        {error ?? status?.message ?? "Loading approved-source metrics from the dashboard API…"}
      </section>

      <section className="metrics" aria-label="Network overview metrics">
        {metrics.map((metric) => (
          <article className="metric" key={metric.label}>
            <p>{metric.label}</p><strong>{metric.value}</strong><small>{metric.detail}</small>
          </article>
        ))}
      </section>

      <section className="grid">
        <article className="panel"><h2>Network overview</h2><p className="summary">Median arrival delay: <strong>{overview?.median_arrival_delay_minutes == null ? "—" : `${number(overview.median_arrival_delay_minutes, 1)} min`}</strong></p><p className="empty">{number(overview?.station_stop_observations)} station-stop observations from {overview?.coverage_start_date ?? "—"} to {overview?.coverage_end_date ?? "—"}. Historical RSTGCN coverage only; live RailRadar lookups are shown separately and are not retained.</p></article>
        {!staticMode && liveLookupEnabled && <article className="panel">
          <h2>Live train status</h2>
          <form className="live-form" onSubmit={loadLiveStatus}>
            <label htmlFor="live-train-number">Five-digit train number</label>
            <input id="live-train-number" value={liveTrainNumber} onChange={(event) => setLiveTrainNumber(event.target.value)} inputMode="numeric" pattern="[0-9]{5}" maxLength={5} required />
            <button type="submit" disabled={liveLoading}>{liveLoading ? "Checking…" : "Check live status"}</button>
          </form>
          {liveStatus ? <div className="live-result"><p className="summary">{liveStatus.data_status.message}</p>{liveStatus.data_status.state === "ready" && <><p><strong>{liveStatus.train_name}</strong> ({liveStatus.train_number}) · {liveStatus.status}</p><p>Delay: <strong>{number(liveStatus.delay_minutes, 1)} min</strong> · Current: {liveStatus.current_station_code ?? "—"} · Next: {liveStatus.next_station_name ?? liveStatus.next_station_code ?? "—"}</p><small>RailRadar snapshot at {dateTime(liveStatus.provider_updated_at)}{liveStatus.cached ? " (cached)" : ""}. Not retained as history.</small></>}</div> : <p className="empty">Enter a train number for a personal-use live RailRadar snapshot.</p>}
        </article>}
        <article className="panel"><h2>Delay prediction</h2>{prediction?.data_status.state === "ready" ? <><p className="summary">Baseline MAE: <strong>{number(prediction.mae_minutes, 2)} min</strong></p><p className="empty">{number(prediction.evaluation_rows)} untouched chronological holdout rows · RMSE {number(prediction.rmse_minutes, 2)} min · global-mean MAE {number(prediction.global_mean_mae_minutes, 2)} min · {prediction.accepted_for_prediction ? "improves on the global-mean reference." : "does not improve on the global-mean reference."}</p></> : <EmptyState text={prediction?.data_status.message ?? "Loading prediction-evaluation status…"} />}</article>
        <article className="panel"><h2>Pipeline health</h2><p className="summary">Latest run: <strong>{health?.last_run_status ?? "—"}</strong></p><p className="empty">Received {number(health?.records_received)} records; rejected {number(health?.records_rejected)}. Completed {dateTime(health?.data_status.last_successful_pipeline_at)}.</p></article>
      </section>

      {!staticMode && <section className="insights" aria-label="Historical delay analysis">
        <article className="panel wide"><h2>Delay distribution</h2>
          {distribution?.bands?.length ? <div className="band-list">{distribution.bands.map((band) => <div className="band" key={band.label}><span>{band.label}</span><div><i style={{ width: `${Math.max(4, (band.observations / Math.max(...distribution.bands.map((item) => item.observations))) * 100)}%` }} /></div><strong>{number(band.observations)}</strong></div>)}</div> : <EmptyState text={distribution?.data_status.message ?? "Loading delay distribution…"} />}
        </article>
        <article className="panel"><h2>Station hotspots</h2>
          {hotspots?.stations?.length ? <div className="table-wrap"><table><thead><tr><th>Station</th><th>Avg delay</th><th>On time</th></tr></thead><tbody>{hotspots.stations.map((station) => <tr key={station.station_code}><td><strong>{station.station_code}</strong><small>{number(station.observations)} stops</small></td><td>{number(station.average_delay_minutes, 1)} min</td><td>{number(station.on_time_percent, 1)}%</td></tr>)}</tbody></table></div> : <EmptyState text={hotspots?.data_status.message ?? "Loading station rankings…"} />}
        </article>
        <article className="panel"><h2>Daily delay trend</h2>
          {trend?.days?.length ? <><div className="trend-bars">{trend.days.map((day) => <span title={`${day.journey_date}: ${number(day.median_delay_minutes, 1)} min median`} key={day.journey_date} style={{ height: `${Math.max(4, Math.min(100, day.median_delay_minutes * 2))}%` }} />)}</div><p className="summary">Each bar is one September day; height is median arrival delay.</p></> : <EmptyState text={trend?.data_status.message ?? "Loading daily trend…"} />}
        </article>
        <article className="panel"><h2>Train punctuality explorer</h2>
          <form className="live-form" onSubmit={loadTrainProfile}><label htmlFor="profile-train-number">Five-digit train number</label><input id="profile-train-number" value={profileNumber} onChange={(event) => setProfileNumber(event.target.value)} inputMode="numeric" pattern="[0-9]{5}" maxLength={5} required /><button type="submit" disabled={profileLoading}>{profileLoading ? "Loading…" : "View September profile"}</button></form>
          {profile ? <div className="live-result"><p className="summary">{profile.data_status.message}</p>{profile.data_status.state === "ready" && <p><strong>{profile.train_number}</strong> · {number(profile.journeys)} journeys · median <strong>{number(profile.median_delay_minutes, 1)} min</strong> · on time {number(profile.on_time_percent, 1)}%</p>}</div> : <p className="empty">Search the historical September 2024 profile for a train.</p>}
        </article>
        <article className="panel wide"><h2>Prospective RailRadar archive</h2>
          {archive?.data_status.state === "ready" ? <p className="summary"><strong>{number(archive.snapshots)}</strong> snapshots across <strong>{number(archive.trains)}</strong> watchlist trains since {dateTime(archive.first_retrieved_at)}. Latest capture: {dateTime(archive.latest_retrieved_at)}. This is a separate prospective source, never blended into RSTGCN history.</p> : <EmptyState text={archive?.data_status.message ?? "Loading prospective archive status…"} />}
        </article>
      </section>}

      <footer>This is an independent portfolio project and is not affiliated with Indian Railways, IRCTC, CRIS, or the Government of India.</footer>
    </main>
  );
}

function EmptyState({ text }: { text: string }) { return <p className="empty">{text}</p>; }

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
