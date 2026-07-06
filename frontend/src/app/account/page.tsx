"use client";

import { FormEvent, useState } from "react";
import { KeyRound, ShieldCheck } from "lucide-react";

import { ProtectedPage } from "@/components/layout/ProtectedPage";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function AccountPage() {
  const { user } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setNotice(null);

    if (newPassword.length < 8) {
      setError("New password must be at least 8 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }

    setIsSaving(true);
    try {
      await apiRequest<{ detail: string }>("/api/v1/users/me/change-password", {
        method: "PATCH",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setNotice("Password changed successfully.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not change password.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <ProtectedPage>
      <PageHeader
        eyebrow="Account"
        title="Account Settings"
        description="Manage your local CRM account password."
      />

      <div className="command-hero">
        <div>
          <h2>{user?.full_name ?? "CRM User"}</h2>
          <p>{user?.email}</p>
        </div>
        <ShieldCheck size={28} />
      </div>

      <SectionCard>
        <div className="section-heading">
          <h2>Change password</h2>
          <p>Enter your current password and choose a new password for future sign-ins.</p>
        </div>
        <form className="form-stack" onSubmit={submit}>
          <Input
            autoComplete="current-password"
            label="Current password"
            required
            type="password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
          />
          <div className="two-column">
            <Input
              autoComplete="new-password"
              helperText="Use at least 8 characters."
              label="New password"
              required
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
            />
            <Input
              autoComplete="new-password"
              label="Confirm new password"
              required
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
            />
          </div>
          {error ? <div className="alert alert--error">{error}</div> : null}
          {notice ? <div className="alert alert--success">{notice}</div> : null}
          <Button disabled={isSaving} type="submit">
            <KeyRound size={16} />
            {isSaving ? "Saving..." : "Change password"}
          </Button>
        </form>
      </SectionCard>
    </ProtectedPage>
  );
}
