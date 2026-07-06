import { AlertTriangle } from "lucide-react";

import { Badge } from "@/components/ui/Badge";

type WarningSummaryProps = {
  bySeverity?: Record<string, number>;
  byCode?: Record<string, number>;
};

function severityTone(severity: string) {
  if (severity === "ERROR") return "danger" as const;
  if (severity === "WARNING") return "warning" as const;
  return "info" as const;
}

export function WarningSummary({ bySeverity = {}, byCode = {} }: WarningSummaryProps) {
  const codeEntries = Object.entries(byCode);

  return (
    <div className="warning-summary">
      <div className="summary-title">
        <AlertTriangle size={18} />
        <h3>Validation warnings</h3>
      </div>
      <div className="badge-row">
        {Object.entries(bySeverity).length ? (
          Object.entries(bySeverity).map(([severity, count]) => (
            <Badge key={severity} tone={severityTone(severity)}>
              {severity}: {count}
            </Badge>
          ))
        ) : (
          <Badge tone="success">No warnings reported</Badge>
        )}
      </div>
      {codeEntries.length ? (
        <div className="warning-code-grid">
          {codeEntries.map(([code, count]) => (
            <div key={code}>
              <span>{code}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
