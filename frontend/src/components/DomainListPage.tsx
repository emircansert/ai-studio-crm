"use client";

import { Download, Plus, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Input, Select } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { Table } from "@/components/ui/Table";
import { VerticalLabel } from "@/components/ui/VerticalHelp";
import { apiRequest, apiUrl, getStoredToken } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type {
  BorusanCompany,
  CategoryOption,
  EventRecord,
  Opportunity,
  Organization,
  PaginatedOrganizations,
  StatusOption
} from "@/types/api";

type DomainKind = "companies" | "events" | "opportunities" | "network";

type DomainListPageProps = {
  kind: DomainKind;
  eyebrow: string;
  title: string;
  description: string;
};

// "VENDOR" is intentionally absent: vendors are managed in the dedicated Vendor Library.
const typeOptions = ["STARTUP", "AI_TOOL_VENDOR", "NETWORK_INSTITUTION", "BORUSAN_COMPANY"];
const networkCategoryOptions = ["VC", "CVC", "Fund", "Institution", "Accelerator"];

const startupProcessStatusCodes = [
  "INFORMATION_RECEIVED",
  "MEETING_HELD",
  "NOT_A_FIT",
  "IN_PROGRESS",
  "NDA",
  "POC_IN_PROGRESS",
  "POC_FAILED",
  "POC_SUCCESSFUL",
  "PARTNERED"
];

const startupProcessStatusLabels: Record<string, string> = {
  INFORMATION_RECEIVED: "1- Info",
  MEETING_HELD: "2- Contacted/Positive",
  NOT_A_FIT: "2- Contacted/Negative",
  IN_PROGRESS: "3-Planned for the Future",
  NDA: "4-NDA/Contract",
  POC_IN_PROGRESS: "5-PoC in Progress",
  POC_FAILED: "6- PoC Failed",
  POC_SUCCESSFUL: "6- PoC Successful",
  PARTNERED: "7- Partnered"
};

// Intentional-looking placeholder for missing values (visual only).
const EMPTY_VALUE = <span className="empty-value">-</span>;

