import Link from "next/link";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { SectionCard } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";

export default function AdminPage() {
  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Controls"
        title="Admin Panel"
        description="Administrative controls for branding, audit review, imports, and controlled vocabularies."
      />
      <div className="two-column">
        <SectionCard>
          <div className="section-heading">
            <h2>Branding</h2>
            <p>Prepare the Borusan AI Studio logo workflow.</p>
          </div>
          <Link className="button button--secondary" href="/admin/branding">
            Open branding
          </Link>
        </SectionCard>
        <SectionCard>
          <div className="section-heading">
            <h2>User management</h2>
            <p>Create local users, manage roles, deactivate accounts, and reset temporary passwords.</p>
          </div>
          <Link className="button button--secondary" href="/admin/users">
            Open users
          </Link>
        </SectionCard>
        <SectionCard>
          <div className="section-heading">
            <h2>Leaderboard management</h2>
            <p>Dry-run and reset manual contribution scores without deleting CRM records.</p>
          </div>
          <Link className="button button--secondary" href="/admin/leaderboard">
            Open leaderboard reset
          </Link>
        </SectionCard>
        <SectionCard>
          <div className="section-heading">
            <h2>Champion Program</h2>
            <p>Record case studies, training, event participation, and external use-case activities for YZ Champion Score.</p>
          </div>
          <Link className="button button--secondary" href="/admin/champion-program">
            Open Champion Program
          </Link>
        </SectionCard>
        <SectionCard>
          <div className="section-heading">
            <h2>Audit logs</h2>
            <p>Review authenticated activity and import actions as the workflow expands.</p>
          </div>
          <Link className="button button--secondary" href="/admin/audit-logs">
            Open audit logs
          </Link>
        </SectionCard>
        <SectionCard>
          <div className="section-heading">
            <h2>Diagnostics</h2>
            <p>Check application connectivity, backend health, readiness, and dashboard summary.</p>
          </div>
          <Link className="button button--secondary" href="/admin/diagnostics">
            Open diagnostics
          </Link>
        </SectionCard>
      </div>
    </ProtectedPage>
  );
}
