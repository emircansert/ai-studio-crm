"use client";

import { Archive, ArrowLeft, Download, ExternalLink, FileText, Plus, RefreshCw, Save, UploadCloud } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Input, Select } from "@/components/ui/Input";
import { VerticalLabel } from "@/components/ui/VerticalHelp";
import { apiRequest, apiUrl, getStoredToken } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { BorusanCompany, CategoryOption, Contact, FollowUp, Note, Organization, OrganizationDocument, StatusOption, User } from "@/types/api";

export default function CompanyDetailPage({ params }: { params: { id: string } }) {
  const { user } = useAuth();
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [statuses, setStatuses] = useState<StatusOption[]>([]);
  const [borusanCompanies, setBorusanCompanies] = useState<BorusanCompany[]>([]);
  const [categories, setCategories] = useState<CategoryOption[]>([]);
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [activeUsers, setActiveUsers] = useState<User[]>([]);
  const [documents, setDocuments] = useState<OrganizationDocument[]>([]);
  const [auxiliaryErrors, setAuxiliaryErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState(true);

  function setAuxiliaryError(key: string, caught: unknown) {
    setAuxiliaryErrors((current) => ({
      ...current,
      [key]: caught instanceof Error ? caught.message : "Could not load this supporting data"
    }));
  }

  function clearAuxiliaryError(key: string) {
    setAuxiliaryErrors((current) => {
      const next = { ...current };
      delete next[key];
      return next;
    });
  }

  async function loadActiveUsers() {
    try {
      clearAuxiliaryError("users");
      setActiveUsers(await apiRequest<User[]>("/api/v1/users/active?limit=500"));
    } catch (caught) {
      setActiveUsers([]);
      setAuxiliaryError("users", caught);
    }
  }

  async function load() {
    setIsLoading(true);
    setError(null);
    setAuxiliaryErrors({});
    try {
      const org = await apiRequest<Organization>(`/api/v1/organizations/${params.id}`);
      setOrganization(org);
    } catch (caught) {
      setError(caught);
      setIsLoading(false);
      return;
    }

    setIsLoading(false);
    const [statusResult, companyResult, categoryResult, followUpResult, usersResult, documentResult] = await Promise.allSettled([
      apiRequest<StatusOption[]>("/api/v1/statuses?limit=500"),
      apiRequest<BorusanCompany[]>("/api/v1/borusan-companies?is_active=true&limit=100"),
      apiRequest<CategoryOption[]>("/api/v1/vocabularies/categories"),
      apiRequest<FollowUp[]>(`/api/v1/follow-ups?entity_type=ORGANIZATION&entity_id=${params.id}&limit=100`),
      apiRequest<User[]>("/api/v1/users/active?limit=500"),
      apiRequest<OrganizationDocument[]>(`/api/v1/organizations/${params.id}/documents`)
    ]);

    if (statusResult.status === "fulfilled") {
      setStatuses(statusResult.value);
    } else {
      setStatuses([]);
      setAuxiliaryError("statuses", statusResult.reason);
    }
    if (companyResult.status === "fulfilled") {
      setBorusanCompanies(companyResult.value);
    } else {
      setBorusanCompanies([]);
      setAuxiliaryError("borusanCompanies", companyResult.reason);
    }
    if (categoryResult.status === "fulfilled") {
      setCategories(categoryResult.value);
    } else {
      setCategories([]);
      setAuxiliaryError("categories", categoryResult.reason);
    }
    if (followUpResult.status === "fulfilled") {
      setFollowUps(followUpResult.value);
    } else {
      setFollowUps([]);
      setAuxiliaryError("followUps", followUpResult.reason);
    }
    if (usersResult.status === "fulfilled") {
      setActiveUsers(usersResult.value);
    } else {
      setActiveUsers([]);
      setAuxiliaryError("users", usersResult.reason);
    }
    if (documentResult.status === "fulfilled") {
      setDocuments(documentResult.value);
    } else {
      setDocuments([]);
      setAuxiliaryError("documents", documentResult.reason);
    }
  }

  async function reloadFollowUps() {
    try {
      clearAuxiliaryError("followUps");
      setFollowUps(await apiRequest<FollowUp[]>(`/api/v1/follow-ups?entity_type=ORGANIZATION&entity_id=${params.id}&limit=100`));
    } catch (caught) {
      setFollowUps([]);
      setAuxiliaryError("followUps", caught);
    }
  }

  async function reloadDocuments() {
    try {
      clearAuxiliaryError("documents");
      setDocuments(await apiRequest<OrganizationDocument[]>(`/api/v1/organizations/${params.id}/documents`));
    } catch (caught) {
      setDocuments([]);
      setAuxiliaryError("documents", caught);
    } finally {
      try {
        setOrganization(await apiRequest<Organization>(`/api/v1/organizations/${params.id}`));
      } catch {
        // Keep the existing company detail visible; the next full refresh will reconcile metadata.
      }
    }
  }

  async function archiveCompany() {
    if (!organization) return;
    const endpoint = organization.is_archived ? "unarchive" : "archive";
    const reason = window.prompt(`${organization.is_archived ? "Restore" : "Archive"} "${organization.name}"? Optional reason:`);
    if (reason === null) return;
    await apiRequest(`/api/v1/organizations/${organization.id}/${endpoint}`, {
      method: "PATCH",
      body: JSON.stringify({ reason })
    });
    await load();
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  if (isLoading) {
    return (
      <ProtectedPage>
        <EmptyState title="Loading company" description="Opening the CRM record..." />
      </ProtectedPage>
    );
  }

  if (error || !organization) {
    return (
      <ProtectedPage>
        <SectionCard>
          <ErrorState
            title="Could not load company details"
            error={error ?? new Error("Company not found")}
            onRetry={() => void load()}
            backHref="/companies"
            backLabel="Back to Startup Library"
          />
        </SectionCard>
      </ProtectedPage>
    );
  }

  return (
    <ProtectedPage>
    <div className="company-layout">
      <section className="company-hero">
        <div>
          <Link className="link-button" href="/companies">
            <ArrowLeft size={14} /> Back to Startup Library
          </Link>
          <h1>{organization.name}</h1>
          <div className="chip-row">
            <Badge>{organization.organization_type}</Badge>
            {organization.organization_subtype ? <Badge tone="info">{organization.organization_subtype}</Badge> : null}
            {organization.category_label ? <Badge tone="info">{organization.category_label}</Badge> : null}
            <Badge tone="info">{organization.lifecycle_status?.label ?? "No status"}</Badge>
          </div>
          <p>{organization.solution_summary ?? "No solution summary has been captured yet."}</p>
          <div className="metadata-row">
            {organization.website_url ? (
              <a className="link-button" href={organization.website_url} target="_blank">
                <ExternalLink size={14} /> {organization.website_domain ?? organization.website_url}
              </a>
            ) : (
              <span className="record-subtitle">No website</span>
            )}
            <span className="record-subtitle">{organization.geography_text ?? "No geography"}</span>
            <span className="record-subtitle">{organization.vertical_text ?? "No vertical"}</span>
            <span className="record-subtitle">Last contact: {organization.last_contact_date ? formatDateOnly(organization.last_contact_date) : "No last contact"}</span>
            <span className="record-subtitle">Added by {organization.added_by_display ?? "-"}</span>
            <span className="record-subtitle">{organization.source_text ?? "No source"}</span>
          </div>
        </div>
        <Button variant="secondary" onClick={() => void load()}>
          <RefreshCw size={16} />
          Refresh
        </Button>
        {user?.role === "ADMIN" ? (
          <Button variant={organization.is_archived ? "secondary" : "danger"} onClick={() => void archiveCompany()}>
            {organization.is_archived ? "Unarchive" : "Archive"}
          </Button>
        ) : null}
      </section>

      <div className="detail-grid">
        <EditCompanyCard organization={organization} statuses={statuses} categories={categories} onSaved={load} />
        <BorusanFitCard organization={organization} companies={borusanCompanies} isAdmin={user?.role === "ADMIN"} onChanged={load} />
        <NotesCard organization={organization} isAdmin={user?.role === "ADMIN"} onChanged={load} />
        <FollowUpsCard
          organization={organization}
          followUps={followUps}
          users={activeUsers}
          usersError={auxiliaryErrors.users}
          followUpsError={auxiliaryErrors.followUps}
          isAdmin={user?.role === "ADMIN"}
          onRetryUsers={() => void loadActiveUsers()}
          onChanged={reloadFollowUps}
        />
      </div>

      <div className="detail-grid">
        <ContactsCard organization={organization} isAdmin={user?.role === "ADMIN"} onChanged={load} />
        <DocumentsCard
          organization={organization}
          documents={documents}
          documentsError={auxiliaryErrors.documents}
          isAdmin={user?.role === "ADMIN"}
          currentUserId={user?.id}
          onChanged={reloadDocuments}
        />
        <OpportunitiesCard organization={organization} companies={borusanCompanies} onChanged={load} />
        <MetadataCard organization={organization} />
      </div>
    </div>
    </ProtectedPage>
  );
}

function EditCompanyCard({
  organization,
  statuses,
  categories,
  onSaved
}: {
  organization: Organization;
  statuses: StatusOption[];
  categories: CategoryOption[];
  onSaved: () => Promise<void>;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: organization.name,
    organization_type: organization.organization_type,
    organization_subtype: organization.organization_subtype ?? "",
    category_code: organization.category_code ?? "",
    category_label: organization.category_label ?? "",
    vertical_text: organization.vertical_text ?? "",
    website_url: organization.website_url ?? "",
    solution_summary: organization.solution_summary ?? "",
    geography_text: organization.geography_text ?? "",
    source_text: organization.source_text ?? "",
    last_contact_date: organization.last_contact_date ?? "",
    lifecycle_status_id: organization.lifecycle_status_id ?? ""
  });

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await apiRequest(`/api/v1/organizations/${organization.id}`, {
        method: "PUT",
        body: JSON.stringify(clean(form))
      });
      setIsOpen(false);
      await onSaved();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not update company");
    }
  }

  return (
    <SectionCard>
      <div className="section-heading section-heading--inline">
        <div>
          <h2>Profile</h2>
          <p>Edit the normalized CRM record without touching raw import history.</p>
        </div>
        <Button variant="secondary" onClick={() => setIsOpen((value) => !value)}>
          Edit
        </Button>
      </div>
      {isOpen ? (
        <form className="form-stack" onSubmit={submit}>
          <Input label="Name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          <Input label="Website" value={form.website_url} onChange={(event) => setForm({ ...form, website_url: event.target.value })} />
          <Select
            label="Category"
            value={form.category_code}
            onChange={(event) => {
              const selected = categories.find((category) => (category.code ?? category.label) === event.target.value);
              setForm({
                ...form,
                category_code: selected?.code ?? "",
                category_label: selected?.label ?? ""
              });
            }}
          >
            <option value="">No category</option>
            {categories.map((category) => (
              <option key={category.code ?? category.label ?? ""} value={category.code ?? category.label ?? ""}>
                {category.label ?? category.code}
              </option>
            ))}
          </Select>
          <Input label={<VerticalLabel />} value={form.vertical_text} onChange={(event) => setForm({ ...form, vertical_text: event.target.value })} />
          <Input label="Geography" value={form.geography_text} onChange={(event) => setForm({ ...form, geography_text: event.target.value })} />
          <Input label="Source" value={form.source_text} onChange={(event) => setForm({ ...form, source_text: event.target.value })} />
          <Input label="Last contact" type="date" value={form.last_contact_date} onChange={(event) => setForm({ ...form, last_contact_date: event.target.value })} />
          <Select
            label="Lifecycle status"
            value={form.lifecycle_status_id}
            onChange={(event) => setForm({ ...form, lifecycle_status_id: event.target.value })}
          >
            <option value="">Not set</option>
            {statuses
              .filter((status) => status.status_group === "COMPANY_STATUS")
              .map((status) => (
                <option key={status.id} value={status.id}>
                  {status.label}
                </option>
              ))}
          </Select>
          <label className="field">
            <span>Solution / use-case summary</span>
            <textarea
              className="input textarea"
              value={form.solution_summary}
              onChange={(event) => setForm({ ...form, solution_summary: event.target.value })}
            />
          </label>
          {error ? <div className="alert alert--error">{error}</div> : null}
          <Button type="submit">
            <Save size={16} />
            Save changes
          </Button>
        </form>
      ) : (
        <dl className="metadata-list">
          <div>
            <dt>Domain</dt>
            <dd>{organization.website_domain ?? "-"}</dd>
          </div>
          <div>
            <dt>Category</dt>
            <dd>{organization.category_label ?? "-"}</dd>
          </div>
          <div>
            <dt><VerticalLabel /></dt>
            <dd>{organization.vertical_text ?? "-"}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{organization.lifecycle_status?.label ?? "No status"}</dd>
          </div>
          <div>
            <dt>Last contact</dt>
            <dd>{organization.last_contact_date ? formatDateOnly(organization.last_contact_date) : "No last contact"}</dd>
          </div>
          <div>
            <dt>Geography</dt>
            <dd>{organization.geography_text ?? "-"}</dd>
          </div>
          <div>
            <dt>Source</dt>
            <dd>{organization.source_text ?? "-"}</dd>
          </div>
        </dl>
      )}
    </SectionCard>
  );
}