export function DomainListPage({ kind, eyebrow, title, description }: DomainListPageProps) {
  const router = useRouter();
  const { user } = useAuth();
  const [rows, setRows] = useState<Array<Organization | EventRecord | Opportunity>>([]);
  const [statuses, setStatuses] = useState<StatusOption[]>([]);
  const [borusanCompanies, setBorusanCompanies] = useState<BorusanCompany[]>([]);
  const [categories, setCategories] = useState<CategoryOption[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [error, setError] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddCompany, setShowAddCompany] = useState(false);
  const [showAddRecord, setShowAddRecord] = useState(false);
  const [pageSize, setPageSize] = useState(50);
  const [offset, setOffset] = useState(0);
  const [sortBy, setSortBy] = useState("newest");
  const [filters, setFilters] = useState({
    q: "",
    organization_type: kind === "network" ? "NETWORK_INSTITUTION" : "STARTUP",
    organization_subtype: "",
    category: "",
    vertical: "",
    expertise: "",
    contact_person: "",
    notes: "",
    borusan_company_code: "",
    status_code: "",
    geography: "",
    source: "",
    added_by: "",
    added_from_date: "",
    added_to_date: "",
    has_website: ""
  });
  const [includeArchived, setIncludeArchived] = useState(false);

  const isOrganizationView = kind === "companies" || kind === "network";
  const isAdmin = user?.role === "ADMIN";

  useEffect(() => {
    async function loadOptions() {
      if (!isOrganizationView) return;
      const [statusData, companyData, categoryData] = await Promise.all([
        apiRequest<StatusOption[]>("/api/v1/statuses?limit=500"),
        apiRequest<BorusanCompany[]>("/api/v1/borusan-companies?is_active=true&limit=100"),
        apiRequest<CategoryOption[]>("/api/v1/vocabularies/categories")
      ]);
      setStatuses(statusData);
      setBorusanCompanies(companyData);
      setCategories(categoryData);
    }

    void loadOptions().catch(() => undefined);
  }, [isOrganizationView]);

  async function load(nextOffset = offset) {
    setIsLoading(true);
    setError(null);
    try {
      const organizationFilters =
        kind === "network"
          ? cleanFilters({
              ...filters,
              organization_type: "NETWORK_INSTITUTION",
              relationship_status_code: filters.status_code,
              status_code: "",
              sort_by: sortBy
            })
          : cleanFilters({ ...filters, sort_by: sortBy });
      const endpoint =
        kind === "companies"
          ? `/api/v1/organizations?${new URLSearchParams(organizationFilters).toString()}&limit=${pageSize}&skip=${nextOffset}`
            : kind === "network"
            ? `/api/v1/organizations?${new URLSearchParams(organizationFilters).toString()}&limit=${pageSize}&skip=${nextOffset}`
            : kind === "events"
              ? `/api/v1/events?limit=200${includeArchived && isAdmin ? "&include_archived=true" : ""}`
              : `/api/v1/opportunities?limit=200${includeArchived && isAdmin ? "&include_archived=true" : ""}`;
      const endpointWithArchive = isOrganizationView && includeArchived && isAdmin ? `${endpoint}&include_archived=true` : endpoint;
      if (isOrganizationView) {
        const data = await apiRequest<PaginatedOrganizations>(endpointWithArchive);
        setRows(data.items);
        setTotalCount(data.total_count);
      } else {
        const data = await apiRequest<Array<EventRecord | Opportunity>>(endpoint);
        setRows(data);
        setTotalCount(data.length);
      }
    } catch (caught) {
      setError(caught);
    } finally {
      setIsLoading(false);
    }
  }

  async function exportOrganizations() {
    setError(null);
    try {
      const exportFilters =
        kind === "network"
          ? {
              ...filters,
              organization_type: "NETWORK_INSTITUTION",
              relationship_status_code: filters.status_code,
              status_code: "",
              sort_by: sortBy,
              include_archived: includeArchived && isAdmin ? "true" : ""
            }
          : { ...filters, sort_by: sortBy, include_archived: includeArchived && isAdmin ? "true" : "" };
      const params = new URLSearchParams(cleanFilters(exportFilters)).toString();
      const token = getStoredToken();
      const response = await fetch(apiUrl(`/api/v1/organizations/export?${params}`), {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined
      });
      if (!response.ok) {
        throw new Error(`Export failed with status ${response.status}`);
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = kind === "network" ? "network_library_export.csv" : "startup_library_export.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not export records");
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind, offset, pageSize, sortBy, includeArchived]);

  async function archiveRecord(row: Organization | EventRecord | Opportunity) {
    const reason = window.prompt(`Archive "${"name" in row ? row.name : row.title}"? Optional reason:`);
    if (reason === null) return;
    const endpoint =
      kind === "events"
        ? `/api/v1/events/${row.id}/archive`
        : kind === "opportunities"
          ? `/api/v1/opportunities/${row.id}/archive`
          : `/api/v1/organizations/${row.id}/archive`;
    await apiRequest(endpoint, {
      method: "PATCH",
      body: JSON.stringify({ reason })
    });
    await load();
  }

  async function unarchiveRecord(row: Organization | EventRecord | Opportunity) {
    const endpoint =
      kind === "events"
        ? `/api/v1/events/${row.id}/unarchive`
        : kind === "opportunities"
          ? `/api/v1/opportunities/${row.id}/unarchive`
          : `/api/v1/organizations/${row.id}/unarchive`;
    await apiRequest(endpoint, {
      method: "PATCH",
      body: JSON.stringify({ reason: "Restored from admin archived view" })
    });
    await load();
  }

  const startupStatusOptions = useMemo(
    () =>
      statuses
        .filter((status) => status.status_group === "COMPANY_STATUS" && startupProcessStatusCodes.includes(status.code))
        .sort((a, b) => startupProcessStatusCodes.indexOf(a.code) - startupProcessStatusCodes.indexOf(b.code)),
    [statuses]
  );
  const statusOptions = useMemo(
    () => (kind === "network" ? statuses.filter((status) => status.status_group === "NETWORK_RELATIONSHIP") : startupStatusOptions),
    [kind, startupStatusOptions, statuses]
  );

  return (
    <>
      <PageHeader
        eyebrow={eyebrow}
        title={title}
        description={description}
        actions={
          isOrganizationView ? (
            <div className="button-row">
              <Button variant="secondary" onClick={() => void exportOrganizations()}>
                <Download size={17} />
                Export CSV
              </Button>
              <Button onClick={() => setShowAddCompany((value) => !value)}>
                <Plus size={17} />
                {kind === "network" ? "Add Institution" : "Add Company"}
              </Button>
            </div>
          ) : kind === "events" || kind === "opportunities" ? (
            <Button onClick={() => setShowAddRecord((value) => !value)}>
              <Plus size={17} />
              {kind === "events" ? "Add Event" : "Add Opportunity"}
            </Button>
          ) : undefined
        }
      />

      {isOrganizationView ? (
        <>
          <div className="command-hero">
            <div>
              <h2>{kind === "network" ? "Network relationship workspace" : "AI ecosystem workspace"}</h2>
              <p>
                {kind === "network"
                  ? "Filter institutions by category, expertise, geography, contact person, relationship, notes, and added-by attribution."
                  : "Search across names, domains, use-cases, tags, source, and Borusan company relevance. For example: GenAI + Borcelik."}
              </p>
            </div>
            <Badge tone="info">{isLoading ? "Syncing" : `${totalCount} records`}</Badge>
          </div>
          <form
            className="crm-toolbar"
            onSubmit={(event) => {
              event.preventDefault();
              setOffset(0);
              void load(0);
            }}
          >
            {kind === "network" ? (
              <>
                <Input
                  aria-label="Institution"
                  placeholder="Search institution"
                  value={filters.q}
                  onChange={(event) => setFilters((value) => ({ ...value, q: event.target.value }))}
                />
                <Select
                  aria-label="Category"
                  value={filters.organization_subtype}
                  onChange={(event) => setFilters((value) => ({ ...value, organization_subtype: event.target.value }))}
                >
                  <option value="">Any category</option>
                  {networkCategoryOptions.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </Select>
                <Input
                  aria-label="Expertise"
                  placeholder="Expertise"
                  value={filters.expertise}
                  onChange={(event) => setFilters((value) => ({ ...value, expertise: event.target.value }))}
                />
                <Input
                  aria-label="Geography"
                  placeholder="Geography"
                  value={filters.geography}
                  onChange={(event) => setFilters((value) => ({ ...value, geography: event.target.value }))}
                />
                <Input
                  aria-label="Contact Person"
                  placeholder="Contact Person"
                  value={filters.contact_person}
                  onChange={(event) => setFilters((value) => ({ ...value, contact_person: event.target.value }))}
                />
                <Select
                  aria-label="Relationship"
                  value={filters.status_code}
                  onChange={(event) => setFilters((value) => ({ ...value, status_code: event.target.value }))}
                >
                  <option value="">Any relationship</option>
                  {statusOptions.map((status) => (
                    <option key={status.id} value={status.code}>
                      {status.label}
                    </option>
                  ))}
                </Select>
                <Input
                  aria-label="Notes"
                  placeholder="Notes"
                  value={filters.notes}
                  onChange={(event) => setFilters((value) => ({ ...value, notes: event.target.value }))}
                />
                <Input
                  aria-label="Added by"
                  placeholder="Added by"
                  value={filters.added_by}
                  onChange={(event) => setFilters((value) => ({ ...value, added_by: event.target.value }))}
                />
              </>
            ) : (
              <>
                <Input
                  aria-label="Search"
                  placeholder="Search name, domain, solution, tag, source..."
                  value={filters.q}
                  onChange={(event) => setFilters((value) => ({ ...value, q: event.target.value }))}
                />
                <Select
                  aria-label="Type"
                  value={filters.organization_type}
                  onChange={(event) => setFilters((value) => ({ ...value, organization_type: event.target.value }))}
                >
                  {typeOptions.map((type) => (
                    <option key={type} value={type}>
                      {type.replaceAll("_", " ")}
                    </option>
                  ))}
                </Select>
                <Select
                  aria-label="Category"
                  value={filters.category}
                  onChange={(event) => setFilters((value) => ({ ...value, category: event.target.value }))}
                >
                  <option value="">Any category</option>
                  {categories.map((category) => (
                    <option key={category.code ?? category.label ?? ""} value={category.code ?? category.label ?? ""}>
                      {category.label ?? category.code}
                    </option>
                  ))}
                </Select>
                <Input
                  aria-label="Vertical"
                  label={<VerticalLabel />}
                  placeholder="Vertical"
                  value={filters.vertical}
                  onChange={(event) => setFilters((value) => ({ ...value, vertical: event.target.value }))}
                />
                <Select
                  aria-label="Borusan company"
                  value={filters.borusan_company_code}
                  onChange={(event) => setFilters((value) => ({ ...value, borusan_company_code: event.target.value }))}
                >
                  <option value="">Any Borusan fit</option>
                  {borusanCompanies.map((company) => (
                    <option key={company.id} value={company.code}>
                      {company.code}
                    </option>
                  ))}
                </Select>
                <Select
                  aria-label="Status"
                  value={filters.status_code}
                  onChange={(event) => setFilters((value) => ({ ...value, status_code: event.target.value }))}
                >
                  <option value="">Any status</option>
                  {statusOptions.map((status) => (
                    <option key={status.id} value={status.code}>
                      {startupProcessStatusLabels[status.code] ?? status.label}
                    </option>
                  ))}
                </Select>
                <Input
                  aria-label="Geography"
                  placeholder="Geography"
                  value={filters.geography}
                  onChange={(event) => setFilters((value) => ({ ...value, geography: event.target.value }))}
                />
                <Input
                  aria-label="Source"
                  placeholder="Source"
                  value={filters.source}
                  onChange={(event) => setFilters((value) => ({ ...value, source: event.target.value }))}
                />
                <Input
                  aria-label="Added by"
                  placeholder="Added by"
                  value={filters.added_by}
                  onChange={(event) => setFilters((value) => ({ ...value, added_by: event.target.value }))}
                />
                <Input
                  aria-label="Added from"
                  type="date"
                  value={filters.added_from_date}
                  onChange={(event) => setFilters((value) => ({ ...value, added_from_date: event.target.value }))}
                />
                <Input
                  aria-label="Added to"
                  type="date"
                  value={filters.added_to_date}
                  onChange={(event) => setFilters((value) => ({ ...value, added_to_date: event.target.value }))}
                />
                <Select
                  aria-label="Has website"
                  value={filters.has_website}
                  onChange={(event) => setFilters((value) => ({ ...value, has_website: event.target.value }))}
                >
                  <option value="">Website: any</option>
                  <option value="true">Has website</option>
                  <option value="false">Missing website</option>
                </Select>
              </>
            )}
            <Select aria-label="Sort" value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
              <option value="newest">Newest first</option>
              <option value="oldest">Oldest first</option>
              <option value="name_asc">{kind === "network" ? "Institution A-Z" : "Name A-Z"}</option>
              <option value="last_contact_desc">Last contact newest</option>
              <option value="last_contact_asc">Last contact oldest</option>
            </Select>
            {isAdmin ? (
              <Select
                aria-label="Archived records"
                value={includeArchived ? "true" : "false"}
                onChange={(event) => {
                  setIncludeArchived(event.target.value === "true");
                  setOffset(0);
                  window.setTimeout(() => void load(), 0);
                }}
              >
                <option value="false">Hide archived</option>
                <option value="true">Show archived</option>
              </Select>
            ) : null}
            <Button type="submit">
              <Search size={16} />
              Search
            </Button>
          </form>
          {showAddCompany ? (
            <AddCompanyPanel
              statuses={startupStatusOptions}
              categories={categories}
              defaultType={kind === "network" ? "NETWORK_INSTITUTION" : "STARTUP"}
              onCreated={() => {
                setShowAddCompany(false);
                void load();
              }}
            />
          ) : null}
        </>
      ) : null}

      {!isOrganizationView && showAddRecord ? (
        <AddOperationalRecordPanel
          kind={kind}
          onCreated={() => {
            setShowAddRecord(false);
            void load();
          }}
        />
      ) : null}

      {!isOrganizationView && isAdmin ? (
        <SectionCard>
          <div className="section-heading section-heading--inline">
            <div>
              <h2>Admin cleanup view</h2>
              <p>Archived records are hidden by default and can be restored from this view.</p>
            </div>
            <Select value={includeArchived ? "true" : "false"} onChange={(event) => setIncludeArchived(event.target.value === "true")}>
              <option value="false">Hide archived</option>
              <option value="true">Show archived</option>
            </Select>
          </div>
        </SectionCard>
      ) : null}

      <SectionCard>
        <div className="section-heading section-heading--inline">
          <div>
            <h2>{isOrganizationView ? "CRM records" : "Records"}</h2>
            <p>{isLoading ? "Loading from backend..." : `${rows.length} shown of ${totalCount || rows.length} records`}</p>
          </div>
          <Badge tone="info">{kind === "companies" ? "Enriched" : "MVP list"}</Badge>
        </div>
        {error ? <ErrorState title="Could not load records" error={error} onRetry={() => void load()} /> : null}
        {!error && rows.length ? (
          <DomainTable
            kind={kind}
            rows={rows}
            isAdmin={isAdmin}
            onArchive={(row) => void archiveRecord(row)}
            onUnarchive={(row) => void unarchiveRecord(row)}
            onOpen={(id) => {
              if (isOrganizationView) router.push(`/companies/${id}`);
              if (kind === "opportunities") router.push(`/opportunities/${id}`);
              if (kind === "events") router.push(`/events/${id}`);
            }}
          />
        ) : null}
        {!error && !rows.length && !isLoading ? (
          <EmptyState
            title="No records match this view"
            description="Import committed data or add the first manual CRM record."
          />
        ) : null}
        {isOrganizationView ? (
          <PaginationControls
            offset={offset}
            pageSize={pageSize}
            totalCount={totalCount}
            onPageSizeChange={(nextPageSize) => {
              setPageSize(nextPageSize);
              setOffset(0);
            }}
            onOffsetChange={setOffset}
          />
        ) : null}
      </SectionCard>
    </>
  );
}

function AddOperationalRecordPanel({ kind, onCreated }: { kind: DomainKind; onCreated: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [companies, setCompanies] = useState<BorusanCompany[]>([]);
  const [eventForm, setEventForm] = useState({ name: "", date_text: "", location_text: "", area_text: "", comments: "" });
  const [opportunityForm, setOpportunityForm] = useState({
    title: "",
    organization_id: "",
    borusan_company_id: "",
    stage: "IDEA",
    topic: ""
  });

  useEffect(() => {
    if (kind !== "opportunities") return;
    Promise.all([
      apiRequest<PaginatedOrganizations>("/api/v1/organizations?limit=500"),
      apiRequest<BorusanCompany[]>("/api/v1/borusan-companies?is_active=true&limit=100")
    ])
      .then(([orgs, companyRows]) => {
        setOrganizations(orgs.items);
        setCompanies(companyRows);
      })
      .catch(() => undefined);
  }, [kind]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      if (kind === "events") {
        await apiRequest<EventRecord>("/api/v1/events", {
          method: "POST",
          body: JSON.stringify({ ...cleanFilters(eventForm), ai_program_relevance: "UNKNOWN", value_creation_potential: "UNKNOWN" })
        });
      } else {
        await apiRequest<Opportunity>("/api/v1/opportunities", {
          method: "POST",
          body: JSON.stringify({ ...cleanFilters(opportunityForm), opportunity_type: "POC" })
        });
      }
      onCreated();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create record");
    }
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>{kind === "events" ? "Add event" : "Add opportunity"}</h2>
        <p>Manual CRM actions are saved directly into normalized domain tables.</p>
      </div>
      <form className="form-stack" onSubmit={submit}>
        {kind === "events" ? (
          <>
            <Input label="Event name" required value={eventForm.name} onChange={(event) => setEventForm({ ...eventForm, name: event.target.value })} />
            <div className="two-column">
              <Input label="Date text" value={eventForm.date_text} onChange={(event) => setEventForm({ ...eventForm, date_text: event.target.value })} />
              <Input label="Location" required value={eventForm.location_text} onChange={(event) => setEventForm({ ...eventForm, location_text: event.target.value })} />
            </div>
            <Input label="Area / category" value={eventForm.area_text} onChange={(event) => setEventForm({ ...eventForm, area_text: event.target.value })} />
          </>
        ) : (
          <>
            <Input label="Title" required value={opportunityForm.title} onChange={(event) => setOpportunityForm({ ...opportunityForm, title: event.target.value })} />
            <div className="two-column">
              <Select label="Organization" required value={opportunityForm.organization_id} onChange={(event) => setOpportunityForm({ ...opportunityForm, organization_id: event.target.value })}>
                <option value="">Select organization</option>
                {organizations.map((organization) => (
                  <option key={organization.id} value={organization.id}>
                    {organization.name}
                  </option>
                ))}
              </Select>
              <Select label="Borusan company" required value={opportunityForm.borusan_company_id} onChange={(event) => setOpportunityForm({ ...opportunityForm, borusan_company_id: event.target.value })}>
                <option value="">Select company</option>
                {companies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.code}
                  </option>
                ))}
              </Select>
            </div>
            <Input label="Topic" value={opportunityForm.topic} onChange={(event) => setOpportunityForm({ ...opportunityForm, topic: event.target.value })} />
          </>
        )}
        {error ? <div className="alert alert--error">{error}</div> : null}
        <Button type="submit">Create</Button>
      </form>
    </SectionCard>
  );
}

