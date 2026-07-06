"use client";

import { Activity, Search } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Input, Select } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { Table } from "@/components/ui/Table";
import { apiRequest } from "@/lib/api";
import type { CrmActivityEvent } from "@/types/api";

const entityTypes = [
  "ORGANIZATION",
  "CONTACT",
  "NOTE",
  "OPPORTUNITY",
  "FOLLOW_UP_ACTION",
  "EVENT",
  "PROGRAM_ACTIVITY",
  "AI_TOOL",
  "VENDOR",
  "USE_CASE_PROPOSAL",
  "ORGANIZATION_DOCUMENT",
  "OPPORTUNITY_DOCUMENT"
];

export default function AdminActivityPage() {
  const [rows, setRows] = useState<CrmActivityEvent[]>([]);
  const [filters, setFilters] = useState({ q: "", entity_type: "", action: "" });
  const [error, setError] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState(true);

  async function load() {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filters.q) params.set("q", filters.q);
      if (filters.entity_type) params.set("entity_type", filters.entity_type);
      if (filters.action) params.set("action", filters.action);
      params.set("limit", "200");
      setRows(await apiRequest<CrmActivityEvent[]>(`/api/v1/admin/activity?${params.toString()}`));
    } catch (caught) {
      setError(caught);
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
        title="CRM Activity"
        description="Business-relevant CRM actions for admins. Technical security events remain in Audit Logs."
      />

      <SectionCard>
        <form className="crm-toolbar" onSubmit={submit}>
          <Input
            placeholder="Search activity"
            value={filters.q}
            onChange={(event) => setFilters({ ...filters, q: event.target.value })}
          />
          <Select value={filters.entity_type} onChange={(event) => setFilters({ ...filters, entity_type: event.target.value })}>
            <option value="">All entities</option>
            {entityTypes.map((entityType) => (
              <option key={entityType} value={entityType}>
                {entityType.replaceAll("_", " ")}
              </option>
            ))}
          </Select>
          <Input
            placeholder="Action, e.g. ORGANIZATION_CREATED"
            value={filters.action}
            onChange={(event) => setFilters({ ...filters, action: event.target.value })}
          />
          <Button type="submit">
            <Search size={16} /> Search
          </Button>
        </form>
      </SectionCard>

      <SectionCard>
        <div className="section-heading section-heading--inline">
          <div>
            <h2>Latest CRM actions</h2>
            <p>{isLoading ? "Loading..." : `${rows.length} activity records`}</p>
          </div>
          <Activity size={22} />
        </div>

        {error ? <ErrorState title="Could not load CRM activity" error={error} onRetry={() => void load()} /> : null}
        {!error && !isLoading && !rows.length ? (
          <EmptyState title="No CRM activity yet" description="New startup, vendor, follow-up, note, PoC, event, and library changes will appear here." />
        ) : null}
        {!error && rows.length ? (
          <Table
            rows={rows}
            getRowKey={(row) => row.id}
            columns={[
              { key: "time", header: "Time", render: (row) => formatDate(row.created_at) },
              {
                key: "activity",
                header: "Activity",
                render: (row) => (
                  <div>
                    <strong>{row.title}</strong>
                    {row.summary ? <p className="record-subtitle">{row.summary}</p> : null}
                  </div>
                )
              },
              { key: "entity", header: "Entity", render: (row) => <Badge tone="info">{row.entity_type.replaceAll("_", " ")}</Badge> },
              { key: "action", header: "Action", render: (row) => row.action.replaceAll("_", " ") }
            ]}
          />
        ) : null}
      </SectionCard>
    </ProtectedPage>
  );
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}
