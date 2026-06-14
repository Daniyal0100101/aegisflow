import { useState } from "react";
import { PRESET_DIRECTIVES } from "../types";

interface OverridePanelProps {
  domain: string;
  onOverride: (directive: string) => void;
  isLoading: boolean;
}

export default function OverridePanel({ domain, onOverride, isLoading }: OverridePanelProps) {
  const [customDirective, setCustomDirective] = useState("");
  const trimmedDirective = customDirective.trim();

  const handleApply = (directive: string) => {
    onOverride(directive);
  };

  const presets = PRESET_DIRECTIVES[domain.toLowerCase()] || [];

  return (
    <div className="intervention-controls">
      <h3 className="sidebar-title" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span
          style={{
            width: "8px",
            height: "8px",
            background: "var(--color-danger)",
            borderRadius: "50%",
            animation: "spin 1s infinite alternate",
          }}
        ></span>
        Commander Override Console
      </h3>
      <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "-6px" }}>
        Inject direct instructions to force agents to re-run pipeline logs and adapt outcomes.
      </p>

      {/* Presets Grid */}
      {presets.length > 0 && (
        <div style={{ marginTop: "10px" }}>
          <span className="stat-label" style={{ display: "block", marginBottom: "8px" }}>
            Operational Presets
          </span>
          <div className="presets-container">
            {presets.map((directive) => (
              <button
                key={directive}
                disabled={isLoading}
                onClick={() => handleApply(directive)}
                className="preset-btn"
              >
                {directive}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Custom directive textarea */}
      <div className="custom-override-container" style={{ marginTop: "10px" }}>
        <span className="stat-label">Custom Action Directive</span>
        <textarea
          value={customDirective}
          disabled={isLoading}
          onChange={(e) => setCustomDirective(e.target.value)}
          placeholder="Input operational directives..."
          className="override-textarea"
        />
        <button
          disabled={isLoading || !trimmedDirective}
          onClick={() => {
            if (trimmedDirective) {
              handleApply(trimmedDirective);
              setCustomDirective("");
            }
          }}
          className="override-send-btn"
        >
          {isLoading ? "Executing Pipeline..." : "Transmit Action Command"}
        </button>
      </div>
    </div>
  );
}
