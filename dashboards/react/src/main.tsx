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
const apiBase = import.meta.env.VITE_DASHBOARD_API_BASE_URL ?? "";
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

  useEffect(() => {
    Promise.all([
      fetch(`${apiBase}/v1/dashboard/network-overview`).then((response) => response.ok ? response.json() : Promise.reject()),
      fetch(`${apiBase}/v1/dashboard/pipeline-health`).then((response) => response.ok ? response.json() : Promise.reject()),
      fetch(`${apiBase}/v1/dashboard/prediction-summary`).then((response) => response.ok ? response.json() : Promise.reject())
    ]).then(([network, pipeline, evaluatedPrediction]) => {
      setOverview(network as NetworkOverview);
      setHealth(pipeline as PipelineHealth);
      setPrediction(evaluatedPrediction as PredictionSummary);
    }).catch(() => setError("The dashboard API is unreachable. Start the local API or configure VITE_DASHBOARD_API_BASE_URL."));
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
        <article className="panel">
          <h2>Live train status</h2>
          <form className="live-form" onSubmit={loadLiveStatus}>
            <label htmlFor="live-train-number">Five-digit train number</label>
            <input id="live-train-number" value={liveTrainNumber} onChange={(event) => setLiveTrainNumber(event.target.value)} inputMode="numeric" pattern="[0-9]{5}" maxLength={5} required />
            <button type="submit" disabled={liveLoading}>{liveLoading ? "Checking…" : "Check live status"}</button>
          </form>
          {liveStatus ? <div className="live-result"><p className="summary">{liveStatus.data_status.message}</p>{liveStatus.data_status.state === "ready" && <><p><strong>{liveStatus.train_name}</strong> ({liveStatus.train_number}) · {liveStatus.status}</p><p>Delay: <strong>{number(liveStatus.delay_minutes, 1)} min</strong> · Current: {liveStatus.current_station_code ?? "—"} · Next: {liveStatus.next_station_name ?? liveStatus.next_station_code ?? "—"}</p><small>RailRadar snapshot at {dateTime(liveStatus.provider_updated_at)}{liveStatus.cached ? " (cached)" : ""}. Not retained as history.</small></>}</div> : <p className="empty">Enter a train number for a personal-use live RailRadar snapshot.</p>}
        </article>
        <article className="panel"><h2>Delay prediction</h2>{prediction?.data_status.state === "ready" ? <><p className="summary">Baseline MAE: <strong>{number(prediction.mae_minutes, 2)} min</strong></p><p className="empty">{number(prediction.evaluation_rows)} untouched chronological holdout rows · RMSE {number(prediction.rmse_minutes, 2)} min · global-mean MAE {number(prediction.global_mean_mae_minutes, 2)} min · {prediction.accepted_for_prediction ? "improves on the global-mean reference." : "does not improve on the global-mean reference."}</p></> : <EmptyState text={prediction?.data_status.message ?? "Loading prediction-evaluation status…"} />}</article>
        <article className="panel"><h2>Pipeline health</h2><p className="summary">Latest run: <strong>{health?.last_run_status ?? "—"}</strong></p><p className="empty">Received {number(health?.records_received)} records; rejected {number(health?.records_rejected)}. Completed {dateTime(health?.data_status.last_successful_pipeline_at)}.</p></article>
      </section>

      <footer>This is an independent portfolio project and is not affiliated with Indian Railways, IRCTC, CRIS, or the Government of India.</footer>
    </main>
  );
}

function EmptyState({ text }: { text: string }) { return <p className="empty">{text}</p>; }

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
