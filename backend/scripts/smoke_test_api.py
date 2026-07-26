import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib import error, request


API_BASE_URL = os.getenv("SMOKE_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
# Authentication is Microsoft Entra ID only, so this script cannot mint its own
# token. Supply a current Entra ID token for an ADMIN user, e.g. copied from the
# signed-in browser session (sessionStorage / the Authorization header).
BEARER_TOKEN = os.getenv("SMOKE_BEARER_TOKEN", "").strip()
VERBOSE = os.getenv("SMOKE_VERBOSE") == "1"


@dataclass
class ApiResult:
    status: int
    body: Any


class SmokeFailure(Exception):
    def __init__(self, endpoint: str, status: int | None, body: Any) -> None:
        self.endpoint = endpoint
        self.status = status
        self.body = body
        super().__init__(f"{endpoint} returned {status}: {body}")


def _decode_body(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="replace")
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def call(
    path: str,
    *,
    method: str = "GET",
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    expected_status: set[int] | None = None,
) -> ApiResult:
    expected = expected_status or {200}
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    endpoint = f"{API_BASE_URL}{path}"
    req = request.Request(endpoint, data=body, method=method)
    req.add_header("Accept", "application/json")
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with request.urlopen(req, timeout=30) as response:
            result = ApiResult(status=response.status, body=_decode_body(response.read()))
    except error.HTTPError as exc:
        result = ApiResult(status=exc.code, body=_decode_body(exc.read()))
    except error.URLError as exc:
        raise SmokeFailure(endpoint, None, str(exc)) from exc

    if result.status not in expected:
        raise SmokeFailure(endpoint, result.status, result.body)
    return result


def check(name: str, fn) -> tuple[bool, Any]:
    try:
        result = fn()
        body = result.body if isinstance(result, ApiResult) else result
        print(f"PASS {name}")
        if VERBOSE and body is not None:
            print(json.dumps(body, indent=2, default=str)[:1600])
        return True, body
    except Exception as exc:  # noqa: BLE001 - smoke test should report every failure plainly.
        print(f"FAIL {name}: {exc}")
        if isinstance(exc, SmokeFailure):
            print(f"  endpoint: {exc.endpoint}")
            print(f"  status: {exc.status}")
            print(f"  body: {json.dumps(exc.body, indent=2, default=str)[:2000]}")
        return False, None


def main() -> int:
    if not BEARER_TOKEN:
        print("FAIL config: set SMOKE_BEARER_TOKEN to a current Entra ID token for an ADMIN user.")
        print("  Sign in to the CRM, then copy the bearer token the browser sends to /api/backend.")
        return 2

    results: list[bool] = []
    user_holder: dict[str, Any] = {}
    organization_holder: dict[str, Any] = {}

    def record(name: str, fn) -> Any:
        passed, body = check(name, fn)
        results.append(passed)
        return body

    record("health", lambda: call("/api/v1/health"))
    readiness = record("readiness", lambda: call("/api/v1/health/readiness", expected_status={200}))
    if readiness and readiness.get("status") not in {"ok", "degraded"}:
        print(f"FAIL readiness status: unexpected payload {readiness}")
        results.append(False)

    token = BEARER_TOKEN
    me_body = record("whoami (auth/me)", lambda: call("/api/v1/auth/me", token=token))
    if not me_body:
        print("  The token is missing, expired, or not accepted. Sign in again and re-copy it.")
        print(f"\nSmoke test summary: {sum(results)}/{len(results)} checks passed against {API_BASE_URL}")
        return 1
    user_holder["user"] = me_body
    record("my section access", lambda: call("/api/v1/users/me/section-access", token=token))
    record("dashboard summary", lambda: call("/api/v1/dashboard/summary", token=token))
    record("active users", lambda: call("/api/v1/users/active?limit=500", token=token))
    record("notifications list", lambda: call("/api/v1/notifications?limit=5", token=token))
    record("notification unread count", lambda: call("/api/v1/notifications/unread-count", token=token))
    org_list = record("organizations list", lambda: call("/api/v1/organizations?limit=5", token=token))
    if org_list and org_list.get("items"):
        org = org_list["items"][0]
        organization_holder["id"] = org["id"]
        org_id = organization_holder["id"]
        record("organization detail", lambda: call(f"/api/v1/organizations/{org_id}", token=token))
        record("organization documents", lambda: call(f"/api/v1/organizations/{org_id}/documents", token=token))
        record("organization contacts", lambda: call(f"/api/v1/organizations/{org_id}/contacts", token=token))
        record("organization notes", lambda: call(f"/api/v1/organizations/{org_id}/notes", token=token))
        record("organization borusan fit", lambda: call(f"/api/v1/organizations/{org_id}/borusan-fit", token=token))
    else:
        print("SKIP organization related checks: no organizations returned")

    record("follow-ups list", lambda: call("/api/v1/follow-ups?limit=5", token=token))
    record("leaderboard", lambda: call("/api/v1/leaderboard?limit=5", token=token))
    record("YZ champion leaderboard", lambda: call("/api/v1/leaderboard/champion?limit=5", token=token))
    record("YZ champion score rules", lambda: call("/api/v1/leaderboard/champion/rules", token=token))
    record("my YZ champion score", lambda: call("/api/v1/leaderboard/champion/me", token=token))
    record("use cases list", lambda: call("/api/v1/use-cases?limit=10", token=token))
    record("program activities list", lambda: call("/api/v1/program-activities?limit=10&activity_type=ALL", token=token))
    record("ai tools list", lambda: call("/api/v1/ai-tools?limit=10", token=token))
    record("import batches", lambda: call("/api/v1/imports?limit=5", token=token))
    record("admin branding active", lambda: call("/api/v1/admin/branding/active", token=token, expected_status={200}))
    if user_holder["user"].get("role") == "ADMIN":
        record("admin section access matrix", lambda: call("/api/v1/admin/users/section-access?limit=10", token=token))
        record("admin CRM activity", lambda: call("/api/v1/admin/activity?limit=5", token=token))
        record("admin audit logs", lambda: call("/api/v1/admin/audit-logs?limit=5", token=token))
        record("admin champion activities", lambda: call("/api/v1/admin/champion-activities?limit=5", token=token))
    else:
        print("SKIP admin audit logs: login user is not ADMIN")

    passed = sum(results)
    total = len(results)
    print(f"\nSmoke test summary: {passed}/{total} checks passed against {API_BASE_URL}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
