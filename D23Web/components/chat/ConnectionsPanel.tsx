"use client";

import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Switch } from "@/components/ui/switch";
import {
  Wrench,
  Link2,
  ChevronDown,
  ChevronUp,
  Loader2,
  Github,
  MessageSquare,
  Calendar,
  FileText,
  Cloud,
  Sparkles,
  Sun,
  Star,
  Newspaper,
  Image,
  Database,
  Globe,
  Search,
  Train,
  Plane,
  Check,
  ExternalLink,
} from "lucide-react";

type Tool = {
  name: string;
  description: string;
  category?: string;
};

type Provider = {
  id: string;
  name: string;
  display_name: string;
  auth_type: string;
  description?: string;
  icon_name?: string;
  is_connected: boolean;
};

type ConnectionsPanelProps = {
  isLoggedIn: boolean;
  onLoginClick?: () => void;
  onManageClick?: () => void;
};

const toolIcons: Record<string, React.ReactNode> = {
  weather: <Cloud className="h-4 w-4" />,
  horoscope: <Star className="h-4 w-4" />,
  numerology: <Sparkles className="h-4 w-4" />,
  panchang: <Sun className="h-4 w-4" />,
  tarot: <Sparkles className="h-4 w-4" />,
  news: <Newspaper className="h-4 w-4" />,
  image: <Image className="h-4 w-4" />,
  pdf: <FileText className="h-4 w-4" />,
  sql: <Database className="h-4 w-4" />,
  web_crawl: <Globe className="h-4 w-4" />,
  kundli: <Star className="h-4 w-4" />,
  pnr: <Train className="h-4 w-4" />,
  flight: <Plane className="h-4 w-4" />,
  search: <Search className="h-4 w-4" />,
};

const providerIcons: Record<string, React.ReactNode> = {
  github: <Github className="h-4 w-4" />,
  slack: <MessageSquare className="h-4 w-4" />,
  jira: <FileText className="h-4 w-4" />,
  notion: <FileText className="h-4 w-4" />,
  google_calendar: <Calendar className="h-4 w-4" />,
  calendar: <Calendar className="h-4 w-4" />,
};

