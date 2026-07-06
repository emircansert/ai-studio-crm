"use client";

import { UploadCloud } from "lucide-react";
import { useRef } from "react";

import { Button } from "@/components/ui/Button";

type FileUploadProps = {
  accept?: string;
  disabled?: boolean;
  selectedFile?: File | null;
  title?: string;
  description?: string;
  onSelect: (file: File | null) => void;
};

export function FileUpload({
  accept = ".xlsx",
  title = "Upload Ecosystem Library workbook",
  description = "Only .xlsx files are accepted. The workbook will be profiled and staged for preview.",
  disabled = false,
  selectedFile,
  onSelect
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="file-upload">
      <input
        ref={inputRef}
        accept={accept}
        disabled={disabled}
        hidden
        type="file"
        onChange={(event) => onSelect(event.target.files?.[0] ?? null)}
      />
      <UploadCloud size={34} />
      <div>
        <h3>{selectedFile ? selectedFile.name : title}</h3>
        <p>{description}</p>
      </div>
      <Button disabled={disabled} variant="secondary" onClick={() => inputRef.current?.click()}>
        Choose file
      </Button>
    </div>
  );
}