function ContactsCard({ organization, isAdmin, onChanged }: { organization: Organization; isAdmin: boolean; onChanged: () => Promise<void> }) {
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", title: "", raw_contact_text: "" });
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await apiRequest<Contact>(`/api/v1/organizations/${organization.id}/contacts`, {
        method: "POST",
        body: JSON.stringify(clean(form))
      });
      setForm({ full_name: "", email: "", phone: "", title: "", raw_contact_text: "" });
      await onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not add contact");
    }
  }

  async function archiveContact(contact: Contact) {
    const reason = window.prompt(`Archive contact "${contact.full_name ?? contact.email ?? "Unnamed contact"}"? Optional reason:`);
    if (reason === null) return;
    await apiRequest(`/api/v1/contacts/${contact.id}/archive`, {
      method: "PATCH",
      body: JSON.stringify({ reason })
    });
    await onChanged();
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Contacts</h2>
        <p>People and raw contact text connected to this organization.</p>
      </div>
      <div className="preview-stack">
        {(organization.contacts ?? []).map((contact) => (
          <div className="contact-card" key={contact.id}>
            <strong>{contact.full_name ?? contact.email ?? "Unnamed contact"}</strong>
            <span className="record-subtitle">{contact.title ?? contact.raw_contact_text ?? "-"}</span>
            <div className="chip-row">
              {contact.email ? <Badge tone="info">{contact.email}</Badge> : null}
              {contact.phone ? <Badge>{contact.phone}</Badge> : null}
            </div>
            {isAdmin ? <Button variant="danger" onClick={() => void archiveContact(contact)}>Archive contact</Button> : null}
          </div>
        ))}
      </div>
      <form className="form-stack" onSubmit={submit}>
        <Input label="Name" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
        <Input label="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
        <Input label="Title" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
        {error ? <div className="alert alert--error">{error}</div> : null}
        <Button type="submit" variant="secondary">
          <Plus size={16} />
          Add contact
        </Button>
      </form>
    </SectionCard>
  );
}

