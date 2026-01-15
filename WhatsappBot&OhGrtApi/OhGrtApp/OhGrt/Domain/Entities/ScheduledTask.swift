import Foundation

/// Represents a scheduled task
struct ScheduledTask: Identifiable, Equatable, Sendable {
    let id: String
    let title: String
    let description: String?
    let taskType: String
    let scheduleType: String
    let scheduledAt: Date?
    let cronExpression: String?
    let timezone: String
    let agentPrompt: String?
    let agentConfig: [String: Any]?
    let notifyVia: NotifyConfig
    let status: TaskStatus
    let nextRunAt: Date?
    let lastRunAt: Date?
    let runCount: Int
    let maxRuns: Int?
    let createdAt: Date
    let updatedAt: Date

    static func == (lhs: ScheduledTask, rhs: ScheduledTask) -> Bool {
        lhs.id == rhs.id
    }
}

/// Notification configuration
struct NotifyConfig: Equatable, Sendable {
    let push: Bool
    let email: Bool
    let whatsapp: Bool

    init(push: Bool = false, email: Bool = false, whatsapp: Bool = false) {
        self.push = push
        self.email = email
        self.whatsapp = whatsapp
    }
}

/// Task status
enum TaskStatus: String, Sendable {
    case active
    case paused
    case completed
    case cancelled

    var displayName: String {
        switch self {
        case .active: return "Active"
        case .paused: return "Paused"
        case .completed: return "Completed"
        case .cancelled: return "Cancelled"
        }
    }
}

/// Task type
enum TaskType: String, Sendable {
    case reminder
    case scheduledQuery = "scheduled_query"
    case recurringReport = "recurring_report"

    var displayName: String {
        switch self {
        case .reminder: return "Reminder"
        case .scheduledQuery: return "AI Query"
        case .recurringReport: return "Report"
        }
    }
}

/// Schedule type
enum ScheduleType: String, Sendable {
    case oneTime = "one_time"
    case daily
    case weekly
    case monthly
    case cron

    var displayName: String {
        switch self {
        case .oneTime: return "One-time"
        case .daily: return "Daily"
        case .weekly: return "Weekly"
        case .monthly: return "Monthly"
        case .cron: return "Custom"
        }
    }
}

/// Task execution record
struct TaskExecution: Identifiable, Equatable, Sendable {
    let id: String
    let taskId: String
    let status: String
    let startedAt: Date
    let completedAt: Date?
    let result: String?
    let errorMessage: String?
    let notificationSent: Bool
}
