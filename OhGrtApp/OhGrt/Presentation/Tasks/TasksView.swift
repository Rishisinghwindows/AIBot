import SwiftUI

/// Main view for scheduled tasks
struct TasksView: View {
    @StateObject private var viewModel = TasksViewModel()
    @State private var showCreateSheet = false
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Stats bar
                statsBar

                // Filter picker
                filterPicker

                // Task list
                if viewModel.isLoading && viewModel.tasks.isEmpty {
                    loadingView
                } else if viewModel.filteredTasks.isEmpty {
                    emptyView
                } else {
                    taskList
                }
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("Scheduled Tasks")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "chevron.left")
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showCreateSheet = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showCreateSheet) {
                CreateTaskSheet(viewModel: viewModel)
            }
            .task {
                await viewModel.loadTasks()
            }
            .refreshable {
                await viewModel.loadTasks()
            }
        }
    }

    private var statsBar: some View {
        HStack(spacing: 12) {
            StatCard(
                title: "Active",
                count: viewModel.activeCount,
                color: .green
            )
            StatCard(
                title: "Paused",
                count: viewModel.pausedCount,
                color: .orange
            )
            StatCard(
                title: "Completed",
                count: viewModel.completedCount,
                color: .blue
            )
        }
        .padding()
    }

    private var filterPicker: some View {
        Picker("Status", selection: $viewModel.selectedStatus) {
            Text("All").tag("all")
            Text("Active").tag("active")
            Text("Paused").tag("paused")
            Text("Completed").tag("completed")
        }
        .pickerStyle(.segmented)
        .padding(.horizontal)
        .padding(.bottom)
    }

    private var loadingView: some View {
        VStack {
            Spacer()
            ProgressView()
                .scaleEffect(1.5)
            Text("Loading tasks...")
                .foregroundColor(.secondary)
                .padding(.top)
            Spacer()
        }
    }

    private var emptyView: some View {
        VStack(spacing: 16) {
            Spacer()
            Image(systemName: "calendar.badge.clock")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            Text(viewModel.selectedStatus == "all" ? "No scheduled tasks yet" : "No \(viewModel.selectedStatus) tasks")
                .font(.headline)
            Text("Create a task to get started")
                .font(.subheadline)
                .foregroundColor(.secondary)
            Button {
                showCreateSheet = true
            } label: {
                Label("Create Task", systemImage: "plus")
            }
            .buttonStyle(.borderedProminent)
            Spacer()
        }
        .padding()
    }

    private var taskList: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(viewModel.filteredTasks) { task in
                    TaskCardView(
                        task: task,
                        onPause: {
                            Task { await viewModel.pauseTask(task.id) }
                        },
                        onResume: {
                            Task { await viewModel.resumeTask(task.id) }
                        },
                        onDelete: {
                            Task { await viewModel.deleteTask(task.id) }
                        }
                    )
                }
            }
            .padding()
        }
    }
}

/// Stat card component
struct StatCard: View {
    let title: String
    let count: Int
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundColor(color)
            Text("\(count)")
                .font(.title2.bold())
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(color.opacity(0.1))
        .cornerRadius(12)
    }
}

/// Individual task card
struct TaskCardView: View {
    let task: ScheduledTask
    let onPause: () -> Void
    let onResume: () -> Void
    let onDelete: () -> Void

    @State private var showDeleteConfirm = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(task.title)
                        .font(.headline)
                    if let description = task.description {
                        Text(description)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .lineLimit(2)
                    }
                }
                Spacer()
                Menu {
                    if task.status == .active {
                        Button {
                            onPause()
                        } label: {
                            Label("Pause", systemImage: "pause")
                        }
                    } else if task.status == .paused {
                        Button {
                            onResume()
                        } label: {
                            Label("Resume", systemImage: "play")
                        }
                    }
                    Button(role: .destructive) {
                        showDeleteConfirm = true
                    } label: {
                        Label("Delete", systemImage: "trash")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .font(.title3)
                        .foregroundColor(.secondary)
                }
            }

            // Badges
            HStack(spacing: 8) {
                StatusBadge(status: task.status)
                TypeBadge(type: task.taskType)
                ScheduleBadge(type: task.scheduleType)
            }

            // Schedule info
            VStack(alignment: .leading, spacing: 4) {
                if let nextRun = task.nextRunAt, task.status == .active {
                    HStack {
                        Image(systemName: "clock")
                            .font(.caption)
                        Text("Next: \(nextRun.formatted(date: .abbreviated, time: .shortened))")
                            .font(.caption)
                    }
                    .foregroundColor(.secondary)
                }
                if let lastRun = task.lastRunAt {
                    HStack {
                        Image(systemName: "checkmark.circle")
                            .font(.caption)
                        Text("Last: \(lastRun.formatted(date: .abbreviated, time: .shortened))")
                            .font(.caption)
                    }
                    .foregroundColor(.secondary)
                }
                HStack {
                    Image(systemName: "arrow.clockwise")
                        .font(.caption)
                    Text("Runs: \(task.runCount)\(task.maxRuns.map { " / \($0)" } ?? "")")
                        .font(.caption)
                }
                .foregroundColor(.secondary)
            }

            // Agent prompt preview
            if let prompt = task.agentPrompt {
                VStack(alignment: .leading, spacing: 4) {
                    Text("AI Prompt")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(prompt)
                        .font(.caption)
                        .lineLimit(2)
                        .padding(8)
                        .background(Color(.systemGray6))
                        .cornerRadius(8)
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 4, x: 0, y: 2)
        .confirmationDialog(
            "Delete Task",
            isPresented: $showDeleteConfirm,
            titleVisibility: .visible
        ) {
            Button("Delete", role: .destructive) {
                onDelete()
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Are you sure you want to delete this task?")
        }
    }
}

/// Status badge
struct StatusBadge: View {
    let status: TaskStatus

    var color: Color {
        switch status {
        case .active: return .green
        case .paused: return .orange
        case .completed: return .blue
        case .cancelled: return .red
        }
    }

    var body: some View {
        Text(status.displayName)
            .font(.caption2.bold())
            .foregroundColor(color)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(color.opacity(0.15))
            .cornerRadius(6)
    }
}

/// Task type badge
struct TypeBadge: View {
    let type: String

    var displayName: String {
        switch type {
        case "reminder": return "Reminder"
        case "scheduled_query": return "AI Query"
        case "recurring_report": return "Report"
        default: return type
        }
    }

    var body: some View {
        Text(displayName)
            .font(.caption2.bold())
            .foregroundColor(.purple)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(Color.purple.opacity(0.15))
            .cornerRadius(6)
    }
}

/// Schedule type badge
struct ScheduleBadge: View {
    let type: String

    var displayName: String {
        switch type {
        case "one_time": return "One-time"
        case "daily": return "Daily"
        case "weekly": return "Weekly"
        case "monthly": return "Monthly"
        case "cron": return "Custom"
        default: return type
        }
    }

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "arrow.clockwise")
                .font(.caption2)
            Text(displayName)
                .font(.caption2.bold())
        }
        .foregroundColor(.secondary)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Color(.systemGray5))
        .cornerRadius(6)
    }
}
