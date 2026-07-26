import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Signing in...",
  robots: { index: false, follow: false }
};

/**
 * Dedicated Microsoft Entra ID redirect page.
 *
 * This is the registered redirect URI target for the MSAL popup flow. The
 * popup window lands here after Microsoft authentication; msal-browser in the
 * opener window reads the auth response from this window's URL hash and closes
 * the popup. This page must therefore:
 *   - be reachable WITHOUT authentication (it renders before any sign-in),
 *   - render as little as possible (it is never meaningfully seen), and
 *   - never navigate away or mutate the URL, or the auth response is lost.
 */
export default function AuthCallbackPage() {
  return (
    <main className="loading-screen">
      <p style={{ color: "var(--muted)" }}>Completing Microsoft sign-in...</p>
    </main>
  );
}
