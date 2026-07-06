"use client";

import { Archive, Plus, RotateCcw, Save, Search } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

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
import { useAuth } from "@/lib/auth";
import type { AITool } from "@/types/api";

const categories = [
  "GenAI",
  "Data & Analytics",
  "Automation",
  "Computer Vision",
  "Sales & Marketing",
  "HR & Learning",
  "Legal & Compliance",
  "Cybersecurity",
  "Productivity",
  "Industry-specific",
  "Other"
];

const pricingModels = ["Free", "Freemium", "Paid", "Enterprise", "Unknown"];
const deploymentTypes = ["SaaS", "API", "On-premise", "Open-source", "Hybrid", "Unknown"];
const sensitivityLevels = ["Low", "Medium", "High", "Unknown"];
const statuses = ["Identified", "Under Review", "Tested", "Approved", "Rejected", "Archived"];

type ToolForm = {
  name: string;
  vendor_name: string;
  website_url: string;
  category_text: string;
  primary_use_case: string;
  description: string;
  pricing_model: string;
  deployment_type: string;
  data_sensitivity_level: string;
  status: string;
  owner_notes: string;
};

const initialForm: ToolForm = {
  name: "",
  vendor_name: "",
  website_url: "",
  category_text: "GenAI",
  primary_use_case: "",
  description: "",
  pricing_model: "Unknown",
  deployment_type: "Unknown",
  data_sensitivity_level: "Unknown",
  status: "Identified",
  owner_notes: ""
};

