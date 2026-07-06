"use client";

import { Archive, CheckCircle2, Plus, RotateCcw, Search } from "lucide-react";
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
import type { EventRecord, ProgramActivitiesResponse, ProgramActivity, ProgramActivityParticipant, User } from "@/types/api";

type ActivityForm = {
  activity_type: string;
  title: string;
  description: string;
  activity_date: string;
  location_text: string;
  owner_team: string;
  tracking_owner: string;
};

type ParticipantForm = {
  program_activity_id: string;
  user_id: string;
  role: string;
  attendance_status: string;
  completion_status: string;
  notes: string;
};

const initialActivityForm: ActivityForm = {
  activity_type: "EVENT",
  title: "",
  description: "",
  activity_date: new Date().toISOString().slice(0, 10),
  location_text: "",
  owner_team: "YZ Dönüşüm Ofisi",
  tracking_owner: "YZ Dönüşüm Ofisi"
};

const initialParticipantForm: ParticipantForm = {
  program_activity_id: "",
  user_id: "",
  role: "ATTENDEE",
  attendance_status: "ATTENDED",
  completion_status: "COMPLETED",
  notes: ""
};

export default function EventsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";
  const [activities, setActivities] = useState<ProgramActivity[]>([]);
  const [legacyEvents, setLegacyEvents] = useState<EventRecord[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [selected, setSelected] = useState<ProgramActivity | null>(null);
  const [activityForm, setActivityForm] = useState<ActivityForm>(initialActivityForm);
  const [participantForm, setParticipantForm] = useState<ParticipantForm>(initialParticipantForm);
  const [filters, setFilters] = useState({ q: "", activity_type: "ALL", date_from: "", date_to: "", include_archived: "false" });
  const [error, setError] = useState<unknown>(null);
  const [userLoadError, setUserLoadError] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  async function load() {
    setIsLoading(true);
    setError(null);
    const params = new URLSearchParams();
    params.set("limit", "200");
    if (filters.q) params.set("q", filters.q);
    if (filters.activity_type) params.set("activity_type", filters.activity_type);
    if (filters.date_from) params.set("date_from", filters.date_from);
    if (filters.date_to) params.set("date_to", filters.date_to);
    if (isAdmin && filters.include_archived === "true") params.set("include_archived", "true");

    try {
      const [programData, legacyData] = await Promise.all([
        apiRequest<ProgramActivitiesResponse>(`/program-activities?${params.toString()}`),
        apiRequest<EventRecord[]>(`/api/v1/events?limit=200${isAdmin && filters.include_archived === "true" ? "&include_archived=true" : ""}`)
      ]);
      setActivities(programData.items);
      setLegacyEvents(legacyData);
    } catch (caught) {
      setError(caught);
    } finally {
      setIsLoading(false);
    }
  }

  async function loadUsers() {
    setUserLoadError(null);
    try {
      const userData = await apiRequest<User[]>("/api/v1/users/active?limit=500");
      setUsers(userData);
      if (!participantForm.user_id && userData[0]) {
        setParticipantForm((current) => ({ ...current, user_id: userData[0].id }));
      }
    } catch (caught) {
      setUserLoadError(caught);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.include_archived]);

  useEffect(() => {
    void loadUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadDetail(activityId: string) {
    setError(null);
    try {
      const detail = await apiRequest<ProgramActivity>(`/program-activities/${activityId}`);
      setSelected(detail);
      setParticipantForm((current) => ({ ...current, program_activity_id: detail.id }));
    } catch (caught) {
      setError(caught);
    }
  }

  async function createActivity(event: FormEvent) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    try {
      const created = await apiRequest<ProgramActivity>("/program-activities", {
        method: "POST",
        body: JSON.stringify({
          ...activityForm,
          description: activityForm.description || null,
          activity_date: activityForm.activity_date || null,
          location_text: activityForm.location_text || null,
          owner_team: activityForm.owner_team || null,
          tracking_owner: activityForm.tracking_owner || null
        })
      });
      setActivityForm(initialActivityForm);
      await load();
      await loadDetail(created.id);
    } catch (caught) {
      setError(caught);
    } finally {
      setIsSaving(false);
    }
  }

  async function addParticipant(event: FormEvent) {
    event.preventDefault();
    if (!participantForm.program_activity_id) return;
    setIsSaving(true);
    setError(null);
    try {
      const isEvent = selected?.activity_type === "EVENT";
      await apiRequest<ProgramActivityParticipant>(`/program-activities/${participantForm.program_activity_id}/participants`, {
        method: "POST",
        body: JSON.stringify({
          user_id: participantForm.user_id,
          role: isEvent ? participantForm.role : null,
          attendance_status: isEvent ? participantForm.attendance_status : null,
          completion_status: isEvent ? null : participantForm.completion_status,
          notes: participantForm.notes || null
        })
      });
      setParticipantForm((current) => ({ ...current, notes: "" }));
      await load();
      await loadDetail(participantForm.program_activity_id);
    } catch (caught) {
      setError(caught);
    } finally {
      setIsSaving(false);
    }
  }

  async function toggleProgramArchive(activity: ProgramActivity) {
    setError(null);
    try {
      const action = activity.is_archived ? "unarchive" : "archive";
      await apiRequest<ProgramActivity>(`/program-activities/${activity.id}/${action}`, {
        method: "PATCH",
        body: JSON.stringify({ reason: activity.is_archived ? "Restored from Events Library" : "Archived from Events Library" })
      });
      await load();
    } catch (caught) {
      setError(caught);
    }
  }

  const filteredLegacyEvents = useMemo(() => {
    if (filters.activity_type === "TRAINING") return [];
    const query = filters.q.trim().toLowerCase();
    return legacyEvents.filter((event) => {
      if (query) {
        const haystack = [event.name, event.location_text, event.area_text, event.comments].filter(Boolean).join(" ").toLowerCase();
        if (!haystack.includes(query)) return false;
      }
      if (filters.date_from && event.starts_on && event.starts_on < filters.date_from) return false;
      if (filters.date_to && event.starts_on && event.starts_on > filters.date_to) return false;
      return true;
    });
  }, [filters.activity_type, filters.date_from, filters.date_to, filters.q, legacyEvents]);

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Ecosystem"
        title="Events Library"
        description="Manage AI Studio events, communication activities, and education/training programs. Attendance and training completion feed the YZ Champion Score automatically."
      />

      <div className="command-hero">
        <div>
          <h2>Events, communication, and learning</h2>
          <p>
            Use one library for AI Studio events and training programs. Admins record attendance or completion evidence;
            the system calculates Champion Score impact automatically.
          </p>
        </div>
        <Badge tone="info">No manual final scores</Badge>
      </div>

      <form
        className="crm-toolbar"
        onSubmit={(event) => {
          event.preventDefault();
          void load();
        }}
      >
        <Input
          aria-label="Search events"
          placeholder="Search title, location, owner..."
          value={filters.q}
          onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
        />
        <Select
          aria-label="Activity type"
          value={filters.activity_type}
          onChange={(event) => setFilters((current) => ({ ...current, activity_type: event.target.value }))}
        >
          <option value="ALL">All types</option>
          <option value="EVENT">Event</option>
          <option value="TRAINING">Training</option>
        </Select>
        <Input
          aria-label="Date from"
          type="date"
          value={filters.date_from}
          onChange={(event) => setFilters((current) => ({ ...current, date_from: event.target.value }))}
        />
        <Input
          aria-label="Date to"
          type="date"
          value={filters.date_to}
          onChange={(event) => setFilters((current) => ({ ...current, date_to: event.target.value }))}
        />
        {isAdmin ? (
          <Select
            aria-label="Archived records"
            value={filters.include_archived}
            onChange={(event) => setFilters((current) => ({ ...current, include_archived: event.target.value }))}
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

      {error ? <ErrorState title="Could not load Events Library" error={error} onRetry={() => void load()} /> : null}

      {isAdmin ? (
        <div className="two-column">
          <SectionCard>
            <div className="section-heading">
              <h2>Create event or training</h2>
              <p>Create a program record, then add participants.</p>
            </div>
            <form className="form-grid" onSubmit={(event) => void createActivity(event)}>
              <Select label="Type" value={activityForm.activity_type} onChange={(event) => setActivityForm((current) => ({ ...current, activity_type: event.target.value }))}>
                <option value="EVENT">Event</option>
                <option value="TRAINING">Training</option>
              </Select>
              <Input label="Title" value={activityForm.title} onChange={(event) => setActivityForm((current) => ({ ...current, title: event.target.value }))} required />
              <Input label="Date" type="date" value={activityForm.activity_date} onChange={(event) => setActivityForm((current) => ({ ...current, activity_date: event.target.value }))} />
              <Input label="Location" value={activityForm.location_text} onChange={(event) => setActivityForm((current) => ({ ...current, location_text: event.target.value }))} />
              <Input label="Owner team" value={activityForm.owner_team} onChange={(event) => setActivityForm((current) => ({ ...current, owner_team: event.target.value }))} />
              <Input label="Tracking owner" value={activityForm.tracking_owner} onChange={(event) => setActivityForm((current) => ({ ...current, tracking_owner: event.target.value }))} />
              <label className="field form-grid__full">
                <span>Description</span>
                <textarea className="input textarea" rows={3} value={activityForm.description} onChange={(event) => setActivityForm((current) => ({ ...current, description: event.target.value }))} />
              </label>
              <button className="button button--primary form-grid__full" disabled={isSaving} type="submit">
                <Plus size={17} />
                {isSaving ? "Saving..." : "Create activity"}
              </button>
            </form>
          </SectionCard>

          <SectionCard>
            <div className="section-heading">
              <h2>Add participant</h2>
              <p>Mark event attendance or training completion. This creates Champion Score evidence.</p>
            </div>
            {userLoadError ? <ErrorState title="Could not load active users" error={userLoadError} onRetry={() => void loadUsers()} /> : null}
            <form className="form-grid" onSubmit={(event) => void addParticipant(event)}>
              <Select label="Activity" value={participantForm.program_activity_id} onChange={(event) => void loadDetail(event.target.value)} required>
                <option value="">Select activity</option>
                {activities.map((activity) => <option key={activity.id} value={activity.id}>{activity.title}</option>)}
              </Select>
              <Select label="User" value={participantForm.user_id} onChange={(event) => setParticipantForm((current) => ({ ...current, user_id: event.target.value }))} required>
                {users.map((row) => <option key={row.id} value={row.id}>{row.full_name}</option>)}
              </Select>
              {selected?.activity_type === "TRAINING" ? (
                <Select label="Completion" value={participantForm.completion_status} onChange={(event) => setParticipantForm((current) => ({ ...current, completion_status: event.target.value }))}>
                  {["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "ABSENT", "EXEMPT"].map((value) => <option key={value}>{value}</option>)}
                </Select>
              ) : (
                <>
                  <Select label="Role" value={participantForm.role} onChange={(event) => setParticipantForm((current) => ({ ...current, role: event.target.value }))}>
                    {["ATTENDEE", "SPEAKER", "ORGANIZER", "SUPPORT"].map((value) => <option key={value}>{value}</option>)}
                  </Select>
                  <Select label="Attendance" value={participantForm.attendance_status} onChange={(event) => setParticipantForm((current) => ({ ...current, attendance_status: event.target.value }))}>
                    {["PLANNED", "ATTENDED", "ABSENT"].map((value) => <option key={value}>{value}</option>)}
                  </Select>
                </>
              )}
              <Input label="Notes" value={participantForm.notes} onChange={(event) => setParticipantForm((current) => ({ ...current, notes: event.target.value }))} />
              <button className="button button--primary form-grid__full" disabled={isSaving || !participantForm.program_activity_id || !participantForm.user_id} type="submit">
                <CheckCircle2 size={17} />
                Record participant
              </button>
            </form>
          </SectionCard>
        </div>
      ) : null}

      <SectionCard>
        <div className="section-heading section-heading--inline">
          <div>
            <h2>Events and training programs</h2>
            <p>{isLoading ? "Loading..." : `${activities.length} program records`}</p>
          </div>
          <Badge tone="success">Feeds Champion Score</Badge>
        </div>
        {!error && activities.length ? (
          <Table
            rows={activities}
            getRowKey={(row) => row.id}
            onRowClick={(row) => void loadDetail(row.id)}
            columns={[
              { key: "title", header: "Title", render: (row) => <div className="record-title"><strong>{row.title}</strong><span className="record-subtitle">{row.description || row.location_text || "-"}</span></div> },
              { key: "type", header: "Type", render: (row) => <Badge tone={row.activity_type === "TRAINING" ? "success" : "info"}>{row.activity_type === "TRAINING" ? "Training" : "Event"}</Badge> },
              { key: "date", header: "Date", render: (row) => formatDate(row.activity_date) },
              { key: "location", header: "Location", render: (row) => row.location_text || "-" },
              { key: "owner", header: "Owner / Tracking owner", render: (row) => row.tracking_owner || row.owner_team || "-" },
              { key: "participants", header: "Participants", render: (row) => row.participant_count ?? row.participants?.length ?? 0 },
              { key: "impact", header: "Champion Score Impact", render: (row) => row.activity_type === "TRAINING" ? "Training Completion" : "Events & Communication Participation" },
              { key: "status", header: "Status / Archived", render: (row) => row.is_archived ? <Badge tone="warning">Archived</Badge> : <Badge tone="success">Active</Badge> },
              {
                key: "actions",
                header: "Actions",
                render: (row) =>
                  isAdmin ? (
                    <Button
                      variant={row.is_archived ? "secondary" : "danger"}
                      onClick={(event) => {
                        event.stopPropagation();
                        void toggleProgramArchive(row);
                      }}
                    >
                      {row.is_archived ? <RotateCcw size={16} /> : <Archive size={16} />}
                      {row.is_archived ? "Restore" : "Archive"}
                    </Button>
                  ) : "-"
              }
            ]}
          />
        ) : null}
        {!error && !activities.length && !isLoading ? (
          <EmptyState title="No events or training programs yet" description="Create an event or training program to begin tracking participation." />
        ) : null}
      </SectionCard>

      {selected ? (
        <SectionCard>
          <div className="section-heading">
            <h2>{selected.title}</h2>
            <p>Participants and score evidence</p>
          </div>
          {selected.participants?.length ? (
            <Table
              rows={selected.participants}
              getRowKey={(row) => row.id}
              columns={[
                { key: "user", header: "User", render: (row) => row.user?.full_name ?? row.user_id },
                { key: "role", header: "Role", render: (row) => row.role ?? "-" },
                { key: "attendance", header: "Attendance", render: (row) => row.attendance_status ?? "-" },
                { key: "completion", header: "Completion", render: (row) => row.completion_status ?? "-" },
                { key: "score", header: "Score Impact", render: (row) => scoreImpact(selected, row) }
              ]}
            />
          ) : (
            <EmptyState title="No participants yet" description="Add participants to create event or training score evidence." />
          )}
        </SectionCard>
      ) : null}

      <SectionCard>
        <div className="section-heading section-heading--inline">
          <div>
            <h2>Imported ecosystem events</h2>
            <p>{filteredLegacyEvents.length} records from the original Events Library data model</p>
          </div>
          <Badge tone="info">Preserved</Badge>
        </div>
        {filteredLegacyEvents.length ? (
          <Table
            rows={filteredLegacyEvents}
            getRowKey={(row) => row.id}
            columns={[
              { key: "name", header: "Event", render: (row) => row.name },
              { key: "date", header: "Date", render: (row) => row.starts_on ?? row.date_text ?? "-" },
              { key: "location", header: "Location", render: (row) => row.location_text },
              { key: "area", header: "Area", render: (row) => row.area_text ?? "-" },
              { key: "relevance", header: "Relevance", render: (row) => <Badge>{row.ai_program_relevance}</Badge> },
              { key: "value", header: "Value", render: (row) => <Badge tone="info">{row.value_creation_potential}</Badge> },
              { key: "status", header: "Status", render: (row) => row.is_archived ? <Badge tone="warning">Archived</Badge> : <Badge tone="success">Active</Badge> }
            ]}
          />
        ) : (
          <EmptyState title="No imported event records match this view" description="Committed Excel events remain visible here when present." />
        )}
      </SectionCard>
    </ProtectedPage>
  );
}

function scoreImpact(activity: ProgramActivity, row: ProgramActivityParticipant) {
  if (activity.activity_type === "EVENT" && row.attendance_status === "ATTENDED") return "Events & Communication Participation";
  if (activity.activity_type === "TRAINING" && row.completion_status === "COMPLETED") return "Training Completion";
  return "-";
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}
