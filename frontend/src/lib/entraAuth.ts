import type { IPublicClientApplication } from "@azure/msal-browser";

export const AUTH_MODE = (process.env.NEXT_PUBLIC_AUTH_MODE ?? "local").toLowerCase();
export const IS_ENTRA_AUTH = AUTH_MODE === "entra";

const ENTRA_CLIENT_ID = process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID ?? "";
const ENTRA_TENANT_ID = process.env.NEXT_PUBLIC_ENTRA_TENANT_ID ?? "";
const ENTRA_REDIRECT_URI = process.env.NEXT_PUBLIC_ENTRA_REDIRECT_URI ?? "";
// Scope of the backend API app registration, e.g. "api://<client-id>/user_impersonation"
// or "api://<client-id>/.default".
const ENTRA_API_SCOPE = process.env.NEXT_PUBLIC_ENTRA_API_SCOPE ?? "";

let msalInstancePromise: Promise<IPublicClientApplication> | null = null;

function requireConfig(): void {
  const missing = [
    !ENTRA_CLIENT_ID && "NEXT_PUBLIC_ENTRA_CLIENT_ID",
    !ENTRA_TENANT_ID && "NEXT_PUBLIC_ENTRA_TENANT_ID",
    !ENTRA_API_SCOPE && "NEXT_PUBLIC_ENTRA_API_SCOPE"
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
          redirectUri: ENTRA_REDIRECT_URI || window.location.origin
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

/** Interactive sign-in; returns a backend-ready access token. */
export async function entraSignIn(): Promise<string> {
  const instance = await getMsalInstance();
  const result = await instance.loginPopup({ scopes: [ENTRA_API_SCOPE] });
  if (result.account) {
    instance.setActiveAccount(result.account);
  }
  if (!result.accessToken) {
    return entraAcquireToken();
  }
  return result.accessToken;
}

/** Silent token acquisition for refresh; throws if interaction is required. */
export async function entraAcquireToken(): Promise<string> {
  const instance = await getMsalInstance();
  const account = instance.getActiveAccount() ?? instance.getAllAccounts()[0];
  if (!account) {
    throw new Error("No signed-in Microsoft account. Sign in again.");
  }
  const result = await instance.acquireTokenSilent({ scopes: [ENTRA_API_SCOPE], account });
  return result.accessToken;
}

export async function entraSignOut(): Promise<void> {
  if (!msalInstancePromise) return;
  const instance = await msalInstancePromise;
  const account = instance.getActiveAccount() ?? instance.getAllAccounts()[0];
  // Local sign-out only: clears the MSAL cache without redirecting the whole
  // browser through the Microsoft logout page.
  await instance.clearCache(account ? { account } : undefined);
}
