"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  PanelLeftClose,
  PanelLeft,
  Sparkles,
  Settings,
  ChevronDown,
  LogOut,
  LogIn,
  User,
  BookOpen,
} from "lucide-react";

type ChatHeaderProps = {
  sidebarOpen: boolean;
  userInitials: string;
  userEmail?: string | null;
  userPhotoUrl?: string | null;
  onToggleSidebar: () => void;
  onLogout: () => void;
  isLoggedIn?: boolean;
  onLogin?: () => void;
};

export function ChatHeader({
  sidebarOpen,
  userInitials,
  userEmail,
  userPhotoUrl,
  onToggleSidebar,
  onLogout,
  isLoggedIn = true,
  onLogin,
}: ChatHeaderProps) {
  const router = useRouter();

  return (
    <header className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleSidebar}
          className="h-9 w-9 text-muted-foreground hover:text-foreground hover:bg-accent"
        >
          {sidebarOpen ? <PanelLeftClose className="h-5 w-5" /> : <PanelLeft className="h-5 w-5" />}
        </Button>
        <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="font-semibold text-foreground">D23<span className="text-primary">.AI</span></span>
        </Link>
      </div>

      <div className="flex items-center gap-2">
        {isLoggedIn ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="gap-2 px-2 hover:bg-accent">
                <Avatar className="h-7 w-7">
                  {userPhotoUrl && <AvatarImage src={userPhotoUrl} />}
                  <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                    {userInitials}
                  </AvatarFallback>
                </Avatar>
                <ChevronDown className="h-4 w-4 opacity-60 text-muted-foreground" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 bg-card border-border">
              <div className="px-2 py-1.5">
                <p className="text-sm font-medium text-foreground">{userEmail}</p>
              </div>
              <DropdownMenuSeparator className="bg-border" />
              <DropdownMenuItem
                onClick={() => router.push("/profile")}
                className="text-muted-foreground focus:text-foreground focus:bg-accent"
              >
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => router.push("/knowledge-base")}
                className="text-muted-foreground focus:text-foreground focus:bg-accent"
              >
                <BookOpen className="mr-2 h-4 w-4" />
                Knowledge Base
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => router.push("/settings")}
                className="text-muted-foreground focus:text-foreground focus:bg-accent"
              >
                <Settings className="mr-2 h-4 w-4" />
                Integrations
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-border" />
              <DropdownMenuItem
                onClick={onLogout}
                className="text-destructive focus:text-destructive focus:bg-accent"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Button
            onClick={onLogin}
            variant="ghost"
            className="gap-2 text-muted-foreground hover:text-foreground hover:bg-accent"
          >
            <LogIn className="h-4 w-4" />
            Sign in
          </Button>
        )}
      </div>
    </header>
  );
}
