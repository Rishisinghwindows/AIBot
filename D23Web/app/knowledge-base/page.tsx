"use client";

import { useAuth } from "@/context/AuthContext";
import React, { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Loader2,
  ArrowLeft,
  Upload,
  FileText,
  Trash2,
  Search,
  BookOpen,
  File,
  Check,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import authFetch from "@/lib/auth_fetch";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface Document {
  id: string;
  filename: string;
  chunks: number;
  uploaded_at: string;
  size?: number;
}

export default function KnowledgeBasePage() {
  const { currentUser, loading, idToken, accessToken } = useAuth();
  const router = useRouter();
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [queryResult, setQueryResult] = useState<string | null>(null);
  const [isQuerying, setIsQuerying] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    const pdfFiles = files.filter(f => f.type === "application/pdf");
    if (pdfFiles.length > 0) {
      handleFileUpload(pdfFiles);
    } else {
      setUploadError("Please upload PDF files only");
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      handleFileUpload(files);
    }
  };

  const handleFileUpload = async (files: File[]) => {
    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    setUploadProgress(0);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      // Check file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setUploadError(`${file.name} exceeds 10MB limit`);
        continue;
      }

      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`${apiBase}/pdf/upload`, {
          method: "POST",
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          setDocuments(prev => [
            {
              id: data.filename,
              filename: file.name,
              chunks: data.chunks,
              uploaded_at: new Date().toISOString(),
              size: file.size,
            },
            ...prev,
          ]);
          setUploadSuccess(`Uploaded ${file.name} (${data.chunks} chunks)`);
        } else {
          const error = await response.json();
          setUploadError(error.detail || "Upload failed");
        }
      } catch (error) {
        console.error("Upload error:", error);
        setUploadError("Upload failed. Please try again.");
      }

      setUploadProgress(((i + 1) / files.length) * 100);
    }

    setIsUploading(false);
    setTimeout(() => {
      setUploadSuccess(null);
      setUploadError(null);
    }, 5000);
  };

  const handleQuery = async () => {
    if (!query.trim()) return;

    setIsQuerying(true);
    setQueryResult(null);

    try {
      const response = await fetch(`${apiBase}/web/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: `Search my documents: ${query}`,
          session_id: "knowledge-base-query",
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setQueryResult(data.response || "No results found.");
      } else {
        setQueryResult("Query failed. Please try again.");
      }
    } catch (error) {
      console.error("Query error:", error);
      setQueryResult("Query failed. Please try again.");
    } finally {
      setIsQuerying(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-white" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-[#0a0a0a]/95 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.back()}
            className="text-white/60 hover:text-white"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-blue-400" />
            <h1 className="text-xl font-semibold">Knowledge Base</h1>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Upload Section */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 transition-colors ${
            isDragging
              ? "border-blue-400 bg-blue-400/10"
              : "border-white/20 hover:border-white/40"
          }`}
        >
          <div className="text-center">
            <Upload className="h-12 w-12 mx-auto text-white/40 mb-4" />
            <h3 className="text-lg font-medium mb-2">Upload Documents</h3>
            <p className="text-white/40 text-sm mb-4">
              Drag & drop PDF files here, or click to browse
            </p>
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload">
              <Button
                variant="outline"
                className="cursor-pointer border-white/20 text-white hover:bg-white/10"
                asChild
              >
                <span>Choose Files</span>
              </Button>
            </label>
            <p className="text-white/30 text-xs mt-2">Max 10MB per file</p>
          </div>

          {/* Upload Progress */}
          {isUploading && (
            <div className="mt-6">
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-blue-400" />
                <span className="text-sm text-white/60">Uploading...</span>
              </div>
              <div className="mt-2 h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-400 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Success/Error Messages */}
          {uploadSuccess && (
            <div className="mt-4 flex items-center gap-2 text-green-400">
              <Check className="h-5 w-5" />
              <span>{uploadSuccess}</span>
            </div>
          )}
          {uploadError && (
            <div className="mt-4 flex items-center gap-2 text-red-400">
              <X className="h-5 w-5" />
              <span>{uploadError}</span>
            </div>
          )}
        </div>

        {/* Query Section */}
        <div className="bg-white/5 rounded-xl p-6 space-y-4">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <Search className="h-5 w-5 text-purple-400" />
            Query Your Documents
          </h3>
          <div className="flex gap-3">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about your documents..."
              className="bg-white/5 border-white/10 text-white flex-1"
              onKeyDown={(e) => e.key === "Enter" && handleQuery()}
            />
            <Button
              onClick={handleQuery}
              disabled={isQuerying || !query.trim()}
              className="bg-gradient-to-r from-purple-500 to-pink-500"
            >
              {isQuerying ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
            </Button>
          </div>

          {queryResult && (
            <div className="mt-4 p-4 bg-white/5 rounded-lg">
              <p className="text-white/80 whitespace-pre-wrap">{queryResult}</p>
            </div>
          )}
        </div>

        {/* Documents List */}
        <div className="bg-white/5 rounded-xl p-6 space-y-4">
          <h3 className="text-lg font-medium flex items-center gap-2">
            <FileText className="h-5 w-5 text-orange-400" />
            Uploaded Documents
            {documents.length > 0 && (
              <span className="text-sm text-white/40 font-normal">
                ({documents.length})
              </span>
            )}
          </h3>

          {documents.length === 0 ? (
            <div className="text-center py-8 text-white/40">
              <File className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No documents uploaded yet</p>
              <p className="text-sm mt-1">Upload PDFs to build your knowledge base</p>
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-4 bg-white/5 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-8 w-8 text-red-400" />
                    <div>
                      <p className="font-medium">{doc.filename}</p>
                      <p className="text-sm text-white/40">
                        {doc.chunks} chunks
                        {doc.size && ` | ${formatFileSize(doc.size)}`}
                      </p>
                    </div>
                  </div>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-white/40 hover:text-red-400"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent className="bg-[#1a1a1a] border-white/10">
                      <AlertDialogHeader>
                        <AlertDialogTitle className="text-white">Delete Document</AlertDialogTitle>
                        <AlertDialogDescription className="text-white/60">
                          Are you sure you want to delete "{doc.filename}"? This action cannot be undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel className="bg-white/10 text-white border-white/10 hover:bg-white/20">
                          Cancel
                        </AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => setDocuments(prev => prev.filter(d => d.id !== doc.id))}
                          className="bg-red-500 hover:bg-red-600"
                        >
                          Delete
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
