"use client"

import { useCallback, useState } from "react"
import { FileImage, Upload } from "lucide-react"
import { useDropzone } from "react-dropzone"

import { Button } from "@/components/ui/button"

interface FileUploaderProps {
  onFileChange: (file: File | null) => void
}

export function FileUploader({ onFileChange }: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false)

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileChange(acceptedFiles[0])
      }
    },
    [onFileChange],
  )

  const { getRootProps, getInputProps, open } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"],
      "application/pdf": [".pdf"],
    },
    maxFiles: 1,
    multiple: false,
    onDragEnter: () => setIsDragging(true),
    onDragLeave: () => setIsDragging(false),
    onDropAccepted: () => setIsDragging(false),
    onDropRejected: () => setIsDragging(false),
  })

  return (
    <div
      {...getRootProps()}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 text-center transition-colors ${
        isDragging ? "border-primary bg-primary/5" : "border-muted-foreground/25"
      }`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-4">
        <div className="rounded-full bg-muted p-4">
          <FileImage className="h-8 w-8 text-muted-foreground" />
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-medium">Upload Sheet Music</h3>
          <p className="text-sm text-muted-foreground">Drag and drop your sheet music image here, or click to browse</p>
        </div>
        <Button type="button" onClick={open} className="mt-2">
          <Upload className="mr-2 h-4 w-4" />
          Select File
        </Button>
        <p className="text-xs text-muted-foreground">Supported formats: PNG, JPG, PDF (max 10MB)</p>
      </div>
    </div>
  )
}
