"use client";

import { ArrowRight, LockKeyhole, Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { loginWithMicrosoft } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleMicrosoftSignIn() {
    setError(null);
    setIsSubmitting(true);
    try {
      await loginWithMicrosoft();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Microsoft sign-in failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-visual">
        <div className="brand brand--login">
          <div className="brand-mark">AI</div>
          <div>
            <strong>Borusan AI Studio</strong>
            <span>Ecosystem CRM</span>
          </div>
        </div>
        <div>
          <p className="eyebrow">Internal intelligence layer</p>
          <h1>Manage the AI ecosystem with cleaner signals than Excel.</h1>
          <p>
            Startups, PoCs, events, network contacts, tools, notes, and audit-ready import
            previews in one controlled workspace.
          </p>
        </div>
        <div className="login-orbit">
          <Sparkles size={20} />
          <span>Controlled imports, CRM records, audit logs, and champion progress in one workspace.</span>
        </div>
      </section>

      <section className="login-panel">
        <div className="lock-icon">
          <LockKeyhole size={22} />
        </div>
        <h2>Sign in</h2>
        <p>Sign in with your Borusan Microsoft account.</p>
        {error ? <div className="alert alert--error">{error}</div> : null}
        <Button disabled={isSubmitting} onClick={() => void handleMicrosoftSignIn()} type="button">
          {isSubmitting ? "Signing in..." : "Sign in with Microsoft"}
          <ArrowRight size={17} />
        </Button>
        <p className="login-note">
          Access is managed entirely through Microsoft Entra ID. The CRM stores no passwords.
        </p>
      </section>
    </main>
  );
}
