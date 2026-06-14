import { SimulationState } from "../types";

interface MetricsPanelProps {
  state: SimulationState | null;
}

export default function MetricsPanel({ state }: MetricsPanelProps) {
  if (!state) {
    return (
      <div className="metrics-card">
        <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
          Awaiting simulation initialization to load telemetry dashboards...
        </p>
      </div>
    );
  }

  const { stability_score, risk_level, state_outcome, status_summary, metrics, interventions_done, pending_actions } = state;

  // Determine outcome pill colors
  const outcomeClass =
    state_outcome === "Improved"
      ? "outcome-improved"
      : state_outcome === "Worsened"
      ? "outcome-worsened"
      : "outcome-unchanged";

  const getMeterColorClass = () => {
    if (state_outcome === "Improved") return "stabil-improving";
    if (state_outcome === "Worsened") return "stabil-worsening";
    return "stabil-unchanged";
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Status Title & Outcome badge */}
      <div className="metrics-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
          <div>
            <span className="sidebar-title" style={{ fontSize: "9px" }}>Current Status Profile</span>
            <h4 style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-primary)", marginTop: "4px" }}>
              {status_summary}
            </h4>
          </div>
          <span className={`eval-card-outcome ${outcomeClass}`} style={{ whiteSpace: "nowrap" }}>
            {state_outcome}
          </span>
        </div>
      </div>

      {/* Stability Score Bar */}
      <div className="metrics-card">
        <div className="stability-header">
          <span className="stat-label">System Stability</span>
          <span style={{ fontSize: "15px", fontWeight: 700, fontFamily: "var(--font-mono)" }}>
            {stability_score}/100
          </span>
        </div>
        <div className="stability-meter-bg">
          <div
            className={`stability-meter-fill ${getMeterColorClass()}`}
            style={{ width: `${stability_score}%` }}
          ></div>
        </div>
      </div>

      {/* Numerical Stats Grid based on domain */}
      <div className="metrics-card">
        <span className="stat-label">Real-Time Telemetry</span>
        <div className="stats-grid">
          {/* Risk Level is domain-agnostic */}
          <div className="stat-box">
            <span className="stat-label">Risk Severity</span>
            <span className={`stat-value ${risk_level.toLowerCase()}`}>{risk_level}</span>
          </div>

          {/* Domain Specific stats */}
          {state.domain === "clinical" && (
            <>
              <div className="stat-box">
                <span className="stat-label">Heart Rate</span>
                <span className="stat-value">{metrics.heart_rate || "—"} bpm</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">SpO2</span>
                <span className="stat-value">{metrics.oxygen_saturation || "—"}%</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Blood Pressure</span>
                <span className="stat-value">{metrics.blood_pressure || "—"}</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Pain Level</span>
                <span className="stat-value">{metrics.pain_level || "0"}/10</span>
              </div>
            </>
          )}

          {state.domain === "disaster" && (
            <>
              <div className="stat-box">
                <span className="stat-label">Vapor Plume density</span>
                <span className="stat-value">{metrics.hazmat_ppm || "—"} ppm</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Plume Containment</span>
                <span className="stat-value">{metrics.containment_rate || "0"}%</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Evacuation Rate</span>
                <span className="stat-value">{metrics.evacuation_percentage || "0"}%</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Casualties Reported</span>
                <span className="stat-value">{metrics.injured_count || "0"}</span>
              </div>
            </>
          )}

          {state.domain === "logistics" && (
            <>
              <div className="stat-box">
                <span className="stat-label">Cargo Backlog</span>
                <span className="stat-value">{metrics.backlog_units || "—"} units</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Transit Delay</span>
                <span className="stat-value">{metrics.routing_delay_hrs || "0"} hrs</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Backup Saturation</span>
                <span className="stat-value">{metrics.warehouse_capacity_percentage || "0"}%</span>
              </div>
              <div className="stat-box">
                <span className="stat-label">Idle Ships</span>
                <span className="stat-value">{metrics.idle_vessels || "0"} vessels</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Applied Interventions List */}
      <div className="metrics-card">
        <span className="stat-label">Applied Decisions Log</span>
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {interventions_done.length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: "12px" }}>No active decisions committed.</p>
          ) : (
            interventions_done.map((item, idx) => (
              <div key={idx} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px" }}>
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span style={{ color: "var(--text-secondary)" }}>{item}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Pending Actions list */}
      <div className="metrics-card">
        <span className="stat-label">Pending Action Items</span>
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {pending_actions.map((item, idx) => (
            <div key={idx} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px" }}>
              <span style={{ color: "var(--color-warning)" }}>⚠</span>
              <span style={{ color: "var(--text-secondary)" }}>{item}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
