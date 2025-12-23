"use client";

import { useAuth } from "@/context/AuthContext";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Loader2,
  ArrowLeft,
  Mail,
  MessageSquare,
  CheckSquare,
  BookOpen,
  Github,
  Layers,
  FileText,
  Database,
  Plus,
  Trash2,
  Settings,
  Check,
  Train,
  Car,
  Sparkles,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import authFetch from "@/lib/auth_fetch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { mcpTemplates, MCPTemplate } from "@/lib/mcp-templates";
import { Tool } from "@/lib/types";

const iconMap: Record<string, React.ReactNode> = {
  Mail: <Mail className="h-5 w-5" />,
  MessageSquare: <MessageSquare className="h-5 w-5" />,
  CheckSquare: <CheckSquare className="h-5 w-5" />,
  BookOpen: <BookOpen className="h-5 w-5" />,
  Github: <Github className="h-5 w-5" />,
  Layers: <Layers className="h-5 w-5" />,
  FileText: <FileText className="h-5 w-5" />,
  Database: <Database className="h-5 w-5" />,
  Train: <Train className="h-5 w-5" />,
  Car: <Car className="h-5 w-5" />,
};

type ProviderStatus = {
  connected: boolean;
  email?: string;
  site_url?: string;
  owner?: string;
  team_name?: string;
  first_name?: string;
};

