"use client";

import { Archive, ArrowLeft, Download, FileText, RefreshCw, Save, UploadCloud } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input, Select } from "@/components/ui/Input";
import { apiRequest, apiUrl } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { BorusanCompany, FollowUp, Opportunity, OpportunityDocument, Organization, PaginatedOrganizations, StatusOption, User } from "@/types/api";

const POC_STAGES = [
  { key: "IDEA", label: "Idea" },
  { key: "SCOUTING", label: "Scouting" },
  { key: "SHORT_LISTING", label: "Short Listing" },
  { key: "POC", label: "PoC" },
  { key: "POST_POC", label: "Post-PoC" }
];

export default function OpportunityDetailPage({ params }: { params: { id: string } }) {
  const { user } = useAuth();
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [companies, setCompanies] = useState<BorusanCompany[]>([]);
  const [statuses, setStatuses] = useState<StatusOption[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [documents, setDocuments] = useState<OpportunityDocument[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  async function load() {
    setIsLoading(true);
    setError(null);
    try {
      const [record, orgs, companyRows, statusRows, userRows, taskRows, documentRows] = await Promise.all([
        apiRequest<Opportunity>(`/api/v1/opportunities/${params.id}`),
        apiRequest<PaginatedOrganizations>("/api/v1/organizations?limit=500"),
        apiRequest<BorusanCompany[]>("/api/v1/borusan-companies?is_active=true&limit=100"),
        apiRequest<StatusOption[]>("/api/v1/statuses?limit=500"),
        apiRequest<User[]>("/api/v1/admin/users?limit=500").catch(() => []),
        apiRequest<FollowUp[]>(`/api/v1/follow-ups?entity_type=OPPORTUNITY&entity_id=${params.id}&limit=100`),
        apiRequest<OpportunityDocument[]>(`/api/v1/opportunities/${params.id}/documents`)
      ]);
      setOpportunity(record);
      setOrganizations(orgs.items);
      setCompanies(companyRows);
      setStatuses(statusRows);
      setUsers(userRows);
      setFollowUps(taskRows);
      setDocuments(documentRows);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load opportunity");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  const organization = useMemo(
    () => organizations.find((item) => item.id === opportunity?.organization_id),
    [opportunity?.organization_id, organizations]
  );
  const borusanCompany = useMemo(
    () => companies.find((item) => item.id === opportunity?.borusan_company_id),
    [companies, opportunity?.borusan_company_id]
  );

  async function toggleArchive() {
    if (!opportunity) return;
    const endpoint = opportunity.is_archived ? "unarchive" : "archive";
    const reason = window.prompt(`${opportunity.is_archived ? "Restore" : "Archive"} this opportunity? Optional reason:`);
    if (reason === null) return;
    await apiRequest(`/api/v1/opportunities/${opportunity.id}/${endpoint}`, {
      method: "PATCH",
      body: JSON.stringify({ reason })
    });
    await load();
  }

  if (isLoading) {
    return (
      <ProtectedPage>
        <EmptyState title="Loading opportunity" description="Opening the PoC pipeline record..." />
      </ProtectedPage>
    );
  }

  if (error || !opportunity) {
    return (
      <ProtectedPage>
        <SectionCard>
          <div className="alert alert--error">{error ?? "Opportunity not found"}</div>
          <Link className="button button--secondary" href="/opportunities">
            <ArrowLeft size={16} />
            Back to pipeline
          </Link>
        </SectionCard>
      </ProtectedPage>
    );
  }

  return (
    <ProtectedPage>
      <section className="company-hero">
        <div>
          <Link className="link-button" href="/opportunities">
            <ArrowLeft size={14} /> Back to PoC Pipeline
          </Link>
          <h1>{opportunity.title}</h1>
          <div className="chip-row">
            <Badge tone="info">{opportunity.stage}</Badge>
            <Badge>{opportunity.opportunity_type ?? "POC"}</Badge>
            {borusanCompany ? <Badge tone="success">{borusanCompany.code}</Badge> : null}
          </div>
          <p>{opportunity.topic ?? "No topic has been captured for this opportunity yet."}</p>
          <div className="metadata-row">
            <span className="record-subtitle">Organization: {organization?.name ?? opportunity.organization_id}</span>
            <span className="record-subtitle">Last contact: {formatDate(opportunity.last_contact_date)}</span>
          </div>
        </div>
        <Button variant="secondary" onClick={() => void load()}>
          <RefreshCw size={16} />
          Refresh
        </Button>
        {user?.role === "ADMIN" ? (
          <Button variant={opportunity.is_archived ? "secondary" : "danger"} onClick={() => void toggleArchive()}>
            {opportunity.is_archived ? "Unarchive" : "Archive"}
          </Button>
        ) : null}
      </section>

      <div className="two-column">
        <OpportunityEditCard opportunity={opportunity} organizations={organizations} companies={companies} statuses={statuses} users={users} onSaved={load} />
        <FollowUpsCard opportunity={opportunity} followUps={followUps} users={users} onChanged={load} />
        <OpportunityDocumentsCard opportunity={opportunity} documents={documents} currentUserId={user?.id ?? null} isAdmin={user?.role === "ADMIN"} onChanged={load} />
        <SectionCard>
          <div className="section-heading">
            <h2>Terms and value</h2>
            <p>Commercial terms and the expected value hypothesis.</p>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>Terms</dt>
              <dd>{opportunity.terms_text ?? "-"}</dd>
            </div>
            <div>
              <dt>Value hypothesis</dt>
              <dd>{opportunity.value_hypothesis ?? "-"}</dd>
            </div>
            <div>
              <dt>Expected dates</dt>
              <dd>{formatDate(opportunity.expected_start_date)} - {formatDate(opportunity.expected_end_date)}</dd>
            </div>
          </dl>
        </SectionCard>
      </div>
    </ProtectedPage>
  );
}

function OpportunityEditCard({
  opportunity,
  organizations,
  companies,
  statuses,
  users,
  onSaved
}: {
  opportunity: Opportunity;
  organizations: Organization[];
  companies: BorusanCompany[];
  statuses: StatusOption[];
  users: User[];
  onSaved: () => Promise<void>;
}) {
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: opportunity.title,
    organization_id: opportunity.organization_id,
    borusan_company_id: opportunity.borusan_company_id,
    opportunity_type: opportunity.opportunity_type ?? "POC",
    stage: opportunity.stage,
    status_id: opportunity.status_id ?? "",
    topic: opportunity.topic ?? "",
    terms_text: opportunity.terms_text ?? "",
    value_hypothesis: opportunity.value_hypothesis ?? "",
    expected_start_date: opportunity.expected_start_date ?? "",
    expected_end_date: opportunity.expected_end_date ?? "",
    last_contact_date: opportunity.last_contact_date ?? "",
    owner_user_id: opportunity.owner_user_id ?? ""
  });

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await apiRequest<Opportunity>(`/api/v1/opportunities/${opportunity.id}`, {
        method: "PUT",
        body: JSON.stringify(clean(form))
      });
      await onSaved();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not update opportunity");
    }
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Edit opportunity</h2>
        <p>Update stage, owner, topic, terms, and expected timing.</p>
      </div>
      <form className="form-stack" onSubmit={submit}>
        <Input label="Title" required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
        <div className="two-column">
          <Select label="Organization" value={form.organization_id} onChange={(event) => setForm({ ...form, organization_id: event.target.value })}>
            {organizations.map((organization) => (
              <option key={organization.id} value={organization.id}>{organization.name}</option>
            ))}
          </Select>
          <Select label="Borusan company" value={form.borusan_company_id} onChange={(event) => setForm({ ...form, borusan_company_id: event.target.value })}>
            {companies.map((company) => (
              <option key={company.id} value={company.id}>{company.code}</option>
            ))}
          </Select>
          <Select label="Stage" value={form.stage} onChange={(event) => setForm({ ...form, stage: event.target.value })}>
            {POC_STAGES.map((stage) => <option key={stage.key} value={stage.key}>{stage.label}</option>)}
          </Select>
          <Select label="Status" value={form.status_id} onChange={(event) => setForm({ ...form, status_id: event.target.value })}>
            <option value="">Not set</option>
            {statuses.filter((status) => status.status_group === "OPPORTUNITY_STATUS").map((status) => (
              <option key={status.id} value={status.id}>{status.label}</option>
            ))}
          </Select>
          <Select label="Owner" value={form.owner_user_id} onChange={(event) => setForm({ ...form, owner_user_id: event.target.value })}>
            <option value="">Unassigned</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>{user.full_name}</option>
            ))}
          </Select>
          <Input label="Last contact" type="date" value={form.last_contact_date} onChange={(event) => setForm({ ...form, last_contact_date: event.target.value })} />
          <Input label="Expected start" type="date" value={form.expected_start_date} onChange={(event) => setForm({ ...form, expected_start_date: event.target.value })} />
          <Input label="Expected end" type="date" value={form.expected_end_date} onChange={(event) => setForm({ ...form, expected_end_date: event.target.value })} />
        </div>
        <Input label="Topic" value={form.topic} onChange={(event) => setForm({ ...form, topic: event.target.value })} />
        <label className="field">
          <span>Terms</span>
          <textarea className="input textarea" value={form.terms_text} onChange={(event) => setForm({ ...form, terms_text: event.target.value })} />
        </label>
        <label className="field">
          <span>Value hypothesis</span>
          <textarea className="input textarea" value={form.value_hypothesis} onChange={(event) => setForm({ ...form, value_hypothesis: event.target.value })} />
        </label>
        {error ? <div className="alert alert--error">{error}</div> : null}
        <Button type="submit"><Save size={16} /> Save opportunity</Button>
      </form>
    </SectionCard>
  );
}

