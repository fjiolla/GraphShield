"use client";

import React, { useCallback } from "react";
import { useDropzone, type Accept } from "react-dropzone";
import { cn } from "@/utils/cn";
import { Upload, FileText, X } from "lucide-react";
import { formatBytes } from "@/utils/formatters";

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  accept?: Accept;
  maxSize?: number;
  label?: string;
  description?: string;
  selectedFile?: File | null;
  onClear?: () => void;
  className?: string;
  disabled?: boolean;
}

export function DropZone({
  onFileSelect,
  accept,
  maxSize = 50 * 1024 * 1024, // 50MB default
  label = "Upload a file",
  description = "Drag and drop or click to browse",
  selectedFile,
  onClear,
  className,
  disabled = false,
}: DropZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } =
    useDropzone({
      onDrop,
      accept,
      maxSize,
      multiple: false,
      disabled,
    });

  if (selectedFile) {
    return (
      <div
        className={cn(
          "gs-card-static p-4 flex items-center gap-3",
          className
        )}
      >
        <div className="w-10 h-10 rounded-xl bg-sage-50 flex items-center justify-center flex-shrink-0">
          <FileText className="w-5 h-5 text-sage-500" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[13px] font-medium text-warm-800 truncate">
            {selectedFile.name}
          </p>
          <p className="text-[12px] text-warm-400">
            {formatBytes(selectedFile.size)}
          </p>
        </div>
        {onClear && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClear();
            }}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-warm-400 hover:bg-warm-100 hover:text-warm-600 transition-colors"
            aria-label="Remove file"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={cn(
        "gs-card-static p-8 flex flex-col items-center justify-center text-center cursor-pointer",
        "border-2 border-dashed border-warm-200 rounded-2xl",
        "transition-all duration-150 ease-out",
        isDragActive && "border-sage-500 bg-sage-50/50",
        disabled && "opacity-50 cursor-not-allowed",
        !isDragActive && !disabled && "hover:border-warm-300 hover:bg-warm-50",
        className
      )}
    >
      <input {...getInputProps()} />
      <div className="w-12 h-12 rounded-2xl bg-warm-100 flex items-center justify-center mb-3">
        <Upload
          className={cn(
            "w-5 h-5",
            isDragActive ? "text-sage-500" : "text-warm-400"
          )}
        />
      </div>
      <p className="text-[13px] font-medium text-warm-700 mb-1">{label}</p>
      <p className="text-[12px] text-warm-400">{description}</p>

      {fileRejections.length > 0 && (
        <p className="text-[12px] text-danger-500 mt-2">
          {fileRejections[0].errors[0]?.message || "File rejected"}
        </p>
      )}
    </div>
  );
}
