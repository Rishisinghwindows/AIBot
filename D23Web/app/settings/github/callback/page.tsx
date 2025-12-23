"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import authFetch from "@/lib/auth_fetch";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

type Status = "pending" | "success" | "error";

export default function GitHubCallbackPage() {
  const params = useSearchParams();
  const router = useRouter();
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [status, setStatus] = useState<Status>("pending");
  const [message, setMessage] = useState("Completing GitHub connection...");

  useEffect(() => {
    const code = params.get("code");
    if (!code) {
      setStatus("error");
      setMessage("Missing authorization code. Try connecting GitHub again.");
      return;
    }
    const state = params.get("state");

    const completeConnection = async () => {
      try {
        const response = await authFetch(`${apiBase}/github/exchange`, {
          method: "POST",
          body: JSON.stringify({ code, state }),
        });

        if (!response.ok) {
          let detail = "Failed to complete GitHub connection.";
          try {
            const error = await response.json();
            detail = error.detail || detail;
          } catch {
            // Ignore JSON parsing errors
          }
          throw new Error(detail);
        }

        setStatus("success");
        setMessage("GitHub connected! Redirecting...");
        setTimeout(() => router.replace("/settings"), 1200);
      } catch (error) {
        setStatus("error");
        setMessage((error as Error).message || "Failed to connect GitHub. Please try again.");
      }
    };

    completeConnection();
  }, [apiBase, params, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-black px-4">
      <div className="max-w-md w-full bg-zinc-900 border border-zinc-800 rounded-xl p-8">
        <div className="flex flex-col items-center gap-4">
          {status === "pending" && <Loader2 className="h-12 w-12 animate-spin text-violet-500" />}
          {status === "success" && <CheckCircle2 className="h-12 w-12 text-green-500" />}
          {status === "error" && <XCircle className="h-12 w-12 text-red-500" />}

          <h2 className="text-xl font-semibold text-white">GitHub Authorization</h2>
          <p className="text-sm text-zinc-400 text-center">{message}</p>

          {status === "error" && (
            <button
              onClick={() => router.push("/settings")}
              className="mt-4 px-6 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors"
            >
              Back to Settings
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
