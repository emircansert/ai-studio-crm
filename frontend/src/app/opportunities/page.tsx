"use client";

import { AlertTriangle, ArrowRight, GripVertical, Plus, RefreshCw, Search } from "lucide-react";
import Link from "next/link";
import { DragEvent, FormEvent, useEffect, useMemo, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Input, Select } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { apiRequest } from "@/lib/api";
import { canEditSection } from "@/lib/sectionAccess";
import { useAuth } from "@/lib/auth";
import type { BorusanCompany, CurrentUserSectionAccessResponse, Opportunity, Organization, PaginatedOrganizations, SectionAccessLevel } from "@/types/api";

const POC_STAGES = [
  { key: "IDEA", label: "Idea", description: "Early signal or rough opportunity." },
  { key: "SCOUTING", label: "Scouting", description: "Exploring startup/vendor fit." },
  { key: "SHORT_LISTING", label: "Short Listing", description: "Narrowed candidates and owners." },
  { key: "POC", label: "PoC", description: "Proof of concept planned or active." },
  { key: "POST_POC", label: "Post-PoC", description: "Completed, paused, cancelled, or next-step review." }
] as const;

type StageKey = (typeof POC_STAGES)[number]["key"];

const EMPTY_FORM = {
  title: "",
  organization_id: "",
  borusan_company_id: "",
  stage: "IDEA",
  topic: ""
};