export default function SettingsPage() {
  const { currentUser, loading, idToken, accessToken } = useAuth();
  const router = useRouter();
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [tools, setTools] = useState<Tool[]>([]);
  const [isLoadingTools, setIsLoadingTools] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<MCPTemplate | null>(null);
  const [configValues, setConfigValues] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [providerStatuses, setProviderStatuses] = useState<Record<string, ProviderStatus>>({});
  const [loadingProviders, setLoadingProviders] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!loading && !currentUser) {
      router.push("/");
    }
  }, [currentUser, loading, router]);

  const fetchProviderStatus = async (provider: string) => {
    if (!accessToken) {
      console.log(`[OAuth] No accessToken available for ${provider} status check`);
      console.log(`[OAuth] idToken available: ${!!idToken}`);
      console.log(`[OAuth] localStorage access_token: ${!!localStorage.getItem("access_token")}`);
      return;
    }
    console.log(`[OAuth] Fetching ${provider} status with accessToken`);
    setLoadingProviders(prev => ({ ...prev, [provider]: true }));
    try {
      const response = await authFetch(`${apiBase}/${provider}/status`, {}, accessToken);
      console.log(`[OAuth] ${provider} status response:`, response.status);
      if (response.ok) {
        const data = await response.json();
        console.log(`[OAuth] ${provider} status data:`, data);
        setProviderStatuses(prev => ({ ...prev, [provider]: data }));
      } else {
        const errorText = await response.text();
        console.error(`[OAuth] ${provider} status error:`, response.status, errorText);
        setProviderStatuses(prev => ({ ...prev, [provider]: { connected: false } }));
      }
    } catch (error) {
      console.error(`[OAuth] Error fetching ${provider} status:`, error);
      setProviderStatuses(prev => ({ ...prev, [provider]: { connected: false } }));
    } finally {
      setLoadingProviders(prev => ({ ...prev, [provider]: false }));
    }
  };

  const fetchTools = async () => {
    if (!accessToken) return;
    setIsLoadingTools(true);
    try {
      const response = await fetch(`${apiBase}/chat/mcp-tools`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
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

  useEffect(() => {
    if (currentUser && accessToken) {
      fetchTools();
      // Fetch status for OAuth providers
      ['gmail', 'jira', 'github', 'slack', 'uber'].forEach(fetchProviderStatus);
    }
  }, [currentUser, accessToken, idToken]);

  const handleAddIntegration = (template: MCPTemplate) => {
    setSelectedTemplate(template);
    setConfigValues({});
    setSaveSuccess(false);
    if (['gmail', 'jira', 'github', 'slack', 'uber'].includes(template.id)) {
      fetchProviderStatus(template.id);
    }
  };

  const handleSaveIntegration = async () => {
    if (!selectedTemplate || !accessToken) return;
    const missingFields = selectedTemplate.config.fields
      .filter((field) => field.required)
      .filter((field) => !configValues[field.name]?.trim())
      .map((field) => field.label);
    if (missingFields.length > 0) {
      alert(`Please fill required fields: ${missingFields.join(", ")}`);
      return;
    }
    setIsSaving(true);
    setSaveSuccess(false);

    try {
      const response = await fetch(`${apiBase}/chat/mcp-tools`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          name: selectedTemplate.name,
          description: selectedTemplate.description,
          tool_type: selectedTemplate.config.type,
          config: configValues,
        }),
      });

      if (response.ok) {
        setSaveSuccess(true);
        await fetchTools();
        setTimeout(() => {
          setSelectedTemplate(null);
          setConfigValues({});
          setSaveSuccess(false);
        }, 1500);
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to save integration");
      }
    } catch (error) {
      console.error("Error saving integration:", error);
      alert("Failed to save integration");
    } finally {
      setIsSaving(false);
    }
  };

  const handleStartOAuthConnect = async (provider: string) => {
    console.log(`[OAuth] Starting ${provider} OAuth connect`);
    console.log(`[OAuth] accessToken available: ${!!accessToken}`);
    console.log(`[OAuth] idToken available: ${!!idToken}`);
    console.log(`[OAuth] localStorage access_token: ${localStorage.getItem("access_token")?.substring(0, 50)}...`);

    if (!accessToken) {
      console.error(`[OAuth] No accessToken - user may not be logged in properly`);
      alert("Please log in first. Your session may have expired.");
      return;
    }

    setIsSaving(true);
    try {
      console.log(`[OAuth] Calling ${apiBase}/${provider}/oauth-url`);
      const response = await authFetch(`${apiBase}/${provider}/oauth-url`, {}, accessToken);
      console.log(`[OAuth] ${provider} oauth-url response:`, response.status);

      if (!response.ok) {
        let detail = `Failed to start ${provider} OAuth`;
        try {
          const error = await response.json();
          console.error(`[OAuth] ${provider} oauth-url error:`, error);
          detail = error.detail || detail;
        } catch {
          const text = await response.text();
          console.error(`[OAuth] ${provider} oauth-url raw error:`, text);
        }
        throw new Error(detail);
      }
      const data = await response.json();
      console.log(`[OAuth] ${provider} oauth-url success:`, data);
      if (data.auth_url) {
        window.location.href = data.auth_url;
      } else {
        throw new Error(`Missing ${provider} authorization URL`);
      }
    } catch (error) {
      console.error(`[OAuth] Error starting ${provider} OAuth:`, error);
      alert((error as Error).message || `Failed to start ${provider} OAuth`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteTool = async (toolId: string) => {
    if (!accessToken) return;
    try {
      const response = await fetch(`${apiBase}/chat/mcp-tools/${toolId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (response.ok) {
        await fetchTools();
      }
    } catch (error) {
      console.error("Error deleting tool:", error);
    }
  };

  const handleToggleTool = async (tool: Tool) => {
    if (!accessToken) return;
    try {
      const response = await fetch(`${apiBase}/chat/mcp-tools/${tool.id}/toggle`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (response.ok) {
        await fetchTools();
      }
    } catch (error) {
      console.error("Error toggling tool:", error);
    }
  };

  const isIntegrationConfigured = (templateId: string) => {
    const oauthProviders = ['gmail', 'jira', 'github', 'slack', 'uber'];
    if (oauthProviders.includes(templateId)) {
      return providerStatuses[templateId]?.connected ?? false;
    }
    return tools.some((t) => t.name.toLowerCase() === templateId.toLowerCase());
  };

  if (loading || !currentUser) {
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

  const configuredIntegrations = tools.filter((t) => t.enabled);
  const categories = ["communication", "productivity", "development", "data", "travel"] as const;
  const missingRequiredFields =
    selectedTemplate?.config.fields
      .filter((field) => field.required)
      .filter((field) => !configValues[field.name]?.trim())
      .map((field) => field.label) ?? [];
  const canSave = missingRequiredFields.length === 0 && !isSaving;

  const isOAuthProvider = (templateId: string) => {
    return ['gmail', 'jira', 'github', 'slack', 'uber'].includes(templateId);
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Background gradients */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-violet-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-fuchsia-600/10 rounded-full blur-[120px]" />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-zinc-800 bg-black/50 backdrop-blur-xl">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push("/chat")}
            className="text-zinc-400 hover:text-white hover:bg-zinc-800"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-xl font-semibold bg-gradient-to-r from-violet-400 via-fuchsia-400 to-pink-400 bg-clip-text text-transparent">
              Integrations
            </h1>
            <p className="text-sm text-zinc-500">
              Connect your tools and services
            </p>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-5xl mx-auto px-4 py-8">
        {/* Active Integrations */}
        {configuredIntegrations.length > 0 && (
          <section className="mb-12">
            <h2 className="text-lg font-semibold mb-4 text-zinc-200">Active Integrations</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {configuredIntegrations.map((tool) => {
                const template = mcpTemplates.find(
                  (t) => t.name.toLowerCase() === tool.name.toLowerCase()
                );
                return (
                  <div
                    key={tool.id}
                    className="relative rounded-xl border border-zinc-800 bg-zinc-900/50 backdrop-blur-sm p-4 hover:border-violet-500/50 transition-all"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 text-violet-400">
                          {template ? iconMap[template.icon] : <Settings className="h-5 w-5" />}
                        </div>
                        <div>
                          <h3 className="font-medium text-white">{tool.name}</h3>
                          <p className="text-xs text-emerald-400">Connected</p>
                        </div>
                      </div>
                      <Switch
                        checked={tool.enabled}
                        onCheckedChange={() => handleToggleTool(tool)}
                        className="data-[state=checked]:bg-violet-600"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-zinc-500">
                        Added {new Date(tool.created_at).toLocaleDateString()}
                      </span>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-400 hover:text-red-300 hover:bg-red-500/10 h-8"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent className="bg-zinc-900 border-zinc-800">
                          <AlertDialogHeader>
                            <AlertDialogTitle className="text-white">Remove integration?</AlertDialogTitle>
                            <AlertDialogDescription className="text-zinc-400">
                              This will disconnect {tool.name}. You can add it again later.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel className="bg-zinc-800 border-zinc-700 text-white hover:bg-zinc-700">
                              Cancel
                            </AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleDeleteTool(tool.id)}
                              className="bg-red-600 hover:bg-red-700 text-white"
                            >
                              Remove
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Available Integrations */}
        <section>
          <h2 className="text-lg font-semibold mb-4 text-zinc-200">Available Integrations</h2>

          {categories.map((category) => {
            const categoryTemplates = mcpTemplates.filter((t) => t.category === category);
            if (categoryTemplates.length === 0) return null;

            return (
              <div key={category} className="mb-8">
                <h3 className="text-sm font-medium text-zinc-500 uppercase tracking-wider mb-3">
                  {category}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {categoryTemplates.map((template) => {
                    const isConfigured = isIntegrationConfigured(template.id);
                    const isComingSoon = template.comingSoon;
                    return (
                      <div
                        key={template.id}
                        className={`rounded-xl border border-zinc-800 bg-zinc-900/50 backdrop-blur-sm p-4 transition-all ${
                          isComingSoon
                            ? "opacity-70 cursor-default"
                            : isConfigured
                            ? "opacity-60 cursor-default"
                            : "cursor-pointer hover:border-violet-500/50 hover:shadow-lg hover:shadow-violet-500/5"
                        }`}
                        onClick={() => !isConfigured && !isComingSoon && handleAddIntegration(template)}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${isComingSoon ? "bg-zinc-800/50 text-zinc-500" : "bg-zinc-800 text-zinc-400"}`}>
                              {iconMap[template.icon]}
                            </div>
                            <h3 className={`font-medium ${isComingSoon ? "text-zinc-400" : "text-white"}`}>{template.name}</h3>
                          </div>
                          {isComingSoon ? (
                            <span className="text-xs text-amber-500 flex items-center gap-1 bg-amber-500/10 px-2 py-1 rounded-full">
                              <Clock className="h-3 w-3" /> Coming Soon
                            </span>
                          ) : isConfigured ? (
                            <span className="text-xs text-violet-400 flex items-center gap-1">
                              <Check className="h-3 w-3" /> Added
                            </span>
                          ) : (
                            <Plus className="h-5 w-5 text-zinc-600" />
                          )}
                        </div>
                        <p className="text-sm text-zinc-500">
                          {template.description}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </section>
      </main>

      {/* Configuration Dialog */}
      <Dialog open={!!selectedTemplate} onOpenChange={() => setSelectedTemplate(null)}>
        <DialogContent className="sm:max-w-md bg-zinc-900 border-zinc-800 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3 text-white">
              {selectedTemplate && (
                <>
                  <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 text-violet-400">
                    {iconMap[selectedTemplate.icon]}
                  </div>
                  Connect {selectedTemplate.name}
                </>
              )}
            </DialogTitle>
            <DialogDescription className="text-zinc-400">
              {selectedTemplate?.description}
            </DialogDescription>
          </DialogHeader>

          {selectedTemplate && (
            <div className="space-y-4 py-4">
              {selectedTemplate.help && (
                <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 px-4 py-3 space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-zinc-200">How to connect</p>
                    {selectedTemplate.help.ctaUrl && (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        className="border-zinc-700 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-white"
                        onClick={() =>
                          window.open(
                            selectedTemplate.help?.ctaUrl,
                            "_blank",
                            "noopener,noreferrer"
                          )
                        }
                      >
                        {selectedTemplate.help.ctaLabel || "Open guide"}
                      </Button>
                    )}
                  </div>
                  {selectedTemplate.help.steps && (
                    <ol className="list-decimal list-inside text-sm text-zinc-400 space-y-1">
                      {selectedTemplate.help.steps.map((step, idx) => (
                        <li key={idx}>{step}</li>
                      ))}
                    </ol>
                  )}
                  {selectedTemplate.help.note && (
                    <p className="text-xs text-zinc-500">
                      {selectedTemplate.help.note}
                    </p>
                  )}
                </div>
              )}

              {isOAuthProvider(selectedTemplate.id) ? (
                <div className="space-y-3">
                  <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 px-4 py-3">
                    <p className="text-sm font-medium text-zinc-200">Connection status</p>
                    <p className="text-sm text-zinc-400">
                      {loadingProviders[selectedTemplate.id]
                        ? `Checking ${selectedTemplate.name} connection...`
                        : providerStatuses[selectedTemplate.id]?.connected
                        ? `${selectedTemplate.name} is connected for your account.`
                        : `${selectedTemplate.name} is not connected yet.`}
                    </p>
                  </div>
                  <p className="text-xs text-zinc-500">
                    We use your current Firebase session to start the OAuth flow and
                    store the tokens securely for your user.
                  </p>
                </div>
              ) : (
                selectedTemplate.config.fields.map((field) => (
                  <div key={field.name} className="space-y-2">
                    <Label htmlFor={field.name} className="text-zinc-300">
                      {field.label}
                      {field.required && <span className="text-red-400 ml-1">*</span>}
                    </Label>
                    {field.type === "textarea" ? (
                      <Textarea
                        id={field.name}
                        placeholder={field.placeholder}
                        value={configValues[field.name] || ""}
                        onChange={(e) =>
                          setConfigValues((prev) => ({ ...prev, [field.name]: e.target.value }))
                        }
                        className="min-h-[100px] font-mono text-sm bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-500 focus:border-violet-500 focus:ring-violet-500/20"
                      />
                    ) : (
                      <Input
                        id={field.name}
                        type={field.type}
                        placeholder={field.placeholder}
                        value={configValues[field.name] || ""}
                        onChange={(e) =>
                          setConfigValues((prev) => ({ ...prev, [field.name]: e.target.value }))
                        }
                        className="bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-500 focus:border-violet-500 focus:ring-violet-500/20"
                      />
                    )}
                    {field.helper && (
                      <p className="text-xs text-zinc-500">{field.helper}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSelectedTemplate(null)}
              className="border-zinc-700 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-white"
            >
              Cancel
            </Button>
            {selectedTemplate && isOAuthProvider(selectedTemplate.id) ? (
              <Button
                onClick={() => handleStartOAuthConnect(selectedTemplate.id)}
                disabled={isSaving || loadingProviders[selectedTemplate.id]}
                className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white"
              >
                {isSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                {providerStatuses[selectedTemplate.id]?.connected
                  ? `Reconnect ${selectedTemplate.name}`
                  : `Connect ${selectedTemplate.name}`}
              </Button>
            ) : (
              <div className="flex flex-col items-end gap-1">
                {missingRequiredFields.length > 0 && (
                  <p className="text-xs text-red-400">
                    Fill required fields: {missingRequiredFields.join(", ")}
                  </p>
                )}
                <Button
                  onClick={handleSaveIntegration}
                  disabled={!canSave}
                  className="bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white disabled:opacity-50"
                >
                  {isSaving ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : saveSuccess ? (
                    <Check className="h-4 w-4 mr-2" />
                  ) : null}
                  {saveSuccess ? "Connected!" : isSaving ? "Connecting..." : "Connect"}
                </Button>
              </div>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
