"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type WhatsAppUser = {
  phone: string;
  last_seen?: string | null;
  message_count?: number;
};

type WhatsAppMessage = {
  direction: "incoming" | "outgoing";
  text?: string | null;
  created_at?: string | null;
};

type UsersResponse = {
  count: number;
  users: WhatsAppUser[];
};

type ChatResponse = {
  phone: string;
  count: number;
  messages: WhatsAppMessage[];
};

type CountsResponse = {
  whatsapp_users_total: number;
  whatsapp_users_active_24h: number;
};

const PAGE_SIZE = 15;

function formatTimestamp(value?: string | null) {
  if (!value) return "";
  return value.replace("T", " ").replace("Z", "");
}

export default function WhatsappAdminPanel() {
  const apiBase = useMemo(
    () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:9002",
    []
  );
  const [users, setUsers] = useState<WhatsAppUser[]>([]);
  const [counts, setCounts] = useState<CountsResponse | null>(null);
  const [selectedPhone, setSelectedPhone] = useState<string | null>(null);
  const [messages, setMessages] = useState<WhatsAppMessage[]>([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chatRef = useRef<HTMLDivElement | null>(null);

  const loadUsers = useCallback(async () => {
    setLoadingUsers(true);
    setError(null);
    try {
      const [usersRes, countsRes] = await Promise.all([
        fetch(`${apiBase}/admin/whatsapp-users-list`),
        fetch(`${apiBase}/admin/whatsapp-users`),
      ]);
      if (!usersRes.ok) {
        throw new Error("Failed to load users.");
      }
      if (!countsRes.ok) {
        throw new Error("Failed to load stats.");
      }
      const usersJson = (await usersRes.json()) as UsersResponse;
      const countsJson = (await countsRes.json()) as CountsResponse;
      setUsers(usersJson.users || []);
      setCounts(countsJson);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data.");
    } finally {
      setLoadingUsers(false);
    }
  }, [apiBase]);

  const loadChat = useCallback(
    async (phone: string, reset = true) => {
      setLoadingChat(true);
      setError(null);
      try {
        const currentOffset = reset ? 0 : offset;
        const res = await fetch(
          `${apiBase}/admin/whatsapp-chats?phone=${encodeURIComponent(
            phone
          )}&limit=${PAGE_SIZE}&offset=${currentOffset}`
        );
        if (!res.ok) {
          throw new Error("Failed to load chat.");
        }
        const data = (await res.json()) as ChatResponse;
        const nextMessages = data.messages || [];
        setHasMore(nextMessages.length === PAGE_SIZE);
        setOffset(currentOffset + nextMessages.length);
        setMessages((prev) =>
          reset ? nextMessages : [...nextMessages, ...prev]
        );
        if (reset) {
          setSelectedPhone(phone);
        }
        if (reset && chatRef.current) {
          requestAnimationFrame(() => {
            if (chatRef.current) {
              chatRef.current.scrollTop = chatRef.current.scrollHeight;
            }
          });
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load chat.");
      } finally {
        setLoadingChat(false);
      }
    },
    [apiBase, offset]
  );

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  return (
    <div className="h-[100dvh] overflow-hidden bg-[var(--background)] text-[var(--foreground)]">
      <div className="mx-auto flex h-full max-w-6xl flex-col gap-6 px-6 py-6">
        <div>
          <div className="text-2xl font-semibold tracking-tight">
            WhatsApp Admin Dashboard
          </div>
          <p className="mt-2 text-sm text-[var(--muted-foreground)]">
            Connected users and chat history from your WhatsApp bot.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-4">
            <div className="text-xs uppercase tracking-widest text-[var(--muted-foreground)]">
              Total Connected Users
            </div>
            <div className="mt-2 text-3xl font-semibold">
              {counts?.whatsapp_users_total ?? "—"}
            </div>
          </div>
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-4">
            <div className="text-xs uppercase tracking-widest text-[var(--muted-foreground)]">
              Active in Last 24 Hours
            </div>
            <div className="mt-2 text-3xl font-semibold">
              {counts?.whatsapp_users_active_24h ?? "—"}
            </div>
          </div>
        </div>

        {error ? (
          <div className="rounded-xl border border-red-400/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        ) : null}

        <div className="grid flex-1 min-h-0 gap-6 md:grid-cols-2">
          <div className="flex min-h-0 flex-col rounded-2xl border border-[var(--border)] bg-[var(--card)] p-4">
            <div className="text-xs uppercase tracking-widest text-[var(--muted-foreground)]">
              Users
            </div>
            <div className="mt-3 flex-1 overflow-auto">
              {loadingUsers ? (
                <div className="text-sm text-[var(--muted-foreground)]">
                  Loading users...
                </div>
              ) : users.length === 0 ? (
                <div className="text-sm text-[var(--muted-foreground)]">
                  No users yet.
                </div>
              ) : (
                <div className="space-y-2">
                  {users.map((user) => (
                    <button
                      key={user.phone}
                      type="button"
                      onClick={() => loadChat(user.phone, true)}
                      className={`w-full rounded-xl border px-4 py-3 text-left transition ${
                        selectedPhone === user.phone
                          ? "border-[var(--accent)] bg-[var(--secondary)]"
                          : "border-transparent hover:border-[var(--border)] hover:bg-[var(--secondary)]"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3 text-sm font-medium">
                        <span>{user.phone}</span>
                        <span className="text-xs text-[var(--muted-foreground)]">
                          {formatTimestamp(user.last_seen)}
                        </span>
                      </div>
                      <div className="mt-1 text-xs text-[var(--muted-foreground)]">
                        Messages: {user.message_count ?? 0}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="flex min-h-0 flex-col rounded-2xl border border-[var(--border)] bg-[var(--card)] p-4">
            <div className="text-xs uppercase tracking-widest text-[var(--muted-foreground)]">
              Chat
            </div>
            <div
              ref={chatRef}
              className="mt-3 flex-1 overflow-auto scroll-smooth"
            >
              {!selectedPhone ? (
                <div className="text-sm text-[var(--muted-foreground)]">
                  Select a user to view messages.
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="text-sm font-semibold">
                    {selectedPhone}
                  </div>
                  {hasMore ? (
                    <button
                      type="button"
                      onClick={() => selectedPhone && loadChat(selectedPhone, false)}
                      className="w-full rounded-lg border border-[var(--border)] px-3 py-2 text-xs uppercase tracking-widest text-[var(--muted-foreground)]"
                      disabled={loadingChat}
                    >
                      {loadingChat ? "Loading..." : "Load older messages"}
                    </button>
                  ) : null}
                  {messages.length === 0 ? (
                    <div className="text-sm text-[var(--muted-foreground)]">
                      No messages yet.
                    </div>
                  ) : (
                    messages.map((msg, index) => (
                      <div
                        key={`${msg.created_at}-${index}`}
                        className={`flex ${
                          msg.direction === "incoming"
                            ? "justify-start"
                            : "justify-end"
                        }`}
                      >
                        <div
                          className={`max-w-[72%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                            msg.direction === "incoming"
                              ? "bg-[var(--secondary)] text-[var(--foreground)]"
                              : "bg-emerald-500/15 text-[var(--foreground)]"
                          }`}
                        >
                          <div className="whitespace-pre-wrap">
                            {msg.text || ""}
                          </div>
                          <div className="mt-2 text-[10px] text-[var(--muted-foreground)]">
                            {formatTimestamp(msg.created_at)}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