function NotesCard({ organization, isAdmin, onChanged }: { organization: Organization; isAdmin: boolean; onChanged: () => Promise<void> }) {
  const [body, setBody] = useState("");
  const [noteType, setNoteType] = useState("GENERAL");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!body.trim()) return;
    await apiRequest<Note>(`/api/v1/organizations/${organization.id}/notes`, {
      method: "POST",
      body: JSON.stringify({ note_type: noteType, body, occurred_at: new Date().toISOString() })
    });
    setBody("");
    await onChanged();
  }

  async function archiveNote(note: Note) {
    const reason = window.prompt("Archive this note? Optional reason:");
    if (reason === null) return;
    await apiRequest(`/api/v1/notes/${note.id}/archive`, {
      method: "PATCH",
      body: JSON.stringify({ reason })
    });
    await onChanged();
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Notes timeline</h2>
        <p>Meeting notes, decisions, and follow-up context.</p>
      </div>
      <div className="preview-stack">
        {(organization.notes ?? []).map((note) => (
          <div className="timeline-item" key={note.id}>
            <div className="chip-row">
              <Badge tone={note.note_type === "IMPORT_NOTE" ? "info" : "neutral"}>{note.note_type}</Badge>
              <span className="timeline-meta">{note.occurred_at ? new Date(note.occurred_at).toLocaleString() : "-"}</span>
            </div>
            <p>{note.body}</p>
            {isAdmin ? <Button variant="danger" onClick={() => void archiveNote(note)}>Archive note</Button> : null}
          </div>
        ))}
      </div>
      <form className="form-stack" onSubmit={submit}>
        <Select value={noteType} onChange={(event) => setNoteType(event.target.value)}>
          {["GENERAL", "MEETING", "DECISION", "FOLLOW_UP"].map((type) => (
            <option key={type} value={type}>
              {type.replaceAll("_", " ")}
            </option>
          ))}
        </Select>
        <label className="field">
          <span>New note</span>
          <textarea className="input textarea" value={body} onChange={(event) => setBody(event.target.value)} />
        </label>
        <Button type="submit" variant="secondary">
          <Plus size={16} />
          Add note
        </Button>
      </form>
    </SectionCard>
  );
}

