"use client";

import { Archive, RotateCcw, Save } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Input, Select } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { Table } from "@/components/ui/Table";
import { apiRequest } from "@/lib/api";
import type { ChampionActivitiesResponse, ChampionActivity, User } from "@/types/api";

const CATEGORY_OPTIONS = [
  "VISION_STRATEGY",
  "ECOSYSTEM_LIBRARY",
  "STARTUP_SCOUTING",
  "COMMUNICATION_CASE_STUDY",
  "COMMUNICATION_EVENT",
  "TRAINING"
];

const ACTIVITY_TYPES_BY_CATEGORY: Record<string, string[]> = {
  VISION_STRATEGY: ["USE_CASE_PROPOSED", "USE_CASE_PROJECTIZED", "OPPORTUNITY_CREATED", "OPPORTUNITY_MOVED_TO_PROJECT"],
  ECOSYSTEM_LIBRARY: ["STARTUP_ADDED", "VENDOR_ADDED", "AI_TOOL_ADDED", "EVENT_ADDED", "CONTACT_ADDED", "DECK_UPLOADED", "ORGANIZATION_ENRICHED"],
  STARTUP_SCOUTING: ["STARTUP_REVIEWED", "STARTUP_SHORTLISTED", "FOLLOW_UP_COMPLETED"],
  COMMUNICATION_CASE_STUDY: ["CASE_STUDY_SUBMITTED", "CASE_STUDY_APPROVED"],
  COMMUNICATION_EVENT: ["EVENT_PARTICIPATION"],
  TRAINING: ["TRAINING_COMPLETED"]
};

type FormState = {
  user_id: string;
  category: string;
  activity_type: string;
  activity_date: string;
  quantity: number;
  evidence_url: string;
  notes: string;
};

const initialForm: FormState = {
  user_id: "",
  category: "VISION_STRATEGY",
  activity_type: "USE_CASE_PROPOSED",
  activity_date: new Date().toISOString().slice(0, 10),
  quantity: 1,
  evidence_url: "",
  notes: ""
};

