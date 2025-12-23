import Foundation

/// DTO for schedule configuration
struct ScheduleConfigDTO: Codable {
    let scheduleType: String
    let scheduledAt: String?
    let cronExpression: String?
    let timezone: String

    enum CodingKeys: String, CodingKey {
        case scheduleType = "schedule_type"
        case scheduledAt = "scheduled_at"
        case cronExpression = "cron_expression"
        case timezone
    }
}

/// DTO for notification configuration
struct NotifyConfigDTO: Codable {
    let push: Bool
    let email: Bool
    let whatsapp: Bool
}

/// DTO for creating a scheduled task
struct CreateScheduledTaskDTO: Codable {
    let title: String
    let description: String?
    let taskType: String
    let schedule: ScheduleConfigDTO
    let agentPrompt: String?
    let agentConfig: [String: String]?
    let notifyVia: NotifyConfigDTO
    let maxRuns: Int?

    enum CodingKeys: String, CodingKey {
        case title
        case description
        case taskType = "task_type"
        case schedule
        case agentPrompt = "agent_prompt"
        case agentConfig = "agent_config"
        case notifyVia = "notify_via"
        case maxRuns = "max_runs"
    }
}

/// DTO for scheduled task response
struct ScheduledTaskDTO: Codable {
    let id: String
    let title: String
    let description: String?
    let taskType: String
    let scheduleType: String
    let scheduledAt: String?
    let cronExpression: String?
    let timezone: String
    let agentPrompt: String?
    let agentConfig: [String: String]?
    let notifyVia: NotifyConfigDTO
    let status: String
    let nextRunAt: String?
    let lastRunAt: String?
    let runCount: Int
    let maxRuns: Int?
    let createdAt: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case description
        case taskType = "task_type"
        case scheduleType = "schedule_type"
        case scheduledAt = "scheduled_at"
        case cronExpression = "cron_expression"
        case timezone
        case agentPrompt = "agent_prompt"
        case agentConfig = "agent_config"
        case notifyVia = "notify_via"
        case status
        case nextRunAt = "next_run_at"
        case lastRunAt = "last_run_at"
        case runCount = "run_count"
        case maxRuns = "max_runs"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

/// DTO for scheduled tasks list response
struct ScheduledTasksListDTO: Codable {
    let tasks: [ScheduledTaskDTO]
    let total: Int
    let hasMore: Bool

    enum CodingKeys: String, CodingKey {
        case tasks
        case total
        case hasMore = "has_more"
    }
}

/// DTO for task execution
struct TaskExecutionDTO: Codable {
    let id: String
    let taskId: String
    let status: String
    let startedAt: String
    let completedAt: String?
    let result: String?
    let errorMessage: String?
    let notificationSent: Bool
    let notificationChannels: [String: Bool]?

    enum CodingKeys: String, CodingKey {
        case id
        case taskId = "task_id"
        case status
        case startedAt = "started_at"
        case completedAt = "completed_at"
        case result
        case errorMessage = "error_message"
        case notificationSent = "notification_sent"
        case notificationChannels = "notification_channels"
    }
}

/// DTO for update scheduled task
struct UpdateScheduledTaskDTO: Codable {
    let title: String?
    let description: String?
    let schedule: ScheduleConfigDTO?
    let agentPrompt: String?
    let notifyVia: NotifyConfigDTO?
    let status: String?
    let maxRuns: Int?

    enum CodingKeys: String, CodingKey {
        case title
        case description
        case schedule
        case agentPrompt = "agent_prompt"
        case notifyVia = "notify_via"
        case status
        case maxRuns = "max_runs"
    }
}