function BorusanFitCard({
  organization,
  companies,
  isAdmin,
  onChanged
}: {
  organization: Organization;
  companies: BorusanCompany[];
  isAdmin: boolean;
  onChanged: () => Promise<void>;
}) {
  const [form, setForm] = useState({ borusan_company_id: "", fit_level: "RELEVANT", fit_reason: "" });

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.borusan_company_id) return;
    await apiRequest(`/api/v1/organizations/${organization.id}/borusan-fit`, {
      method: "POST",
      body: JSON.stringify({ ...clean(form), source: "MANUAL" })
    });
    setForm({ borusan_company_id: "", fit_level: "RELEVANT", fit_reason: "" });
    await onChanged();
  }

  async function archiveFit(fitId: string) {
    const reason = window.prompt("Archive this Borusan fit? Optional reason:");
    if (reason === null) return;
    await apiRequest(`/api/v1/organizations/${organization.id}/borusan-fit/${fitId}/archive`, {
      method: "PATCH",
      body: JSON.stringify({ reason })
    });
    await onChanged();
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Borusan fit</h2>
        <p>Critical relevance signal for filtering and opportunity discovery.</p>
      </div>
      <div className="preview-stack">
        {(organization.borusan_fit_summary ?? []).map((fit) => (
          <div className="fit-card" key={fit.id}>
            <div className="chip-row">
              <Badge tone={fit.fit_level === "HIGH" ? "success" : "info"}>{fit.borusan_company_code}</Badge>
              <Badge>{fit.fit_level}</Badge>
            </div>
            <p className="record-subtitle">{fit.fit_reason ?? fit.source}</p>
            {isAdmin ? <Button variant="danger" onClick={() => void archiveFit(fit.id)}>Archive fit</Button> : null}
          </div>
        ))}
      </div>
      <form className="form-stack" onSubmit={submit}>
        <Select
          label="Borusan company"
          value={form.borusan_company_id}
          onChange={(event) => setForm({ ...form, borusan_company_id: event.target.value })}
        >
          <option value="">Select company</option>
          {companies.map((company) => (
            <option key={company.id} value={company.id}>
              {company.code} - {company.english_name ?? company.name}
            </option>
          ))}
        </Select>
        <Select label="Fit level" value={form.fit_level} onChange={(event) => setForm({ ...form, fit_level: event.target.value })}>
          {["HIGH", "MEDIUM", "LOW", "RELEVANT", "UNKNOWN"].map((level) => (
            <option key={level} value={level}>
              {level}
            </option>
          ))}
        </Select>
        <Input label="Reason" value={form.fit_reason} onChange={(event) => setForm({ ...form, fit_reason: event.target.value })} />
        <Button type="submit" variant="secondary">
          <Plus size={16} />
          Add fit
        </Button>
      </form>
    </SectionCard>
  );
}

