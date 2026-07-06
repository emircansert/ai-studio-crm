export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/backend";

const TOKEN_KEY = "borusan_crm_token";

export type ApiErrorPayload = {
  error?: string;
  error_code?: string;
  detail?: string;
  details?: unknown;
  message?: string;
  request_id?: string;
  targetUrl?: string;
};

export class ApiError extends Error {
  status: number;
  path: string;
  payload: unknown;
  technicalDetails?: string;

  constructor(status: number, path: string, message: string, payload?: unknown, technicalDetails?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.path = path;
    this.payload = payload;
    this.technicalDetails = technicalDetails;
  }
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(TOKEN_KEY);
}

function clearAuthAndRedirect(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem("borusan_crm_user");
  if (window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
}

function getErrorMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === "object" && "error" in payload) {
    const error = (payload as ApiErrorPayload).error;
    if (typeof error === "string" && error === "Backend proxy failed") {
      const targetUrl = (payload as ApiErrorPayload).targetUrl;
      const message = (payload as ApiErrorPayload).message;
      return `Backend proxy failed${targetUrl ? ` for ${targetUrl}` : ""}${message ? `: ${message}` : ""}`;
    }
  }
  if (payload && typeof payload === "object" && "message" in payload) {
    const message = (payload as ApiErrorPayload).message;
    if (typeof message === "string") {
      return message;
    }
  }
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as ApiErrorPayload).detail;
    if (typeof detail === "string") {
      return detail;
    }
  }
  return fallback;
}

function getTechnicalDetails(payload: unknown, response: Response, path: string): string {
  const requestId = response.headers.get("x-request-id");
  const parts = [`Path: ${path}`, `Status: ${response.status}`];
  if (requestId) parts.push(`Request ID: ${requestId}`);
  if (payload && typeof payload === "object") {
    const typed = payload as ApiErrorPayload;
    if (typed.error_code) parts.push(`Error code: ${typed.error_code}`);
    if (typed.targetUrl) parts.push(`Target URL: ${typed.targetUrl}`);
    if (typed.details) parts.push(`Details: ${JSON.stringify(typed.details)}`);
  } else if (typeof payload === "string" && payload) {
    parts.push(`Body: ${payload.slice(0, 1000)}`);
  }
  return parts.join("\n");
}

function trimTrailingSlash(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

export function apiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  const baseUrl = trimTrailingSlash(API_BASE_URL);
  let normalizedPath = path.startsWith("/") ? path : `/${path}`;

  if (normalizedPath.startsWith("/api/backend")) {
    return normalizedPath;
  }

  if (baseUrl.endsWith("/api/backend") && normalizedPath.startsWith("/api/v1/")) {
    normalizedPath = normalizedPath.replace(/^\/api\/v1/, "");
  }

  return `${baseUrl}${normalizedPath}`;
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(apiUrl(path), {
      ...options,
      headers,
      cache: "no-store"
    });
  } catch (caught) {
    throw new ApiError(
      0,
      path,
      `Could not reach the API for ${path}. Check that the frontend proxy and FastAPI backend are running.`,
      undefined,
      caught instanceof Error ? caught.message : undefined
    );
  }

  const contentType = response.headers.get("content-type") ?? "";
  let payload: unknown;
  try {
    payload = contentType.includes("application/json")
      ? await response.json()
      : await response.text();
  } catch {
    payload = "";
  }

  if (!response.ok) {
    if (response.status === 401) {
      clearAuthAndRedirect();
    }
    throw new ApiError(
      response.status,
      path,
      getErrorMessage(payload, `Request to ${path} failed with status ${response.status}`),
      payload,
      getTechnicalDetails(payload, response, path)
    );
  }

  return payload as T;
}

export function getHealth() {
  return apiRequest<{ status: string; service: string }>("/api/v1/health");
}
