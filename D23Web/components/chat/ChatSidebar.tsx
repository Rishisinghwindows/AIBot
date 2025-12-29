"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
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
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Conversation } from "@/lib/types";
import {
  Plus,
  MessageSquare,
  Edit,
  Trash2,
  Wrench,
  X,
  Check,
  Link2,
  ChevronDown,
  ChevronUp,
  Calendar,
  BookOpen,
  Bot,
  User,
} from "lucide-react";
import { ConnectionsPanel } from "./ConnectionsPanel";

type ChatSidebarProps = {
  sidebarOpen: boolean;
  conversations: Conversation[];
  currentConversationId: string | null;
  isLoadingConversations: boolean;
  editingConversationId: string | null;
  editingTitle: string;
  isLoggedIn?: boolean;
  onStartNewChat: () => void;
  onSelectConversation: (id: string) => void;
  onBeginEdit: (id: string, title: string) => void;
  onTitleChange: (value: string) => void;
  onRename: (id: string) => void;
  onCancelEdit: () => void;
  onDelete: (id: string) => void;
  onLoginClick?: () => void;
};

export function ChatSidebar({
  sidebarOpen,
  conversations,
  currentConversationId,
  isLoadingConversations,
  editingConversationId,
  editingTitle,
  isLoggedIn = false,
  onStartNewChat,
  onSelectConversation,
  onBeginEdit,
  onTitleChange,
  onRename,
  onCancelEdit,
  onDelete,
  onLoginClick,
}: ChatSidebarProps) {
  const router = useRouter();
  const [showConnections, setShowConnections] = useState(false);

  return (
    <aside
      className={`${
        sidebarOpen ? "w-72" : "w-0"
      } transition-all duration-300 ease-in-out flex flex-col bg-background border-r border-border overflow-hidden`}
    >
      <div className="flex-shrink-0 p-4">
        <Button
          onClick={onStartNewChat}
          className="w-full justify-start gap-3 bg-primary hover:bg-primary/90 text-primary-foreground"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      <ScrollArea className="flex-1 px-2 h-full overflow-hidden">
        <div className="space-y-1 pb-4">
          {isLoadingConversations ? (
            <div className="flex justify-center py-8">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-foreground border-t-primary" />
            </div>
          ) : conversations.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground py-8">
              No conversations yet
            </p>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                  currentConversationId === conv.id
                    ? "bg-primary/20 text-foreground"
                    : "hover:bg-accent text-muted-foreground hover:text-foreground"
                }`}
              >
                <MessageSquare className="h-4 w-4 flex-shrink-0 opacity-60" />
                {editingConversationId === conv.id ? (
                  <div className="flex-1 flex items-center gap-1">
                    <input
                      value={editingTitle}
                      onChange={(e) => onTitleChange(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") onRename(conv.id);
                        if (e.key === "Escape") onCancelEdit();
                      }}
                      autoFocus
                      className="flex-1 bg-muted border border-primary rounded px-2 py-1 focus:outline-none text-sm"
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() => onRename(conv.id)}
                    >
                      <Check className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={onCancelEdit}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <span
                      className="flex-1 truncate text-sm"
                      onClick={() => onSelectConversation(conv.id)}
                    >
                      {conv.title}
                    </span>
                    <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 hover:bg-accent"
                        onClick={(e) => {
                          e.stopPropagation();
                          onBeginEdit(conv.id, conv.title);
                        }}
                      >
                        <Edit className="h-3.5 w-3.5" />
                      </Button>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-7 w-7 hover:bg-accent">
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent className="bg-background border-border">
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete conversation?</AlertDialogTitle>
                            <AlertDialogDescription className="text-muted-foreground">
                              This will permanently delete this conversation and all its messages.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel className="bg-muted border-border hover:bg-accent">Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => onDelete(conv.id)}
                              className="bg-destructive hover:bg-destructive/90"
                            >
                              Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Connections Panel or Toggle Button */}
      <div className="flex-shrink-0 border-t border-border">
        {showConnections ? (
          <div className="flex flex-col" style={{ maxHeight: "320px" }}>
            <div className="flex items-center justify-between px-3 py-2 border-b border-border bg-muted/30">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <Link2 className="h-3.5 w-3.5" />
                Tools & Connections
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 hover:bg-accent"
                onClick={() => setShowConnections(false)}
              >
                <ChevronDown className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-hidden">
              <ConnectionsPanel
                isLoggedIn={isLoggedIn}
                onLoginClick={onLoginClick}
                onManageClick={() => router.push("/settings")}
              />
            </div>
          </div>
        ) : (
          <div className="p-3 space-y-1">
            <Button
              variant="ghost"
              className="w-full justify-between gap-3 text-sm text-muted-foreground hover:text-foreground hover:bg-accent"
              onClick={() => setShowConnections(true)}
            >
              <span className="flex items-center gap-3">
                <Link2 className="h-4 w-4" />
                Tools & Connections
              </span>
              <ChevronUp className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-start gap-3 text-sm text-muted-foreground hover:text-foreground hover:bg-accent"
              onClick={() => router.push("/persona")}
            >
              <Bot className="h-4 w-4" />
              AI Personas
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-start gap-3 text-sm text-muted-foreground hover:text-foreground hover:bg-accent"
              onClick={() => router.push("/profile")}
            >
              <User className="h-4 w-4" />
              Profile
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-start gap-3 text-sm text-muted-foreground hover:text-foreground hover:bg-accent"
              onClick={() => router.push("/knowledge-base")}
            >
              <BookOpen className="h-4 w-4" />
              Knowledge Base
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-start gap-3 text-sm text-muted-foreground hover:text-foreground hover:bg-accent"
              onClick={() => router.push("/tasks")}
            >
              <Calendar className="h-4 w-4" />
              Scheduled Tasks
            </Button>
            <Button
              variant="ghost"
              className="w-full justify-start gap-3 text-sm text-muted-foreground hover:text-foreground hover:bg-accent"
              onClick={() => router.push("/settings")}
            >
              <Wrench className="h-4 w-4" />
              Manage Integrations
            </Button>
          </div>
        )}
      </div>
    </aside>
  );
}