function OpportunitiesCard({
  organization,
  companies,
  onChanged
}: {
  organization: Organization;
  companies: BorusanCompany[];
  onChanged: () => Promise<void>;
}) {
  const [form, setForm] = useState({ title: "", borusan_company_id: "", stage: "IDEA", topic: "" });

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.title || !form.borusan_company_id) return;
    await apiRequest("/api/v1/opportunities", {
      method: "POST",
      body: JSON.stringify({ ...clean(form), organization_id: organization.id, opportunity_type: "POC" })
    });
    setForm({ title: "", borusan_company_id: "", stage: "IDEA", topic: "" });
    await onChanged();
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Opportunities</h2>
        <p>PoC or engagement pipeline items related to this organization.</p>
      </div>
      <div className="preview-stack">
        {(organization.opportunities ?? []).map((opportunity) => (
          <div className="opportunity-card" key={opportunity.id}>
            <strong>{opportunity.title}</strong>
            <div className="chip-row">
              <Badge tone="info">{opportunity.stage}</Badge>
              <span className="record-subtitle">{opportunity.topic ?? "-"}</span>
            </div>
          </div>
        ))}
      </div>
      <form className="form-stack" onSubmit={submit}>
        <Input label="Title" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
        <Select
          label="Borusan company"
          value={form.borusan_company_id}
          onChange={(event) => setForm({ ...form, borusan_company_id: event.target.value })}
        >
          <option value="">Select company</option>
          {companies.map((company) => (
            <option key={company.id} value={company.id}>
              {company.code}
            </option>
          ))}
        </Select>
        <Input label="Topic" value={form.topic} onChange={(event) => setForm({ ...form, topic: event.target.value })} />
        <Button type="submit" variant="secondary">
          <Plus size={16} />
          Add opportunity
        </Button>
      </form>
    </SectionCard>
  );
}

