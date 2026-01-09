"use client";

import { useState } from "react";
import { Mail, ChevronRight, X, Loader2, Calendar, User } from "lucide-react";
import { cn } from "@/lib/utils";
import authFetch from "@/lib/auth_fetch";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Email {
  id: string;
  subject: string;
  from: string;
  date: string;
  snippet: string;
}

interface EmailDetail {
  id: string;
  threadId: string;
  subject: string;
  from: string;
  to: string;
  cc?: string;
  date: string;
  body: string;
  snippet: string;
  labelIds: string[];
}

interface EmailListCardProps {
  data: {
    type: "email_list";
    emails: Email[];
    count: number;
  };
}

export function EmailListCard({ data }: EmailListCardProps) {
  const [selectedEmail, setSelectedEmail] = useState<EmailDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const handleEmailClick = async (emailId: string) => {
    setIsLoading(true);
    setError(null);
    setIsDialogOpen(true);

    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        throw new Error("Please log in to view email details");
      }

      const response = await authFetch(`/api/chat/email/${emailId}`, {}, token);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to load email");
      }

      const emailDetail = await response.json();
      setSelectedEmail(emailDetail);
    } catch (err) {
      console.error("Error loading email:", err);
      setError(err instanceof Error ? err.message : "Failed to load email");
    } finally {
      setIsLoading(false);
    }
  };

  const closeDialog = () => {
    setIsDialogOpen(false);
    setSelectedEmail(null);
    setError(null);
  };

  // Parse sender name from "Name <email@example.com>" format
  const parseSender = (from: string) => {
    const match = from.match(/^(.+?)\s*<(.+?)>$/);
    if (match) {
      return { name: match[1].trim(), email: match[2] };
    }
    return { name: from, email: from };
  };

  // Format date for display
  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));

      if (days === 0) {
        return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      } else if (days === 1) {
        return "Yesterday";
      } else if (days < 7) {
        return date.toLocaleDateString([], { weekday: "short" });
      } else {
        return date.toLocaleDateString([], { month: "short", day: "numeric" });
      }
    } catch {
      return dateStr;
    }
  };

  return (
    <>
      <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-b border-border">
          <Mail className="w-5 h-5 text-blue-500" />
          <span className="font-semibold text-foreground">
            Emails ({data.count})
          </span>
        </div>

        {/* Email List */}
        <div className="divide-y divide-border">
          {data.emails.map((email) => {
            const sender = parseSender(email.from);
            return (
              <button
                key={email.id}
                onClick={() => handleEmailClick(email.id)}
                className={cn(
                  "w-full text-left px-4 py-3 hover:bg-muted/50 transition-colors",
                  "focus:outline-none focus:bg-muted/70"
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    {/* Sender */}
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm text-foreground truncate">
                        {sender.name}
                      </span>
                      <span className="text-xs text-muted-foreground flex-shrink-0">
                        {formatDate(email.date)}
                      </span>
                    </div>
                    {/* Subject */}
                    <div className="text-sm text-foreground truncate mb-1">
                      {email.subject || "(No subject)"}
                    </div>
                    {/* Snippet */}
                    <div className="text-xs text-muted-foreground line-clamp-1">
                      {email.snippet}
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-1" />
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Email Detail Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Mail className="w-5 h-5" />
              {isLoading ? "Loading..." : selectedEmail?.subject || "Email"}
            </DialogTitle>
          </DialogHeader>

          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {error && (
            <div className="flex flex-col items-center justify-center py-12 gap-4">
              <p className="text-destructive">{error}</p>
              <Button variant="outline" onClick={closeDialog}>
                Close
              </Button>
            </div>
          )}

          {selectedEmail && !isLoading && !error && (
            <div className="flex flex-col gap-4 flex-1 min-h-0">
              {/* Email metadata */}
              <div className="space-y-2 text-sm border-b border-border pb-4">
                <div className="flex items-start gap-2">
                  <User className="w-4 h-4 mt-0.5 text-muted-foreground flex-shrink-0" />
                  <div>
                    <span className="text-muted-foreground">From: </span>
                    <span className="text-foreground">{selectedEmail.from}</span>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <User className="w-4 h-4 mt-0.5 text-muted-foreground flex-shrink-0" />
                  <div>
                    <span className="text-muted-foreground">To: </span>
                    <span className="text-foreground">{selectedEmail.to}</span>
                  </div>
                </div>
                {selectedEmail.cc && (
                  <div className="flex items-start gap-2">
                    <User className="w-4 h-4 mt-0.5 text-muted-foreground flex-shrink-0" />
                    <div>
                      <span className="text-muted-foreground">CC: </span>
                      <span className="text-foreground">{selectedEmail.cc}</span>
                    </div>
                  </div>
                )}
                <div className="flex items-start gap-2">
                  <Calendar className="w-4 h-4 mt-0.5 text-muted-foreground flex-shrink-0" />
                  <div>
                    <span className="text-muted-foreground">Date: </span>
                    <span className="text-foreground">{selectedEmail.date}</span>
                  </div>
                </div>
              </div>

              {/* Email body */}
              <ScrollArea className="flex-1 min-h-0">
                <div
                  className="text-sm text-foreground whitespace-pre-wrap pr-4"
                  dangerouslySetInnerHTML={{
                    __html: selectedEmail.body.includes("<")
                      ? selectedEmail.body
                      : selectedEmail.body.replace(/\n/g, "<br />"),
                  }}
                />
              </ScrollArea>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
