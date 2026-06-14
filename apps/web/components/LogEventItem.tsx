import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { EventSchema } from "../types";

interface LogEventItemProps {
  event: EventSchema;
}

export default function LogEventItem({ event }: LogEventItemProps) {
  const [showTrace, setShowTrace] = useState(false);
  
  const isSystem = event.role === "system";
  const isHuman = event.role === "human";

  const formattedTime = new Date(event.timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  if (isSystem) {
    return (
      <div className="event-row system" style={{ margin: "12px 0" }}>
        <div className="chat-bubble system">
          <div style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "12px" }}>
            <span style={{ color: "var(--text-muted)" }}>[SYS]</span>
            <span style={{ color: "var(--text-secondary)" }}>{event.content}</span>
            <span className="chat-time" style={{ fontSize: "9px" }}>{formattedTime}</span>
            {event.execution_steps && event.execution_steps.length > 0 && (
              <button 
                onClick={() => setShowTrace(!showTrace)}
                className="system-badge" 
                style={{ cursor: "pointer", border: "1px solid rgba(59, 130, 246, 0.4)", color: "#93c5fd" }}
              >
                {showTrace ? "Hide Engine Trace" : "View Engine Trace"}
              </button>
            )}
          </div>
          
          {/* Engine Trace Dropdown */}
          {showTrace && event.execution_steps && (
            <div style={{ 
              marginTop: "12px", 
              padding: "12px", 
              background: "rgba(0,0,0,0.3)", 
              border: "1px solid var(--border-light)", 
              borderRadius: "8px", 
              width: "100%",
              maxWidth: "500px",
              textAlign: "left"
            }}>
              <span className="stat-label" style={{ display: "block", marginBottom: "8px" }}>Pipeline Process Audit</span>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {event.execution_steps.map((step, idx) => (
                  <div key={idx} style={{ 
                    display: "flex", 
                    justifyContent: "between", 
                    alignItems: "center", 
                    fontSize: "11px", 
                    fontFamily: "var(--font-mono)",
                    borderBottom: "1px solid rgba(255,255,255,0.03)",
                    paddingBottom: "4px"
                  }}>
                    <span style={{ color: step.status === "completed" ? "var(--color-success)" : "var(--color-danger)" }}>
                      {step.status === "completed" ? "●" : "○"} {step.node_name}
                    </span>
                    <span style={{ color: "var(--text-muted)", marginLeft: "auto" }}>
                      {step.duration_ms ? `${step.duration_ms.toFixed(0)}ms` : "pending"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Determine card style based on role
  const roleClass = event.role;

  return (
    <div className={`event-row ${roleClass}`} style={{ margin: "16px 0" }}>
      <div className={`chat-bubble ${roleClass}`}>
        {/* Header containing name and timestamp */}
        <div className="chat-meta">
          <span>{event.display_name}</span>
          <span className="chat-time">{formattedTime}</span>
          {event.status === "revised" && (
            <span className="system-badge" style={{ borderColor: "rgba(245, 158, 11, 0.4)", color: "#fcd34d", marginLeft: "auto" }}>
              Revised Output
            </span>
          )}
        </div>

        {/* Content markdown */}
        <div className="chat-content">
          <ReactMarkdown
            allowedElements={["p", "ul", "ol", "li", "strong", "em", "code", "pre"]}
          >
            {event.content}
          </ReactMarkdown>
        </div>

        {/* Specialist Action proposal subcard */}
        {event.action_metadata && (
          <div className="eval-card">
            <div className="eval-card-header">
              <span>Evaluated Action Proposal</span>
              <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                <span className="system-badge">{event.action_metadata.urgency}</span>
                <span className="system-badge">{event.action_metadata.target_metric}</span>
                {event.state_change_summary && (
                  <span className={`eval-card-outcome ${
                    event.action_metadata.effect_label === "improving" ? "outcome-improved" :
                    event.action_metadata.effect_label === "worsening" ? "outcome-worsened" :
                    "outcome-unchanged"
                  }`}>
                    {event.action_metadata.effect_label === "improving" ? "Improved" :
                     event.action_metadata.effect_label === "worsening" ? "Worsened" :
                     "Unchanged"}
                  </span>
                )}
              </div>
            </div>
            <div className="eval-card-title">{event.action_metadata.recommended_action}</div>
            <div className="eval-card-reason">{event.action_metadata.short_reason}</div>
            {event.state_change_summary && (
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "10px", borderTop: "1px solid rgba(255,255,255,0.03)", paddingTop: "8px" }}>
                <span style={{ fontWeight: 600, color: "var(--text-secondary)" }}>State Update: </span>
                {event.state_change_summary}
              </div>
            )}
          </div>
        )}

        {/* Critic Review Report subcard */}
        {event.review_metadata && (
          <div className="eval-card">
            <div className="eval-card-header">
              <span>Critic Audit Log</span>
              <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                <span className={`eval-card-outcome ${
                  event.review_metadata.is_approved ? "outcome-improved" : "outcome-worsened"
                }`} style={{ textTransform: "uppercase" }}>
                  {event.review_metadata.is_approved ? "Approved" : "Flags Active"}
                </span>
                <span className="system-badge">Audit Score: {event.review_metadata.confidence_score}</span>
              </div>
            </div>
            
            {event.review_metadata.criticism && (
              <div className="eval-card-reason" style={{ color: "var(--text-primary)" }}>
                {event.review_metadata.criticism}
              </div>
            )}
            
            {event.review_metadata.suggested_modification && (
              <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "8px" }}>
                <span style={{ fontWeight: 600, color: "var(--text-muted)" }}>Suggested Modifier: </span>
                {event.review_metadata.suggested_modification}
              </div>
            )}

            {event.review_metadata.safety_flags.length > 0 && (
              <div style={{ marginTop: "10px", display: "flex", flexDirection: "column", gap: "4px" }}>
                {event.review_metadata.safety_flags.map((flag, idx) => (
                  <div key={idx} style={{ 
                    fontSize: "11px", 
                    color: "#f87171", 
                    background: "rgba(239, 68, 68, 0.1)", 
                    border: "1px solid rgba(239, 68, 68, 0.2)", 
                    padding: "4px 8px", 
                    borderRadius: "4px" 
                  }}>
                    ⚠ Warning: {flag}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
