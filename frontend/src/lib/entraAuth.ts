import type { IPublicClientApplication } from "@azure/msal-browser";

// Microsoft Entra ID is the only authentication method. There is no local
// password path in the application, so there is no auth mode to switch on.
const ENTRA_CLIENT_ID = process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID ?? "";
const ENTRA_TENANT_ID = process.env.NEXT_PUBLIC_ENTRA_TENANT_ID ?? "";
// Base origin for the redirect URI (e.g. https://ecosystem.borusan.com). The
// dedicated callback path below is appended to it; the full registered
// redirect URI in Azure must be <base><ENTRA_CALLBACK_PATH>.
const ENTRA_REDIRECT_URI = process.env.NEXT_PUBLIC_ENTRA_REDIRECT_URI ?? "";

/**
 * Standard delegated Microsoft Graph scopes granted on the app registration.
 *
 * The registration deliberately exposes no custom API, so there is no
 * "api://<client-id>/..." scope to request. Sign-in therefore asks only for
 * these delegated permissions, and the CRM API is authenticated with the
 * resulting OIDC **ID token**, whose audience is the client id itself.
 *
 * `profile` and `email` are what populate the name/`preferred_username`/`email`
 * claims the backend uses to resolve the user's UPN.
 */
const ENTRA_LOGIN_SCOPES = ["openid", "profile", "email", "User.Read"];

/**
 * Dedicated, unauthenticated redirect page (src/app/auth/callback/page.tsx).
 * Using a minimal page instead of the app root means the MSAL popup never has
 * to load the full application to complete sign-in.
 */
export const ENTRA_CALLBACK_PATH = "/auth/callback";

/** Resolve the exact redirect URI MSAL sends to Microsoft. Exported for tests/diagnostics. */
export function buildEntraRedirectUri(configuredBase: string, origin: string): string {
  const base = (configuredBase || origin).replace(/\/+$/, "");
  // Tolerate an env value that already includes the callback path.
  return base.endsWith(ENTRA_CALLBACK_PATH) ? base : `${base}${ENTRA_CALLBACK_PATH}`;
}

let msalInstancePromise: Promise<IPublicClientApplication> | null = null;

function requireConfig(): void {
  const missing = [
    !ENTRA_CLIENT_ID && "NEXT_PUBLIC_ENTRA_CLIENT_ID",
    !ENTRA_TENANT_ID && "NEXT_PUBLIC_ENTRA_TENANT_ID"
  ].filter(Boolean);
  if (missing.length) {
    throw new Error(`Microsoft Entra ID sign-in is not configured (missing ${missing.join(", ")}).`);
  }
}

async function getMsalInstance(): Promise<IPublicClientApplication> {
  requireConfig();
  if (!msalInstancePromise) {
    msalInstancePromise = (async () => {
      const { PublicClientApplication } = await import("@azure/msal-browser");
      const instance = new PublicClientApplication({
        auth: {
          clientId: ENTRA_CLIENT_ID,
          authority: `https://login.microsoftonline.com/${ENTRA_TENANT_ID}`,
          redirectUri: buildEntraRedirectUri(ENTRA_REDIRECT_URI, window.location.origin)
        },
        cache: {
          // Session-scoped cache; the API bearer token continues to live in the
          // app's existing storage handled by lib/api.ts.
          cacheLocation: "sessionStorage"
        }
      });
      await instance.initialize();
      return instance;
    })();
  }
  return msalInstancePromise;
}

/**
 * Interactive sign-in. Returns the OIDC **ID token**, which is what the CRM
 * backend accepts as its bearer credential (audience = this client id).
 *
 * The Graph access token that MSAL also obtains is deliberately not used: it is
 * addressed to Microsoft Graph, not to this application.
 */
export async function entraSignIn(): Promise<string> {
  const instance = await getMsalInstance();
  const result = await instance.loginPopup({ scopes: ENTRA_LOGIN_SCOPES });
  if (result.account) {
    instance.setActiveAccount(result.account);
  }
  if (!result.idToken) {
    return entraAcquireToken();
  }
  return result.idToken;
}

/** Silent ID-token refresh; throws if interaction is required. */
export async function entraAcquireToken(): Promise<string> {
  const instance = await getMsalInstance();
  const account = instance.getActiveAccount() ?? instance.getAllAccounts()[0];
  if (!account) {
    throw new Error("No signed-in Microsoft account. Sign in again.");
  }
  const result = await instance.acquireTokenSilent({ scopes: ENTRA_LOGIN_SCOPES, account });
  if (!result.idToken) {
    throw new Error("Microsoft sign-in did not return an ID token.");
  }
  return result.idToken;
}

export async function entraSignOut(): Promise<void> {
  if (!msalInstancePromise) return;
  const instance = await msalInstancePromise;
  const account = instance.getActiveAccount() ?? instance.getAllAccounts()[0];
  // Local sign-out only: clears the MSAL cache without redirecting the whole
  // browser through the Microsoft logout page.
  await instance.clearCache(account ? { account } : undefined);
}
