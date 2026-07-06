"use client";

import { CheckCircle2, Plus } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { Input, Select } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { Table } from "@/components/ui/Table";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { FollowUp, Organization, PaginatedOrganizations, User } from "@/types/api";

export default function FollowUpsPage() {
  const { user } = useAuth();
  const [rows, setRows] = useState<FollowUp[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [statusFilter, setStatusFilter] = useState("OPEN");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", entity_id: "", due_date: "", assigned_to_user_id: "" });

  async function load() {
    setError(null);
    try {
      const [followUps, orgs, userRows] = await Promise.all([
        apiRequest<FollowUp[]>(`/api/v1/follow-ups?status=${statusFilter}&limit=200${includeArchived && user?.role === "ADMIN" ? "&include_archived=true" : ""}`),
        apiRequest<PaginatedOrganizations>("/api/v1/organizations?limit=200"),
        apiRequest<User[]>("/api/v1/admin/users?limit=200").catch(() => [])
      ]);
      setRows(followUps);
      setOrganizations(orgs.items);
      setUsers(userRows);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load follow-ups");
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, includeArchived]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await apiRequest<FollowUp>("/api/v1/follow-ups", {
      method: "POST",
      body: JSON.stringify({
        title: form.title,
        entity_type: "ORGANIZATION",
        entity_id: form.entity_id,
        due_date: form.due_date || null,
        assigned_to_user_id: form.assigned_to_user_id || null,
        status: "OPEN"
      })
    });
    setForm({ title: "", entity_id: "", due_date: "", assigned_to_user_id: "" });
    await load();
  }

  async function complete(id: string) {
    await apiRequest(`/api/v1/follow-ups/${id}/complete`, { method: "PATCH" });
    await load();
  }

  async function archive(id: string) {
    const reason = window.prompt("Archive this follow-up? Optional reason:");
    if (reason === null) return;
    await apiRequest(`/api/v1/follow-ups/${id}/archive`, {
      method: "PATCH",
      body: JSON.stringify({ reason })
    });
    await load();
  }

  return (
    <ProtectedPage>
      <PageHeader eyebrow="Tasks" title="Follow-ups" description="Operational tasks tied to CRM entities." />
      <SectionCard>
        <form className="form-stack" onSubmit={submit}>
          <div className="crm-toolbar">
            <Input required placeholder="Follow-up title" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
            <Select required value={form.entity_id} onChange={(event) => setForm({ ...form, entity_id: event.target.value })}>
              <option value="">Select organization</option>
              {organizations.map((organization) => (
                <option key={organization.id} value={organization.id}>{organization.name}</option>
              ))}
            </Select>
            <Input type="date" value={form.due_date} onChange={(event) => setForm({ ...form, due_date: event.target.value })} />
            <Select value={form.assigned_to_user_id} onChange={(event) => setForm({ ...form, assigned_to_user_id: event.target.value })}>
              <option value="">Unassigned</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>{user.full_name}</option>
              ))}
            </Select>
            <Button type="submit"><Plus size={16} /> Add</Button>
          </div>
        </form>
        {error ? <div className="alert alert--error">{error}</div> : null}
      </SectionCard>
      <SectionCard>
        <div className="section-heading section-heading--inline">
          <div>
            <h2>Tasks</h2>
            <p>{rows.length} follow-ups</p>
          </div>
          <Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="OPEN">Open</option>
            <option value="DONE">Done</option>
            <option value="CANCELLED">Cancelled</option>
          </Select>
          {user?.role === "ADMIN" ? (
            <Select value={includeArchived ? "true" : "false"} onChange={(event) => setIncludeArchived(event.target.value === "true")}>
              <option value="false">Hide archived</option>
              <option value="true">Show archived</option>
            </Select>
          ) : null}
        </div>
        <Table
          rows={rows}
          getRowKey={(row) => row.id}
          columns={[
            { key: "title", header: "Title", render: (row) => row.title },
            { key: "due", header: "Due", render: (row) => dueLabel(row) },
            { key: "status", header: "Status", render: (row) => <Badge tone={row.status === "DONE" ? "success" : "info"}>{row.status}</Badge> },
            {
              key: "action",
              header: "Action",
              render: (row) => (
                <div className="button-row">
                  {row.status === "OPEN" ? <Button variant="secondary" onClick={() => void complete(row.id)}><CheckCircle2 size={15} /> Complete</Button> : null}
                  {user?.role === "ADMIN" ? <Button variant="danger" onClick={() => void archive(row.id)}>Archive</Button> : null}
                </div>
              )
            }
          ]}
        />
      </SectionCard>
    </ProtectedPage>
  );
}

function dueLabel(row: FollowUp) {
  if (!row.due_date) return <span className="empty-value">—</span>;
  const overdue = row.status === "OPEN" && new Date(row.due_date) < new Date();
  return overdue ? <Badge tone="danger">Overdue {row.due_date}</Badge> : row.due_date;
}