function MetadataCard({ organization }: { organization: Organization }) {
  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Metadata</h2>
        <p>Source, tags, import reference, and record tracking.</p>
      </div>
      <div className="chip-row">
        {(organization.tags ?? organization.tags_summary ?? []).map((tag) => (
          <Badge key={tag.id} tone="info">
            {tag.label}
          </Badge>
        ))}
      </div>
      <dl className="metadata-list">
        <div>
          <dt>Added by</dt>
          <dd>{organization.added_by_display ?? "-"}</dd>
        </div>
        <div>
          <dt>Excel Added By</dt>
          <dd>{organization.added_by_text ?? "-"}</dd>
        </div>
        <div>
          <dt>Added date</dt>
          <dd>{new Date(organization.added_at ?? organization.created_at).toLocaleString()}</dd>
        </div>
        <div>
          <dt>Last contact</dt>
          <dd>{organization.last_contact_date ? new Date(organization.last_contact_date).toLocaleDateString() : "-"}</dd>
        </div>
        <div>
          <dt>Created by user</dt>
          <dd>{organization.created_by_user?.full_name ?? "-"}</dd>
        </div>
        <div>
          <dt>Updated by user</dt>
          <dd>{organization.updated_by_user?.full_name ?? "-"}</dd>
        </div>
        <div>
          <dt>Updated at</dt>
          <dd>{new Date(organization.updated_at).toLocaleString()}</dd>
        </div>
        <div>
          <dt>Import row</dt>
          <dd>{String(organization.raw_source_reference?.import_row_id ?? "-")}</dd>
        </div>
      </dl>
    </SectionCard>
  );
}

