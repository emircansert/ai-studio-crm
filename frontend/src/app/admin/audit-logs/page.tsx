"use client";

import { RefreshCw } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { Input, Select } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { Table } from "@/components/ui/Table";
import { apiRequest } from "@/lib/api";
import type { AuditLog } from "@/types/api";

export default function AuditLogsPage() {
  const [rows, setRows] = useState<AuditLog[]>([]);
  const [filters, setFilters] = useState({ action: "", entity_type: "", actor_user_id: "" });
  const [expanded, setExpanded] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  async function load() {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams(clean(filters));
      params.set("limit", "200");
      setRows(await apiRequest<AuditLog[]>(`/api/v1/admin/audit-logs?${params.toString()}`));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load audit logs");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void load();
  }

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Admin"
        title="Audit Logs"
        description="Accountability trail for imports, user administration, CRM edits, branding, and operational actions."
        actions={
          <Button variant="secondary" onClick={() => void load()}>
            <RefreshCw size={16} />
            Refresh
          </Button>
        }
      />
      <SectionCard>
        <form className="crm-toolbar" onSubmit={submit}>
          <Input placeholder="Action, e.g. ORGANIZATION_UPDATED" value={filters.action} onChange={(event) => setFilters({ ...filters, action: event.target.value })} />
          <Select value={filters.entity_type} onChange={(event) => setFilters({ ...filters, entity_type: event.target.value })}>
            <option value="">Any entity</option>
            {["ORGANIZATION", "USER", "IMPORT_BATCH", "FOLLOW_UP_ACTION", "OPPORTUNITY", "EVENT", "BRANDING_ASSET"].map((entity) => (
              <option key={entity} value={entity}>{entity}</option>
            ))}
          </Select>
          <Input placeholder="Actor user id" value={filters.actor_user_id} onChange={(event) => setFilters({ ...filters, actor_user_id: event.target.value })} />
          <Button type="submit">Filter logs</Button>
        </form>
        {error ? <div className="alert alert--error">{error}</div> : null}
      </SectionCard>
      <SectionCard>
        <div className="section-heading section-heading--inline">
          <div>
            <h2>Activity trail</h2>
            <p>{isLoading ? "Loading..." : `${rows.length} most recent entries`}</p>
          </div>
          <Badge tone="info">Admin only</Badge>
        </div>
        <Table
          rows={rows}
          getRowKey={(row) => row.id}
          columns={[
            { key: "time", header: "Time", render: (row) => formatDate(row.created_at) },
            { key: "action", header: "Action", render: (row) => <Badge tone="info">{row.action}</Badge> },
            { key: "entity", header: "Entity", render: (row) => `${row.entity_type}${row.entity_id ? ` / ${row.entity_id.slice(0, 8)}` : ""}` },
            { key: "actor", header: "Actor", render: (row) => row.actor_user_id?.slice(0, 8) ?? "System" },
            {
              key: "payload",
              header: "Payload",
              render: (row) => (
                <div className="record-title">
                  <button className="link-button" type="button" onClick={() => setExpanded(expanded === row.id ? null : row.id)}>
                    {expanded === row.id ? "Hide details" : "Show details"}
                  </button>
                  {expanded === row.id ? (
                    <pre className="json-preview">{JSON.stringify({ before: row.before_data, after: row.after_data }, null, 2)}</pre>
                  ) : null}
                </div>
              )
            }
          ]}
        />
      </SectionCard>
    </ProtectedPage>
  );
}

function clean(values: Record<string, string>) {
  return Object.fromEntries(Object.entries(values).filter(([, value]) => value !== ""));
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}
