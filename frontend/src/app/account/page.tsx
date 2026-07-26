"use client";

import { ShieldCheck } from "lucide-react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { SectionCard } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { useAuth } from "@/lib/auth";

/**
 * Read-only account view. Sign-in is handled entirely by Microsoft Entra ID, so
 * there is no password to change here: name, email, and password are managed in
 * the Microsoft account, and CRM role/section access is managed by an admin.
 */
export default function AccountPage() {
  const { user } = useAuth();

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Account"
        title="Account Settings"
        description="Your CRM profile, as provided by Microsoft Entra ID single sign-on."
      />

      <div className="command-hero">
        <div>
          <h2>{user?.full_name ?? "CRM User"}</h2>
          <p>{user?.email ?? "-"}</p>
        </div>
        <ShieldCheck size={28} />
      </div>

      <SectionCard>
        <div className="section-heading">
          <h2>Sign-in method</h2>
          <p>
            You sign in with your Borusan Microsoft account. The CRM stores no password and cannot
            change one — update your password, name, or multi-factor settings in your Microsoft
            account.
          </p>
        </div>
        <dl className="metadata-list">
          <div>
            <dt>Full name</dt>
            <dd>{user?.full_name ?? "-"}</dd>
          </div>
          <div>
            <dt>Sign-in address (UPN)</dt>
            <dd>{user?.email ?? "-"}</dd>
          </div>
          <div>
            <dt>CRM role</dt>
            <dd>{user?.role ?? "USER"}</dd>
          </div>
          <div>
            <dt>Authentication</dt>
            <dd>Microsoft Entra ID single sign-on</dd>
          </div>
        </dl>
      </SectionCard>

      <SectionCard>
        <div className="section-heading">
          <h2>Access requests</h2>
          <p>
            Section access and role changes are managed by a CRM administrator. Contact an admin if
            a section you need is hidden.
          </p>
        </div>
      </SectionCard>
    </ProtectedPage>
  );
}