function FollowUpsCard({
  organization,
  followUps,
  users,
  usersError,
  followUpsError,
  isAdmin,
  onRetryUsers,
  onChanged
}: {
  organization: Organization;
  followUps: FollowUp[];
  users: User[];
  usersError?: string;
  followUpsError?: string;
  isAdmin: boolean;
  onRetryUsers: () => void;
  onChanged: () => Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [assignedToUserId, setAssignedToUserId] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim()) return;
    await apiRequest("/api/v1/follow-ups", {
      method: "POST",
      body: JSON.stringify({
        title,
        due_date: dueDate || null,
        assigned_to_user_id: assignedToUserId || null,
        entity_type: "ORGANIZATION",
        entity_id: organization.id,
        status: "OPEN"
      })
    });
    setTitle("");
    setDueDate("");
    setAssignedToUserId("");
    await onChanged();
  }

  async function complete(id: string) {
    await apiRequest(`/api/v1/follow-ups/${id}/complete`, { method: "PATCH" });
    await onChanged();
  }

  async function archive(id: string) {
    const reason = window.prompt("Archive this follow-up? Optional reason:");
    if (reason === null) return;
    await apiRequest(`/api/v1/follow-ups/${id}/archive`, {
      method: "PATCH",
      body: JSON.stringify({ reason })
    });
    await onChanged();
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Follow-ups</h2>
        <p>Tasks and next actions connected to this organization.</p>
      </div>
      {followUpsError ? <div className="alert alert--warning">{followUpsError}</div> : null}
      <div className="preview-stack">
        {followUps.map((item) => (
          <div className="opportunity-card" key={item.id}>
            <div className="section-heading--inline">
              <strong>{item.title}</strong>
              <Badge tone={item.status === "DONE" ? "success" : "info"}>{item.status}</Badge>
            </div>
            <span className="record-subtitle">Assigned to: {users.find((user) => user.id === item.assigned_to_user_id)?.full_name ?? "Unassigned"}</span>
            <span className={isOverdue(item) ? "record-subtitle overdue-text" : "record-subtitle"}>Due: {item.due_date ? formatDateOnly(item.due_date) : "-"}</span>
            {item.status === "OPEN" ? <Button variant="secondary" onClick={() => void complete(item.id)}>Complete</Button> : null}
            {isAdmin ? <Button variant="danger" onClick={() => void archive(item.id)}>Archive follow-up</Button> : null}
          </div>
        ))}
      </div>
      <form className="form-stack" onSubmit={submit}>
        <Input label="Task / description" value={title} onChange={(event) => setTitle(event.target.value)} />
        <Select label="Assign to" value={assignedToUserId} onChange={(event) => setAssignedToUserId(event.target.value)}>
          <option value="">{usersError ? "Could not load active users" : "Unassigned"}</option>
          {users.map((user) => (
            <option key={user.id} value={user.id}>
              {user.full_name} ({user.email})
            </option>
          ))}
        </Select>
        {usersError ? (
          <div className="alert alert--warning">
            <span>{usersError}</span>
            <Button variant="secondary" type="button" onClick={onRetryUsers}>
              Retry users
            </Button>
          </div>
        ) : null}
        <Input label="Due date" type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
        <Button type="submit" variant="secondary">Assign follow-up</Button>
      </form>
    </SectionCard>
  );
}

