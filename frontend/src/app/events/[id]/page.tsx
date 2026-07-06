"use client";

import { ArrowLeft, RefreshCw, Save } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input, Select } from "@/components/ui/Input";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { EventRecord } from "@/types/api";

export default function EventDetailPage({ params }: { params: { id: string } }) {
  const { user } = useAuth();
  const [eventRecord, setEventRecord] = useState<EventRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  async function load() {
    setIsLoading(true);
    setError(null);
    try {
      setEventRecord(await apiRequest<EventRecord>(`/api/v1/events/${params.id}`));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load event");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  async function toggleArchive() {
    if (!eventRecord) return;
    const endpoint = eventRecord.is_archived ? "unarchive" : "archive";
    const reason = window.prompt(`${eventRecord.is_archived ? "Restore" : "Archive"} this event? Optional reason:`);
    if (reason === null) return;
    await apiRequest(`/api/v1/events/${eventRecord.id}/${endpoint}`, {
      method: "PATCH",
      body: JSON.stringify({ reason })
    });
    await load();
  }

  if (isLoading) {
    return (
      <ProtectedPage>
        <EmptyState title="Loading event" description="Opening the ecosystem event..." />
      </ProtectedPage>
    );
  }

  if (error || !eventRecord) {
    return (
      <ProtectedPage>
        <SectionCard>
          <div className="alert alert--error">{error ?? "Event not found"}</div>
          <Link className="button button--secondary" href="/events">
            <ArrowLeft size={16} />
            Back to events
          </Link>
        </SectionCard>
      </ProtectedPage>
    );
  }

  return (
    <ProtectedPage>
      <section className="company-hero">
        <div>
          <Link className="link-button" href="/events">
            <ArrowLeft size={14} /> Back to Events Library
          </Link>
          <h1>{eventRecord.name}</h1>
          <div className="chip-row">
            <Badge tone="info">{eventRecord.ai_program_relevance}</Badge>
            <Badge>{eventRecord.value_creation_potential}</Badge>
            {eventRecord.area_text ? <Badge tone="success">{eventRecord.area_text}</Badge> : null}
          </div>
          <p>{eventRecord.comments ?? "No comments have been captured for this event yet."}</p>
          <div className="metadata-row">
            <span className="record-subtitle">Date: {formatDate(eventRecord.starts_on) || eventRecord.date_text || "-"}</span>
            <span className="record-subtitle">Location: {eventRecord.location_text}</span>
          </div>
        </div>
        <Button variant="secondary" onClick={() => void load()}>
          <RefreshCw size={16} />
          Refresh
        </Button>
        {user?.role === "ADMIN" ? (
          <Button variant={eventRecord.is_archived ? "secondary" : "danger"} onClick={() => void toggleArchive()}>
            {eventRecord.is_archived ? "Unarchive" : "Archive"}
          </Button>
        ) : null}
      </section>

      <div className="two-column">
        <EventEditCard eventRecord={eventRecord} onSaved={load} />
        <SectionCard>
          <div className="section-heading">
            <h2>Event intelligence</h2>
            <p>Program relevance and value creation potential from the normalized CRM record.</p>
          </div>
          <dl className="metadata-list">
            <div>
              <dt>Starts</dt>
              <dd>{formatDate(eventRecord.starts_on)}</dd>
            </div>
            <div>
              <dt>Ends</dt>
              <dd>{formatDate(eventRecord.ends_on)}</dd>
            </div>
            <div>
              <dt>Date text</dt>
              <dd>{eventRecord.date_text ?? "-"}</dd>
            </div>
            <div>
              <dt>Geography</dt>
              <dd>{eventRecord.geography_text ?? "-"}</dd>
            </div>
          </dl>
        </SectionCard>
      </div>
    </ProtectedPage>
  );
}

function EventEditCard({ eventRecord, onSaved }: { eventRecord: EventRecord; onSaved: () => Promise<void> }) {
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: eventRecord.name,
    starts_on: eventRecord.starts_on ?? "",
    ends_on: eventRecord.ends_on ?? "",
    date_text: eventRecord.date_text ?? "",
    location_text: eventRecord.location_text ?? "",
    geography_text: eventRecord.geography_text ?? "",
    area_text: eventRecord.area_text ?? "",
    ai_program_relevance: eventRecord.ai_program_relevance ?? "UNKNOWN",
    value_creation_potential: eventRecord.value_creation_potential ?? "UNKNOWN",
    comments: eventRecord.comments ?? ""
  });

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await apiRequest<EventRecord>(`/api/v1/events/${eventRecord.id}`, {
        method: "PUT",
        body: JSON.stringify(clean(form))
      });
      await onSaved();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not update event");
    }
  }

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Edit event</h2>
        <p>Maintain the event record without touching import staging history.</p>
      </div>
      <form className="form-stack" onSubmit={submit}>
        <Input label="Event name" required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
        <div className="two-column">
          <Input label="Starts on" type="date" value={form.starts_on} onChange={(event) => setForm({ ...form, starts_on: event.target.value })} />
          <Input label="Ends on" type="date" value={form.ends_on} onChange={(event) => setForm({ ...form, ends_on: event.target.value })} />
          <Input label="Date text" value={form.date_text} onChange={(event) => setForm({ ...form, date_text: event.target.value })} />
          <Input label="Location" required value={form.location_text} onChange={(event) => setForm({ ...form, location_text: event.target.value })} />
          <Input label="Geography" value={form.geography_text} onChange={(event) => setForm({ ...form, geography_text: event.target.value })} />
          <Input label="Area / category" value={form.area_text} onChange={(event) => setForm({ ...form, area_text: event.target.value })} />
          <Select label="AI program relevance" value={form.ai_program_relevance} onChange={(event) => setForm({ ...form, ai_program_relevance: event.target.value })}>
            {["HIGH", "MEDIUM", "LOW", "UNKNOWN"].map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </Select>
          <Select label="Value potential" value={form.value_creation_potential} onChange={(event) => setForm({ ...form, value_creation_potential: event.target.value })}>
            {["HIGH", "MEDIUM", "LOW", "UNKNOWN"].map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </Select>
        </div>
        <label className="field">
          <span>Comments</span>
          <textarea className="input textarea" value={form.comments} onChange={(event) => setForm({ ...form, comments: event.target.value })} />
        </label>
        {error ? <div className="alert alert--error">{error}</div> : null}
        <Button type="submit"><Save size={16} /> Save event</Button>
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
