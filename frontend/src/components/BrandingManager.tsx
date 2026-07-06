"use client";

import { CheckCircle2, UploadCloud } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { SectionCard } from "@/components/ui/Card";
import { FileUpload } from "@/components/ui/FileUpload";
import { apiRequest, apiUrl } from "@/lib/api";
import type { BrandingAsset } from "@/types/api";

export function BrandingManager() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [activeLogo, setActiveLogo] = useState<BrandingAsset | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    apiRequest<BrandingAsset | null>("/api/v1/admin/branding/active")
      .then(setActiveLogo)
      .catch(() => undefined);
  }, []);

  function handleSelect(nextFile: File | null) {
    setFile(nextFile);
    setError(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(nextFile ? URL.createObjectURL(nextFile) : null);
  }

  async function saveLogo() {
    if (!file) return;
    setIsSaving(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const uploaded = await apiRequest<BrandingAsset>("/api/v1/admin/branding/upload", {
        method: "POST",
        body: formData
      });
      setActiveLogo(uploaded);
      setFile(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not upload logo");
    } finally {
      setIsSaving(false);
    }
  }

  const logoUrl = activeLogo?.content_url ? apiUrl(activeLogo.content_url) : null;

  return (
    <SectionCard>
      <div className="section-heading">
        <h2>Logo asset</h2>
        <p>Upload a safe local logo file. The backend keeps one active logo and writes an audit log entry.</p>
      </div>
      <div className="branding-preview">
        {previewUrl || logoUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={previewUrl ?? logoUrl ?? undefined} alt="Borusan AI Studio logo preview" />
        ) : (
          <div className="brand">
            <div className="brand-mark">AI</div>
            <div>
              <strong>Borusan AI Studio</strong>
              <span>Ecosystem CRM</span>
            </div>
          </div>
        )}
      </div>
      <FileUpload
        accept=".png,.jpg,.jpeg,.svg,.webp"
        description="PNG, JPG, SVG, or WebP. Maximum size is 5 MB."
        selectedFile={file}
        title="Select Borusan AI Studio logo"
        onSelect={handleSelect}
      />
      {activeLogo ? (
        <div className="alert alert--success">
          <CheckCircle2 size={18} />
          Active logo: {activeLogo.original_filename}
        </div>
      ) : null}
      {error ? <div className="alert alert--error">{error}</div> : null}
      <Button disabled={!file || isSaving} onClick={saveLogo}>
        <UploadCloud size={17} />
        {isSaving ? "Saving..." : "Save logo"}
      </Button>
    </SectionCard>
  );
}
