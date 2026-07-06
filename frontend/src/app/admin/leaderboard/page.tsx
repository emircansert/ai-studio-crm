"use client";

import { AlertTriangle, RotateCcw } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { Input, Select } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { apiRequest } from "@/lib/api";
import type { LeaderboardResetResponse, User } from "@/types/api";

export default function AdminLeaderboardPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [scope, setScope] = useState<"all" | "user">("all");
  const [userId, setUserId] = useState("");
  const [reason, setReason] = useState("");
  const [dryRunResult, setDryRunResult] = useState<LeaderboardResetResponse | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<User[]>("/api/v1/admin/users?limit=500")
      .then(setUsers)
      .catch(() => undefined);
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setDryRunResult(null);
    try {
      const result = await apiRequest<LeaderboardResetResponse>("/api/v1/admin/leaderboard/reset", {
        method: "POST",
        body: JSON.stringify({
          scope,
          user_id: scope === "user" ? userId : null,
          reason,
          dry_run: true
        })
      });
      setDryRunResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not run reset preview");
    }
  }

  async function applyReset() {
    if (!dryRunResult) return;
    const confirmed = window.confirm(
      `Reset ${dryRunResult.affected_count} leaderboard scoring records? This does not delete CRM records.`
    );
    if (!confirmed) return;
    setError(null);
    setNotice(null);
    try {
      const result = await apiRequest<LeaderboardResetResponse>("/api/v1/admin/leaderboard/reset", {
        method: "POST",
        body: JSON.stringify({
          scope,
          user_id: scope === "user" ? userId : null,
          reason,
          dry_run: false
        })
      });
      setNotice(
        `Leaderboard reset applied. ${result.affected_count} scoring records excluded or archived.`
      );
      setDryRunResult(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not apply reset");
    }
  }

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Admin"
        title="Leaderboard Management"
        description="Reset test leaderboard scores safely without deleting CRM records."
      />

      <div className="command-hero">
        <div>
          <h2>Safe scoring reset</h2>
          <p>
            This does not delete companies, notes, contacts, opportunities, events, follow-ups, or audit logs. It excludes
            CRM Activity Points and archives YZ Champion activity evidence so test-session scores stop counting.
          </p>
        </div>
        <Badge tone="warning">Dry run required</Badge>
      </div>

      <SectionCard>
        <div className="section-heading">
          <h2>Reset scope</h2>
          <p>Run a dry run first, review the affected count, then apply the reset if it is correct.</p>
        </div>
        <form className="form-stack" onSubmit={submit}>
          <div className="two-column">
            <Select label="Scope" value={scope} onChange={(event) => setScope(event.target.value as "all" | "user")}>
              <option value="all">All users</option>
              <option value="user">Selected user</option>
            </Select>
            {scope === "user" ? (
              <Select label="User" required value={userId} onChange={(event) => setUserId(event.target.value)}>
                <option value="">Select user</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.full_name} - {user.email}
                  </option>
                ))}
              </Select>
            ) : null}
          </div>
          <Input
            label="Reason"
            required
            placeholder="Example: Resetting demo/test contribution data before internal demo"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
          {error ? <div className="alert alert--error">{error}</div> : null}
          {notice ? <div className="alert alert--success">{notice}</div> : null}
          <Button type="submit" variant="secondary">
            <RotateCcw size={16} />
            Dry run reset
          </Button>
        </form>
      </SectionCard>

      {dryRunResult ? (
        <SectionCard>
          <div className="section-heading">
            <h2>Dry run result</h2>
            <p>{dryRunResult.affected_count} scoring records would be reset.</p>
          </div>
          <div className="placeholder-grid">
            <div>
              <strong>{dryRunResult.crm_activity_affected_count ?? 0}</strong>
              <p className="record-subtitle">CRM Activity Point records</p>
            </div>
            <div>
              <strong>{dryRunResult.champion_activity_affected_count ?? 0}</strong>
              <p className="record-subtitle">YZ Champion activity records</p>
            </div>
          </div>
          <div className="alert alert--warning">
            <AlertTriangle size={18} />
            Final reset changes leaderboard scoring only. CRM records and audit logs remain intact.
          </div>
          <Button variant="danger" disabled={!dryRunResult.affected_count} onClick={() => void applyReset()}>
            Apply reset
          </Button>
        </SectionCard>
      ) : null}
    </ProtectedPage>
  );
}