function cleanFilters(filters: Record<string, string>) {
  return Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== ""));
}

function AddCompanyPanel({
  statuses,
  categories,
  defaultType,
  onCreated
}: {
  statuses: StatusOption[];
  categories: CategoryOption[];
  defaultType: string;
  onCreated: () => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({
    name: "",
    organization_type: defaultType,
    organization_subtype: "",
    category_code: "",
    category_label: "",
    vertical_text: "",
    website_url: "",
    solution_summary: "",
    geography_text: "",
    source_text: "MANUAL",
    lifecycle_status_id: ""
  });

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSaving(true);
    try {
      await apiRequest<Organization>("/api/v1/organizations", {
        method: "POST",
        body: JSON.stringify(cleanFilters(form))
      });
      onCreated();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create organization");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Add company</h2>
        <p>Manual entries are tracked to the logged-in CRM user for future contribution metrics.</p>
      </div>
      <form className="form-stack" onSubmit={submit}>
        <div className="two-column">
          <Input label="Name" required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          <Select
            label="Type"
            value={form.organization_type}
            onChange={(event) => setForm({ ...form, organization_type: event.target.value })}
          >
            {typeOptions.map((type) => (
              <option key={type} value={type}>
                {type.replaceAll("_", " ")}
              </option>
            ))}
          </Select>
          <Input
            label="Subtype"
            value={form.organization_subtype}
            onChange={(event) => setForm({ ...form, organization_subtype: event.target.value })}
          />
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
          <Input
            label={<VerticalLabel />}
            value={form.vertical_text}
            onChange={(event) => setForm({ ...form, vertical_text: event.target.value })}
          />
          <Input
            label="Website"
            value={form.website_url}
            onChange={(event) => setForm({ ...form, website_url: event.target.value })}
          />
          <Input
            label="Geography"
            value={form.geography_text}
            onChange={(event) => setForm({ ...form, geography_text: event.target.value })}
          />
          <Select
            label="Lifecycle status"
            value={form.lifecycle_status_id}
            onChange={(event) => setForm({ ...form, lifecycle_status_id: event.target.value })}
          >
            <option value="">Not set</option>
            {statuses.map((status) => (
              <option key={status.id} value={status.id}>
                {startupProcessStatusLabels[status.code] ?? status.label}
              </option>
            ))}
          </Select>
        </div>
        <Input
          label="Solution / use-case summary"
          value={form.solution_summary}
          onChange={(event) => setForm({ ...form, solution_summary: event.target.value })}
        />
        {error ? <div className="alert alert--error">{error}</div> : null}
        <div className="button-row">
          <Button disabled={isSaving} type="submit">
            {isSaving ? "Saving..." : "Create company"}
          </Button>
        </div>
      </form>
    </SectionCard>
  );
}

function PaginationControls({
  offset,
  pageSize,
  totalCount,
  onPageSizeChange,
  onOffsetChange
}: {
  offset: number;
  pageSize: number;
  totalCount: number;
  onPageSizeChange: (value: number) => void;
  onOffsetChange: (value: number) => void;
}) {
  const currentPage = Math.floor(offset / pageSize) + 1;
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  return (
    <div className="pagination-row">
      <span>
        Page {currentPage} of {totalPages}
      </span>
      <Select
        aria-label="Page size"
        value={String(pageSize)}
        onChange={(event) => onPageSizeChange(Number(event.target.value))}
      >
        <option value="50">50</option>
        <option value="100">100</option>
        <option value="200">200</option>
      </Select>
      <div className="button-row">
        <Button variant="secondary" disabled={offset === 0} onClick={() => onOffsetChange(Math.max(0, offset - pageSize))}>
          Previous
        </Button>
        <Button
          variant="secondary"
          disabled={offset + pageSize >= totalCount}
          onClick={() => onOffsetChange(offset + pageSize)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

function DomainTable({
  kind,
  rows,
  isAdmin,
  onArchive,
  onUnarchive,
  onOpen
}: {
  kind: DomainKind;
  rows: Array<Organization | EventRecord | Opportunity>;
  isAdmin: boolean;
  onArchive: (row: Organization | EventRecord | Opportunity) => void;
  onUnarchive: (row: Organization | EventRecord | Opportunity) => void;
  onOpen: (id: string) => void;
}) {
  if (kind === "events") {
    return (
      <Table
        rows={rows as EventRecord[]}
        getRowKey={(row) => row.id}
        onRowClick={(row) => onOpen(row.id)}
        columns={[
          { key: "name", header: "Event", render: (row) => row.name },
          { key: "date", header: "Date", render: (row) => row.starts_on ?? row.date_text ?? EMPTY_VALUE },
          { key: "location", header: "Location", render: (row) => row.location_text },
          { key: "relevance", header: "Relevance", render: (row) => <Badge>{row.ai_program_relevance}</Badge> },
          { key: "value", header: "Value", render: (row) => <Badge tone="info">{row.value_creation_potential}</Badge> },
          archiveColumn<EventRecord>(isAdmin, onArchive, onUnarchive)
        ]}
      />
    );
  }

  if (kind === "opportunities") {
    return (
      <Table
        rows={rows as Opportunity[]}
        getRowKey={(row) => row.id}
        onRowClick={(row) => onOpen(row.id)}
        columns={[
          { key: "title", header: "Opportunity", render: (row) => row.title },
          { key: "stage", header: "Stage", render: (row) => <Badge tone="info">{row.stage}</Badge> },
          { key: "topic", header: "Topic", render: (row) => row.topic ?? EMPTY_VALUE },
          { key: "date", header: "Last contact", render: (row) => row.last_contact_date ?? EMPTY_VALUE },
          archiveColumn<Opportunity>(isAdmin, onArchive, onUnarchive)
        ]}
      />
    );
  }

  if (kind === "network") {
    return (
      <Table
        rows={rows as Organization[]}
        getRowKey={(row) => row.id}
        onRowClick={(row) => onOpen(row.id)}
        columns={[
          {
            key: "institution",
            header: "Institution",
            render: (row) => (
              <div className="record-title">
                <strong>{row.name}</strong>
                {row.website_domain ?? row.website_url ? (
                  <span className="record-subtitle">{row.website_domain ?? row.website_url}</span>
                ) : null}
              </div>
            )
          },
          { key: "addedBy", header: "Added by", render: (row) => row.added_by_display ?? row.added_by_text ?? EMPTY_VALUE },
          {
            key: "category",
            header: "Category",
            render: (row) => (row.organization_subtype ? <Badge tone="info">{row.organization_subtype}</Badge> : EMPTY_VALUE)
          },
          { key: "expertise", header: "Expertise", render: (row) => row.expertise_text ?? EMPTY_VALUE },
          { key: "geography", header: "Geography", render: (row) => row.geography_text ?? EMPTY_VALUE },
          {
            key: "contactPerson",
            header: "Contact Person",
            render: (row) => row.primary_contact?.full_name ?? row.primary_contact?.email ?? EMPTY_VALUE
          },
          {
            key: "relationship",
            header: "Relationship",
            render: (row) => (row.relationship_status?.label ? <Badge tone="info">{row.relationship_status.label}</Badge> : EMPTY_VALUE)
          },
          {
            key: "notes",
            header: "Notes",
            render: (row) => (row.notes_preview ? <span title={row.notes_preview}>{row.notes_preview.slice(0, 120)}</span> : EMPTY_VALUE)
          },
          archiveColumn<Organization>(isAdmin, onArchive, onUnarchive)
        ]}
      />
    );
  }

  return (
    <Table
      rows={rows as Organization[]}
      getRowKey={(row) => row.id}
      onRowClick={(row) => onOpen(row.id)}
      columns={[
        {
          key: "name",
          header: "Organization",
          render: (row) => (
            <div className="record-title">
              <strong>{row.name}</strong>
              {row.website_domain ?? row.website_url ? (
                <span className="record-subtitle">{row.website_domain ?? row.website_url}</span>
              ) : (
                <span className="record-subtitle empty-value">No website yet</span>
              )}
            </div>
          )
        },
        { key: "type", header: "Type", render: (row) => <Badge>{row.organization_type}</Badge> },
        { key: "category", header: "Category", render: (row) => row.category_label ? <Badge tone="info">{row.category_label}</Badge> : EMPTY_VALUE },
        { key: "vertical", header: "Vertical", render: (row) => row.vertical_text ?? EMPTY_VALUE },
        {
          key: "solution",
          header: "Solution / use-case",
          render: (row) => row.solution_summary ? <span title={row.solution_summary}>{row.solution_summary.slice(0, 110)}</span> : EMPTY_VALUE
        },
        {
          key: "fit",
          header: "Borusan fit",
          render: (row) => (
            <div className="chip-row">
              {(row.borusan_fit_summary ?? []).slice(0, 4).map((fit) => (
                <Badge key={fit.id} tone={fit.fit_level === "HIGH" ? "success" : "info"}>
                  {fit.borusan_company_code ?? fit.borusan_company_name}: {fit.fit_level}
                </Badge>
              ))}
              {!(row.borusan_fit_summary ?? []).length ? EMPTY_VALUE : null}
            </div>
          )
        },
        {
          key: "status",
          header: "Process status",
          render: (row) =>
            row.lifecycle_status?.code ? (
              <Badge tone="info">{startupProcessStatusLabels[row.lifecycle_status.code] ?? row.lifecycle_status.label}</Badge>
            ) : (
              EMPTY_VALUE
            )
        },
        { key: "geo", header: "Geography", render: (row) => row.geography_text ?? EMPTY_VALUE },
        { key: "addedBy", header: "Added by", render: (row) => row.added_by_display ?? row.added_by_text ?? EMPTY_VALUE },
        { key: "addedDate", header: "Added date", render: (row) => formatDateOnly(row.added_at ?? row.created_at) },
        { key: "lastContact", header: "Last contact", render: (row) => formatDateOnly(row.last_contact_date) },
        { key: "source", header: "Source", render: (row) => row.source_text ?? EMPTY_VALUE },
        {
          key: "activity",
          header: "Activity",
          render: (row) => `${row.contact_count ?? 0} contacts / ${row.note_count ?? 0} notes / ${row.opportunity_count ?? 0} opps / ${row.deck_count ?? 0} decks`
        },
        archiveColumn<Organization>(isAdmin, onArchive, onUnarchive)
      ]}
    />
  );
}

function archiveColumn<T extends Organization | EventRecord | Opportunity>(
  isAdmin: boolean,
  onArchive: (row: Organization | EventRecord | Opportunity) => void,
  onUnarchive: (row: Organization | EventRecord | Opportunity) => void
) {
  return {
    key: "archive",
    header: "Cleanup",
    render: (row: T) =>
      isAdmin ? (
        <Button
          variant={row.is_archived ? "secondary" : "danger"}
          onClick={(event) => {
            event.stopPropagation();
            row.is_archived ? onUnarchive(row) : onArchive(row);
          }}
        >
          {row.is_archived ? "Unarchive" : "Archive"}
        </Button>
      ) : row.is_archived ? (
        <Badge tone="warning">Archived</Badge>
      ) : (
        EMPTY_VALUE
      )
  };
}

function formatDateOnly(value?: string | null) {
  if (!value) return EMPTY_VALUE;
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}
