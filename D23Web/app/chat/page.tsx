"use client";

import { useAuth } from "@/context/AuthContext";
import React, { useEffect, useState, useRef, FormEvent, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  LogIn,
  Mic,
  MicOff,
  Paperclip,
  Plus,
  Cloud,
  Train,
  Star,
  Newspaper,
  Hash,
  Languages,
  ImageIcon,
  Calendar,
  Send,
  X,
  StopCircle,
} from "lucide-react";
import { ChatMessage, Conversation } from "@/lib/types";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { ChatArea } from "@/components/chat/ChatArea";
import { LocationPrompt } from "@/components/chat/LocationPrompt";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

type UserLocation = {
  latitude: number;
  longitude: number;
  accuracy?: number;
};

const parseStructuredData = (value: unknown): Record<string, unknown> | undefined => {
  if (!value) return undefined;
  if (typeof value === "string") {
    try {
      return JSON.parse(value);
    } catch {
      return undefined;
    }
  }
  if (typeof value === "object") {
    return value as Record<string, unknown>;
  }
  return undefined;
};

const normalizeMessage = (msg: any): ChatMessage => {
  const metadata = msg.message_metadata || msg.metadata || {};
  const structuredData =
    parseStructuredData(
      msg.structured_data ??
      metadata.structured_data ??
      metadata.structuredData ??
      metadata.structured_data_json ??
      metadata.structuredDataJson
    );

  return {
    id: msg.id ?? crypto.randomUUID(),
    conversation_id: msg.conversation_id ?? msg.conversationId ?? null,
    role: msg.role ?? "assistant",
    content: msg.content ?? msg.message ?? "",
    created_at: msg.created_at ?? msg.timestamp ?? new Date().toISOString(),
    media_url: msg.media_url ?? metadata.media_url ?? metadata.mediaUrl,
    intent: msg.intent ?? metadata.intent,
    structured_data: structuredData,
  };
};

