"use client";

import { useRef, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import type { DocumentSummary } from "@/lib/types";

export function UploadPanel({
  file,
  onFile,
  document: doc,
  maxUploadMb,
  allowedExtensions,
  disabled,
}: {
  file: File | null;
  onFile: (file: File | null) => void;
  document: DocumentSummary | null;
  maxUploadMb: number;
  allowedExtensions: string[];
  disabled?: boolean;
}) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function pick(files: FileList | null) {
    const next = files?.[0];
    if (next) onFile(next);
  }

  return (
    <Card>
      <CardHeader
        title="Resume"
        description={`${allowedExtensions.join(", ")} · up to ${maxUploadMb}MB`}
      />
      <CardBody>
        <div
          onDragOver={(e) => {
            e.preventDefault();
            if (!disabled) setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            if (!disabled) pick(e.dataTransfer.files);
          }}
          className={cn(
            "rounded-lg border-2 border-dashed px-6 py-8 text-center transition-colors",
            dragging
              ? "border-accent bg-accent-soft"
              : "border-[var(--border-strong)]",
            disabled && "opacity-55",
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept={allowedExtensions.join(",")}
            className="sr-only"
            disabled={disabled}
            onChange={(e) => pick(e.target.files)}
          />
          <p className="text-sm text-muted">
            Drag a file here, or{" "}
            <button
              type="button"
              disabled={disabled}
              onClick={() => inputRef.current?.click()}
              className="rounded font-medium text-accent underline-offset-2 hover:underline disabled:cursor-not-allowed"
            >
              browse
            </button>
          </p>
        </div>

        {file && (
          <div className="mt-3 flex items-center justify-between gap-3 rounded-lg border bg-surface-2 px-3 py-2">
            <span className="truncate text-sm font-medium">{file.name}</span>
            <button
              type="button"
              disabled={disabled}
              onClick={() => {
                onFile(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
              className="shrink-0 rounded text-sm text-muted hover:text-fg disabled:cursor-not-allowed"
            >
              Remove
            </button>
          </div>
        )}

        {doc && (
          <div className="mt-4 border-t pt-4">
            <p className="mb-2 text-xs font-semibold tracking-wide text-subtle uppercase">
              Parsed successfully
            </p>
            <div className="flex flex-wrap gap-1.5">
              <Badge tone="success">{doc.word_count} words</Badge>
              <Badge>{doc.bullet_count} bullets</Badge>
              {doc.section_names.map((name) => (
                <Badge key={name}>{name}</Badge>
              ))}
              {doc.contact.email && <Badge tone="accent">email found</Badge>}
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
}