export default function OpportunitiesPage() {
  const { user } = useAuth();
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [companies, setCompanies] = useState<BorusanCompany[]>([]);
  const [sectionAccess, setSectionAccess] = useState<Record<string, SectionAccessLevel> | null>(null);
  const [query, setQuery] = useState("");
  const [draggedId, setDraggedId] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<StageKey | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [isAdding, setIsAdding] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const canEditPipeline = canEditSection(sectionAccess, user, "POC_PIPELINE");

  useEffect(() => {
    apiRequest<CurrentUserSectionAccessResponse>("/api/v1/users/me/section-access")
      .then((response) => setSectionAccess(response.access))
      .catch(() => setSectionAccess(null));
  }, []);

  async function load() {
    setIsLoading(true);
    setError(null);
    try {
      const [opportunityRows, orgRows, companyRows] = await Promise.all([
        apiRequest<Opportunity[]>("/api/v1/opportunities?limit=500"),
        apiRequest<PaginatedOrganizations>("/api/v1/organizations?limit=500"),
        apiRequest<BorusanCompany[]>("/api/v1/borusan-companies?is_active=true&limit=100")
      ]);
      setOpportunities(opportunityRows);
      setOrganizations(orgRows.items);
      setCompanies(companyRows);
    } catch (caught) {
      setError(caught);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const organizationById = useMemo(() => new Map(organizations.map((item) => [item.id, item])), [organizations]);
  const companyById = useMemo(() => new Map(companies.map((item) => [item.id, item])), [companies]);

  const filteredOpportunities = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return opportunities;
    return opportunities.filter((item) => {
      const organization = organizationById.get(item.organization_id);
      const company = companyById.get(item.borusan_company_id);
      return [
        item.title,
        item.topic,
        item.stage,
        organization?.name,
        organization?.website_domain,
        company?.code,
        company?.name,
        company?.english_name
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [companyById, opportunities, organizationById, query]);

  const cardsByStage = useMemo(() => {
    const grouped: Record<StageKey, Opportunity[]> = {
      IDEA: [],
      SCOUTING: [],
      SHORT_LISTING: [],
      POC: [],
      POST_POC: []
    };
    for (const opportunity of filteredOpportunities) {
      const stage = normalizeStage(opportunity.stage);
      grouped[stage].push(opportunity);
    }
    for (const stage of POC_STAGES) {
      grouped[stage.key].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
    }
    return grouped;
  }, [filteredOpportunities]);

  async function moveOpportunity(opportunityId: string, nextStage: StageKey) {
    if (!canEditPipeline) {
      setActionError("This section is view-only for your account. Ask an admin for full access to move PoCs.");
      return;
    }
    const original = opportunities;
    const current = original.find((item) => item.id === opportunityId);
    if (!current || normalizeStage(current.stage) === nextStage) return;
    setActionError(null);
    setOpportunities((items) => items.map((item) => (item.id === opportunityId ? { ...item, stage: nextStage, updated_at: new Date().toISOString() } : item)));
    try {
      const updated = await apiRequest<Opportunity>(`/api/v1/opportunities/${opportunityId}/stage`, {
        method: "PATCH",
        body: JSON.stringify({ stage: nextStage })
      });
      setOpportunities((items) => items.map((item) => (item.id === opportunityId ? updated : item)));
    } catch (caught) {
      setOpportunities(original);
      setActionError(caught instanceof Error ? caught.message : "Could not move PoC. No data was changed.");
    }
  }

  function handleDragStart(event: DragEvent<HTMLElement>, opportunityId: string) {
    if (!canEditPipeline) {
      event.preventDefault();
      return;
    }
    setDraggedId(opportunityId);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", opportunityId);
  }

  function handleDragOver(event: DragEvent<HTMLElement>, stage: StageKey) {
    if (!canEditPipeline) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    setDropTarget(stage);
  }

  async function handleDrop(event: DragEvent<HTMLElement>, stage: StageKey) {
    if (!canEditPipeline) return;
    event.preventDefault();
    const opportunityId = event.dataTransfer.getData("text/plain") || draggedId;
    setDraggedId(null);
    setDropTarget(null);
    if (opportunityId) {
      await moveOpportunity(opportunityId, stage);
    }
  }

  async function createOpportunity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canEditPipeline) return;
    setIsSaving(true);
    setActionError(null);
    try {
      const created = await apiRequest<Opportunity>("/api/v1/opportunities", {
        method: "POST",
        body: JSON.stringify({ ...clean(form), opportunity_type: "POC" })
      });
      setOpportunities((items) => [created, ...items]);
      setForm(EMPTY_FORM);
      setIsAdding(false);
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : "Could not create PoC.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Pipeline"
        title="PoC Pipeline"
        description="Move PoC opportunities through the funnel from idea to post-PoC review. Drag cards between columns to update stage."
        actions={
          <div className="button-row">
            <Button variant="secondary" onClick={() => void load()}>
              <RefreshCw size={16} /> Refresh
            </Button>
            {canEditPipeline ? (
              <Button onClick={() => setIsAdding((value) => !value)}>
                <Plus size={16} /> Add PoC
              </Button>
            ) : null}
          </div>
        }
      />

      <SectionCard className="pipeline-toolbar">
        <Input
          label="Search pipeline"
          placeholder="Search project, startup, Borusan company, topic..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <div className="pipeline-toolbar__meta">
          <Search size={16} />
          <span>{filteredOpportunities.length} visible PoCs</span>
        </div>
      </SectionCard>

      {isAdding && canEditPipeline ? (
        <SectionCard>
          <div className="section-heading">
            <h2>Add PoC</h2>
            <p>Create a new pipeline card in the normalized five-stage funnel.</p>
          </div>
          <form className="form-stack" onSubmit={createOpportunity}>
            <Input label="Project name" required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
            <div className="two-column">
              <Select label="Startup / organization" required value={form.organization_id} onChange={(event) => setForm({ ...form, organization_id: event.target.value })}>
                <option value="">Select organization</option>
                {organizations.map((organization) => (
                  <option key={organization.id} value={organization.id}>{organization.name}</option>
                ))}
              </Select>
              <Select label="Borusan company" required value={form.borusan_company_id} onChange={(event) => setForm({ ...form, borusan_company_id: event.target.value })}>
                <option value="">Select Borusan company</option>
                {companies.map((company) => (
                  <option key={company.id} value={company.id}>{company.english_name ?? company.name ?? company.code}</option>
                ))}
              </Select>
              <Select label="Stage" value={form.stage} onChange={(event) => setForm({ ...form, stage: event.target.value })}>
                {POC_STAGES.map((stage) => <option key={stage.key} value={stage.key}>{stage.label}</option>)}
              </Select>
            </div>
            <Input label="Topic" value={form.topic} onChange={(event) => setForm({ ...form, topic: event.target.value })} />
            <Button type="submit" disabled={isSaving}>{isSaving ? "Creating..." : "Create PoC"}</Button>
          </form>
        </SectionCard>
      ) : null}

      {actionError ? <div className="alert alert--error">{actionError}</div> : null}

      {error ? (
        <ErrorState title="Could not load PoC Pipeline" error={error} onRetry={load} />
      ) : isLoading ? (
        <EmptyState title="Loading pipeline" description="Preparing the funnel board..." />
      ) : (
        <div className="poc-board" aria-label="PoC Pipeline Kanban board">
          {POC_STAGES.map((stage) => (
            <section
              className={`poc-column ${dropTarget === stage.key ? "poc-column--drop" : ""}`}
              key={stage.key}
              onDragOver={(event) => handleDragOver(event, stage.key)}
              onDragLeave={() => setDropTarget(null)}
              onDrop={(event) => void handleDrop(event, stage.key)}
            >
              <div className="poc-column__header">
                <div>
                  <h2>{stage.label}</h2>
                  <p>{stage.description}</p>
                </div>
                <Badge tone="neutral">{cardsByStage[stage.key].length}</Badge>
              </div>
              <div className="poc-column__cards">
                {cardsByStage[stage.key].map((opportunity) => {
                  const company = companyById.get(opportunity.borusan_company_id);
                  return (
                    <article
                      className={`poc-card ${draggedId === opportunity.id ? "poc-card--dragging" : ""}`}
                      draggable={canEditPipeline}
                      key={opportunity.id}
                      onDragEnd={() => {
                        setDraggedId(null);
                        setDropTarget(null);
                      }}
                      onDragStart={(event) => handleDragStart(event, opportunity.id)}
                    >
                      <div className="poc-card__top">
                        {canEditPipeline ? <GripVertical size={16} aria-hidden /> : null}
                        <Link href={`/opportunities/${opportunity.id}`}>{opportunity.title}</Link>
                      </div>
                      <span>{company?.english_name ?? company?.name ?? company?.code ?? "Borusan company not set"}</span>
                      <small>Last update: {formatDate(opportunity.updated_at)}</small>
                      {opportunity.stage_migration_note ? (
                        <div className="poc-card__warning" title={opportunity.stage_migration_note}>
                          <AlertTriangle size={13} /> Stage mapping needs review
                        </div>
                      ) : null}
                      <Link className="poc-card__detail" href={`/opportunities/${opportunity.id}`}>
                        Open details <ArrowRight size={13} />
                      </Link>
                    </article>
                  );
                })}
                {!cardsByStage[stage.key].length ? <p className="poc-column__empty">No PoCs in this stage.</p> : null}
              </div>
            </section>
          ))}
        </div>
      )}
    </ProtectedPage>
  );
}

function normalizeStage(stage: string): StageKey {
  const normalized = stage.trim().toUpperCase().replace(/[\s-]+/g, "_");
  if (normalized === "DISCOVERY" || normalized === "DISCUSSIONS_ONGOING") return "SCOUTING";
  if (["EVALUATION", "SHORTLIST", "SHORT_LIST"].includes(normalized)) return "SHORT_LISTING";
  if (["POC_PLANNED", "POC_ACTIVE", "PILOT"].includes(normalized)) return "POC";
  if (["COMPLETED", "ON_HOLD", "CANCELLED"].includes(normalized)) return "POST_POC";
  return POC_STAGES.some((item) => item.key === normalized) ? (normalized as StageKey) : "IDEA";
}

function clean(values: Record<string, string>) {
  return Object.fromEntries(Object.entries(values).filter(([, value]) => value !== ""));
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}
