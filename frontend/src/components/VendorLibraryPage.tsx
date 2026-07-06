"use client";

import { Plus, Search, Store } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Input, Select } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { StarRating } from "@/components/ui/StarRating";
import { Table } from "@/components/ui/Table";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { canEditSection } from "@/lib/sectionAccess";
import type { CurrentUserSectionAccessResponse, PaginatedVendors, SectionAccessLevel, Vendor } from "@/types/api";

const EMPTY_VALUE = <span className="empty-value">—</span>;

const STATUS_LABELS: Record<string, string> = {
  PROSPECT: "Prospect",
  EVALUATING: "Evaluating",
  ACTIVE: "Active",
  ON_HOLD: "On Hold",
  DISCONTINUED: "Discontinued"
};

function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

function formatDateOnly(value?: string | null) {
  if (!value) return EMPTY_VALUE;
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}

export function VendorLibraryPage() {
  const router = useRouter();
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";
  const [rows, setRows] = useState<Vendor[]>([]);
  const [statuses, setStatuses] = useState<string[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [error, setError] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddVendor, setShowAddVendor] = useState(false);
  const [pageSize, setPageSize] = useState(50);
  const [offset, setOffset] = useState(0);
  const [sortBy, setSortBy] = useState("newest");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [sectionAccess, setSectionAccess] = useState<Record<string, SectionAccessLevel> | null>(null);
  const [filters, setFilters] = useState({ q: "", category: "", status: "", geography: "" });

  const canEdit = canEditSection(sectionAccess, user, "VENDOR_LIBRARY");

  useEffect(() => {
    apiRequest<CurrentUserSectionAccessResponse>("/api/v1/users/me/section-access")
      .then((response) => setSectionAccess(response.access))
      .catch(() => setSectionAccess(null));
  }, []);

  async function load(nextOffset = offset) {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams(
        Object.fromEntries(Object.entries({ ...filters, sort_by: sortBy }).filter(([, value]) => value !== ""))
      );
      params.set("limit", String(pageSize));
      params.set("skip", String(nextOffset));
      if (includeArchived && isAdmin) params.set("include_archived", "true");
      const data = await apiRequest<PaginatedVendors>(`/api/v1/vendors?${params.toString()}`);
      setRows(data.items);
      setTotalCount(data.total_count);
      setStatuses(data.statuses);
    } catch (caught) {
      setError(caught);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset, pageSize, sortBy, includeArchived]);

  async function archiveVendor(vendor: Vendor) {
    const reason = window.prompt(`Archive "${vendor.name}"? Optional reason:`);
    if (reason === null) return;
    await apiRequest(`/api/v1/vendors/${vendor.id}/archive`, { method: "PATCH", body: JSON.stringify({ reason }) });
    await load();
  }

  async function unarchiveVendor(vendor: Vendor) {
    await apiRequest(`/api/v1/vendors/${vendor.id}/unarchive`, {
      method: "PATCH",
      body: JSON.stringify({ reason: "Restored from admin archived view" })
    });
    await load();
  }

  return (
    <>
      <PageHeader
        eyebrow="Library"
        title="Vendor Library"
        description="Technology and service vendors with weighted team ratings, separate from the startup and network libraries."
        actions={
          canEdit ? (
            <Button onClick={() => setShowAddVendor((value) => !value)}>
              <Plus size={17} />
              Add Vendor
            </Button>
          ) : undefined
        }
      />

      <form
        className="crm-toolbar"
        onSubmit={(event) => {
          event.preventDefault();
          setOffset(0);
          void load(0);
        }}
      >
        <Input
          aria-label="Search"
          placeholder="Search name, category, description..."
          value={filters.q}
          onChange={(event) => setFilters((value) => ({ ...value, q: event.target.value }))}
        />
        <Input
          aria-label="Category"
          placeholder="Category"
          value={filters.category}
          onChange={(event) => setFilters((value) => ({ ...value, category: event.target.value }))}
        />
        <Select
          aria-label="Status"
          value={filters.status}
          onChange={(event) => setFilters((value) => ({ ...value, status: event.target.value }))}
        >
          <option value="">Any status</option>
          {statuses.map((status) => (
            <option key={status} value={status}>
              {statusLabel(status)}
            </option>
          ))}
        </Select>
        <Input
          aria-label="Geography"
          placeholder="Geography"
          value={filters.geography}
          onChange={(event) => setFilters((value) => ({ ...value, geography: event.target.value }))}
        />
        <Select aria-label="Sort" value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
          <option value="name_asc">Name A-Z</option>
          <option value="score_desc">Score high to low</option>
          <option value="score_asc">Score low to high</option>
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

      {showAddVendor && canEdit ? (
        <AddVendorPanel
          statuses={statuses}
          onCreated={() => {
            setShowAddVendor(false);
            void load();
          }}
        />
      ) : null}

      <SectionCard>
        <div className="section-heading section-heading--inline">
          <div>
            <h2>Vendors</h2>
            <p>{isLoading ? "Loading from backend..." : `${rows.length} shown of ${totalCount} vendors`}</p>
          </div>
          <Badge tone="info">Weighted ratings</Badge>
        </div>
        {error ? <ErrorState title="Could not load vendors" error={error} onRetry={() => void load()} /> : null}
        {!error && rows.length ? (
          <Table
            rows={rows}
            getRowKey={(row) => row.id}
            onRowClick={(row) => router.push(`/vendors/${row.id}`)}
            columns={[
              {
                key: "name",
                header: "Vendor",
                render: (row) => (
                  <div className="record-title">
                    <strong>{row.name}</strong>
                    {row.website_url ? (
                      <span className="record-subtitle">{row.website_url.replace(/^https?:\/\//, "")}</span>
                    ) : (
                      <span className="record-subtitle empty-value">No website yet</span>
                    )}
                  </div>
                )
              },
              { key: "category", header: "Category", render: (row) => (row.category_text ? <Badge tone="info">{row.category_text}</Badge> : EMPTY_VALUE) },
              {
                key: "score",
                header: "Overall score",
                render: (row) =>
                  row.rating_summary.overall_score != null ? (
                    <span className="rating-value">
                      <StarRating value={row.rating_summary.overall_score} size={15} ariaLabel={`${row.name} overall score`} />
                      <strong>{row.rating_summary.overall_score.toFixed(1)}</strong>
                      <span>
                        {row.rating_summary.rating_count} rating{row.rating_summary.rating_count === 1 ? "" : "s"}
                      </span>
                    </span>
                  ) : (
                    <span className="empty-value">Not rated yet</span>
                  )
              },
              { key: "status", header: "Status", render: (row) => <Badge>{statusLabel(row.status)}</Badge> },
              { key: "geo", header: "Geography", render: (row) => row.geography_text ?? EMPTY_VALUE },
              { key: "addedBy", header: "Added by", render: (row) => row.added_by_display ?? EMPTY_VALUE },
              { key: "addedDate", header: "Date added", render: (row) => formatDateOnly(row.added_at ?? row.created_at) },
              { key: "lastContact", header: "Last contacted", render: (row) => formatDateOnly(row.last_contact_date) },
              {
                key: "archive",
                header: "Cleanup",
                render: (row) =>
                  isAdmin ? (
                    <Button
                      variant={row.is_archived ? "secondary" : "danger"}
                      onClick={(event) => {
                        event.stopPropagation();
                        row.is_archived ? void unarchiveVendor(row) : void archiveVendor(row);
                      }}
                    >
                      {row.is_archived ? "Unarchive" : "Archive"}
                    </Button>
                  ) : row.is_archived ? (
                    <Badge tone="warning">Archived</Badge>
                  ) : (
                    EMPTY_VALUE
                  )
              }
            ]}
          />
        ) : null}
        {!error && !rows.length && !isLoading ? (
          <EmptyState
            title="No vendors yet"
            description={
              canEdit
                ? 'Add the first vendor with "Add Vendor" to start building the shared vendor knowledge base.'
                : "Vendors added by the team will appear here with their weighted ratings."
            }
          />
        ) : null}
        {totalCount > pageSize ? (
          <div className="pagination-row">
            <span>
              Page {Math.floor(offset / pageSize) + 1} of {Math.max(1, Math.ceil(totalCount / pageSize))}
            </span>
            <Select aria-label="Page size" value={String(pageSize)} onChange={(event) => { setPageSize(Number(event.target.value)); setOffset(0); }}>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
            </Select>
            <div className="button-row">
              <Button variant="secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - pageSize))}>
                Previous
              </Button>
              <Button variant="secondary" disabled={offset + pageSize >= totalCount} onClick={() => setOffset(offset + pageSize)}>
                Next
              </Button>
            </div>
          </div>
        ) : null}
      </SectionCard>
    </>
  );
}

function AddVendorPanel({ statuses, onCreated }: { statuses: string[]; onCreated: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({
    name: "",
    category_text: "",
    description: "",
    contact_info: "",
    website_url: "",
    status: "PROSPECT",
    geography_text: "",
    last_contact_date: ""
  });

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSaving(true);
    try {
      const payload = Object.fromEntries(Object.entries(form).filter(([, value]) => value !== ""));
      await apiRequest<Vendor>("/api/v1/vendors", { method: "POST", body: JSON.stringify(payload) });
      onCreated();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create vendor");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>
          <Store size={17} style={{ verticalAlign: -2, marginRight: 6 }} />
          Add vendor
        </h2>
        <p>Vendors are tracked separately from startups and network institutions.</p>
      </div>
      <form className="form-stack" onSubmit={submit}>
        <div className="two-column">
          <Input label="Vendor name" required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          <Input label="Category" placeholder="e.g. Cloud, Consulting, IoT hardware" value={form.category_text} onChange={(event) => setForm({ ...form, category_text: event.target.value })} />
          <Input label="Website" value={form.website_url} onChange={(event) => setForm({ ...form, website_url: event.target.value })} />
          <Select label="Status" value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
            {(statuses.length ? statuses : ["PROSPECT"]).map((status) => (
              <option key={status} value={status}>
                {statusLabel(status)}
              </option>
            ))}
          </Select>
          <Input label="Geography" value={form.geography_text} onChange={(event) => setForm({ ...form, geography_text: event.target.value })} />
          <Input label="Last contacted" type="date" value={form.last_contact_date} onChange={(event) => setForm({ ...form, last_contact_date: event.target.value })} />
        </div>
        <Input label="Contact info" placeholder="Name, email, phone..." value={form.contact_info} onChange={(event) => setForm({ ...form, contact_info: event.target.value })} />
        <Input label="Description" placeholder="What does this vendor provide?" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
        {error ? <div className="alert alert--error">{error}</div> : null}
        <div className="button-row">
          <Button disabled={isSaving} type="submit">
            {isSaving ? "Saving..." : "Create vendor"}
          </Button>
        </div>
      </form>
    </SectionCard>
  );
}
