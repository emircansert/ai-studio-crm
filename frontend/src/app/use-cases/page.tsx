"use client";

import { Archive, Plus, RotateCcw } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Input, Select } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { Table } from "@/components/ui/Table";
import { apiRequest } from "@/lib/api";
import type { UseCaseProposal, UseCasesResponse } from "@/types/api";

type UseCaseForm = {
  title: string;
  business_unit_text: string;
  status: string;
  stage: string;
  priority: string;
  description: string;
  problem_area: string;
  proposed_solution: string;
  expected_impact: string;
};

const initialForm: UseCaseForm = {
  title: "",
  business_unit_text: "",
  status: "IDEA",
  stage: "IDEA",
  priority: "MEDIUM",
  description: "",
  problem_area: "",
  proposed_solution: "",
  expected_impact: ""
};

export default function UseCasesPage() {
  const [items, setItems] = useState<UseCaseProposal[]>([]);
  const [form, setForm] = useState<UseCaseForm>(initialForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function load() {
    setError(null);
    try {
      const data = await apiRequest<UseCasesResponse>("/use-cases?limit=200");
      setItems(data.items);
    } catch (caught) {
      setError(caught);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function updateForm(partial: Partial<UseCaseForm>) {
    setForm((current) => ({ ...current, ...partial }));
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    const payload = {
      ...form,
      description: form.description || null,
      business_unit_text: form.business_unit_text || null,
      problem_area: form.problem_area || null,
      proposed_solution: form.proposed_solution || null,
      expected_impact: form.expected_impact || null
    };
    try {
      if (editingId) {
        await apiRequest<UseCaseProposal>(`/use-cases/${editingId}`, {
          method: "PUT",
          body: JSON.stringify(payload)
        });
      } else {
        await apiRequest<UseCaseProposal>("/use-cases", {
          method: "POST",
          body: JSON.stringify(payload)
        });
      }
      setEditingId(null);
      setForm(initialForm);
      await load();
    } catch (caught) {
      setError(caught);
    } finally {
      setIsSaving(false);
    }
  }

  function edit(row: UseCaseProposal) {
    setEditingId(row.id);
    setForm({
      title: row.title,
      business_unit_text: row.business_unit_text ?? "",
      status: row.status,
      stage: row.stage,
      priority: row.priority,
      description: row.description ?? "",
      problem_area: row.problem_area ?? "",
      proposed_solution: row.proposed_solution ?? "",
      expected_impact: row.expected_impact ?? ""
    });
  }

  async function toggleArchive(row: UseCaseProposal) {
    setError(null);
    try {
      await apiRequest<UseCaseProposal>(`/use-cases/${row.id}/${row.is_archived ? "unarchive" : "archive"}`, {
        method: "PATCH",
        body: JSON.stringify({ reason: row.is_archived ? "Restored from Use Cases page" : "Archived from Use Cases page" })
      });
      await load();
    } catch (caught) {
      setError(caught);
    }
  }

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="YZ Champion Program"
        title="Use Case & Project Development"
        description="Create and projectize AI use-case proposals. These records feed the official YZ Champion Score while also preserving CRM Activity Points."
        actions={<Badge tone="info">Use-case Onerisi ve Projelendirme</Badge>}
      />

      {error ? <ErrorState title="Could not load use cases" error={error} onRetry={() => void load()} /> : null}

      <div className="two-column">
        <SectionCard>
          <div className="section-heading">
            <h2>{editingId ? "Edit use case" : "Add use case"}</h2>
            <p>Creating a use case contributes to Use Case & Project Development. Moving it to PROJECTIZED adds projectization evidence.</p>
          </div>
          <form className="form-grid" onSubmit={(event) => void save(event)}>
            <Input label="Title" value={form.title} onChange={(event) => updateForm({ title: event.target.value })} required />
            <Input label="Business unit" value={form.business_unit_text} onChange={(event) => updateForm({ business_unit_text: event.target.value })} />
            <Select label="Status" value={form.status} onChange={(event) => updateForm({ status: event.target.value })}>
              {["IDEA", "UNDER_REVIEW", "PROJECTIZED", "REJECTED", "ON_HOLD"].map((value) => <option key={value}>{value}</option>)}
            </Select>
            <Select label="Stage" value={form.stage} onChange={(event) => updateForm({ stage: event.target.value })}>
              {["IDEA", "UNDER_REVIEW", "PROJECTIZED", "REJECTED", "ON_HOLD"].map((value) => <option key={value}>{value}</option>)}
            </Select>
            <Select label="Priority" value={form.priority} onChange={(event) => updateForm({ priority: event.target.value })}>
              {["LOW", "MEDIUM", "HIGH"].map((value) => <option key={value}>{value}</option>)}
            </Select>
            <label className="field form-grid__full">
              <span>Description</span>
              <textarea className="input textarea" rows={3} value={form.description} onChange={(event) => updateForm({ description: event.target.value })} />
            </label>
            <label className="field form-grid__full">
              <span>Problem area</span>
              <textarea className="input textarea" rows={3} value={form.problem_area} onChange={(event) => updateForm({ problem_area: event.target.value })} />
            </label>
            <label className="field form-grid__full">
              <span>Proposed solution</span>
              <textarea className="input textarea" rows={3} value={form.proposed_solution} onChange={(event) => updateForm({ proposed_solution: event.target.value })} />
            </label>
            <label className="field form-grid__full">
              <span>Expected impact</span>
              <textarea className="input textarea" rows={3} value={form.expected_impact} onChange={(event) => updateForm({ expected_impact: event.target.value })} />
            </label>
            <div className="button-row form-grid__full">
              <button className="button button--primary" disabled={isSaving} type="submit">
                <Plus size={17} />
                {isSaving ? "Saving..." : editingId ? "Save use case" : "Add use case"}
              </button>
              {editingId ? <button className="button button--secondary" type="button" onClick={() => { setEditingId(null); setForm(initialForm); }}>Cancel</button> : null}
            </div>
          </form>
        </SectionCard>

        <SectionCard>
          <div className="section-heading">
            <h2>Score impact</h2>
            <p>Target logic is calculated by the system.</p>
          </div>
          <div className="candidate-count-grid">
            <div className="mini-stat"><span>0 projects</span><strong>0</strong></div>
            <div className="mini-stat"><span>1 project</span><strong>50</strong></div>
            <div className="mini-stat"><span>2+ projects</span><strong>100</strong></div>
          </div>
          <div className="phase-note">This category carries 40% of the YZ Champion Score.</div>
        </SectionCard>
      </div>

      <SectionCard>
        <div className="section-heading section-heading--inline">
          <div>
            <h2>Use cases</h2>
            <p>{items.length} records</p>
          </div>
          <Badge tone="success">Feeds Champion Score</Badge>
        </div>
        {items.length ? (
          <Table
            rows={items}
            getRowKey={(row) => row.id}
            columns={[
              { key: "title", header: "Use Case", render: (row) => <div className="record-title"><strong>{row.title}</strong><span className="record-subtitle">{row.business_unit_text || "-"}</span></div> },
              { key: "status", header: "Status", render: (row) => <Badge>{row.status}</Badge> },
              { key: "stage", header: "Stage", render: (row) => <Badge tone={row.stage === "PROJECTIZED" ? "success" : "neutral"}>{row.stage}</Badge> },
              { key: "priority", header: "Priority", render: (row) => row.priority },
              { key: "proposer", header: "Proposer", render: (row) => row.proposer_user?.full_name ?? "-" },
              { key: "created", header: "Created", render: (row) => formatDate(row.created_at) },
              {
                key: "actions",
                header: "Actions",
                render: (row) => (
                  <div className="button-row">
                    <button className="button button--secondary" type="button" onClick={() => edit(row)}>Edit</button>
                    <button className="button button--ghost" type="button" onClick={() => void toggleArchive(row)}>
                      {row.is_archived ? <RotateCcw size={16} /> : <Archive size={16} />}
                      {row.is_archived ? "Restore" : "Archive"}
                    </button>
                  </div>
                )
              }
            ]}
          />
        ) : (
          <EmptyState title="No use cases yet" description="Add a use case proposal to begin tracking project development evidence." />
        )}
      </SectionCard>
    </ProtectedPage>
  );
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}
