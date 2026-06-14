"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "../lib/api";
import { EventSchema, SimulationState, SessionSnapshot } from "../types";
import WorkflowGraph from "../components/WorkflowGraph";
import MetricsPanel from "../components/MetricsPanel";
import OverridePanel from "../components/OverridePanel";
import LogEventItem from "../components/LogEventItem";

export default function OperationsDashboard() {
  const [domain, setDomain] = useState<string>("clinical");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [scenarioName, setScenarioName] = useState<string>("");
  const [caseData, setCaseData] = useState<Record<string, any>>({});
  const [events, setEvents] = useState<EventSchema[]>([]);
  const [simulationState, setSimulationState] = useState<SimulationState | null>(null);
  const [activeDirective, setActiveDirective] = useState<string | null>(null);
  
  const [isOffline, setIsOffline] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const scrollRef = useRef<HTMLDivElement>(null);

  // Check backend availability
  const checkConnection = async () => {
    const reachable = await api.isBackendReachable();
    setIsOffline(!reachable);
    if (!reachable) {
      setErrorMsg("Operational Server offline. Verify python apps/api/main.py is running on port 8000.");
    } else {
      setErrorMsg(null);
    }
  };

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 10000);
    return () => clearInterval(interval);
  }, []);

  // Scroll to bottom when events update
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events, isLoading]);

  // Start a new session
  const handleStart = async (selectedDomain = domain) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res: SessionSnapshot = await api.startSession(selectedDomain);
      setSessionId(res.session_id);
      setDomain(res.domain);
      setScenarioName(res.scenario_name);
      setCaseData(res.case_data);
      setEvents(res.events);
      setSimulationState(res.simulation_state);
      setActiveDirective(res.active_directive);
    } catch (e) {
      console.error(e);
      setErrorMsg(e instanceof Error ? e.message : "Failed to initialize simulation session.");
    } finally {
      setIsLoading(false);
    }
  };

  // Switch domains
  const handleDomainChange = (newDomain: string) => {
    setDomain(newDomain);
    // If a session was active, reset it and launch new scenario
    if (sessionId) {
      setSessionId(null);
      setEvents([]);
      setSimulationState(null);
      handleStart(newDomain);
    }
  };

  // Submit Commander Override
  const handleOverride = async (directive: string) => {
    if (!sessionId) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res: SessionSnapshot = await api.applyOverride(sessionId, directive);
      setEvents(res.events);
      setSimulationState(res.simulation_state);
      setActiveDirective(res.active_directive);
    } catch (e) {
      console.error(e);
      setErrorMsg(e instanceof Error ? e.message : "Failed to transmit override command.");
    } finally {
      setIsLoading(false);
    }
  };

  // Get active step nodes from latest system_event
  const getActiveSteps = () => {
    const sysEvents = events.filter(e => e.role === "system" && e.execution_steps);
    if (sysEvents.length > 0) {
      return sysEvents[sysEvents.length - 1].execution_steps;
    }
    return undefined;
  };

  return (
    <div className="app-container">
      {/* Top Header Bar */}
      <header className="control-header">
        <div className="brand-section">
          <div className="brand-logo"></div>
          <h1 className="brand-name">
            AEGISFLOW <span style={{ fontSize: "10px", color: "var(--text-muted)", letterSpacing: "0.2em", fontWeight: 400 }}>CONTROL ROOM</span>
          </h1>
        </div>

        {/* Dynamic Domain Selection Tab array */}
        <div className="domain-tabs">
          <button 
            onClick={() => handleDomainChange("clinical")}
            className={`domain-tab ${domain === "clinical" ? "active" : ""}`}
          >
            Clinical Coordination
          </button>
          <button 
            onClick={() => handleDomainChange("disaster")}
            className={`domain-tab ${domain === "disaster" ? "active" : ""}`}
          >
            Disaster Mitigation
          </button>
          <button 
            onClick={() => handleDomainChange("logistics")}
            className={`domain-tab ${domain === "logistics" ? "active" : ""}`}
          >
            Supply Chain Logistics
          </button>
        </div>

        {/* Server Connection status */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {isOffline ? (
            <span style={{ color: "var(--color-danger)", fontSize: "11px", fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
              <span className="spinner" style={{ borderTopColor: "var(--color-danger)", width: "10px", height: "10px" }}></span>
              SERVER OFFLINE
            </span>
          ) : (
            <span style={{ color: "var(--color-success)", fontSize: "11px", fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ width: "6px", height: "6px", background: "var(--color-success)", borderRadius: "50%" }}></span>
              SYS OPERATIONAL
            </span>
          )}
          {sessionId && (
            <span className="system-badge" style={{ fontSize: "10px" }}>
              NODE_ID: {sessionId.substring(0, 8).toUpperCase()}
            </span>
          )}
        </div>
      </header>

      {/* Main Sandbox Layout Frame */}
      <div className="control-room">
        {!sessionId ? (
          /* EMPTY/INITIALIZATION STATE */
          <div className="empty-state">
            <h2 className="empty-title">Multi-Agent Decision Simulator</h2>
            <p className="empty-desc">
              AegisFlow resolves operational bottlenecks across complex domains. Leverage specialists, validation critics, and custom commanders to simulate and trace state impacts.
            </p>

            {errorMsg && (
              <div style={{ 
                background: "rgba(244, 63, 94, 0.1)", 
                border: "1px solid rgba(244, 63, 94, 0.2)", 
                color: "#f87171", 
                padding: "12px 18px", 
                borderRadius: "var(--radius-lg)", 
                fontSize: "13px",
                width: "100%"
              }}>
                {errorMsg}
              </div>
            )}

            {/* Interactive Domain Presentation Cards */}
            <div style={{ 
              display: "grid", 
              gridTemplateColumns: "repeat(3, 1fr)", 
              gap: "16px", 
              width: "100%", 
              maxWidth: "800px", 
              margin: "20px 0",
              textAlign: "left"
            }}>
              <div 
                onClick={() => setDomain("clinical")}
                style={{ 
                  background: domain === "clinical" ? "var(--bg-surface-solid)" : "var(--bg-surface)",
                  border: domain === "clinical" ? "1px solid var(--border-active)" : "1px solid var(--border-light)",
                  borderRadius: "var(--radius-lg)",
                  padding: "20px",
                  cursor: "pointer",
                  transition: "var(--transition-fast)"
                }}
              >
                <h4 style={{ color: "var(--text-primary)", fontSize: "14px", fontWeight: 700 }}>Clinical Coordination</h4>
                <p style={{ color: "var(--text-secondary)", fontSize: "12px", marginTop: "8px", lineHeight: "1.5" }}>
                  Cardiologist and Pharmacist check critical STEMI cardiac cases. Audited for safety contraindications.
                </p>
              </div>

              <div 
                onClick={() => setDomain("disaster")}
                style={{ 
                  background: domain === "disaster" ? "var(--bg-surface-solid)" : "var(--bg-surface)",
                  border: domain === "disaster" ? "1px solid var(--border-active)" : "1px solid var(--border-light)",
                  borderRadius: "var(--radius-lg)",
                  padding: "20px",
                  cursor: "pointer",
                  transition: "var(--transition-fast)"
                }}
              >
                <h4 style={{ color: "var(--text-primary)", fontSize: "14px", fontWeight: 700 }}>Disaster Mitigation</h4>
                <p style={{ color: "var(--text-secondary)", fontSize: "12px", marginTop: "8px", lineHeight: "1.5" }}>
                  Hazmat Engineer and Evacuation Captain contain gas leakage plumes. Audited for safety paths.
                </p>
              </div>

              <div 
                onClick={() => setDomain("logistics")}
                style={{ 
                  background: domain === "logistics" ? "var(--bg-surface-solid)" : "var(--bg-surface)",
                  border: domain === "logistics" ? "1px solid var(--border-active)" : "1px solid var(--border-light)",
                  borderRadius: "var(--radius-lg)",
                  padding: "20px",
                  cursor: "pointer",
                  transition: "var(--transition-fast)"
                }}
              >
                <h4 style={{ color: "var(--text-primary)", fontSize: "14px", fontWeight: 700 }}>Supply Chain Logistics</h4>
                <p style={{ color: "var(--text-secondary)", fontSize: "12px", marginTop: "8px", lineHeight: "1.5" }}>
                  Route and Inventory Specialists reroute vessels on terminal lockdown. Audited for capacity caps.
                </p>
              </div>
            </div>

            <button 
              onClick={() => handleStart()}
              disabled={isLoading || isOffline}
              className="start-btn"
            >
              {isLoading ? "Starting Simulation Node..." : "Initialize Simulation Node"}
            </button>
          </div>
        ) : (
          /* ACTIVE CONTROL ROOM DASHBOARD */
          <div className="dashboard-content" style={{ flexDirection: "column" }}>
            {/* Horizontal workflow steps guide */}
            <WorkflowGraph steps={getActiveSteps()} isLoading={isLoading} />

            <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
              {/* Column 1: Center Timeline Event Transcript Logs */}
              <div className="timeline-viewport" ref={scrollRef}>
                {errorMsg && (
                  <div style={{ 
                    background: "rgba(244, 63, 94, 0.1)", 
                    border: "1px solid rgba(244, 63, 94, 0.2)", 
                    color: "#f87171", 
                    padding: "12px 18px", 
                    borderRadius: "var(--radius-md)", 
                    fontSize: "13px"
                  }}>
                    {errorMsg}
                  </div>
                )}

                {/* Case Metadata Bar */}
                <div className="chat-bubble system" style={{ maxWidth: "100%", width: "100%", borderRadius: "var(--radius-md)", borderStyle: "dashed" }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--border-light)", paddingBottom: "6px" }}>
                      <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>{scenarioName}</span>
                      <span style={{ color: "var(--text-muted)" }}>Domain Case Files</span>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px" }}>
                      {Object.entries(caseData).slice(0, 8).map(([key, val]) => (
                        <div key={key} style={{ display: "flex", flexDirection: "column" }}>
                          <span style={{ fontSize: "9px", textTransform: "uppercase", color: "var(--text-muted)" }}>
                            {key.replace("_", " ")}
                          </span>
                          <span style={{ color: "var(--text-secondary)", fontWeight: 500 }}>
                            {String(val)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Timeline Log Events */}
                {events.map((evt) => (
                  <LogEventItem key={evt.id} event={evt} />
                ))}

                {/* Dynamic Loading bubbles */}
                {isLoading && (
                  <div className="loading-container">
                    <span className="spinner"></span>
                    <span style={{ fontSize: "12px", color: "var(--text-secondary)", fontWeight: 500, fontFamily: "var(--font-mono)" }}>
                      Resolving Agent Orchestration Pipeline...
                    </span>
                  </div>
                )}
              </div>

              {/* Column 2: Right Sidebar - Telemetry Panel & Overrides */}
              <aside className="operations-sidebar">
                <div className="operations-sidebar-content">
                  <MetricsPanel state={simulationState} />
                </div>
                <OverridePanel 
                  domain={domain}
                  onOverride={handleOverride}
                  isLoading={isLoading}
                />
              </aside>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