function OpportunityDocumentsCard({
  opportunity,
  documents,
  currentUserId,
  isAdmin,
  onChanged
}: {
  opportunity: Opportunity;
  documents: OpportunityDocument[];
  currentUserId: string | null;
  isAdmin: boolean;
  onChanged: () => Promise<void>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function uploadDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!file) return;
    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ];
    const allowedExtensions = [".pdf", ".pptx", ".docx", ".xlsx"];
    const lowerName = file.name.toLowerCase();
    if (!allowedTypes.includes(file.type) && !allowedExtensions.some((extension) => lowerName.endsWith(extension))) {
      setError("Only PDF, PPTX, DOCX, and XLSX PoC documents are supported.");
      return;
    }
    const data = new FormData();
    data.append("file", file);
    setIsUploading(true);
    try {
      await apiRequest<OpportunityDocument>(`/api/v1/opportunities/${opportunity.id}/documents`, {
        method: "POST",
        body: data
      });
      setFile(null);
      await onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not upload PoC document");
    } finally {
      setIsUploading(false);
    }
  }

  async function downloadDocument(document: OpportunityDocument) {
    const response = await fetch(apiUrl(document.download_url ?? `/api/v1/opportunities/${opportunity.id}/documents/${document.id}/download`), {
      headers: { Authorization: `Bearer ${window.localStorage.getItem("borusan_crm_token") ?? ""}` }
    });
    if (!response.ok) {
      setError(`Download failed with status ${response.status}`);
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = window.document.createElement("a");
    link.href = url;
    link.download = document.original_filename;
    window.document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function archiveDocument(document: OpportunityDocument) {
    const reason = window.prompt(`Archive "${document.original_filename}"? Optional reason:`);
    if (reason === null) return;
    await apiRequest(`/api/v1/opportunities/${opportunity.id}/documents/${document.id}/archive`, {
      method: "PATCH",
      body: JSON.stringify({ reason })
    });
    await onChanged();
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>PoC documents</h2>
        <p>Upload presentations and supporting documents for this PoC.</p>
      </div>
      {error ? <div className="alert alert--error">{error}</div> : null}
      <div className="preview-stack">
        {documents.map((document) => (
          <div className="opportunity-card" key={document.id}>
            <div className="section-heading--inline">
              <strong><FileText size={16} /> {document.original_filename}</strong>
              <Badge tone="info">{document.original_filename.split(".").pop()?.toUpperCase() ?? "FILE"}</Badge>
            </div>
            <span className="record-subtitle">
              {formatFileSize(document.file_size_bytes)} · uploaded {formatDate(document.uploaded_at)} by {document.uploaded_by_user?.full_name ?? "-"}
            </span>
            <div className="button-row">
              <Button variant="secondary" onClick={() => void downloadDocument(document)}>
                <Download size={15} /> Download
              </Button>
              {(isAdmin || document.uploaded_by_user_id === currentUserId) && !document.is_archived ? (
                <Button variant="danger" onClick={() => void archiveDocument(document)}>
                  <Archive size={15} /> Archive
                </Button>
              ) : null}
            </div>
          </div>
        ))}
        {!documents.length ? <p className="record-subtitle">No PoC documents have been uploaded yet.</p> : null}
      </div>
      <form className="form-stack" onSubmit={uploadDocument}>
        <label className="field">
          <span>Upload PoC file</span>
          <input
            className="input"
            accept=".pdf,.pptx,.docx,.xlsx,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            type="file"
          />
        </label>
        <Button disabled={!file || isUploading} type="submit">
          <UploadCloud size={16} /> {isUploading ? "Uploading..." : "Upload document"}
        </Button>
      </form>
    </SectionCard>
  );
}

function FollowUpsCard({ opportunity, followUps, users, onChanged }: { opportunity: Opportunity; followUps: FollowUp[]; users: User[]; onChanged: () => Promise<void> }) {
  const [form, setForm] = useState({ title: "", due_date: "", assigned_to_user_id: "" });

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.title.trim()) return;
    await apiRequest<FollowUp>("/api/v1/follow-ups", {
      method: "POST",
      body: JSON.stringify({ ...clean(form), entity_type: "OPPORTUNITY", entity_id: opportunity.id, status: "OPEN" })
    });
    setForm({ title: "", due_date: "", assigned_to_user_id: "" });
    await onChanged();
  }

  async function complete(id: string) {
    await apiRequest(`/api/v1/follow-ups/${id}/complete`, { method: "PATCH" });
    await onChanged();
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Related follow-ups</h2>
        <p>Next actions for this opportunity.</p>
      </div>
      <div className="preview-stack">
        {followUps.map((item) => (
          <div className="opportunity-card" key={item.id}>
            <div className="section-heading--inline">
              <strong>{item.title}</strong>
              <Badge tone={item.status === "DONE" ? "success" : "info"}>{item.status}</Badge>
            </div>
            <span className="record-subtitle">Due: {formatDate(item.due_date)}</span>
            {item.status === "OPEN" ? <Button variant="secondary" onClick={() => void complete(item.id)}>Complete</Button> : null}
          </div>
        ))}
      </div>
      <form className="form-stack" onSubmit={submit}>
        <Input label="New follow-up" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
        <div className="two-column">
          <Input label="Due date" type="date" value={form.due_date} onChange={(event) => setForm({ ...form, due_date: event.target.value })} />
          <Select label="Assignee" value={form.assigned_to_user_id} onChange={(event) => setForm({ ...form, assigned_to_user_id: event.target.value })}>
            <option value="">Unassigned</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>{user.full_name}</option>
            ))}
          </Select>
        </div>
        <Button type="submit" variant="secondary">Add follow-up</Button>
      </form>
    </SectionCard>
  );
}

function clean(values: Record<string, string>) {
  return Object.fromEntries(Object.entries(values).filter(([, value]) => value !== ""));
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
