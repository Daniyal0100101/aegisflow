import { ExecutionStep } from "../types";

interface WorkflowGraphProps {
  steps?: ExecutionStep[];
  isLoading: boolean;
}

export default function WorkflowGraph({ steps = [], isLoading }: WorkflowGraphProps) {
  const stepsDef = [
    { key: "PROPOSAL_GENERATION", index: 1, label: "Specialists Mobilized" },
    { key: "CRITIC_REVIEW", index: 2, label: "Safety Audited" },
    { key: "RESOLVE_CONSENSUS", index: 3, label: "Consensus Resolved" },
    { key: "STATE_MUTATION", index: 4, label: "State Delta Applied" },
  ];

  // Map steps to status
  const stepMap = steps.reduce<Record<string, ExecutionStep>>((acc, s) => {
    acc[s.node_name] = s;
    return acc;
  }, {});

  return (
    <div className="workflow-guided-bar">
      {stepsDef.map((step, idx) => {
        const execution = stepMap[step.key];
        let status = "pending";

        if (isLoading) {
          // Approximate active state based on steps generated so far
          const activeIndex = steps.length;
          if (idx < activeIndex) status = "completed";
          else if (idx === activeIndex) status = "active";
          else status = "pending";
        } else if (execution) {
          status = execution.status.toLowerCase();
        }

        const isLast = idx === stepsDef.length - 1;

        return (
          <div key={step.key} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div className={`workflow-guide-step ${status === "active" ? "active" : ""} ${status === "completed" ? "completed" : ""}`}>
              <span className="workflow-guide-bullet">{step.index}</span>
              <span>{step.label}</span>
            </div>
            {!isLast && <span className="workflow-guide-arrow">➜</span>}
          </div>
        );
      })}
    </div>
  );
}
