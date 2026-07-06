"use client";

import { ArrowLeft, Save, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { Input, Select } from "@/components/ui/Input";
import { StarRating } from "@/components/ui/StarRating";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { canEditSection } from "@/lib/sectionAccess";
import type {
  CurrentUserSectionAccessResponse,
  SectionAccessLevel,
  Vendor,
  VendorDetail,
  VendorRatingUpsertResponse
} from "@/types/api";

const EMPTY_VALUE = <span className="empty-value">—</span>;

const STATUS_LABELS: Record<string, string> = {
  PROSPECT: "Prospect",
  EVALUATING: "Evaluating",
  ACTIVE: "Active",
  ON_HOLD: "On Hold",
  DISCONTINUED: "Discontinued"
};

const RATING_CATEGORIES: Array<{ key: "quality_score" | "reliability_score" | "pricing_score" | "borusan_fit_score"; label: string; weight: string }> = [
  { key: "quality_score", label: "Quality of Product/Service", weight: "35%" },
  { key: "reliability_score", label: "Reliability & Support Responsiveness", weight: "25%" },
  { key: "pricing_score", label: "Pricing / Value for Money", weight: "20%" },
  { key: "borusan_fit_score", label: "Borusan Fit / Strategic Relevance", weight: "20%" }
];

function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

function formatDateOnly(value?: string | null) {
  if (!value) return EMPTY_VALUE;
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}

export default function VendorDetailPage() {
  return (
    <ProtectedPage>
      <VendorDetailContent />
    </ProtectedPage>
  );
}

function VendorDetailContent() {
  const params = useParams<{ id: string }>();
  const vendorId = params.id;
  const { user } = useAuth();
  const [vendor, setVendor] = useState<VendorDetail | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [sectionAccess, setSectionAccess] = useState<Record<string, SectionAccessLevel> | null>(null);
  const [showEdit, setShowEdit] = useState(false);

  const canEdit = canEditSection(sectionAccess, user, "VENDOR_LIBRARY");

  useEffect(() => {
    apiRequest<CurrentUserSectionAccessResponse>("/api/v1/users/me/section-access")
      .then((response) => setSectionAccess(response.access))
      .catch(() => setSectionAccess(null));
  }, []);

  async function load() {
    setError(null);
    try {
      setVendor(await apiRequest<VendorDetail>(`/api/v1/vendors/${vendorId}`));
    } catch (caught) {
      setError(caught);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vendorId]);

  if (error) {
    return <ErrorState title="Could not load vendor" error={error} onRetry={() => void load()} />;
  }
  if (!vendor) {
    return (
      <SectionCard>
        <p>Loading vendor...</p>
      </SectionCard>
    );
  }

  const summary = vendor.rating_summary;

  return (
    <>
      <div className="button-row" style={{ marginBottom: 14 }}>
        <Link href="/vendors">
          <Button variant="ghost">
            <ArrowLeft size={16} />
            Back to Vendor Library
          </Button>
        </Link>
      </div>

      <div className="company-hero">
        <div>
          <p className="eyebrow">Vendor Library</p>
          <h1>{vendor.name}</h1>
          <div className="chip-row" style={{ marginTop: 8 }}>
            <Badge>{statusLabel(vendor.status)}</Badge>
            {vendor.category_text ? <Badge tone="info">{vendor.category_text}</Badge> : null}
            {vendor.is_archived ? <Badge tone="warning">Archived</Badge> : null}
          </div>
          {vendor.description ? <p style={{ marginTop: 10 }}>{vendor.description}</p> : null}
        </div>
        <div>
          <div className="rating-value" style={{ display: "grid", gap: 6, textAlign: "right" }}>
            <StarRating value={summary.overall_score} size={26} ariaLabel="Overall vendor score" />
            {summary.overall_score != null ? (
              <span>
                <strong style={{ fontSize: 30 }}>{summary.overall_score.toFixed(1)}</strong>
                <span style={{ marginLeft: 6 }}>
                  / 5 · {summary.rating_count} rating{summary.rating_count === 1 ? "" : "s"}
                </span>
              </span>
            ) : (
              <span className="empty-value">Not rated yet</span>
            )}
          </div>
        </div>
      </div>

      <div className="two-column" style={{ marginTop: 18, alignItems: "start" }}>
        <SectionCard>
          <div className="section-heading section-heading--inline">
            <div>
              <h2>Vendor details</h2>
              <p>Core record fields for this vendor.</p>
            </div>
            {canEdit ? (
              <Button variant="secondary" onClick={() => setShowEdit((value) => !value)}>
                {showEdit ? "Close" : "Edit"}
              </Button>
            ) : null}
          </div>
          {showEdit && canEdit ? (
            <EditVendorForm vendor={vendor} onSaved={() => { setShowEdit(false); void load(); }} />
          ) : (
            <dl className="metadata-list">
              <div>
                <dt>Website</dt>
                <dd>
                  {vendor.website_url ? (
                    <a href={vendor.website_url} rel="noreferrer" target="_blank" style={{ color: "var(--accent)" }}>
                      {vendor.website_url}
                    </a>
                  ) : (
                    EMPTY_VALUE
                  )}
                </dd>
              </div>
              <div>
                <dt>Contact info</dt>
                <dd>{vendor.contact_info ?? EMPTY_VALUE}</dd>
              </div>
              <div>
                <dt>Geography</dt>
                <dd>{vendor.geography_text ?? EMPTY_VALUE}</dd>
              </div>
              <div>
                <dt>Added by</dt>
                <dd>{vendor.added_by_display ?? EMPTY_VALUE}</dd>
              </div>
              <div>
                <dt>Date added</dt>
                <dd>{formatDateOnly(vendor.added_at ?? vendor.created_at)}</dd>
              </div>
              <div>
                <dt>Last contacted</dt>
                <dd>{formatDateOnly(vendor.last_contact_date)}</dd>
              </div>
            </dl>
          )}
        </SectionCard>

        <div className="detail-grid">
          <SectionCard>
            <div className="section-heading">
              <h2>Score breakdown</h2>
              <p>Team averages per weighted category.</p>
            </div>
            {RATING_CATEGORIES.map((category) => (
              <div className="rating-category-row" key={category.key}>
                <span>{category.label}</span>
                <StarRating value={summary.category_averages[category.key]} size={15} ariaLabel={`${category.label} average`} />
                <span className="rating-weight">{category.weight}</span>
              </div>
            ))}
          </SectionCard>

          {canEdit && !vendor.is_archived ? (
            <MyRatingCard vendor={vendor} onChanged={() => void load()} />
          ) : null}

          <SectionCard>
            <div className="section-heading">
              <h2>Team ratings</h2>
              <p>{vendor.ratings.length ? "Individual weighted scores per rater." : "No one has rated this vendor yet."}</p>
            </div>
            {vendor.ratings.map((rating) => (
              <div className="rating-category-row" key={rating.id} style={{ gridTemplateColumns: "minmax(0,1fr) auto auto" }}>
                <span>
                  {rating.rater?.full_name ?? rating.rater?.email ?? "Unknown user"}
                  {rating.comment ? <span style={{ display: "block", fontWeight: 450 }}>{rating.comment}</span> : null}
                </span>
                <StarRating value={rating.weighted_score} size={14} ariaLabel="Rater weighted score" />
                <strong>{rating.weighted_score.toFixed(1)}</strong>
              </div>
            ))}
          </SectionCard>
        </div>
      </div>
    </>
  );
}

function MyRatingCard({ vendor, onChanged }: { vendor: VendorDetail; onChanged: () => void }) {
  const [scores, setScores] = useState<Record<string, number>>({
    quality_score: vendor.my_rating?.quality_score ?? 0,
    reliability_score: vendor.my_rating?.reliability_score ?? 0,
    pricing_score: vendor.my_rating?.pricing_score ?? 0,
    borusan_fit_score: vendor.my_rating?.borusan_fit_score ?? 0
  });
  const [comment, setComment] = useState(vendor.my_rating?.comment ?? "");
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const allRated = RATING_CATEGORIES.every((category) => (scores[category.key] ?? 0) >= 1);

  async function save() {
    setError(null);
    setIsSaving(true);
    try {
      await apiRequest<VendorRatingUpsertResponse>(`/api/v1/vendors/${vendor.id}/my-rating`, {
        method: "PUT",
        body: JSON.stringify({ ...scores, comment: comment || null })
      });
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save rating");
    } finally {
      setIsSaving(false);
    }
  }

  async function removeRating() {
    setError(null);
    try {
      await apiRequest<VendorRatingUpsertResponse>(`/api/v1/vendors/${vendor.id}/my-rating`, { method: "DELETE" });
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not remove rating");
    }
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Your rating</h2>
        <p>{vendor.my_rating ? "Update your scores; the overall average recalculates instantly." : "Rate each category from 1 to 5 stars."}</p>
      </div>
      {RATING_CATEGORIES.map((category) => (
        <div className="rating-category-row" key={category.key}>
          <span>{category.label}</span>
          <StarRating
            value={scores[category.key]}
            onChange={(value) => setScores((current) => ({ ...current, [category.key]: value }))}
            size={19}
            ariaLabel={category.label}
          />
          <span className="rating-weight">{category.weight}</span>
        </div>
      ))}
      <Input label="Comment (optional)" value={comment} onChange={(event) => setComment(event.target.value)} />
      {error ? <div className="alert alert--error" style={{ marginTop: 10 }}>{error}</div> : null}
      <div className="button-row" style={{ marginTop: 12 }}>
        <Button disabled={!allRated || isSaving} onClick={() => void save()}>
          <Save size={16} />
          {isSaving ? "Saving..." : vendor.my_rating ? "Update rating" : "Save rating"}
        </Button>
        {vendor.my_rating ? (
          <Button variant="ghost" onClick={() => void removeRating()}>
            <Trash2 size={16} />
            Remove my rating
          </Button>
        ) : null}
      </div>
      {!allRated ? <p style={{ marginTop: 8, color: "var(--muted)", fontSize: 13 }}>Rate all four categories to enable saving.</p> : null}
    </SectionCard>
  );
}

function EditVendorForm({ vendor, onSaved }: { vendor: Vendor; onSaved: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({
    name: vendor.name,
    category_text: vendor.category_text ?? "",
    description: vendor.description ?? "",
    contact_info: vendor.contact_info ?? "",
    website_url: vendor.website_url ?? "",
    status: vendor.status,
    geography_text: vendor.geography_text ?? "",
    last_contact_date: vendor.last_contact_date ?? ""
  });

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSaving(true);
    try {
      const payload: Record<string, string | null> = {};
      for (const [key, value] of Object.entries(form)) {
        payload[key] = value === "" ? null : value;
      }
      if (!payload.name) {
        throw new Error("Vendor name is required");
      }
      await apiRequest<Vendor>(`/api/v1/vendors/${vendor.id}`, { method: "PATCH", body: JSON.stringify(payload) });
      onSaved();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not update vendor");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="form-stack" onSubmit={submit}>
      <div className="two-column">
        <Input label="Vendor name" required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
        <Input label="Category" value={form.category_text} onChange={(event) => setForm({ ...form, category_text: event.target.value })} />
        <Input label="Website" value={form.website_url} onChange={(event) => setForm({ ...form, website_url: event.target.value })} />
        <Select label="Status" value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>
          {Object.keys(STATUS_LABELS).map((status) => (
            <option key={status} value={status}>
              {statusLabel(status)}
            </option>
          ))}
        </Select>
        <Input label="Geography" value={form.geography_text} onChange={(event) => setForm({ ...form, geography_text: event.target.value })} />
        <Input label="Last contacted" type="date" value={form.last_contact_date} onChange={(event) => setForm({ ...form, last_contact_date: event.target.value })} />
      </div>
      <Input label="Contact info" value={form.contact_info} onChange={(event) => setForm({ ...form, contact_info: event.target.value })} />
      <Input label="Description" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
      {error ? <div className="alert alert--error">{error}</div> : null}
      <div className="button-row">
        <Button disabled={isSaving} type="submit">
          {isSaving ? "Saving..." : "Save changes"}
        </Button>
      </div>
    </form>
  );
}
