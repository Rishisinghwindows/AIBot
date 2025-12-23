import SwiftUI

/// Sheet for creating a new scheduled task
struct CreateTaskSheet: View {
    @ObservedObject var viewModel: TasksViewModel
    @Environment(\.dismiss) private var dismiss

    @State private var title = ""
    @State private var description = ""
    @State private var taskType = "reminder"
    @State private var scheduleType = "one_time"
    @State private var scheduledAt = Date().addingTimeInterval(3600) // 1 hour from now
    @State private var cronExpression = ""
    @State private var agentPrompt = ""
    @State private var notifyPush = true
    @State private var notifyEmail = false
    @State private var notifyWhatsapp = false
    @State private var maxRuns: String = ""
    @State private var isSubmitting = false

    var body: some View {
        NavigationStack {
            Form {
                // Basic Info
                Section {
                    TextField("Title", text: $title)
                    TextField("Description (optional)", text: $description, axis: .vertical)
                        .lineLimit(2...4)
                } header: {
                    Text("Task Details")
                }

                // Task Type
                Section {
                    Picker("Type", selection: $taskType) {
                        Label("Reminder", systemImage: "bell")
                            .tag("reminder")
                        Label("AI Query", systemImage: "sparkles")
                            .tag("scheduled_query")
                        Label("Report", systemImage: "doc.text")
                            .tag("recurring_report")
                    }
                } header: {
                    Text("Task Type")
                }

                // Schedule
                Section {
                    Picker("Schedule", selection: $scheduleType) {
                        Text("One-time").tag("one_time")
                        Text("Daily").tag("daily")
                        Text("Weekly").tag("weekly")
                        Text("Monthly").tag("monthly")
                        Text("Custom (Cron)").tag("cron")
                    }

                    if scheduleType == "one_time" {
                        DatePicker(
                            "When",
                            selection: $scheduledAt,
                            in: Date()...,
                            displayedComponents: [.date, .hourAndMinute]
                        )
                    }

                    if scheduleType == "cron" {
                        TextField("Cron Expression", text: $cronExpression)
                        Text("e.g., 0 9 * * 1-5 (weekdays at 9am)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    if scheduleType != "one_time" {
                        TextField("Max Runs (optional)", text: $maxRuns)
                            .keyboardType(.numberPad)
                    }
                } header: {
                    Text("Schedule")
                }

                // AI Prompt (for AI tasks)
                if taskType == "scheduled_query" || taskType == "recurring_report" {
                    Section {
                        TextField("What should the AI do?", text: $agentPrompt, axis: .vertical)
                            .lineLimit(3...6)
                    } header: {
                        Text("AI Prompt")
                    } footer: {
                        Text("Describe what you want the AI to do when this task runs")
                    }
                }

                // Notifications
                Section {
                    Toggle(isOn: $notifyPush) {
                        Label("Push Notification", systemImage: "bell.badge")
                    }
                    Toggle(isOn: $notifyEmail) {
                        Label("Email", systemImage: "envelope")
                    }
                    Toggle(isOn: $notifyWhatsapp) {
                        Label("WhatsApp", systemImage: "message")
                    }
                } header: {
                    Text("Notifications")
                }
            }
            .navigationTitle("New Task")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        createTask()
                    }
                    .disabled(isSubmitting || !isValid)
                }
            }
            .disabled(isSubmitting)
            .overlay {
                if isSubmitting {
                    Color.black.opacity(0.3)
                        .ignoresSafeArea()
                    ProgressView()
                        .scaleEffect(1.5)
                        .tint(.white)
                }
            }
        }
    }

    private var isValid: Bool {
        guard !title.isEmpty else { return false }

        if scheduleType == "one_time" && scheduledAt <= Date() {
            return false
        }

        if scheduleType == "cron" && cronExpression.isEmpty {
            return false
        }

        if (taskType == "scheduled_query" || taskType == "recurring_report") && agentPrompt.isEmpty {
            return false
        }

        return true
    }

    private func createTask() {
        isSubmitting = true

        Task {
            let success = await viewModel.createTask(
                title: title,
                description: description.isEmpty ? nil : description,
                taskType: taskType,
                scheduleType: scheduleType,
                scheduledAt: scheduleType == "one_time" ? scheduledAt : nil,
                cronExpression: scheduleType == "cron" ? cronExpression : nil,
                agentPrompt: agentPrompt.isEmpty ? nil : agentPrompt,
                notifyPush: notifyPush,
                notifyEmail: notifyEmail,
                notifyWhatsapp: notifyWhatsapp,
                maxRuns: Int(maxRuns)
            )

            isSubmitting = false

            if success {
                dismiss()
            }
        }
    }
}

#Preview {
    CreateTaskSheet(viewModel: TasksViewModel())
}
