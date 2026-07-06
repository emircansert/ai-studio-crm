"use client";

import {
  AlertCircle,
  CheckCircle2,
  FileSpreadsheet,
  GitBranch,
  RefreshCw,
  Send,
  UploadCloud
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { FileUpload } from "@/components/ui/FileUpload";
import { Table } from "@/components/ui/Table";
import { WarningSummary } from "@/components/ui/WarningSummary";
import { apiRequest } from "@/lib/api";
import type {
  CommitResult,
  ImportBatch,
  ImportCandidate,
  ImportCandidatesPreview,
  ImportPreview,
  ImportPreviewSheet
} from "@/types/api";

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function formatUnknown(value: unknown): string {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function ImportCenter() {
  const [file, setFile] = useState<File | null>(null);
  const [batches, setBatches] = useState<ImportBatch[]>([]);
  const [selectedBatch, setSelectedBatch] = useState<ImportBatch | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [candidatePreview, setCandidatePreview] = useState<ImportCandidatesPreview | null>(null);
  const [commitResult, setCommitResult] = useState<CommitResult | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [batchError, setBatchError] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [candidateError, setCandidateError] = useState<string | null>(null);
  const [commitError, setCommitError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [isLoadingBatches, setIsLoadingBatches] = useState(false);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);

  async function loadBatches() {
    setIsLoadingBatches(true);
    setBatchError(null);
    try {
      const data = await apiRequest<ImportBatch[]>("/api/v1/imports");
      setBatches(data);
    } catch (caught) {
      setBatchError(`Could not load import batches: ${caught instanceof Error ? caught.message : "Request failed"}`);
    } finally {
      setIsLoadingBatches(false);
    }
  }

  async function loadPreview(batchId: string) {
    setIsLoadingPreview(true);
    setPreviewError(null);
    setCandidateError(null);
    try {
      const data = await apiRequest<ImportPreview>(`/api/v1/imports/${batchId}/preview`);
      setPreview(data);
      setUploadError(null);
      setPreviewError(null);
      await loadCandidates(batchId, false);
    } catch (caught) {
      setPreview(null);
      setPreviewError(`Could not load import preview: ${caught instanceof Error ? caught.message : "Request failed"}`);
    } finally {
      setIsLoadingPreview(false);
    }
  }

  async function loadCandidates(batchId: string, showError = true) {
    setCandidateError(null);
    try {
      const data = await apiRequest<ImportCandidatesPreview>(`/api/v1/imports/${batchId}/candidates`);
      setCandidatePreview(data);
      setCandidateError(null);
    } catch (caught) {
      setCandidatePreview(null);
      if (showError) {
        setCandidateError(`Could not load import candidates: ${caught instanceof Error ? caught.message : "Request failed"}`);
      }
    }
  }

  async function generateCandidates() {
    if (!selectedBatch) return;
    setIsGenerating(true);
    setCandidateError(null);
    setUploadError(null);
    setPreviewError(null);
    setCommitError(null);
    setCommitResult(null);
    try {
      const data = await apiRequest<ImportCandidatesPreview>(
        `/api/v1/imports/${selectedBatch.id}/candidates/generate`,
        { method: "POST" }
      );
      setCandidatePreview(data);
      setCandidateError(null);
      setUploadError(null);
      await loadBatches();
    } catch (caught) {
      setCandidateError(`Candidate generation failed: ${caught instanceof Error ? caught.message : "Request failed"}`);
    } finally {
      setIsGenerating(false);
    }
  }

  async function updateDecision(candidateId: string, decisionStatus: "APPROVED" | "REJECTED" | "SKIPPED") {
    if (!selectedBatch) return;
    setCandidateError(null);
    setCommitError(null);
    try {
      await apiRequest(`/api/v1/imports/candidates/${candidateId}/decision`, {
        method: "PATCH",
        body: JSON.stringify({
          decision_status: decisionStatus,
          decision_reason: `Marked ${decisionStatus.toLowerCase()} in Import Center`
        })
      });
      await loadCandidates(selectedBatch.id);
    } catch (caught) {
      setCandidateError(`Could not update candidate decision: ${caught instanceof Error ? caught.message : "Request failed"}`);
    }
  }

  async function commitImport() {
    if (!selectedBatch) return;
    setIsCommitting(true);
    setCommitError(null);
    setCandidateError(null);
    try {
      const result = await apiRequest<CommitResult>(`/api/v1/imports/${selectedBatch.id}/commit`, {
        method: "POST"
      });
      setCommitResult(result);
      await loadBatches();
      await loadCandidates(selectedBatch.id);
    } catch (caught) {
      setCommitError(`Commit failed: ${caught instanceof Error ? caught.message : "Request failed"}`);
    } finally {
      setIsCommitting(false);
    }
  }

  async function uploadWorkbook() {
    if (!file) return;
    setIsUploading(true);
    setUploadError(null);
    setPreviewError(null);
    setCandidateError(null);
    setCommitError(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const batch = await apiRequest<ImportBatch>("/api/v1/imports/upload", {
        method: "POST",
        body: formData
      });
      setSelectedBatch(batch);
      setCandidatePreview(null);
      setCommitResult(null);
      await loadPreview(batch.id);
      await loadBatches();
    } catch (caught) {
      setUploadError(`Upload failed: ${caught instanceof Error ? caught.message : "Request failed"}`);
    } finally {
      setIsUploading(false);
    }
  }

  useEffect(() => {
    void loadBatches();
  }, []);

  const duplicateCount = useMemo(() => {
    if (!preview?.duplicate_candidates) return 0;
    return Object.values(preview.duplicate_candidates).reduce(
      (sum, group) => sum + Object.keys(group ?? {}).length,
      0
    );
  }, [preview]);
  const candidateCount = useMemo(() => {
    if (!candidatePreview) return 0;
    return Object.values(candidatePreview.candidate_counts_by_entity_type).reduce((sum, count) => sum + count, 0);
  }, [candidatePreview]);

  return (
    <div className="import-layout">
      <SectionCard>
        <div className="section-heading">
          <h2>Workbook upload</h2>
          <p>Upload the current Ecosystem Library. Rows are staged only after profiling.</p>
        </div>
        <FileUpload disabled={isUploading} selectedFile={file} onSelect={setFile} />
        <div className="button-row">
          <Button disabled={!file || isUploading} onClick={uploadWorkbook}>
            <UploadCloud size={17} />
            {isUploading ? "Uploading..." : "Upload and preview"}
          </Button>
          <Button variant="secondary" onClick={loadBatches} disabled={isLoadingBatches}>
            <RefreshCw size={16} />
            Refresh batches
          </Button>
        </div>
        {uploadError ? (
          <div className="alert alert--error">
            <AlertCircle size={18} />
            {uploadError}
          </div>
        ) : null}
      </SectionCard>

      <SectionCard>
        <div className="section-heading section-heading--inline">
          <div>
            <h2>Previous import batches</h2>
            <p>Select a batch to inspect its staged preview.</p>
          </div>
          {isLoadingBatches ? <Badge tone="info">Loading</Badge> : null}
        </div>
        {batchError ? (
          <div className="alert alert--warning">
            <AlertCircle size={18} />
            {batchError}
          </div>
        ) : null}
        {batches.length ? (
          <Table
            rows={batches}
            getRowKey={(row) => row.id}
            columns={[
              {
                key: "file",
                header: "Workbook",
                render: (row) => (
                  <button
                    className="link-button"
                    onClick={() => {
                      setSelectedBatch(row);
                      setCommitResult(null);
                      setPreviewError(null);
                      setCandidateError(null);
                      setCommitError(null);
                      void loadPreview(row.id);
                    }}
                    type="button"
                  >
                    {row.original_filename}
                  </button>
                )
              },
              { key: "status", header: "Status", render: (row) => <Badge tone="info">{row.status}</Badge> },
              { key: "created", header: "Created", render: (row) => formatDate(row.created_at) }
            ]}
          />
        ) : (
          <EmptyState
            title="No import batches yet"
            description="Upload Ekosistem_Library_V2.xlsx to create the first staged preview."
          />
        )}
      </SectionCard>

      <SectionCard className="wide-card">
        <div className="section-heading section-heading--inline">
          <div>
            <h2>Preview</h2>
            <p>
              {selectedBatch
                ? `Batch ${selectedBatch.id}`
                : "Upload or select an import batch to see staged rows and warnings."}
            </p>
          </div>
          <Button
            disabled={!selectedBatch || isGenerating || selectedBatch.status === "COMMITTED"}
            variant="secondary"
            onClick={generateCandidates}
          >
            <GitBranch size={16} />
            {isGenerating ? "Generating..." : "Generate Candidates"}
          </Button>
          <Button
            disabled={!candidatePreview?.can_commit || isCommitting || selectedBatch?.status === "COMMITTED"}
            title={
              candidatePreview?.can_commit
                ? "Commit approved candidates"
                : "Resolve review items and blocking errors before commit"
            }
            onClick={commitImport}
          >
            <Send size={16} />
            {isCommitting ? "Committing..." : "Commit Import"}
          </Button>
        </div>

        <div className="phase-note">
          Commit writes only approved candidates. Pending, rejected, skipped, and error candidates are not committed.
        </div>

        <div className="stepper">
          {["Upload", "Preview", "Candidates", "Review", "Commit"].map((step) => {
            const active =
              (step === "Upload" && Boolean(selectedBatch)) ||
              (step === "Preview" && Boolean(preview)) ||
              (step === "Candidates" && Boolean(candidatePreview)) ||
              (step === "Review" && Boolean(candidatePreview?.needs_review.length)) ||
              (step === "Commit" && Boolean(commitResult || selectedBatch?.status === "COMMITTED"));
            return (
              <div className={`step ${active ? "step--active" : ""}`} key={step}>
                {step}
              </div>
            );
          })}
        </div>

        {commitResult ? (
          <div className="alert alert--success">
            <CheckCircle2 size={18} />
            Commit complete. Created records are available in Startup Library, Events, Network, and PoC Pipeline.
          </div>
        ) : null}

        {previewError ? (
          <div className="alert alert--error">
            <AlertCircle size={18} />
            {previewError}
          </div>
        ) : null}

        {candidateError ? (
          <div className="alert alert--error">
            <AlertCircle size={18} />
            {candidateError}
          </div>
        ) : null}

        {commitError ? (
          <div className="alert alert--error">
            <AlertCircle size={18} />
            {commitError}
          </div>
        ) : null}

        {isLoadingPreview ? <EmptyState title="Loading preview" description="Reading staged workbook data..." /> : null}

        {preview ? (
          <div className="preview-stack">
            <div className="stat-grid stat-grid--compact">
              <div className="mini-stat">
                <span>Sheets</span>
                <strong>{preview.detected_sheets.length}</strong>
              </div>
              <div className="mini-stat">
                <span>Staged rows</span>
                <strong>{Object.values(preview.staged_row_counts).reduce((sum, count) => sum + count, 0)}</strong>
              </div>
              <div className="mini-stat">
                <span>Duplicate candidates</span>
                <strong>{duplicateCount}</strong>
              </div>
              <div className="mini-stat">
                <span>Status</span>
                <strong>{preview.batch.status}</strong>
              </div>
            </div>

            <WarningSummary
              byCode={preview.warning_counts.by_code}
              bySeverity={preview.warning_counts.by_severity}
            />

            <PreviewSheets sheets={preview.detected_sheets} />
            {candidatePreview && candidateCount > 0 ? (
              <CandidateSummary
                preview={candidatePreview}
                onDecision={(candidateId, decisionStatus) => void updateDecision(candidateId, decisionStatus)}
              />
            ) : (
              <EmptyState
                title="Candidates not generated yet"
                description="Generate candidates to review exactly which CRM records will be created or matched."
              />
            )}
            <PreviewSamples preview={preview} />
            <PreviewIssues preview={preview} />
          </div>
        ) : (
          !isLoadingPreview && (
            <EmptyState
              title="Preview waiting"
              description="A staged workbook preview will appear here after upload."
              action={<FileSpreadsheet size={22} />}
            />
          )
        )}
      </SectionCard>
    </div>
  );
}

function PreviewSheets({ sheets }: { sheets: ImportPreviewSheet[] }) {
  return (
    <div>
      <div className="section-heading">
        <h3>Detected sheets</h3>
      </div>
      <Table
        rows={sheets}
        getRowKey={(row) => row.id}
        columns={[
          { key: "sheet", header: "Sheet", render: (row) => row.sheet_name },
          { key: "entity", header: "Mapped entity", render: (row) => <Badge>{row.detected_entity}</Badge> },
          { key: "rows", header: "Rows", render: (row) => row.row_count ?? 0 },
          { key: "staged", header: "Staged", render: (row) => row.staged_row_count }
        ]}
      />
    </div>
  );
}

function CandidateSummary({
  preview,
  onDecision
}: {
  preview: ImportCandidatesPreview;
  onDecision: (candidateId: string, decisionStatus: "APPROVED" | "REJECTED" | "SKIPPED") => void;
}) {
  const importantEntities = [
    "ORGANIZATION",
    "CONTACT",
    "ORGANIZATION_BORUSAN_FIT",
    "OPPORTUNITY",
    "EVENT",
    "EVENT_PARTICIPANT",
    "AI_TOOL",
    "NOTE"
  ];
  const needsReview = preview.needs_review.filter((candidate) => candidate.decision_status === "PENDING");

  return (
    <div className="candidate-stack">
      <div className="section-heading">
        <h3>Candidate summary</h3>
        <p>These are normalized records proposed from staged Excel rows.</p>
      </div>

      <div className="candidate-count-grid">
        {importantEntities.map((entity) => (
          <div className="mini-stat" key={entity}>
            <span>{entity.replaceAll("_", " ")}</span>
            <strong>{preview.candidate_counts_by_entity_type[entity] ?? 0}</strong>
          </div>
        ))}
      </div>

      <div className="candidate-status-grid">
        <div>
          <h4>Actions</h4>
          <div className="badge-row">
            {Object.entries(preview.action_counts).map(([action, count]) => (
              <Badge key={action} tone={action === "NEEDS_REVIEW" ? "warning" : "info"}>
                {action}: {count}
              </Badge>
            ))}
          </div>
        </div>
        <div>
          <h4>Decisions</h4>
          <div className="badge-row">
            {Object.entries(preview.decision_counts).map(([decision, count]) => (
              <Badge key={decision} tone={decision === "PENDING" ? "warning" : "success"}>
                {decision}: {count}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      {needsReview.length ? (
        <div className="sample-panel">
          <div className="section-heading">
            <h3>Needs review</h3>
            <p>Resolve these before commit. Error candidates cannot be approved.</p>
          </div>
          {needsReview.slice(0, 12).map((candidate) => (
            <CandidateReviewRow candidate={candidate} key={candidate.id} onDecision={onDecision} />
          ))}
        </div>
      ) : (
        <div className="alert alert--success">
          <CheckCircle2 size={18} />
          Candidate decisions are ready for commit.
        </div>
      )}
    </div>
  );
}

function CandidateReviewRow({
  candidate,
  onDecision
}: {
  candidate: ImportCandidate;
  onDecision: (candidateId: string, decisionStatus: "APPROVED" | "REJECTED" | "SKIPPED") => void;
}) {
  const reason =
    typeof candidate.candidate_data.reason === "string"
      ? candidate.candidate_data.reason
      : candidate.validation_status;

  return (
    <div className="candidate-review-row">
      <div>
        <Badge tone={candidate.validation_status === "ERROR" ? "danger" : "warning"}>
          {candidate.entity_type}
        </Badge>
        <strong>{candidate.action_type}</strong>
        <p>{reason}</p>
      </div>
      <div className="button-row">
        <Button
          disabled={candidate.validation_status === "ERROR"}
          variant="secondary"
          onClick={() => onDecision(candidate.id, "APPROVED")}
        >
          Approve
        </Button>
        <Button variant="secondary" onClick={() => onDecision(candidate.id, "SKIPPED")}>
          Skip
        </Button>
        <Button variant="danger" onClick={() => onDecision(candidate.id, "REJECTED")}>
          Reject
        </Button>
      </div>
    </div>
  );
}

function PreviewSamples({ preview }: { preview: ImportPreview }) {
  const entries = Object.entries(preview.sample_rows);
  if (!entries.length) return null;

  return (
    <div className="sample-grid">
      {entries.map(([entity, rows]) => (
        <div className="sample-panel" key={entity}>
          <div className="section-heading">
            <h3>{entity}</h3>
            <p>Sample staged rows</p>
          </div>
          {rows.slice(0, 3).map((row) => (
            <div className="sample-row" key={row.id}>
              <div>
                <Badge tone={row.validation_status === "VALID" ? "success" : "warning"}>
                  Row {row.excel_row_number}
                </Badge>
              </div>
              <dl>
                {Object.entries(row.cleaned_values ?? {})
                  .slice(0, 5)
                  .map(([key, value]) => (
                    <div key={key}>
                      <dt>{key}</dt>
                      <dd>{formatUnknown(value)}</dd>
                    </div>
                  ))}
              </dl>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function PreviewIssues({ preview }: { preview: ImportPreview }) {
  const missing = preview.missing_mappings_or_columns ?? [];
  const duplicateGroups = Object.entries(preview.duplicate_candidates ?? {});

  if (!missing.length && !duplicateGroups.length) {
    return null;
  }

  return (
    <div className="issue-grid">
      {missing.length ? (
        <div className="sample-panel">
          <div className="section-heading">
            <h3>Missing mappings / columns</h3>
          </div>
          {missing.map((item, index) => (
            <div className="issue-item" key={`${item.code}-${index}`}>
              <Badge tone={item.code === "MISSING_REQUIRED_COLUMN" ? "danger" : "warning"}>{item.code}</Badge>
              <span>{item.message}</span>
            </div>
          ))}
        </div>
      ) : null}

      {duplicateGroups.length ? (
        <div className="sample-panel">
          <div className="section-heading">
            <h3>Duplicate candidates</h3>
          </div>
          {duplicateGroups.map(([group, candidates]) => (
            <div className="issue-item" key={group}>
              <Badge tone="warning">{group}</Badge>
              <span>{Object.keys(candidates ?? {}).join(", ")}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
