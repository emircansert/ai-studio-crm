import Link from "next/link";

import { ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";

type ErrorStateProps = {
  title: string;
  error: unknown;
  onRetry?: () => void;
  backHref?: string;
  backLabel?: string;
};

export function ErrorState({ title, error, onRetry, backHref, backLabel }: ErrorStateProps) {
  const message = error instanceof Error ? error.message : typeof error === "string" ? error : "Something went wrong.";
  const technicalDetails = error instanceof ApiError ? error.technicalDetails : undefined;

  return (
    <div className="error-state">
      <div>
        <h2>{title}</h2>
        <p>{message}</p>
      </div>
      {technicalDetails && process.env.NODE_ENV !== "production" ? (
        <details>
          <summary>Technical details</summary>
          <pre className="json-preview">{technicalDetails}</pre>
        </details>
      ) : null}
      <div className="button-row">
        {onRetry ? (
          <Button variant="secondary" onClick={onRetry}>
            Retry
          </Button>
        ) : null}
        {backHref ? (
          <Link className="button button--secondary" href={backHref}>
            {backLabel ?? "Go back"}
          </Link>
        ) : null}
      </div>
    </div>
  );
}