export function ConnectionsPanel({ isLoggedIn, onLoginClick, onManageClick }: ConnectionsPanelProps) {
  const [tools, setTools] = useState<Tool[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [isLoadingTools, setIsLoadingTools] = useState(true);
  const [isLoadingProviders, setIsLoadingProviders] = useState(true);
  const [toolsExpanded, setToolsExpanded] = useState(true);
  const [providersExpanded, setProvidersExpanded] = useState(true);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    const fetchTools = async () => {
      setIsLoadingTools(true);
      try {
        const response = await fetch(`${apiBase}/web/tools`);
        if (response.ok) {
          const data = await response.json();
          setTools(data);
        }
      } catch (error) {
        console.error("Error fetching tools:", error);
      } finally {
        setIsLoadingTools(false);
      }
    };

    const fetchProviders = async () => {
      setIsLoadingProviders(true);
      try {
        const response = await fetch(`${apiBase}/web/providers`);
        if (response.ok) {
          const data = await response.json();
          setProviders(data);
        }
      } catch (error) {
        console.error("Error fetching providers:", error);
      } finally {
        setIsLoadingProviders(false);
      }
    };

    fetchTools();
    fetchProviders();
  }, [apiBase]);

  return (
    <div className="flex flex-col h-full bg-background">
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-4">
          {/* Tools Section */}
          <div>
            <button
              onClick={() => setToolsExpanded(!toolsExpanded)}
              className="flex items-center justify-between w-full text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 hover:text-foreground transition-colors"
            >
              <span className="flex items-center gap-2">
                <Wrench className="h-3.5 w-3.5" />
                AI Tools ({tools.length})
              </span>
              {toolsExpanded ? (
                <ChevronUp className="h-3.5 w-3.5" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5" />
              )}
            </button>

            {toolsExpanded && (
              <div className="space-y-0.5">
                {isLoadingTools ? (
                  <div className="flex justify-center py-4">
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  </div>
                ) : tools.length === 0 ? (
                  <p className="text-xs text-muted-foreground py-2">No tools available</p>
                ) : (
                  tools.slice(0, 6).map((tool) => (
                    <div
                      key={tool.name}
                      className="flex items-center gap-2.5 px-2 py-1.5 rounded-md hover:bg-accent/50 transition-colors group"
                    >
                      <div className="p-1.5 rounded-md bg-primary/10 text-primary">
                        {toolIcons[tool.name.toLowerCase()] || <Wrench className="h-4 w-4" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground truncate capitalize">
                          {tool.name.replace(/_/g, " ")}
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-[10px] text-emerald-500 font-medium bg-emerald-500/10 px-1.5 py-0.5 rounded">
                          Active
                        </span>
                      </div>
                    </div>
                  ))
                )}
                {tools.length > 6 && (
                  <button
                    onClick={onManageClick}
                    className="w-full text-xs text-primary hover:text-primary/80 text-center py-1.5 hover:bg-accent/30 rounded-md transition-colors"
                  >
                    View all {tools.length} tools
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Providers/Connections Section */}
          <div>
            <button
              onClick={() => setProvidersExpanded(!providersExpanded)}
              className="flex items-center justify-between w-full text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 hover:text-foreground transition-colors"
            >
              <span className="flex items-center gap-2">
                <Link2 className="h-3.5 w-3.5" />
                Connections ({providers.filter(p => p.is_connected).length}/{providers.length})
              </span>
              {providersExpanded ? (
                <ChevronUp className="h-3.5 w-3.5" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5" />
              )}
            </button>

            {providersExpanded && (
              <div className="space-y-0.5">
                {isLoadingProviders ? (
                  <div className="flex justify-center py-4">
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  </div>
                ) : providers.length === 0 ? (
                  <p className="text-xs text-muted-foreground py-2">No connections available</p>
                ) : (
                  providers.map((provider) => (
                    <div
                      key={provider.id}
                      className="flex items-center gap-2.5 px-2 py-1.5 rounded-md hover:bg-accent/50 transition-colors group"
                    >
                      <div className={`p-1.5 rounded-md ${provider.is_connected ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}>
                        {providerIcons[provider.icon_name || provider.name] || (
                          <Link2 className="h-4 w-4" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium truncate ${provider.is_connected ? 'text-foreground' : 'text-muted-foreground'}`}>
                          {provider.display_name}
                        </p>
                      </div>
                      {provider.is_connected ? (
                        <span className="text-[10px] text-emerald-500 font-medium bg-emerald-500/10 px-1.5 py-0.5 rounded flex items-center gap-1">
                          <Check className="h-3 w-3" />
                          Connected
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-6 px-2 text-xs text-primary hover:text-primary hover:bg-primary/10"
                          onClick={isLoggedIn ? onManageClick : onLoginClick}
                        >
                          Connect
                        </Button>
                      )}
                    </div>
                  ))
                )}

                {/* Sign in prompt for anonymous users */}
                {!isLoggedIn && (
                  <div className="mt-3 p-3 rounded-lg bg-primary/5 border border-primary/10">
                    <p className="text-xs text-muted-foreground mb-2">
                      Sign in to connect your accounts and unlock more features
                    </p>
                    <Button
                      size="sm"
                      className="w-full text-xs h-8 bg-primary hover:bg-primary/90"
                      onClick={onLoginClick}
                    >
                      Sign in with Google
                    </Button>
                  </div>
                )}

                {/* Manage integrations link */}
                {isLoggedIn && (
                  <button
                    onClick={onManageClick}
                    className="w-full flex items-center justify-center gap-1.5 text-xs text-primary hover:text-primary/80 py-2 mt-2 hover:bg-accent/30 rounded-md transition-colors"
                  >
                    <ExternalLink className="h-3 w-3" />
                    Manage all integrations
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
