"use client";

import { ArrowRight, LockKeyhole, Sparkles } from "lucide-react";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Login failed");
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
        <p>Use your Borusan AI Studio CRM account.</p>
        <form className="form-stack" onSubmit={handleSubmit}>
          <Input
            autoComplete="email"
            label="Email"
            onChange={(event) => setEmail(event.target.value)}
            placeholder="admin@example.com"
            required
            type="email"
            value={email}
          />
          <Input
            autoComplete="current-password"
            label="Password"
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter password"
            required
            type="password"
            value={password}
          />
          {error ? <div className="alert alert--error">{error}</div> : null}
          <Button disabled={isSubmitting} type="submit">
            {isSubmitting ? "Signing in..." : "Sign in"}
            <ArrowRight size={17} />
          </Button>
        </form>
      </section>
    </main>
  );
}
