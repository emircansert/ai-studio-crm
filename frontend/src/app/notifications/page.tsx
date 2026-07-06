"use client";

import { Bell, CheckCircle2 } from "lucide-react";
import { useEffect, useState } from "react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { PageHeader } from "@/components/ui/PageHeader";
import { Table } from "@/components/ui/Table";
import { apiRequest } from "@/lib/api";
import type { NotificationItem, NotificationUnreadCount } from "@/types/api";

export default function NotificationsPage() {
  const [rows, setRows] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [error, setError] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState(true);

  async function load() {
    setIsLoading(true);
    setError(null);
    try {
      const [notifications, count] = await Promise.all([
        apiRequest<NotificationItem[]>("/api/v1/notifications?limit=100"),
        apiRequest<NotificationUnreadCount>("/api/v1/notifications/unread-count")
      ]);
      setRows(notifications);
      setUnreadCount(count.unread_count);
    } catch (caught) {
      setError(caught);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function markRead(id: string) {
    await apiRequest<NotificationItem>(`/api/v1/notifications/${id}/read`, { method: "PATCH" });
    await load();
  }

  async function markAllRead() {
    await apiRequest<NotificationUnreadCount>("/api/v1/notifications/read-all", { method: "PATCH" });
    await load();
  }

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Notifications"
        title="Notification Center"
        description="Follow-up assignments and CRM tasks that need your attention."
        actions={
          <Button disabled={!unreadCount} variant="secondary" onClick={() => void markAllRead()}>
            <CheckCircle2 size={16} /> Mark all read
          </Button>
        }
      />

      <div className="command-hero">
        <div>
          <h2>{unreadCount} unread notification{unreadCount === 1 ? "" : "s"}</h2>
          <p>Admins can assign follow-ups to any user, including other admins. Those assignments appear here.</p>
        </div>
        <Bell size={28} />
      </div>

      <SectionCard>
        {error ? <ErrorState title="Could not load notifications" error={error} onRetry={() => void load()} /> : null}
        {!error && !isLoading && !rows.length ? (
          <EmptyState title="No notifications yet" description="Assigned follow-ups and important CRM notifications will appear here." />
        ) : null}
        {!error && rows.length ? (
          <Table
            rows={rows}
            getRowKey={(row) => row.id}
            columns={[
              {
                key: "status",
                header: "Status",
                render: (row) => <Badge tone={row.is_read ? "neutral" : "warning"}>{row.is_read ? "Read" : "Unread"}</Badge>
              },
              {
                key: "title",
                header: "Notification",
                render: (row) => (
                  <div>
                    <strong>{row.title}</strong>
                    {row.body ? <p className="record-subtitle">{row.body}</p> : null}
                  </div>
                )
              },
              { key: "type", header: "Type", render: (row) => row.notification_type.replaceAll("_", " ") },
              { key: "created", header: "Created", render: (row) => formatDate(row.created_at) },
              {
                key: "action",
                header: "Action",
                render: (row) =>
                  row.is_read ? null : (
                    <Button variant="secondary" onClick={() => void markRead(row.id)}>
                      Mark read
                    </Button>
                  )
              }
            ]}
          />
        ) : null}
      </SectionCard>
    </ProtectedPage>
  );
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}
