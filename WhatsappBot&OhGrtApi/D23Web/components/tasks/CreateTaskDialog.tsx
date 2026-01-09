"use client";

import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Loader2, Calendar, Clock, Bell, Sparkles } from "lucide-react";

type CreateTaskDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (task: CreateTaskData) => Promise<void>;
};

export type CreateTaskData = {
  title: string;
  description?: string;
  task_type: string;
  schedule: {
    schedule_type: string;
    scheduled_at?: string;
    cron_expression?: string;
    timezone: string;
  };
  agent_prompt?: string;
  notify_via: {
    push: boolean;
    email: boolean;
    whatsapp: boolean;
  };
  max_runs?: number;
};

export function CreateTaskDialog({ open, onOpenChange, onSubmit }: CreateTaskDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [taskType, setTaskType] = useState("reminder");
  const [scheduleType, setScheduleType] = useState("one_time");
  const [scheduledAt, setScheduledAt] = useState("");
  const [cronExpression, setCronExpression] = useState("");
  const [agentPrompt, setAgentPrompt] = useState("");
  const [notifyPush, setNotifyPush] = useState(true);
  const [notifyEmail, setNotifyEmail] = useState(false);
  const [notifyWhatsapp, setNotifyWhatsapp] = useState(false);
  const [maxRuns, setMaxRuns] = useState<number | undefined>(undefined);

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setTaskType("reminder");
    setScheduleType("one_time");
    setScheduledAt("");
    setCronExpression("");
    setAgentPrompt("");
    setNotifyPush(true);
    setNotifyEmail(false);
    setNotifyWhatsapp(false);
    setMaxRuns(undefined);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsSubmitting(true);
    try {
      const taskData: CreateTaskData = {
        title: title.trim(),
        description: description.trim() || undefined,
        task_type: taskType,
        schedule: {
          schedule_type: scheduleType,
          scheduled_at: scheduleType === "one_time" && scheduledAt ? new Date(scheduledAt).toISOString() : undefined,
          cron_expression: scheduleType === "cron" ? cronExpression : undefined,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        },
        agent_prompt: (taskType === "scheduled_query" || taskType === "recurring_report") && agentPrompt ? agentPrompt : undefined,
        notify_via: {
          push: notifyPush,
          email: notifyEmail,
          whatsapp: notifyWhatsapp,
        },
        max_runs: scheduleType !== "one_time" && maxRuns ? maxRuns : undefined,
      };

      await onSubmit(taskData);
      resetForm();
      onOpenChange(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] bg-background border-border">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle className="text-foreground">Create Scheduled Task</DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Schedule a reminder or AI-powered task to run automatically.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="title" className="text-foreground">Title *</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., Daily weather report"
                className="bg-muted border-border"
                required
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-foreground">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description..."
                className="bg-muted border-border resize-none"
                rows={2}
              />
            </div>

            {/* Task Type */}
            <div className="space-y-2">
              <Label className="text-foreground">Task Type</Label>
              <Select value={taskType} onValueChange={setTaskType}>
                <SelectTrigger className="bg-muted border-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-background border-border">
                  <SelectItem value="reminder">
                    <div className="flex items-center gap-2">
                      <Bell className="h-4 w-4" />
                      <span>Reminder</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="scheduled_query">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4" />
                      <span>AI Query</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="recurring_report">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      <span>Recurring Report</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Schedule Type */}
            <div className="space-y-2">
              <Label className="text-foreground">Schedule</Label>
              <Select value={scheduleType} onValueChange={setScheduleType}>
                <SelectTrigger className="bg-muted border-border">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-background border-border">
                  <SelectItem value="one_time">One-time</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                  <SelectItem value="cron">Custom (Cron)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* One-time Date/Time Picker */}
            {scheduleType === "one_time" && (
              <div className="space-y-2">
                <Label htmlFor="scheduled_at" className="text-foreground">
                  <Clock className="h-4 w-4 inline mr-1" />
                  When to run
                </Label>
                <Input
                  id="scheduled_at"
                  type="datetime-local"
                  value={scheduledAt}
                  onChange={(e) => setScheduledAt(e.target.value)}
                  className="bg-muted border-border"
                  required
                />
              </div>
            )}

            {/* Cron Expression */}
            {scheduleType === "cron" && (
              <div className="space-y-2">
                <Label htmlFor="cron" className="text-foreground">Cron Expression</Label>
                <Input
                  id="cron"
                  value={cronExpression}
                  onChange={(e) => setCronExpression(e.target.value)}
                  placeholder="e.g., 0 9 * * 1-5 (weekdays at 9am)"
                  className="bg-muted border-border"
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Format: minute hour day month weekday
                </p>
              </div>
            )}

            {/* Max Runs for recurring */}
            {scheduleType !== "one_time" && (
              <div className="space-y-2">
                <Label htmlFor="max_runs" className="text-foreground">Maximum Runs (optional)</Label>
                <Input
                  id="max_runs"
                  type="number"
                  min="1"
                  value={maxRuns || ""}
                  onChange={(e) => setMaxRuns(e.target.value ? parseInt(e.target.value) : undefined)}
                  placeholder="Leave empty for unlimited"
                  className="bg-muted border-border"
                />
              </div>
            )}

            {/* Agent Prompt for AI tasks */}
            {(taskType === "scheduled_query" || taskType === "recurring_report") && (
              <div className="space-y-2">
                <Label htmlFor="agent_prompt" className="text-foreground">
                  <Sparkles className="h-4 w-4 inline mr-1" />
                  AI Prompt
                </Label>
                <Textarea
                  id="agent_prompt"
                  value={agentPrompt}
                  onChange={(e) => setAgentPrompt(e.target.value)}
                  placeholder="e.g., Get me the weather forecast for Mumbai and summarize any important news"
                  className="bg-muted border-border resize-none"
                  rows={3}
                  required
                />
              </div>
            )}

            {/* Notifications */}
            <div className="space-y-3">
              <Label className="text-foreground">Notifications</Label>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="notify_push" className="text-sm text-muted-foreground cursor-pointer">
                    Push notification
                  </Label>
                  <Switch
                    id="notify_push"
                    checked={notifyPush}
                    onCheckedChange={setNotifyPush}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="notify_email" className="text-sm text-muted-foreground cursor-pointer">
                    Email
                  </Label>
                  <Switch
                    id="notify_email"
                    checked={notifyEmail}
                    onCheckedChange={setNotifyEmail}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="notify_whatsapp" className="text-sm text-muted-foreground cursor-pointer">
                    WhatsApp
                  </Label>
                  <Switch
                    id="notify_whatsapp"
                    checked={notifyWhatsapp}
                    onCheckedChange={setNotifyWhatsapp}
                  />
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="border-border"
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !title.trim()}>
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Task"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
