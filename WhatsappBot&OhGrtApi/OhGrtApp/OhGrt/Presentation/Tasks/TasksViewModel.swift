import Foundation
import Combine

/// View model for managing scheduled tasks
@MainActor
final class TasksViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var tasks: [ScheduledTask] = []
    @Published var isLoading = false
    @Published var error: String?
    @Published var selectedStatus: String = "all"

    // MARK: - Private Properties
    private let apiClient: APIClient
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Initialization
    init(apiClient: APIClient? = nil) {
        self.apiClient = apiClient ?? APIClient.shared
    }

    // MARK: - Computed Properties
    var filteredTasks: [ScheduledTask] {
        if selectedStatus == "all" {
            return tasks
        }
        return tasks.filter { $0.status.rawValue == selectedStatus }
    }

    var activeCount: Int {
        tasks.filter { $0.status == .active }.count
    }

    var pausedCount: Int {
        tasks.filter { $0.status == .paused }.count
    }

    var completedCount: Int {
        tasks.filter { $0.status == .completed }.count
    }

    // MARK: - Public Methods
    func loadTasks() async {
        isLoading = true
        error = nil

        do {
            let sessionId = getSessionId()
            let endpoint = APIEndpoint.webTasks(sessionId: sessionId)
            let response: ScheduledTasksListDTO = try await apiClient.request(endpoint: endpoint)
            tasks = response.tasks.compactMap { mapToEntity($0) }
        } catch {
            self.error = error.localizedDescription
            AppConfig.shared.debugLog("Failed to load tasks: \(error)")
        }

        isLoading = false
    }

    func createTask(
        title: String,
        description: String?,
        taskType: String,
        scheduleType: String,
        scheduledAt: Date?,
        cronExpression: String?,
        agentPrompt: String?,
        notifyPush: Bool,
        notifyEmail: Bool,
        notifyWhatsapp: Bool,
        maxRuns: Int?
    ) async -> Bool {
        isLoading = true
        error = nil

        let scheduleConfig = ScheduleConfigDTO(
            scheduleType: scheduleType,
            scheduledAt: scheduledAt.map { ISO8601DateFormatter().string(from: $0) },
            cronExpression: cronExpression,
            timezone: TimeZone.current.identifier
        )

        let notifyConfig = NotifyConfigDTO(
            push: notifyPush,
            email: notifyEmail,
            whatsapp: notifyWhatsapp
        )

        let request = CreateScheduledTaskDTO(
            title: title,
            description: description,
            taskType: taskType,
            schedule: scheduleConfig,
            agentPrompt: agentPrompt,
            agentConfig: nil,
            notifyVia: notifyConfig,
            maxRuns: maxRuns
        )

        do {
            let sessionId = getSessionId()
            let endpoint = APIEndpoint.webCreateTask(sessionId: sessionId)
            let _: ScheduledTaskDTO = try await apiClient.request(endpoint: endpoint, body: request)
            await loadTasks()
            isLoading = false
            return true
        } catch {
            self.error = error.localizedDescription
            isLoading = false
            return false
        }
    }

    func pauseTask(_ taskId: String) async {
        do {
            let sessionId = getSessionId()
            let endpoint = APIEndpoint.webPauseTask(taskId: taskId, sessionId: sessionId)
            let _: ScheduledTaskDTO = try await apiClient.request(endpoint: endpoint)
            await loadTasks()
        } catch {
            self.error = error.localizedDescription
        }
    }

    func resumeTask(_ taskId: String) async {
        do {
            let sessionId = getSessionId()
            let endpoint = APIEndpoint.webResumeTask(taskId: taskId, sessionId: sessionId)
            let _: ScheduledTaskDTO = try await apiClient.request(endpoint: endpoint)
            await loadTasks()
        } catch {
            self.error = error.localizedDescription
        }
    }

    func deleteTask(_ taskId: String) async {
        do {
            let sessionId = getSessionId()
            let endpoint = APIEndpoint.webDeleteTask(taskId: taskId, sessionId: sessionId)
            let _: TaskEmptyResponse = try await apiClient.request(endpoint: endpoint)
            tasks.removeAll { $0.id == taskId }
        } catch {
            self.error = error.localizedDescription
        }
    }

    // MARK: - Private Methods
    private func getSessionId() -> String {
        // Get session ID from UserDefaults or generate one
        if let sessionId = UserDefaults.standard.string(forKey: "ohgrt_session_id") {
            return sessionId
        }
        let newSessionId = UUID().uuidString
        UserDefaults.standard.set(newSessionId, forKey: "ohgrt_session_id")
        return newSessionId
    }

    private func mapToEntity(_ dto: ScheduledTaskDTO) -> ScheduledTask? {
        let dateFormatter = ISO8601DateFormatter()
        dateFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        let status = TaskStatus(rawValue: dto.status) ?? .active

        return ScheduledTask(
            id: dto.id,
            title: dto.title,
            description: dto.description,
            taskType: dto.taskType,
            scheduleType: dto.scheduleType,
            scheduledAt: dto.scheduledAt.flatMap { dateFormatter.date(from: $0) },
            cronExpression: dto.cronExpression,
            timezone: dto.timezone,
            agentPrompt: dto.agentPrompt,
            agentConfig: nil,
            notifyVia: NotifyConfig(
                push: dto.notifyVia.push,
                email: dto.notifyVia.email,
                whatsapp: dto.notifyVia.whatsapp
            ),
            status: status,
            nextRunAt: dto.nextRunAt.flatMap { dateFormatter.date(from: $0) },
            lastRunAt: dto.lastRunAt.flatMap { dateFormatter.date(from: $0) },
            runCount: dto.runCount,
            maxRuns: dto.maxRuns,
            createdAt: dateFormatter.date(from: dto.createdAt) ?? Date(),
            updatedAt: dateFormatter.date(from: dto.updatedAt) ?? Date()
        )
    }
}

/// Empty response for delete operations (task-specific)
struct TaskEmptyResponse: Codable {
    let message: String?
}
