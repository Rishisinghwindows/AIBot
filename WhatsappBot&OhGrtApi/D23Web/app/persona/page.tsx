"use client";

import { useAuth } from "@/context/AuthContext";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Loader2,
  ArrowLeft,
  Plus,
  Users,
  MessageSquare,
  ExternalLink,
  Trash2,
  Edit2,
  Copy,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
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

interface Persona {
  id: string;
  handle: string;
  display_name: string;
  tagline: string | null;
  avatar_url: string | null;
  is_public: boolean;
  total_chats: number;
  created_at: string;
  updated_at: string;
}

export default function PersonasPage() {
  const { currentUser, loading, idToken, accessToken } = useAuth();
  const router = useRouter();
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "/api"; // Use Next.js proxy to avoid CORS
  const webBase = typeof window !== "undefined" ? window.location.origin : "";

  const [personas, setPersonas] = useState<Persona[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [copiedHandle, setCopiedHandle] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !currentUser) {
      router.push("/");
    }
  }, [currentUser, loading, router]);

  useEffect(() => {
    if (idToken || accessToken) {
      fetchPersonas();
    }
  }, [idToken, accessToken]);

  const fetchPersonas = async () => {
    const token = accessToken || idToken;
    if (!token) return;

    try {
      const response = await authFetch(`${apiBase}/personas`, {}, token);
      if (response.ok) {
        const data = await response.json();
        setPersonas(data);
      }
    } catch (error) {
      console.error("Failed to fetch personas:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (personaId: string) => {
    const token = accessToken || idToken;
    if (!token) return;

    try {
      const response = await authFetch(
        `${apiBase}/personas/${personaId}`,
        { method: "DELETE" },
        token
      );
      if (response.ok) {
        setPersonas(prev => prev.filter(p => p.id !== personaId));
      }
    } catch (error) {
      console.error("Failed to delete persona:", error);
    }
  };

  const copyProfileUrl = (handle: string) => {
    const url = `${webBase}/p/${handle}`;
    navigator.clipboard.writeText(url);
    setCopiedHandle(handle);
    setTimeout(() => setCopiedHandle(null), 2000);
  };

  if (loading || isLoading) {
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
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.back()}
              className="text-white/60 hover:text-white"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-purple-400" />
              <h1 className="text-xl font-semibold">AI Personas</h1>
            </div>
          </div>
          <Button
            onClick={() => router.push("/persona/create")}
            className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Persona
          </Button>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {personas.length === 0 ? (
          <div className="text-center py-16">
            <Users className="h-16 w-16 mx-auto text-white/20 mb-4" />
            <h2 className="text-xl font-semibold mb-2">No Personas Yet</h2>
            <p className="text-white/40 mb-6">
              Create an AI persona that others can chat with
            </p>
            <Button
              onClick={() => router.push("/persona/create")}
              className="bg-gradient-to-r from-purple-500 to-pink-500"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Persona
            </Button>
          </div>
        ) : (
          <div className="grid gap-4">
            {personas.map((persona) => (
              <div
                key={persona.id}
                className="bg-white/5 rounded-xl p-6 hover:bg-white/10 transition-colors"
              >
                <div className="flex items-start gap-4">
                  <Avatar className="h-16 w-16">
                    <AvatarImage src={persona.avatar_url || ""} />
                    <AvatarFallback className="bg-gradient-to-br from-purple-500 to-pink-500 text-white text-xl">
                      {persona.display_name[0].toUpperCase()}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold">{persona.display_name}</h3>
                      <span className="text-white/40">@{persona.handle}</span>
                      {!persona.is_public && (
                        <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">
                          Private
                        </span>
                      )}
                    </div>
                    {persona.tagline && (
                      <p className="text-white/60 mt-1">{persona.tagline}</p>
                    )}
                    <div className="flex items-center gap-4 mt-3 text-sm text-white/40">
                      <span className="flex items-center gap-1">
                        <MessageSquare className="h-4 w-4" />
                        {persona.total_chats} chats
                      </span>
                      <span>
                        Created {new Date(persona.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => copyProfileUrl(persona.handle)}
                      className="text-white/40 hover:text-white"
                      title="Copy profile URL"
                    >
                      {copiedHandle === persona.handle ? (
                        <Check className="h-4 w-4 text-green-400" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => window.open(`/p/${persona.handle}`, "_blank")}
                      className="text-white/40 hover:text-white"
                      title="Open profile"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => router.push(`/persona/edit/${persona.id}`)}
                      className="text-white/40 hover:text-white"
                      title="Edit persona"
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-white/40 hover:text-red-400"
                          title="Delete persona"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent className="bg-[#1a1a1a] border-white/10">
                        <AlertDialogHeader>
                          <AlertDialogTitle className="text-white">Delete Persona</AlertDialogTitle>
                          <AlertDialogDescription className="text-white/60">
                            Are you sure you want to delete "{persona.display_name}"? This will also delete all chat history. This action cannot be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel className="bg-white/10 text-white border-white/10 hover:bg-white/20">
                            Cancel
                          </AlertDialogCancel>
                          <AlertDialogAction
                            onClick={() => handleDelete(persona.id)}
                            className="bg-red-500 hover:bg-red-600"
                          >
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