export default function AIToolsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";
  const [items, setItems] = useState<AITool[]>([]);
  const [selected, setSelected] = useState<AITool | null>(null);
  const [form, setForm] = useState<ToolForm>(initialForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    q: "",
    category: "",
    status: "",
    deployment_type: "",
    pricing_model: "",
    include_archived: "false"
  });
  const [error, setError] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  async function load() {
    setIsLoading(true);
    setError(null);
    const params = new URLSearchParams();
    params.set("limit", "200");
    if (filters.q) params.set("q", filters.q);
    if (filters.category) params.set("category", filters.category);
    if (filters.status) params.set("status", filters.status);
    if (filters.deployment_type) params.set("deployment_type", filters.deployment_type);
    if (filters.pricing_model) params.set("pricing_model", filters.pricing_model);
    if (isAdmin && filters.include_archived === "true") params.set("include_archived", "true");
    try {
      const data = await apiRequest<AITool[]>(`/ai-tools?${params.toString()}`);
      setItems(data);
    } catch (caught) {
      setError(caught);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.include_archived]);

  function updateForm(partial: Partial<ToolForm>) {
    setForm((current) => ({ ...current, ...partial }));
  }

  function startEdit(tool: AITool) {
    setSelected(tool);
    setEditingId(tool.id);
    setForm({
      name: tool.name,
      vendor_name: tool.vendor_name ?? "",
      website_url: tool.website_url ?? "",
      category_text: tool.category_text ?? "Other",
      primary_use_case: tool.primary_use_case ?? "",
      description: tool.description ?? tool.solution_summary ?? "",
      pricing_model: tool.pricing_model ?? "Unknown",
      deployment_type: tool.deployment_type ?? "Unknown",
      data_sensitivity_level: tool.data_sensitivity_level ?? "Unknown",
      status: tool.status ?? "Identified",
      owner_notes: tool.owner_notes ?? tool.notes ?? ""
    });
  }

  function resetForm() {
    setEditingId(null);
    setSelected(null);
    setForm(initialForm);
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    const payload = cleanPayload({
      ...form,
      solution_summary: form.primary_use_case || form.description,
      notes: form.owner_notes,
      source: "MANUAL"
    });
    try {
      if (editingId) {
        await apiRequest<AITool>(`/ai-tools/${editingId}`, {
          method: "PUT",
          body: JSON.stringify(payload)
        });
      } else {
        await apiRequest<AITool>("/ai-tools", {
          method: "POST",
          body: JSON.stringify(payload)
        });
      }
      resetForm();
      await load();
    } catch (caught) {
      setError(caught);
    } finally {
      setIsSaving(false);
    }
  }

  async function toggleArchive(tool: AITool) {
    setError(null);
    try {
      const action = tool.is_archived ? "unarchive" : "archive";
      await apiRequest<AITool>(`/ai-tools/${tool.id}/${action}`, {
        method: "PATCH",
        body: JSON.stringify({ reason: tool.is_archived ? "Restored from AI Tools Library" : "Archived from AI Tools Library" })
      });
      await load();
      if (selected?.id === tool.id) {
        setSelected(null);
      }
    } catch (caught) {
      setError(caught);
    }
  }

  const approvedCount = useMemo(() => items.filter((item) => item.status === "Approved").length, [items]);

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Tools"
        title="AI Tools Library"
        description="Catalog internal and external AI tools, vendors, use cases, and evaluation notes."
        actions={<Badge tone="success">Feeds Ecosystem Library Contribution</Badge>}
      />

      <div className="command-hero">
        <div>
          <h2>Tool intelligence workspace</h2>
          <p>
            Track tools by vendor, use case, deployment model, pricing, and review status. Manual additions create CRM
            Activity Points and YZ Champion Ecosystem Library evidence.
          </p>
        </div>
        <div className="candidate-count-grid">
          <div className="mini-stat">
            <span>Total tools</span>
            <strong>{items.length}</strong>
          </div>
          <div className="mini-stat">
            <span>Approved</span>
            <strong>{approvedCount}</strong>
          </div>
        </div>
      </div>

      <form
        className="crm-toolbar"
        onSubmit={(event) => {
          event.preventDefault();
          void load();
        }}
      >
        <Input
          aria-label="Search AI tools"
          placeholder="Search name, vendor, use case..."
          value={filters.q}
          onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
        />
        <Select aria-label="Category" value={filters.category} onChange={(event) => setFilters((current) => ({ ...current, category: event.target.value }))}>
          <option value="">Any category</option>
          {categories.map((value) => <option key={value}>{value}</option>)}
        </Select>
        <Select aria-label="Status" value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}>
          <option value="">Any status</option>
          {statuses.map((value) => <option key={value}>{value}</option>)}
        </Select>
        <Select aria-label="Deployment type" value={filters.deployment_type} onChange={(event) => setFilters((current) => ({ ...current, deployment_type: event.target.value }))}>
          <option value="">Any deployment</option>
          {deploymentTypes.map((value) => <option key={value}>{value}</option>)}
        </Select>
        <Select aria-label="Pricing model" value={filters.pricing_model} onChange={(event) => setFilters((current) => ({ ...current, pricing_model: event.target.value }))}>
          <option value="">Any pricing</option>
          {pricingModels.map((value) => <option key={value}>{value}</option>)}
        </Select>
        {isAdmin ? (
          <Select aria-label="Archived records" value={filters.include_archived} onChange={(event) => setFilters((current) => ({ ...current, include_archived: event.target.value }))}>
            <option value="false">Hide archived</option>
            <option value="true">Show archived</option>
          </Select>
        ) : null}
        <Button type="submit">
          <Search size={16} />
          Search
        </Button>
      </form>

      {error ? <ErrorState title="Could not load AI Tools Library" error={error} onRetry={() => void load()} /> : null}

      <div className="two-column">
        <SectionCard>
          <div className="section-heading">
            <h2>{editingId ? "Edit AI tool" : "Add AI tool"}</h2>
            <p>Manual tool additions count as ecosystem library evidence. Imported Excel records remain excluded unless mapped later.</p>
          </div>
          <form className="form-grid" onSubmit={(event) => void save(event)}>
            <Input label="Tool name" value={form.name} onChange={(event) => updateForm({ name: event.target.value })} required />
            <Input label="Vendor" value={form.vendor_name} onChange={(event) => updateForm({ vendor_name: event.target.value })} />
            <Input label="Website" value={form.website_url} onChange={(event) => updateForm({ website_url: event.target.value })} />
            <Select label="Category" value={form.category_text} onChange={(event) => updateForm({ category_text: event.target.value })}>
              {categories.map((value) => <option key={value}>{value}</option>)}
            </Select>
            <Input label="Primary use case" value={form.primary_use_case} onChange={(event) => updateForm({ primary_use_case: event.target.value })} />
            <Select label="Pricing" value={form.pricing_model} onChange={(event) => updateForm({ pricing_model: event.target.value })}>
              {pricingModels.map((value) => <option key={value}>{value}</option>)}
            </Select>
            <Select label="Deployment" value={form.deployment_type} onChange={(event) => updateForm({ deployment_type: event.target.value })}>
              {deploymentTypes.map((value) => <option key={value}>{value}</option>)}
            </Select>
            <Select label="Data sensitivity" value={form.data_sensitivity_level} onChange={(event) => updateForm({ data_sensitivity_level: event.target.value })}>
              {sensitivityLevels.map((value) => <option key={value}>{value}</option>)}
            </Select>
            <Select label="Status" value={form.status} onChange={(event) => updateForm({ status: event.target.value })}>
              {statuses.map((value) => <option key={value}>{value}</option>)}
            </Select>
            <label className="field form-grid__full">
              <span>Description</span>
              <textarea className="input textarea" rows={3} value={form.description} onChange={(event) => updateForm({ description: event.target.value })} />
            </label>
            <label className="field form-grid__full">
              <span>Owner notes</span>
              <textarea className="input textarea" rows={3} value={form.owner_notes} onChange={(event) => updateForm({ owner_notes: event.target.value })} />
            </label>
            <div className="button-row form-grid__full">
              <button className="button button--primary" disabled={isSaving} type="submit">
                <Save size={17} />
                {isSaving ? "Saving..." : editingId ? "Save changes" : "Add AI tool"}
              </button>
              {editingId ? (
                <button className="button button--secondary" type="button" onClick={resetForm}>
                  Cancel edit
                </button>
              ) : null}
            </div>
          </form>
        </SectionCard>

        <SectionCard>
          <div className="section-heading">
            <h2>{selected ? selected.name : "Tool detail"}</h2>
            <p>{selected ? "Selected AI tool profile and evaluation notes." : "Select a tool from the table to inspect it."}</p>
          </div>
          {selected ? (
            <div className="detail-stack">
              <div className="record-title">
                <strong>{selected.vendor_name || "No vendor set"}</strong>
                <span className="record-subtitle">{selected.website_url || "No website"}</span>
              </div>
              <div className="chip-row">
                <Badge>{selected.category_text || "Uncategorized"}</Badge>
                <Badge tone="info">{selected.status}</Badge>
                <Badge tone="success">{selected.deployment_type || "Unknown deployment"}</Badge>
              </div>
              <p>{selected.description || selected.solution_summary || "No description yet."}</p>
              <div className="phase-note">{selected.owner_notes || selected.notes || "No owner notes yet."}</div>
              <div className="button-row">
                <Button variant="secondary" onClick={() => startEdit(selected)}>
                  Edit
                </Button>
                {isAdmin ? (
                  <Button variant={selected.is_archived ? "secondary" : "danger"} onClick={() => void toggleArchive(selected)}>
                    {selected.is_archived ? <RotateCcw size={16} /> : <Archive size={16} />}
                    {selected.is_archived ? "Restore" : "Archive"}
                  </Button>
                ) : null}
              </div>
            </div>
          ) : (
            <EmptyState title="No tool selected" description="Click a row to see details or edit the tool." />
          )}
        </SectionCard>
      </div>

      <SectionCard>
        <div className="section-heading section-heading--inline">
          <div>
            <h2>AI tools</h2>
            <p>{isLoading ? "Loading..." : `${items.length} tools shown`}</p>
          </div>
          <Badge tone="info">MVP library</Badge>
        </div>
        {!error && items.length ? (
          <Table
            rows={items}
            getRowKey={(row) => row.id}
            onRowClick={(row) => setSelected(row)}
            columns={[
              { key: "name", header: "Tool name", render: (row) => <div className="record-title"><strong>{row.name}</strong><span className="record-subtitle">{row.website_url || "No website"}</span></div> },
              { key: "vendor", header: "Vendor", render: (row) => row.vendor_name || "-" },
              { key: "category", header: "Category", render: (row) => row.category_text ? <Badge>{row.category_text}</Badge> : "-" },
              { key: "use-case", header: "Primary use case", render: (row) => row.primary_use_case || row.solution_summary || "-" },
              { key: "status", header: "Status", render: (row) => <Badge tone={row.status === "Approved" ? "success" : row.status === "Rejected" ? "warning" : "info"}>{row.status}</Badge> },
              { key: "deployment", header: "Deployment", render: (row) => row.deployment_type || "-" },
              { key: "pricing", header: "Pricing", render: (row) => row.pricing_model || "-" },
              { key: "source", header: "Source", render: (row) => row.source || "-" },
              { key: "added", header: "Added by", render: (row) => row.added_by_user_id ? "CRM user" : "-" },
              { key: "updated", header: "Last updated", render: (row) => formatDate(row.updated_at) },
              {
                key: "actions",
                header: "Actions",
                render: (row) => (
                  <div className="button-row">
                    <button className="button button--secondary" type="button" onClick={(event) => { event.stopPropagation(); startEdit(row); }}>
                      Edit
                    </button>
                    {isAdmin ? (
                      <button className="button button--ghost" type="button" onClick={(event) => { event.stopPropagation(); void toggleArchive(row); }}>
                        {row.is_archived ? <RotateCcw size={16} /> : <Archive size={16} />}
                        {row.is_archived ? "Restore" : "Archive"}
                      </button>
                    ) : null}
                  </div>
                )
              }
            ]}
          />
        ) : null}
        {!error && !items.length && !isLoading ? (
          <EmptyState
            title="No AI tools added yet"
            description="Add the first tool to start building the AI Tools Library."
          />
        ) : null}
      </SectionCard>
    </ProtectedPage>
  );
}

function cleanPayload(values: Record<string, string>) {
  return Object.fromEntries(Object.entries(values).map(([key, value]) => [key, value.trim()]).filter(([, value]) => value !== ""));
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}
