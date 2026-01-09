"use client";

import React from "react";
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
    <header className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-zinc-800 bg-black/50 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleSidebar}
          className="h-9 w-9 text-zinc-400 hover:text-white hover:bg-zinc-800"
        >
          {sidebarOpen ? <PanelLeftClose className="h-5 w-5" /> : <PanelLeft className="h-5 w-5" />}
        </Button>
        <div
          className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
          onClick={() => router.push("/")}
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <span className="font-semibold text-white">D23 <span className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">AI</span></span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {isLoggedIn ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="gap-2 px-2 hover:bg-zinc-800">
                <Avatar className="h-7 w-7">
                  {userPhotoUrl && <AvatarImage src={userPhotoUrl} />}
                  <AvatarFallback className="bg-gradient-to-br from-violet-600 to-fuchsia-600 text-white text-xs">
                    {userInitials}
                  </AvatarFallback>
                </Avatar>
                <ChevronDown className="h-4 w-4 opacity-60 text-zinc-400" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 bg-zinc-900 border-zinc-800">
              <div className="px-2 py-1.5">
                <p className="text-sm font-medium text-white">{userEmail}</p>
              </div>
              <DropdownMenuSeparator className="bg-zinc-800" />
              <DropdownMenuItem
                onClick={() => router.push("/profile")}
                className="text-zinc-300 focus:text-white focus:bg-zinc-800"
              >
                <User className="mr-2 h-4 w-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => router.push("/knowledge-base")}
                className="text-zinc-300 focus:text-white focus:bg-zinc-800"
              >
                <BookOpen className="mr-2 h-4 w-4" />
                Knowledge Base
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => router.push("/settings")}
                className="text-zinc-300 focus:text-white focus:bg-zinc-800"
              >
                <Settings className="mr-2 h-4 w-4" />
                Integrations
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-zinc-800" />
              <DropdownMenuItem
                onClick={onLogout}
                className="text-red-400 focus:text-red-300 focus:bg-zinc-800"
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
            className="gap-2 text-zinc-300 hover:text-white hover:bg-zinc-800"
          >
            <LogIn className="h-4 w-4" />
            Sign in
          </Button>
        )}
      </div>
    </header>
  );
}
