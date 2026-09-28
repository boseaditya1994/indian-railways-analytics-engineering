import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Metric = { label: string; value: string; detail: string };

type DataStatus = { state: string; message: string; last_successful_pipeline_at?: string | null };
type NetworkOverview = {
  data_status: DataStatus; journeys_analysed?: number | null; stations?: number | null;
  average_arrival_delay_minutes?: number | null; median_arrival_delay_minutes?: number | null;
  on_time_or_early_percent?: number | null;
};
type PipelineHealth = {
  data_status: DataStatus; last_run_status?: string | null; records_received?: number | null;
  records_rejected?: number | null;
};
const apiBase = import.meta.env.VITE_DASHBOARD_API_BASE_URL ?? "";
const number = (value?: number | null, digits = 0) => value == null ? "—" : value.toLocaleString(undefined, { maximumFractionDigits: digits });
const dateTime = (value?: string | null) => value ? new Date(value).toLocaleString() : "Not available";

function App() {
  const [overview, setOverview] = useState<NetworkOverview | null>(null);
  const [health, setHealth] = useState<PipelineHealth | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch(`${apiBase}/v1/dashboard/network-overview`).then((response) => response.ok ? response.json() : Promise.reject()),
      fetch(`${apiBase}/v1/dashboard/pipeline-health`).then((response) => response.ok ? response.json() : Promise.reject())
    ]).then(([network, pipeline]) => {
      setOverview(network as NetworkOverview);
      setHealth(pipeline as PipelineHealth);
    }).catch(() => setError("The dashboard API is unreachable. Start the local API or configure VITE_DASHBOARD_API_BASE_URL."));
  }, []);

  const status = overview?.data_status;
  const metrics: Metric[] = [
    { label: "Journeys analysed", value: number(overview?.journeys_analysed), detail: "Unique train-day journeys" },
    { label: "Stations", value: number(overview?.stations), detail: "Observed route stations" },
    { label: "Average arrival delay", value: overview?.average_arrival_delay_minutes == null ? "—" : `${number(overview.average_arrival_delay_minutes, 1)} min`, detail: "Across observed station stops" },
    { label: "On time or early", value: overview?.on_time_or_early_percent == null ? "—" : `${number(overview.on_time_or_early_percent, 1)}%`, detail: "Arrival delay at or below zero" }
  ];
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
        <article className="panel"><h2>Network overview</h2><p className="summary">Median arrival delay: <strong>{overview?.median_arrival_delay_minutes == null ? "—" : `${number(overview.median_arrival_delay_minutes, 1)} min`}</strong></p><p className="empty">The published source covers September 2024 historical observations only.</p></article>
        <article className="panel"><h2>Train punctuality</h2><p className="summary">Historical aggregate metrics are sourced from the validated Snowflake mart.</p><p className="empty">Train-level exploration is the next API enhancement.</p></article>
        <article className="panel"><h2>Delay prediction</h2><EmptyState text="Predictions appear only after chronological baseline/ML evaluation." /></article>
        <article className="panel"><h2>Pipeline health</h2><p className="summary">Latest run: <strong>{health?.last_run_status ?? "—"}</strong></p><p className="empty">Received {number(health?.records_received)} records; rejected {number(health?.records_rejected)}. Completed {dateTime(health?.data_status.last_successful_pipeline_at)}.</p></article>
      </section>

      <footer>This is an independent portfolio project and is not affiliated with Indian Railways, IRCTC, CRIS, or the Government of India.</footer>
    </main>
  );
}

function EmptyState({ text }: { text: string }) { return <p className="empty">{text}</p>; }

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
