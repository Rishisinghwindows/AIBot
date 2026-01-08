"use client";

import React, { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import {
  Loader2,
  Send,
  User,
  Briefcase,
  MessageSquare,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface Persona {
  handle: string;
  display_name: string;
  tagline: string | null;
  avatar_url: string | null;
  expertise_area: string | null;
  topics: string[] | null;
  job_title: string | null;
  industry: string | null;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}

export default function PublicPersonaPage() {
  const params = useParams();
  const handle = params.handle as string;
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "/api"; // Use Next.js proxy to avoid CORS

  const [persona, setPersona] = useState<Persona | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (handle) {
      fetchPersona();
    }
  }, [handle]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchPersona = async () => {
    try {
      const response = await fetch(`${apiBase}/p/${handle}`);
      if (response.ok) {
        const data = await response.json();
        setPersona(data);
      } else if (response.status === 404) {
        setNotFound(true);
      }
    } catch (error) {
      console.error("Failed to fetch persona:", error);
      setNotFound(true);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isSending) return;

    const userMessage = inputMessage.trim();
    setInputMessage("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setIsSending(true);

    try {
      const response = await fetch(`${apiBase}/p/${handle}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        setMessages(prev => [...prev, { role: "assistant", content: data.response }]);
      } else {
        setMessages(prev => [
          ...prev,
          { role: "assistant", content: "Sorry, I'm having trouble responding right now. Please try again." },
        ]);
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: "Connection error. Please try again." },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-white" />
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center text-white">
        <div className="text-center">
          <User className="h-16 w-16 mx-auto text-white/20 mb-4" />
          <h1 className="text-2xl font-semibold mb-2">Persona Not Found</h1>
          <p className="text-white/40 mb-6">@{handle} doesn't exist or is private</p>
          <Button
            onClick={() => window.location.href = "/"}
            className="bg-gradient-to-r from-purple-500 to-pink-500"
          >
            Go Home
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col">
      {/* Header with Profile */}
      <div className="bg-gradient-to-b from-purple-500/20 to-transparent">
        <div className="max-w-3xl mx-auto px-4 py-8">
          <div className="flex items-start gap-4">
            <Avatar className="h-20 w-20">
              <AvatarImage src={persona?.avatar_url || ""} />
              <AvatarFallback className="bg-gradient-to-br from-purple-500 to-pink-500 text-white text-2xl">
                {persona?.display_name?.[0]?.toUpperCase() || "?"}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1">
              <h1 className="text-2xl font-bold">{persona?.display_name}</h1>
              <p className="text-white/40">@{persona?.handle}</p>
              {persona?.tagline && (
                <p className="text-white/60 mt-2">{persona.tagline}</p>
              )}

              <div className="flex flex-wrap gap-4 mt-4 text-sm">
                {persona?.job_title && (
                  <div className="flex items-center gap-1 text-white/50">
                    <Briefcase className="h-4 w-4" />
                    {persona.job_title}
                  </div>
                )}
                {persona?.expertise_area && (
                  <div className="flex items-center gap-1 text-white/50">
                    <Sparkles className="h-4 w-4" />
                    {persona.expertise_area}
                  </div>
                )}
              </div>

              {persona?.topics && persona.topics.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {persona.topics.slice(0, 5).map((topic, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 bg-white/10 rounded-full text-xs text-white/60"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Chat Section */}
      <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <MessageSquare className="h-12 w-12 mx-auto text-white/20 mb-4" />
              <h3 className="text-lg font-medium mb-2">Start a conversation</h3>
              <p className="text-white/40 text-sm">
                Ask {persona?.display_name} anything about their expertise
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.role === "user"
                    ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                    : "bg-white/10 text-white"
                }`}
              >
                {message.role === "assistant" && (
                  <div className="flex items-center gap-2 mb-2">
                    <Avatar className="h-6 w-6">
                      <AvatarImage src={persona?.avatar_url || ""} />
                      <AvatarFallback className="bg-purple-500 text-white text-xs">
                        {persona?.display_name?.[0]}
                      </AvatarFallback>
                    </Avatar>
                    <span className="text-xs text-white/40">{persona?.display_name}</span>
                  </div>
                )}
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}

          {isSending && (
            <div className="flex justify-start">
              <div className="bg-white/10 rounded-2xl px-4 py-3">
                <div className="flex items-center gap-2">
                  <Avatar className="h-6 w-6">
                    <AvatarImage src={persona?.avatar_url || ""} />
                    <AvatarFallback className="bg-purple-500 text-white text-xs">
                      {persona?.display_name?.[0]}
                    </AvatarFallback>
                  </Avatar>
                  <Loader2 className="h-4 w-4 animate-spin text-white/40" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-white/10 p-4">
          <div className="flex gap-3">
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={`Message ${persona?.display_name}...`}
              className="bg-white/5 border-white/10 text-white flex-1"
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              disabled={isSending}
            />
            <Button
              onClick={sendMessage}
              disabled={isSending || !inputMessage.trim()}
              className="bg-gradient-to-r from-purple-500 to-pink-500"
            >
              {isSending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center py-4 text-xs text-white/30">
          <a
            href="/"
            className="hover:text-white/50 inline-flex items-center gap-1"
          >
            Powered by OhGrt <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </div>
  );
}