function DocumentsCard({
  organization,
  documents,
  documentsError,
  isAdmin,
  currentUserId,
  onChanged
}: {
  organization: Organization;
  documents: OrganizationDocument[];
  documentsError?: string;
  isAdmin: boolean;
  currentUserId?: string;
  onChanged: () => Promise<void>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function uploadDeck(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return;
    setError(null);
    if (!["application/pdf", "application/vnd.openxmlformats-officedocument.presentationml.presentation"].includes(file.type)) {
      setError("Only PDF and PPTX startup decks are supported.");
      return;
    }
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      await apiRequest<OrganizationDocument>(`/api/v1/organizations/${organization.id}/documents`, {
        method: "POST",
        body: formData
      });
      setFile(null);
      await onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not upload startup deck");
    } finally {
      setIsUploading(false);
    }
  }

  async function downloadDeck(document: OrganizationDocument) {
    const token = getStoredToken();
    const response = await fetch(apiUrl(document.download_url ?? `/api/v1/organizations/${organization.id}/documents/${document.id}/download`), {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined
    });
    if (!response.ok) {
      setError(`Download failed with status ${response.status}`);
      return;
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = window.document.createElement("a");
    link.href = url;
    link.download = document.original_filename;
    window.document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }

  async function archiveDeck(document: OrganizationDocument) {
    const reason = window.prompt(`Archive "${document.original_filename}"? Optional reason:`);
    if (reason === null) return;
    await apiRequest(`/api/v1/organizations/${organization.id}/documents/${document.id}/archive`, {
      method: "PATCH",
      body: JSON.stringify({ reason })
    });
    await onChanged();
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Startup deck</h2>
        <p>Upload and manage PDF or PPTX decks attached to this startup.</p>
      </div>
      {documentsError ? <div className="alert alert--warning">{documentsError}</div> : null}
      <div className="preview-stack">
        {documents.map((document) => (
          <div className="opportunity-card" key={document.id}>
            <div className="section-heading--inline">
              <div className="record-title">
                <strong><FileText size={16} /> {document.original_filename}</strong>
                <span className="record-subtitle">
                  {formatFileSize(document.file_size_bytes)} · uploaded {formatDateOnly(document.uploaded_at)} by {document.uploaded_by_user?.full_name ?? "-"}
                </span>
              </div>
              <Badge tone="info">{document.original_filename.toLowerCase().endsWith(".pptx") ? "PPTX" : "PDF"}</Badge>
            </div>
            <div className="button-row">
              <Button variant="secondary" onClick={() => void downloadDeck(document)}>
                <Download size={16} />
                Download
              </Button>
              {(isAdmin || document.uploaded_by_user_id === currentUserId) && !document.is_archived ? (
                <Button variant="danger" onClick={() => void archiveDeck(document)}>
                  <Archive size={16} />
                  Archive
                </Button>
              ) : null}
            </div>
          </div>
        ))}
        {!documents.length ? <p className="record-subtitle">No startup deck has been uploaded yet.</p> : null}
      </div>
      <form className="form-stack" onSubmit={uploadDeck}>
        <Input
          label="Upload startup deck"
          type="file"
          accept=".pdf,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.presentationml.presentation"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        {error ? <div className="alert alert--error">{error}</div> : null}
        <Button disabled={!file || isUploading} type="submit" variant="secondary">
          <UploadCloud size={16} />
          {isUploading ? "Uploading..." : "Upload deck"}
        </Button>
      </form>
    </SectionCard>
  );
}

function clean(values: Record<string, string>) {
  return Object.fromEntries(Object.entries(values).filter(([, value]) => value !== ""));
}

function isOverdue(item: FollowUp) {
  if (item.status !== "OPEN" || !item.due_date) return false;
  return new Date(item.due_date) < new Date(new Date().toDateString());
}

function formatDateOnly(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
