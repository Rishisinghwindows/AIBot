"use client";

import React from "react";
import { format } from "date-fns";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Clock,
  Calendar,
  Play,
  Pause,
  Trash2,
  MoreVertical,
  Edit,
  Bell,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
} from "lucide-react";

export type ScheduledTask = {
  id: string;
  title: string;
  description?: string;
  task_type: string;
  schedule_type: string;
  scheduled_at?: string;
  cron_expression?: string;
  timezone: string;
  agent_prompt?: string;
  status: string;
  next_run_at?: string;
  last_run_at?: string;
  run_count: number;
  max_runs?: number;
  notify_via: Record<string, boolean>;
  created_at: string;
  updated_at: string;
};

type TaskCardProps = {
  task: ScheduledTask;
  onPause?: (id: string) => void;
  onResume?: (id: string) => void;
  onDelete?: (id: string) => void;
  onEdit?: (task: ScheduledTask) => void;
};

const statusStyles: Record<string, { color: string; icon: React.ReactNode }> = {
  active: { color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20", icon: <CheckCircle className="h-3 w-3" /> },
  paused: { color: "bg-amber-500/10 text-amber-500 border-amber-500/20", icon: <Pause className="h-3 w-3" /> },
  completed: { color: "bg-blue-500/10 text-blue-500 border-blue-500/20", icon: <CheckCircle className="h-3 w-3" /> },
  cancelled: { color: "bg-red-500/10 text-red-500 border-red-500/20", icon: <XCircle className="h-3 w-3" /> },
};

const scheduleLabels: Record<string, string> = {
  one_time: "One-time",
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
  cron: "Custom",
};

const taskTypeLabels: Record<string, string> = {
  reminder: "Reminder",
  scheduled_query: "AI Query",
  recurring_report: "Report",
};

export function TaskCard({ task, onPause, onResume, onDelete, onEdit }: TaskCardProps) {
  const status = statusStyles[task.status] || statusStyles.active;

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return null;
    try {
      return format(new Date(dateStr), "MMM d, yyyy 'at' h:mm a");
    } catch {
      return null;
    }
  };

  const hasNotifications = Object.values(task.notify_via || {}).some(Boolean);

  return (
    <Card className="bg-background border-border hover:border-primary/30 transition-colors">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base font-medium text-foreground truncate">
              {task.title}
            </CardTitle>
            {task.description && (
              <CardDescription className="mt-1 text-sm text-muted-foreground line-clamp-2">
                {task.description}
              </CardDescription>
            )}
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8 flex-shrink-0">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-background border-border">
              <DropdownMenuItem onClick={() => onEdit?.(task)} className="cursor-pointer">
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </DropdownMenuItem>
              {task.status === "active" && (
                <DropdownMenuItem onClick={() => onPause?.(task.id)} className="cursor-pointer">
                  <Pause className="h-4 w-4 mr-2" />
                  Pause
                </DropdownMenuItem>
              )}
              {task.status === "paused" && (
                <DropdownMenuItem onClick={() => onResume?.(task.id)} className="cursor-pointer">
                  <Play className="h-4 w-4 mr-2" />
                  Resume
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onDelete?.(task.id)}
                className="cursor-pointer text-destructive focus:text-destructive"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="flex flex-wrap gap-2 mt-3">
          <Badge variant="outline" className={status.color}>
            <span className="mr-1">{status.icon}</span>
            {task.status}
          </Badge>
          <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">
            {taskTypeLabels[task.task_type] || task.task_type}
          </Badge>
          <Badge variant="outline" className="bg-muted text-muted-foreground">
            <RefreshCw className="h-3 w-3 mr-1" />
            {scheduleLabels[task.schedule_type] || task.schedule_type}
          </Badge>
          {hasNotifications && (
            <Badge variant="outline" className="bg-muted text-muted-foreground">
              <Bell className="h-3 w-3 mr-1" />
              Notify
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-2 text-sm text-muted-foreground">
          {task.next_run_at && task.status === "active" && (
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 flex-shrink-0" />
              <span>Next run: {formatDate(task.next_run_at)}</span>
            </div>
          )}
          {task.last_run_at && (
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 flex-shrink-0" />
              <span>Last run: {formatDate(task.last_run_at)}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4 flex-shrink-0" />
            <span>
              Runs: {task.run_count}
              {task.max_runs && ` / ${task.max_runs}`}
            </span>
          </div>
        </div>

        {task.agent_prompt && (
          <div className="mt-3 p-2 rounded-md bg-muted/50 text-sm">
            <p className="text-xs text-muted-foreground mb-1">AI Prompt:</p>
            <p className="text-foreground line-clamp-2">{task.agent_prompt}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
