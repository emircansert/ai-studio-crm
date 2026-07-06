import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const DEFAULT_BACKEND_ORIGIN = "http://127.0.0.1:8000";

type ProxyContext = {
  params: {
    path?: string[];
  };
};

function getBackendOrigin(): string {
  const configuredOrigin = process.env.BACKEND_API_ORIGIN?.trim() || DEFAULT_BACKEND_ORIGIN;
  const withoutApiPath = configuredOrigin.replace(/\/+$/, "").replace(/\/api\/v1$/i, "");

  try {
    const parsed = new URL(withoutApiPath);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return DEFAULT_BACKEND_ORIGIN;
    }
    return parsed.origin;
  } catch {
    return DEFAULT_BACKEND_ORIGIN;
  }
}

function getBackendApiBase(): string {
  return `${getBackendOrigin()}/api/v1`;
}

function getBackendPath(pathSegments: string[] = []): string {
  const segments = [...pathSegments];

  if (segments[0]?.toLowerCase() === "api" && segments[1]?.toLowerCase() === "v1") {
    segments.splice(0, 2);
  }

  return segments.map((segment) => encodeURIComponent(segment)).join("/");
}

function getForwardHeaders(request: NextRequest): Headers {
  const headers = new Headers();
  const authorization = request.headers.get("authorization");
  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");

  if (authorization) headers.set("authorization", authorization);
  if (contentType) headers.set("content-type", contentType);
  if (accept) headers.set("accept", accept);

  return headers;
}

function getResponseHeaders(backendResponse: Response): Headers {
  const headers = new Headers(backendResponse.headers);

  headers.delete("connection");
  headers.delete("content-encoding");
  headers.delete("content-length");
  headers.delete("transfer-encoding");

  return headers;
}

async function proxyToBackend(request: NextRequest, context: ProxyContext) {
  const requestedUrl = new URL(request.url);
  const backendPath = getBackendPath(context.params.path);
  const targetUrl = new URL(`${getBackendApiBase()}/${backendPath}`);
  targetUrl.search = requestedUrl.search;

  const method = request.method.toUpperCase();

  try {
    const init: RequestInit = {
      method,
      headers: getForwardHeaders(request),
      cache: "no-store",
      redirect: "manual"
    };

    if (method !== "GET" && method !== "HEAD") {
      const body = await request.arrayBuffer();
      if (body.byteLength > 0) {
        init.body = body;
      }
    }

    const backendResponse = await fetch(targetUrl, init);
    const responseBody = await backendResponse.arrayBuffer();

    return new Response(responseBody, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
      headers: getResponseHeaders(backendResponse)
    });
  } catch (caught) {
    return Response.json(
      {
        error: "Backend proxy failed",
        targetUrl: targetUrl.toString(),
        message: caught instanceof Error ? caught.message : "Unknown proxy error"
      },
      { status: 502 }
    );
  }
}

export async function GET(request: NextRequest, context: ProxyContext) {
  return proxyToBackend(request, context);
}

export async function POST(request: NextRequest, context: ProxyContext) {
  return proxyToBackend(request, context);
}

export async function PUT(request: NextRequest, context: ProxyContext) {
  return proxyToBackend(request, context);
}

export async function PATCH(request: NextRequest, context: ProxyContext) {
  return proxyToBackend(request, context);
}

export async function DELETE(request: NextRequest, context: ProxyContext) {
  return proxyToBackend(request, context);
}

export async function HEAD(request: NextRequest, context: ProxyContext) {
  return proxyToBackend(request, context);
}

export async function OPTIONS(request: NextRequest, context: ProxyContext) {
  return proxyToBackend(request, context);
}
