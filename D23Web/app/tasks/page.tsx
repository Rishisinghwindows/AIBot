"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TaskCard, ScheduledTask } from "@/components/tasks/TaskCard";
import { CreateTaskDialog, CreateTaskData } from "@/components/tasks/CreateTaskDialog";
import {
  Plus,
  Search,
  Calendar,
  ChevronLeft,
  Loader2,
  Clock,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

export default function TasksPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<ScheduledTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Get or create session ID
  useEffect(() => {
    const storedSessionId = localStorage.getItem("ohgrt_session_id");
    if (storedSessionId) {
      setSessionId(storedSessionId);
    } else {
      // Fetch a new session if we don't have one
      fetch(`${apiBase}/web/session`, { method: "POST" })
        .then((res) => res.json())
        .then((data) => {
          localStorage.setItem("ohgrt_session_id", data.session_id);
          setSessionId(data.session_id);
        })
        .catch((err) => console.error("Failed to create session:", err));
    }
  }, [apiBase]);

  // Fetch tasks
  const fetchTasks = useCallback(async () => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ session_id: sessionId });
      if (statusFilter !== "all") {
        params.append("status", statusFilter);
      }

      const response = await fetch(`${apiBase}/web/tasks?${params.toString()}`);
      if (!response.ok) {
        throw new Error("Failed to fetch tasks");
      }

      const data = await response.json();
      setTasks(data.tasks || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  }, [apiBase, sessionId, statusFilter]);

  useEffect(() => {
    if (sessionId) {
      fetchTasks();
    }
  }, [sessionId, fetchTasks]);

  // Create task
  const handleCreateTask = async (taskData: CreateTaskData) => {
    if (!sessionId) return;

    const response = await fetch(`${apiBase}/web/tasks?session_id=${sessionId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(taskData),
    });

    if (!response.ok) {
      throw new Error("Failed to create task");
    }

    await fetchTasks();
  };

  // Pause task
  const handlePauseTask = async (taskId: string) => {
    if (!sessionId) return;

    const response = await fetch(
      `${apiBase}/tasks/${taskId}/pause?session_id=${sessionId}`,
      { method: "POST" }
    );

    if (response.ok) {
      fetchTasks();
    }
  };

  // Resume task
  const handleResumeTask = async (taskId: string) => {
    if (!sessionId) return;

    const response = await fetch(
      `${apiBase}/tasks/${taskId}/resume?session_id=${sessionId}`,
      { method: "POST" }
    );

    if (response.ok) {
      fetchTasks();
    }
  };

  // Delete task
  const handleDeleteTask = async (taskId: string) => {
    if (!sessionId) return;

    const response = await fetch(
      `${apiBase}/web/tasks/${taskId}?session_id=${sessionId}`,
      { method: "DELETE" }
    );

    if (response.ok) {
      fetchTasks();
    }
  };

  // Filter tasks by search query
  const filteredTasks = tasks.filter((task) =>
    task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (task.description?.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Stats
  const activeCount = tasks.filter((t) => t.status === "active").length;
  const pausedCount = tasks.filter((t) => t.status === "paused").length;
  const completedCount = tasks.filter((t) => t.status === "completed").length;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => router.push("/chat")}
                className="hover:bg-accent"
              >
                <ChevronLeft className="h-5 w-5" />
              </Button>
              <div>
                <h1 className="text-xl font-semibold text-foreground flex items-center gap-2">
                  <Calendar className="h-5 w-5 text-primary" />
                  Scheduled Tasks
                </h1>
                <p className="text-sm text-muted-foreground">
                  Manage your reminders and automated tasks
                </p>
              </div>
            </div>
            <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              New Task
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <div className="flex items-center gap-2 text-emerald-500">
              <Clock className="h-4 w-4" />
              <span className="text-sm font-medium">Active</span>
            </div>
            <p className="text-2xl font-bold text-foreground mt-1">{activeCount}</p>
          </div>
          <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
            <div className="flex items-center gap-2 text-amber-500">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm font-medium">Paused</span>
            </div>
            <p className="text-2xl font-bold text-foreground mt-1">{pausedCount}</p>
          </div>
          <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
            <div className="flex items-center gap-2 text-blue-500">
              <CheckCircle className="h-4 w-4" />
              <span className="text-sm font-medium">Completed</span>
            </div>
            <p className="text-2xl font-bold text-foreground mt-1">{completedCount}</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search tasks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-muted border-border"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full sm:w-[180px] bg-muted border-border">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent className="bg-background border-border">
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="paused">Paused</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Task List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <p className="text-destructive">{error}</p>
            <Button variant="outline" onClick={fetchTasks} className="mt-4">
              Retry
            </Button>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="text-center py-12">
            <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              {searchQuery || statusFilter !== "all"
                ? "No matching tasks"
                : "No scheduled tasks yet"}
            </h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery || statusFilter !== "all"
                ? "Try adjusting your filters"
                : "Create your first task to get started"}
            </p>
            {!searchQuery && statusFilter === "all" && (
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Task
              </Button>
            )}
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onPause={handlePauseTask}
                onResume={handleResumeTask}
                onDelete={handleDeleteTask}
              />
            ))}
          </div>
        )}
      </main>

      {/* Create Dialog */}
      <CreateTaskDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSubmit={handleCreateTask}
      />
    </div>
  );
}
