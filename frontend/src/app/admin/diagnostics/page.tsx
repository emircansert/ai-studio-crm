"use client";

import { RefreshCw } from "lucide-react";
import { useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { API_BASE_URL, apiRequest } from "@/lib/api";

type CheckResult = {
  name: string;
  path: string;
  status: "idle" | "pass" | "fail";
  detail?: string;
};

const checks: CheckResult[] = [
  { name: "Health", path: "/api/v1/health", status: "idle" },
  { name: "Readiness", path: "/api/v1/health/readiness", status: "idle" },
  { name: "Dashboard summary", path: "/api/v1/dashboard/summary", status: "idle" }
];

export default function DiagnosticsPage() {
  const [results, setResults] = useState<CheckResult[]>(checks);
  const [isRunning, setIsRunning] = useState(false);

  async function runChecks() {
    setIsRunning(true);
    const nextResults: CheckResult[] = [];

    for (const check of checks) {
      try {
        await apiRequest<unknown>(check.path);
        nextResults.push({ ...check, status: "pass", detail: "Request succeeded through the Next.js proxy." });
      } catch (caught) {
        nextResults.push({
          ...check,
          status: "fail",
          detail: caught instanceof Error ? caught.message : "Request failed"
        });
      }
    }

    setResults(nextResults);
    setIsRunning(false);
  }

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Admin"
        title="Diagnostics"
        description="Validate frontend-to-backend connectivity through the same-origin application route."
        actions={
          <Button disabled={isRunning} onClick={() => void runChecks()}>
            <RefreshCw size={17} />
            {isRunning ? "Checking..." : "Run checks"}
          </Button>
        }
      />

      <SectionCard>
        <div className="section-heading">
          <h2>Proxy configuration</h2>
          <p>
            Browser requests use <strong>{API_BASE_URL}</strong>, and the application forwards them to the FastAPI
            backend.
          </p>
        </div>
        <div className="metric-grid">
          {results.map((result) => (
            <div className="stat-card" key={result.path}>
              <span>{result.name}</span>
              <strong>
                <Badge tone={result.status === "pass" ? "success" : result.status === "fail" ? "danger" : "neutral"}>
                  {result.status.toUpperCase()}
                </Badge>
              </strong>
              <p>{result.detail ?? result.path}</p>
            </div>
          ))}
        </div>
      </SectionCard>
    </ProtectedPage>
  );
}