export default function ChatPage() {
  const { currentUser, currentProfile, loading, accessToken, login, logout } = useAuth();
  const router = useRouter();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const chatAreaRef = useRef<HTMLDivElement>(null);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState<string>("");
  const [currentAIMessage, setCurrentAIMessage] = useState<string>("");
  const [isSending, setIsSending] = useState<boolean>(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState<boolean>(false);
  const [isFetchingMessages, setIsFetchingMessages] = useState<boolean>(false);
  const [editingConversationId, setEditingConversationId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [isScrolledToBottom, setIsScrolledToBottom] = useState<boolean>(true);
  const [hasSelectedInitialConversation, setHasSelectedInitialConversation] = useState<boolean>(false);
  const [showLocationPrompt, setShowLocationPrompt] = useState<boolean>(false);
  const [userLocation, setUserLocation] = useState<UserLocation | null>(null);
  const [pendingLocationMessage, setPendingLocationMessage] = useState<string | null>(null);

  // Track past anonymous sessions for history preservation
  const [pastAnonymousSessions, setPastAnonymousSessions] = useState<Array<{
    sessionId: string;
    title: string;
    messageCount: number;
    lastMessageAt: string;
    createdAt: string;
  }>>([]);

  // Voice input state
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isTranscribing, setIsTranscribing] = useState<boolean>(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Tool menu state
  const [showToolMenu, setShowToolMenu] = useState<boolean>(false);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Quick tools configuration
  const quickTools = [
    { icon: Cloud, label: "Weather", prompt: "What's the weather in ", color: "text-cyan-400" },
    { icon: Train, label: "PNR Status", prompt: "Check PNR ", color: "text-green-400" },
    { icon: Star, label: "Horoscope", prompt: "My horoscope for ", color: "text-purple-400" },
    { icon: Newspaper, label: "News", prompt: "Show me today's news about ", color: "text-orange-400" },
    { icon: Hash, label: "Numerology", prompt: "Numerology for ", color: "text-pink-400" },
    { icon: Languages, label: "Translate", prompt: "Translate to Hindi: ", color: "text-blue-400" },
    { icon: ImageIcon, label: "Generate Image", prompt: "Create an image of ", color: "text-rose-400" },
    { icon: Calendar, label: "Panchang", prompt: "What's today's panchang?", color: "text-amber-400" },
  ];

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    // Use scrollIntoView on the end ref - most reliable method
    const timeoutId = setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
    return () => clearTimeout(timeoutId);
  }, [messages, currentAIMessage]);

  // Track scroll position for showing/hiding scroll button
  useEffect(() => {
    const container = chatAreaRef.current;
    if (!container) return;

    const handleScroll = () => {
      const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight <= 100;
      setIsScrolledToBottom(atBottom);
    };

    container.addEventListener("scroll", handleScroll);
    handleScroll();
    return () => container.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    setIsScrolledToBottom(true);
  };

  // Auto-resize textarea
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
  };

  // Fetch conversations
  const fetchConversations = useCallback(async () => {
    if (!accessToken) return;
    setIsLoadingConversations(true);
    try {
      const response = await fetch(`${apiBase}/chat/conversations`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) throw new Error("Failed to fetch conversations");
      const data: Conversation[] = await response.json();
      setConversations(data);

      const currentExists = currentConversationId && data.some((c) => c.id === currentConversationId);
      if (!hasSelectedInitialConversation && data.length > 0 && !currentConversationId) {
        setCurrentConversationId(data[0].id);
        setHasSelectedInitialConversation(true);
      } else if (currentConversationId && !currentExists) {
        setCurrentConversationId(data.length > 0 ? data[0].id : null);
        setMessages([]);
        setCurrentAIMessage("");
      } else if (data.length === 0 && currentConversationId) {
        setCurrentConversationId(null);
        setMessages([]);
        setCurrentAIMessage("");
      }
    } catch (error) {
      console.error("Error fetching conversations:", error);
    } finally {
      setIsLoadingConversations(false);
    }
  }, [accessToken, currentConversationId, hasSelectedInitialConversation, apiBase]);

  useEffect(() => {
    if (currentUser && accessToken) {
      fetchConversations();
    }
  }, [currentUser, accessToken, fetchConversations]);

  // Fetch messages for current conversation
  useEffect(() => {
    const fetchMessages = async () => {
      if (!accessToken || !currentConversationId) return;
      setIsFetchingMessages(true);
      try {
      const response = await fetch(`${apiBase}/chat/history?conversation_id=${currentConversationId}`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (!response.ok) throw new Error("Failed to fetch messages");
        const data = await response.json();
        const formatted = (data.messages || []).map((msg: unknown) => normalizeMessage(msg));
        setMessages(formatted);
      } catch (error) {
        console.error("Error fetching messages:", error);
      } finally {
        setIsFetchingMessages(false);
      }
    };

    if (currentConversationId && accessToken) {
      fetchMessages();
    }
  }, [currentConversationId, accessToken, apiBase]);

  // Web session ID for anonymous chat
  const [webSessionId, setWebSessionId] = useState<string | null>(null);

  // Get or create web session for anonymous chat
  const getWebSession = async (): Promise<string> => {
    if (webSessionId) return webSessionId;

    // Check localStorage for existing session
    const storedSessionId = localStorage.getItem("ohgrt_session_id");
    if (storedSessionId) {
      // Verify session is still valid
      try {
        const verifyResponse = await fetch(`${apiBase}/web/session/${storedSessionId}`);
        if (verifyResponse.ok) {
          setWebSessionId(storedSessionId);
          return storedSessionId;
        }
      } catch {
        // Session invalid, create new one
      }
    }

    const response = await fetch(`${apiBase}/web/session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) throw new Error("Failed to create web session");
    const data = await response.json();
    setWebSessionId(data.session_id);
    localStorage.setItem("ohgrt_session_id", data.session_id);
    return data.session_id;
  };

  // Track if we've already loaded anonymous history
  const hasLoadedAnonymousHistory = useRef(false);

  // Load anonymous chat history on mount - only once after auth settles
  useEffect(() => {
    const loadAnonymousHistory = async () => {
      // Only run once
      if (hasLoadedAnonymousHistory.current) {
        console.log("[History] Already loaded, skipping");
        return;
      }

      // Wait for auth to finish loading
      if (loading) {
        console.log("[History] Auth still loading, waiting...");
        return;
      }

      // If user is authenticated, don't load anonymous history
      if (currentUser || accessToken) {
        console.log("[History] User is authenticated, skipping anonymous history");
        hasLoadedAnonymousHistory.current = true;
        return;
      }

      const storedSessionId = localStorage.getItem("ohgrt_session_id");
      if (!storedSessionId) {
        console.log("[History] No stored session ID found");
        hasLoadedAnonymousHistory.current = true;
        return;
      }

      console.log("[History] Loading history for session:", storedSessionId);
      hasLoadedAnonymousHistory.current = true;

      try {
        setIsFetchingMessages(true);
        const response = await fetch(`${apiBase}/web/chat/history/${storedSessionId}`);
        console.log("[History] Response status:", response.status);

        if (response.ok) {
          const data = await response.json();
          console.log("[History] Loaded messages:", data.messages?.length || 0);
          setWebSessionId(storedSessionId);
          if (data.messages && data.messages.length > 0) {
            const formattedMessages = data.messages.map((msg: unknown) => normalizeMessage({ ...msg, conversation_id: "anonymous" }));
            setMessages(formattedMessages);
          }
        } else {
          console.log("[History] Session expired or invalid, clearing");
          localStorage.removeItem("ohgrt_session_id");
        }
      } catch (error) {
        console.error("[History] Error loading anonymous history:", error);
      } finally {
        setIsFetchingMessages(false);
      }
    };

    loadAnonymousHistory();
  }, [currentUser, accessToken, apiBase, loading]);

  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isSending) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      conversation_id: currentConversationId || "new",
      role: "user",
      content: inputMessage,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setCurrentAIMessage("");
    setIsSending(true);

    if (inputRef.current) {
      inputRef.current.style.height = "auto";
    }

    try {
      // If user is authenticated, use the authenticated flow
      if (accessToken) {
        let actualConversationId = currentConversationId;

        // Create new conversation if needed
        if (!actualConversationId) {
          const newConvResponse = await fetch(`${apiBase}/chat/conversations`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${accessToken}`,
            },
            body: JSON.stringify({
              title: userMessage.content.substring(0, 50) + (userMessage.content.length > 50 ? "..." : ""),
            }),
          });
          if (!newConvResponse.ok) throw new Error("Failed to create new conversation");
          const newConversation: Conversation = await newConvResponse.json();
          actualConversationId = newConversation.id;
          setCurrentConversationId(actualConversationId);
          setConversations((prev) => [newConversation, ...prev]);
        }

        // Send message via streaming endpoint
        const response = await fetch(`${apiBase}/chat/ask`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            message: userMessage.content,
            conversation_id: actualConversationId,
          }),
        });

        if (!response.ok || !response.body) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let aiFullResponse = "";
        let partialLine = "";
        let mediaUrl: string | undefined;
        let intent: string | undefined;
        let structuredData: Record<string, unknown> | undefined;

        const hydrateFromMetadata = (source: unknown) => {
          if (!source) return;
          let metadata: Record<string, unknown> | undefined;
          if (typeof source === "string") {
            try {
              metadata = JSON.parse(source);
            } catch {
              return;
            }
          } else if (typeof source === "object") {
            metadata = source as Record<string, unknown>;
          }
          if (!metadata) return;

          if (!mediaUrl && typeof metadata.media_url === "string") {
            mediaUrl = metadata.media_url;
          } else if (!mediaUrl && typeof metadata.mediaUrl === "string") {
            mediaUrl = metadata.mediaUrl;
          }
          if (!intent && typeof metadata.intent === "string") {
            intent = metadata.intent;
          }
          if (!structuredData) {
            structuredData = parseStructuredData(
              metadata.structured_data ??
              metadata.structuredData ??
              metadata.structured_data_json ??
              metadata.structuredDataJson
            );
          }
        };

        while (true) {
          const { done, value } = await reader.read();
          partialLine += decoder.decode(value || new Uint8Array(), { stream: !done });

          const lines = partialLine.split("\n");
          partialLine = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("event:")) {
              continue;
            }
            if (line.startsWith("data:")) {
              const data = line.replace(/^data:\s*/, "").trim();
              if (!data) continue;

              try {
                const parsed = JSON.parse(data);

                if (parsed.content) {
                  setCurrentAIMessage((prev) => prev + parsed.content);
                  aiFullResponse += parsed.content;
                }
                if (parsed.media_url) {
                  mediaUrl = parsed.media_url;
                }
                if (parsed.intent) {
                  intent = parsed.intent;
                }
                if (parsed.structured_data) {
                  structuredData = parseStructuredData(parsed.structured_data);
                }
                if (parsed.message_metadata) hydrateFromMetadata(parsed.message_metadata);
                if (parsed.metadata) hydrateFromMetadata(parsed.metadata);
              } catch {
                // Not valid JSON, skip
              }
            }
          }

          if (done) break;
        }

        const aiMessage = normalizeMessage({
          id: crypto.randomUUID(),
          conversation_id: actualConversationId,
          role: "assistant",
          content: aiFullResponse,
          created_at: new Date().toISOString(),
          media_url: mediaUrl,
          intent: intent,
          structured_data: structuredData,
        });
        setMessages((prev) => [...prev, aiMessage]);
        setCurrentAIMessage("");
      } else {
        // Anonymous chat flow using /chat/ask with session_id
        const sessionId = await getWebSession();

        const response = await fetch(`${apiBase}/chat/ask`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: userMessage.content,
            session_id: sessionId,
          }),
        });

        if (!response.ok || !response.body) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Use same SSE streaming as authenticated flow
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let aiFullResponse = "";
        let partialLine = "";
        let mediaUrl: string | undefined;
        let intent: string | undefined;
        let structuredData: Record<string, unknown> | undefined;

        while (true) {
          const { done, value } = await reader.read();
          partialLine += decoder.decode(value || new Uint8Array(), { stream: !done });

          const lines = partialLine.split("\n");
          partialLine = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("event:")) {
              continue;
            }
            if (line.startsWith("data:")) {
              const data = line.replace(/^data:\s*/, "").trim();
              if (!data) continue;

              try {
                const parsed = JSON.parse(data);

                if (parsed.content) {
                  setCurrentAIMessage((prev) => prev + parsed.content);
                  aiFullResponse += parsed.content;
                }
                if (parsed.media_url) {
                  mediaUrl = parsed.media_url;
                }
                if (parsed.intent) {
                  intent = parsed.intent;
                }
                if (parsed.structured_data) {
                  structuredData = parseStructuredData(parsed.structured_data);
                }
              } catch {
                // Not valid JSON, skip
              }
            }
          }

          if (done) break;
        }

        const aiMessage = normalizeMessage({
          id: crypto.randomUUID(),
          conversation_id: "anonymous",
          role: "assistant",
          content: aiFullResponse,
          created_at: new Date().toISOString(),
          media_url: mediaUrl,
          intent: intent,
          structured_data: structuredData,
        });
        setMessages((prev) => [...prev, aiMessage]);
        setCurrentAIMessage("");
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setCurrentAIMessage("");
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          conversation_id: currentConversationId || "anonymous",
          role: "assistant",
          content: `Error: ${error instanceof Error ? error.message : String(error)}`,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleRenameConversation = async (conversationId: string) => {
    if (!accessToken || !editingTitle.trim()) {
      setEditingConversationId(null);
      setEditingTitle("");
      return;
    }
    try {
      const response = await fetch(`${apiBase}/chat/conversations/${conversationId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ title: editingTitle.trim() }),
      });
      if (!response.ok) throw new Error("Failed to rename conversation");
      const updatedConv: Conversation = await response.json();
      setConversations((prev) => prev.map((conv) => (conv.id === updatedConv.id ? updatedConv : conv)));
      setEditingConversationId(null);
      setEditingTitle("");
    } catch (error) {
      console.error("Error renaming conversation:", error);
    }
  };

  const handleDeleteConversation = async (conversationId: string) => {
    if (!accessToken) return;
    try {
      const response = await fetch(`${apiBase}/chat/conversations/${conversationId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) throw new Error("Failed to delete conversation");

      setConversations((prev) => prev.filter((conv) => conv.id !== conversationId));
      if (currentConversationId === conversationId) {
        setCurrentConversationId(null);
        setMessages([]);
        setCurrentAIMessage("");
      }
      fetchConversations();
    } catch (error) {
      console.error("Error deleting conversation:", error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter to send (without shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e as unknown as FormEvent);
    }
    // Escape to clear input
    if (e.key === "Escape") {
      e.preventDefault();
      setInputMessage("");
      if (inputRef.current) {
        inputRef.current.style.height = "auto";
      }
    }
  };

  const startNewChat = () => {
    setHasSelectedInitialConversation(true);

    // For anonymous users, save current session to history before clearing
    if (!currentUser && webSessionId && messages.length > 0) {
      const currentSession = {
        sessionId: webSessionId,
        title: messages[0]?.content?.substring(0, 40) + (messages[0]?.content?.length > 40 ? "..." : "") || "Previous Chat",
        messageCount: messages.length,
        lastMessageAt: messages[messages.length - 1]?.created_at || new Date().toISOString(),
        createdAt: messages[0]?.created_at || new Date().toISOString(),
      };
      // Add to past sessions if not already there
      setPastAnonymousSessions(prev => {
        const exists = prev.some(s => s.sessionId === webSessionId);
        if (exists) return prev;
        return [currentSession, ...prev].slice(0, 10); // Keep max 10 past sessions
      });
    }

    setCurrentConversationId(null);
    setMessages([]);
    setCurrentAIMessage("");

    // Clear anonymous session for fresh start
    if (!currentUser) {
      localStorage.removeItem("ohgrt_session_id");
      setWebSessionId(null);
    }
    inputRef.current?.focus();
  };

  // Handle location share
  const handleLocationShare = async (location: UserLocation) => {
    setUserLocation(location);
    setShowLocationPrompt(false);

    // If there's a pending message that needed location, resend it
    if (pendingLocationMessage) {
      const messageToResend = pendingLocationMessage;
      setPendingLocationMessage(null);

      // Create a synthetic event and resend
      setInputMessage(messageToResend);
      setTimeout(() => {
        const form = document.querySelector("form");
        if (form) {
          form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
        }
      }, 100);
    }
  };

  const handleLocationDismiss = () => {
    setShowLocationPrompt(false);
    setPendingLocationMessage(null);
  };

  // Voice recording handlers
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach(track => track.stop());
        await transcribeAudio(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error starting recording:", error);
      alert("Could not access microphone. Please check permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    setIsTranscribing(true);
    try {
      // Create form data with audio
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.webm");

      // Send to transcription endpoint
      const response = await fetch(`${apiBase}/web/transcribe`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        if (data.text) {
          setInputMessage(prev => prev + data.text);
          inputRef.current?.focus();
        }
      } else {
        // Fallback: Use Web Speech API if available
        console.log("Server transcription failed, audio recorded but transcription unavailable");
      }
    } catch (error) {
      console.error("Transcription error:", error);
    } finally {
      setIsTranscribing(false);
    }
  };

  // Handle tool selection
  const handleToolSelect = (prompt: string) => {
    setInputMessage(prompt);
    setShowToolMenu(false);
    inputRef.current?.focus();
  };

  // Handle regenerate response - resend the last user message
  const handleRegenerate = useCallback(async () => {
    // Find the last user message
    const lastUserMessage = [...messages].reverse().find(m => m.role === "user");
    if (!lastUserMessage) return;

    // Remove the last assistant message
    setMessages(prev => {
      const newMessages = [...prev];
      // Find and remove the last assistant message
      for (let i = newMessages.length - 1; i >= 0; i--) {
        if (newMessages[i].role === "assistant") {
          newMessages.splice(i, 1);
          break;
        }
      }
      return newMessages;
    });

    // Re-send the message
    setInputMessage(lastUserMessage.content);
    setTimeout(() => {
      const form = document.querySelector("form");
      if (form) {
        form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
      }
    }, 100);
  }, [messages]);

  // Handle message feedback
  const handleFeedback = useCallback((messageId: string, feedback: "up" | "down") => {
    console.log(`Feedback for message ${messageId}: ${feedback}`);
    // TODO: Send feedback to backend when endpoint is available
    // For now, just log it - can be extended to persist feedback
  }, []);

  // Handle conversation selection (for both authenticated and anonymous users)
  const handleSelectConversation = async (conversationId: string | null) => {
    if (!conversationId) {
      setCurrentConversationId(null);
      return;
    }

    // For authenticated users, just set the conversation ID (existing behavior)
    if (currentUser) {
      setCurrentConversationId(conversationId);
      return;
    }

    // For anonymous users, check if this is a past session and load its history
    if (conversationId === webSessionId) {
      // Already on this session, nothing to do
      return;
    }

    // This is a past session, load its history
    setIsFetchingMessages(true);
    try {
      const response = await fetch(`${apiBase}/web/chat/history/${conversationId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.messages && data.messages.length > 0) {
          const formattedMessages = data.messages.map((msg: unknown) => normalizeMessage({ ...msg, conversation_id: conversationId }));
          setMessages(formattedMessages);
          setWebSessionId(conversationId);
          localStorage.setItem("ohgrt_session_id", conversationId);
        }
      }
    } catch (error) {
      console.error("[History] Error loading past session:", error);
    } finally {
      setIsFetchingMessages(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-black">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500 p-[2px] animate-spin">
            <div className="w-full h-full rounded-full bg-black flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-violet-400" />
            </div>
          </div>
          <p className="text-zinc-400">Loading...</p>
        </div>
      </div>
    );
  }

  const userInitials = currentUser
    ? (currentProfile?.display_name?.substring(0, 2).toUpperCase() ||
       currentUser.email?.substring(0, 2).toUpperCase() || "U")
    : "G"; // Guest

  // For anonymous users, create conversation entries for current and past sessions
  const displayConversations: Conversation[] = currentUser
    ? conversations
    : (() => {
        const convs: Conversation[] = [];

        // Add current session if it has messages
        if (messages.length > 0 && webSessionId) {
          convs.push({
            id: webSessionId,
            title: messages[0]?.content?.substring(0, 40) + (messages[0]?.content?.length > 40 ? "..." : "") || "Current Session",
            message_count: messages.length,
            last_message_at: messages[messages.length - 1]?.created_at || new Date().toISOString(),
            created_at: messages[0]?.created_at || new Date().toISOString(),
          });
        }

        // Add past sessions
        pastAnonymousSessions.forEach(session => {
          // Don't add if it's the current session
          if (session.sessionId !== webSessionId) {
            convs.push({
              id: session.sessionId,
              title: session.title,
              message_count: session.messageCount,
              last_message_at: session.lastMessageAt,
              created_at: session.createdAt,
            });
          }
        });

        return convs;
      })();

  return (
    <div className="flex h-screen bg-black text-white overflow-hidden">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-violet-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-fuchsia-600/10 rounded-full blur-[120px]" />
      </div>

      <ChatSidebar
        sidebarOpen={sidebarOpen}
        conversations={displayConversations}
        currentConversationId={currentUser ? currentConversationId : webSessionId}
        isLoadingConversations={isLoadingConversations}
        editingConversationId={editingConversationId}
        editingTitle={editingTitle}
        isLoggedIn={!!currentUser}
        onStartNewChat={startNewChat}
        onSelectConversation={handleSelectConversation}
        onBeginEdit={(id, title) => {
          setEditingConversationId(id);
          setEditingTitle(title);
        }}
        onTitleChange={setEditingTitle}
        onRename={handleRenameConversation}
        onCancelEdit={() => {
          setEditingConversationId(null);
          setEditingTitle("");
        }}
        onDelete={handleDeleteConversation}
        onLoginClick={login}
      />

      <main className="relative z-10 flex-1 flex flex-col min-w-0">
        <ChatHeader
          sidebarOpen={sidebarOpen}
          userInitials={userInitials}
          userEmail={currentUser?.email}
          userPhotoUrl={currentProfile?.photo_url}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onLogout={logout}
          isLoggedIn={!!currentUser}
          onLogin={login}
        />

        <ChatArea
          messages={messages}
          currentAIMessage={currentAIMessage}
          isFetchingMessages={isFetchingMessages}
          isSending={isSending}
          inputRef={inputRef}
          chatAreaRef={chatAreaRef}
          messagesEndRef={messagesEndRef}
          isScrolledToBottom={isScrolledToBottom}
          onSuggestionSelect={setInputMessage}
          onScrollToBottom={scrollToBottom}
          onRegenerate={handleRegenerate}
          onFeedback={handleFeedback}
        />

        {/* Input Area */}
        <div className="flex-shrink-0 border-t border-zinc-800 p-4 bg-black/50 backdrop-blur-xl">
          <div className="max-w-6xl w-full mx-auto space-y-3 px-1 sm:px-2">
            {/* Location Prompt */}
            {showLocationPrompt && (
              <LocationPrompt
                onLocationShare={handleLocationShare}
                onDismiss={handleLocationDismiss}
              />
            )}

            {/* Recording Indicator */}
            {isRecording && (
              <div className="flex items-center justify-center gap-3 py-2 px-4 bg-red-500/10 border border-red-500/30 rounded-xl animate-pulse">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                <span className="text-sm text-red-400">Recording... Click mic to stop</span>
              </div>
            )}

            {/* Transcribing Indicator */}
            {isTranscribing && (
              <div className="flex items-center justify-center gap-3 py-2 px-4 bg-violet-500/10 border border-violet-500/30 rounded-xl">
                <div className="w-4 h-4 border-2 border-violet-400/30 border-t-violet-400 rounded-full animate-spin" />
                <span className="text-sm text-violet-400">Transcribing audio...</span>
              </div>
            )}

            <form onSubmit={handleSendMessage}>
              <div className="relative flex items-end gap-2">
                {/* Tool Selection Button */}
                <TooltipProvider delayDuration={300}>
                  <Popover open={showToolMenu} onOpenChange={setShowToolMenu}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <PopoverTrigger asChild>
                          <Button
                            type="button"
                            size="icon"
                            variant="ghost"
                            className="h-10 w-10 rounded-full flex-shrink-0 text-zinc-400 hover:text-white hover:bg-zinc-800"
                          >
                            <Plus className="w-5 h-5" />
                          </Button>
                        </PopoverTrigger>
                      </TooltipTrigger>
                      <TooltipContent side="top">
                        <p>Quick tools</p>
                      </TooltipContent>
                    </Tooltip>
                    <PopoverContent
                      side="top"
                      align="start"
                      className="w-72 p-2 bg-zinc-900 border-zinc-800"
                    >
                      <div className="grid grid-cols-2 gap-1">
                        {quickTools.map((tool, idx) => {
                          const Icon = tool.icon;
                          return (
                            <button
                              key={idx}
                              type="button"
                              onClick={() => handleToolSelect(tool.prompt)}
                              className="flex items-center gap-2 p-2 rounded-lg hover:bg-zinc-800 transition-colors text-left"
                            >
                              <Icon className={`w-4 h-4 ${tool.color}`} />
                              <span className="text-sm text-zinc-300">{tool.label}</span>
                            </button>
                          );
                        })}
                      </div>
                    </PopoverContent>
                  </Popover>
                </TooltipProvider>

                {/* Text Input */}
                <div className="flex-1 relative">
                  <textarea
                    ref={inputRef}
                    value={inputMessage}
                    onChange={handleTextareaChange}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask me anything..."
                    rows={1}
                    disabled={isSending || isRecording || isTranscribing}
                    className="w-full min-h-[48px] max-h-[150px] resize-none bg-zinc-900 border border-zinc-800 rounded-2xl pl-4 pr-12 py-3 text-white placeholder:text-zinc-500 focus:outline-none focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20 transition-all duration-200"
                  />

                  {/* Clear Button (when there's text) */}
                  {inputMessage.trim() && (
                    <button
                      type="button"
                      onClick={() => setInputMessage("")}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-zinc-500 hover:text-zinc-300 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>

                {/* Voice Input Button */}
                <TooltipProvider delayDuration={300}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        type="button"
                        size="icon"
                        variant="ghost"
                        onClick={isRecording ? stopRecording : startRecording}
                        disabled={isSending || isTranscribing}
                        className={`h-10 w-10 rounded-full flex-shrink-0 transition-all ${
                          isRecording
                            ? "bg-red-500/20 text-red-400 hover:bg-red-500/30"
                            : "text-zinc-400 hover:text-white hover:bg-zinc-800"
                        }`}
                      >
                        {isRecording ? (
                          <StopCircle className="w-5 h-5" />
                        ) : (
                          <Mic className="w-5 h-5" />
                        )}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="top">
                      <p>{isRecording ? "Stop recording" : "Voice input"}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                {/* Send Button */}
                <Button
                  type="submit"
                  size="icon"
                  disabled={isSending || !inputMessage.trim() || isRecording || isTranscribing}
                  className={`h-12 w-12 rounded-full flex-shrink-0 transition-all ${
                    inputMessage.trim() && !isSending
                      ? "bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40"
                      : "bg-zinc-800 text-zinc-500"
                  }`}
                >
                  {isSending ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </Button>
              </div>

              <div className="flex items-center justify-center gap-3 text-[10px] text-zinc-600 mt-2">
                <span>D23 AI can make mistakes. Verify important information.</span>
                <span className="text-zinc-700">|</span>
                <span className="hidden sm:inline">
                  <kbd className="px-1 py-0.5 bg-zinc-800/50 rounded text-zinc-500">Enter</kbd> send
                  <span className="mx-1">·</span>
                  <kbd className="px-1 py-0.5 bg-zinc-800/50 rounded text-zinc-500">Shift+Enter</kbd> new line
                  <span className="mx-1">·</span>
                  <kbd className="px-1 py-0.5 bg-zinc-800/50 rounded text-zinc-500">Esc</kbd> clear
                </span>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