export default function AdminChampionProgramPage() {
  const [activities, setActivities] = useState<ChampionActivity[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [form, setForm] = useState<FormState>(initialForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [isSaving, setIsSaving] = useState(false);
  const activityOptions = useMemo(() => ACTIVITY_TYPES_BY_CATEGORY[form.category] ?? [], [form.category]);

  async function load() {
    setError(null);
    try {
      const [userData, activityData] = await Promise.all([
        apiRequest<User[]>("/api/v1/users/active?limit=500"),
        apiRequest<ChampionActivitiesResponse>("/api/v1/admin/champion-activities?limit=200")
      ]);
      setUsers(userData);
      setActivities(activityData.items);
      if (!form.user_id && userData[0]) {
        setForm((current) => ({ ...current, user_id: userData[0].id }));
      }
    } catch (caught) {
      setError(caught);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function updateForm(partial: Partial<FormState>) {
    setForm((current) => {
      const next = { ...current, ...partial };
      if (partial.category) {
        next.activity_type = ACTIVITY_TYPES_BY_CATEGORY[partial.category]?.[0] ?? current.activity_type;
      }
      return next;
    });
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    const payload = {
      user_id: form.user_id,
      category: form.category,
      activity_type: form.activity_type,
      activity_date: new Date(`${form.activity_date}T12:00:00`).toISOString(),
      quantity: Number(form.quantity) || 1,
      source: "ADMIN_RECORDED",
      status: "ACTIVE",
      evidence_url: form.evidence_url || null,
      notes: form.notes || null
    };
    try {
      if (editingId) {
        await apiRequest<ChampionActivity>(`/api/v1/admin/champion-activities/${editingId}`, {
          method: "PUT",
          body: JSON.stringify(payload)
        });
      } else {
        await apiRequest<ChampionActivity>("/api/v1/admin/champion-activities", {
          method: "POST",
          body: JSON.stringify(payload)
        });
      }
      setEditingId(null);
      setForm({ ...initialForm, user_id: form.user_id });
      await load();
    } catch (caught) {
      setError(caught);
    } finally {
      setIsSaving(false);
    }
  }

  function edit(activity: ChampionActivity) {
    setEditingId(activity.id);
    setForm({
      user_id: activity.user_id,
      category: activity.category,
      activity_type: activity.activity_type,
      activity_date: activity.activity_date.slice(0, 10),
      quantity: activity.quantity,
      evidence_url: activity.evidence_url ?? "",
      notes: activity.notes ?? ""
    });
  }

  async function toggleArchive(activity: ChampionActivity) {
    setError(null);
    try {
      const action = activity.is_archived ? "unarchive" : "archive";
      await apiRequest<ChampionActivity>(`/api/v1/admin/champion-activities/${activity.id}/${action}`, {
        method: "PATCH",
        body: JSON.stringify({ reason: activity.is_archived ? "Restored by admin" : "Archived by admin" })
      });
      await load();
    } catch (caught) {
      setError(caught);
    }
  }

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Admin"
        title="Champion Program"
        description="Record CRM-external YZ Champion Program activities. Scores are calculated automatically from scorecard rules."
      />

      {error ? <ErrorState title="Could not load Champion Program data" error={error} onRetry={() => void load()} /> : null}

      <div className="stat-grid">
        <SectionCard>
          <div className="section-heading">
            <h2>Case Study Contributions</h2>
            <p>Record submitted or approved case-study content. The score is calculated from the count.</p>
          </div>
        </SectionCard>
        <SectionCard>
          <div className="section-heading">
            <h2>Event & Training Participation</h2>
            <p>Prefer the Events & Education Programs page for attendance and training completion tracking.</p>
          </div>
        </SectionCard>
        <SectionCard>
          <div className="section-heading">
            <h2>Activity Log</h2>
            <p>Review and archive Champion activity evidence without deleting CRM Activity Points.</p>
          </div>
        </SectionCard>
      </div>

      <div className="two-column">
        <SectionCard>
          <div className="section-heading">
            <h2>{editingId ? "Edit activity" : "Record activity"}</h2>
            <p>Record the underlying activity, not a final score. The leaderboard calculates the weighted score.</p>
          </div>
          <form className="form-grid" onSubmit={(event) => void save(event)}>
            <Select label="User" value={form.user_id} onChange={(event) => updateForm({ user_id: event.target.value })} required>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.full_name} ({user.email})
                </option>
              ))}
            </Select>
            <Select label="Category" value={form.category} onChange={(event) => updateForm({ category: event.target.value })}>
              {CATEGORY_OPTIONS.map((category) => (
                <option key={category} value={category}>
                  {categoryLabel(category)}
                </option>
              ))}
            </Select>
            <Select label="Activity type" value={form.activity_type} onChange={(event) => updateForm({ activity_type: event.target.value })}>
              {activityOptions.map((activityType) => (
                <option key={activityType} value={activityType}>
                  {activityType.replaceAll("_", " ")}
                </option>
              ))}
            </Select>
            <Input label="Date" type="date" value={form.activity_date} onChange={(event) => updateForm({ activity_date: event.target.value })} />
            <Input label="Quantity" min={1} type="number" value={form.quantity} onChange={(event) => updateForm({ quantity: Number(event.target.value) })} />
            <Input label="Evidence URL" value={form.evidence_url} onChange={(event) => updateForm({ evidence_url: event.target.value })} />
            <label className="field form-grid__full">
              <span>Notes</span>
              <textarea className="input" rows={4} value={form.notes} onChange={(event) => updateForm({ notes: event.target.value })} />
            </label>
            <div className="button-row form-grid__full">
              <button className="button button--primary" disabled={isSaving || !form.user_id} type="submit">
                <Save size={17} />
                {isSaving ? "Saving..." : editingId ? "Save changes" : "Record activity"}
              </button>
              {editingId ? (
                <button className="button button--secondary" type="button" onClick={() => { setEditingId(null); setForm({ ...initialForm, user_id: form.user_id }); }}>
                  Cancel edit
                </button>
              ) : null}
            </div>
          </form>
        </SectionCard>

        <SectionCard>
          <div className="section-heading">
            <h2>Program guardrails</h2>
            <p>Imported Excel records do not count. Admin-recorded records represent case studies, training, event participation, and external use-case work.</p>
          </div>
          <div className="candidate-count-grid">
            <div className="mini-stat">
              <span>Scoring model</span>
              <strong>Weighted</strong>
            </div>
            <div className="mini-stat">
              <span>Manual final score</span>
              <strong>No</strong>
            </div>
            <div className="mini-stat">
              <span>Activity source</span>
              <strong>Admin</strong>
            </div>
          </div>
          <div className="phase-note">Use the Leaderboard page Score Rules tab to review category weights and target thresholds.</div>
        </SectionCard>
      </div>

      <SectionCard>
        <div className="section-heading section-heading--inline">
          <div>
            <h2>Recorded Champion activities</h2>
            <p>{activities.length} recent records</p>
          </div>
          <Badge tone="info">Admin-managed</Badge>
        </div>
        {activities.length ? (
          <Table
            rows={activities}
            getRowKey={(row) => row.id}
            columns={[
              { key: "user", header: "User", render: (row) => row.user?.full_name ?? row.user_id },
              { key: "category", header: "Category", render: (row) => categoryLabel(row.category) },
              { key: "type", header: "Activity", render: (row) => row.activity_type.replaceAll("_", " ") },
              { key: "quantity", header: "Qty", render: (row) => row.quantity },
              { key: "source", header: "Source", render: (row) => <Badge>{row.source}</Badge> },
              { key: "status", header: "Status", render: (row) => <Badge tone={row.status === "ACTIVE" ? "success" : "neutral"}>{row.status}</Badge> },
              { key: "date", header: "Date", render: (row) => formatDate(row.activity_date) },
              {
                key: "actions",
                header: "Actions",
                render: (row) => (
                  <div className="button-row">
                    <button className="button button--secondary" type="button" onClick={() => edit(row)}>
                      Edit
                    </button>
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
          <EmptyState title="No Champion activities recorded" description="Use the form above to record external program activities." />
        )}
      </SectionCard>
    </ProtectedPage>
  );
}

function categoryLabel(category: string) {
  return {
    VISION_STRATEGY: "Use Case & Project Development",
    ECOSYSTEM_LIBRARY: "Ecosystem Library Contribution",
    STARTUP_SCOUTING: "Startup Scouting & AI Studio Support",
    COMMUNICATION_CASE_STUDY: "Case Study Contribution",
    COMMUNICATION_EVENT: "Events & Communication Participation",
    TRAINING: "Training Completion"
  }[category] ?? category;
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}
