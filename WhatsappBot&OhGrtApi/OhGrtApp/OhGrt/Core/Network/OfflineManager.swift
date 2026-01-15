import Foundation
import Network
import SwiftUI
import Combine

/// Represents a queued request for offline mode
struct QueuedRequest: Codable, Identifiable {
    let id: UUID
    let endpoint: String
    let method: String
    let body: Data?
    let createdAt: Date
    var retryCount: Int

    init(endpoint: String, method: String, body: Data?) {
        self.id = UUID()
        self.endpoint = endpoint
        self.method = method
        self.body = body
        self.createdAt = Date()
        self.retryCount = 0
    }
}

/// Manages offline mode functionality including network monitoring and request queuing
@MainActor
final class OfflineManager: ObservableObject {
    /// Shared singleton instance
    static let shared = OfflineManager()

    /// Current network connectivity status
    @Published private(set) var isOnline: Bool = true

    /// Whether there are pending requests
    @Published private(set) var hasPendingRequests: Bool = false

    /// Number of pending requests
    @Published private(set) var pendingRequestCount: Int = 0

    /// Whether sync is in progress
    @Published private(set) var isSyncing: Bool = false

    /// Network path monitor
    private let monitor = NWPathMonitor()

    /// Monitor queue
    private let monitorQueue = DispatchQueue(label: "com.ohgrt.networkmonitor")

    /// Queue for pending requests
    private var requestQueue: [QueuedRequest] = []

    /// UserDefaults key for persisted queue
    private let queueKey = "com.ohgrt.offline.requestQueue"

    /// Maximum retry attempts per request
    private let maxRetryAttempts = 3

    /// Maximum age for queued requests (24 hours)
    private let maxRequestAge: TimeInterval = 24 * 60 * 60

    private init() {
        loadPersistedQueue()
        startNetworkMonitoring()
    }

    // MARK: - Network Monitoring

    /// Start monitoring network connectivity
    private func startNetworkMonitoring() {
        monitor.pathUpdateHandler = { [weak self] path in
            Task { @MainActor in
                let wasOffline = !(self?.isOnline ?? true)
                self?.isOnline = path.status == .satisfied

                // Log network status change
                if let isOnline = self?.isOnline {
                    AppConfig.shared.debugLog("Network status: \(isOnline ? "online" : "offline")")
                }

                // If we just came online, try to sync
                if wasOffline && self?.isOnline == true {
                    await self?.syncPendingRequests()
                }
            }
        }
        monitor.start(queue: monitorQueue)
    }

    /// Stop network monitoring
    func stopNetworkMonitoring() {
        monitor.cancel()
    }

    // MARK: - Request Queuing

    /// Queue a request for later execution
    /// - Parameters:
    ///   - endpoint: The API endpoint path
    ///   - method: HTTP method
    ///   - body: Optional request body
    func queueRequest(endpoint: String, method: String, body: Data?) {
        let request = QueuedRequest(endpoint: endpoint, method: method, body: body)
        requestQueue.append(request)
        updateQueueState()
        persistQueue()

        AppConfig.shared.debugLog("Queued request: \(method) \(endpoint)")
    }

    /// Check if a request type should be queued when offline
    /// - Parameter endpoint: The endpoint path
    /// - Returns: Whether this request type can be queued
    func shouldQueueRequest(endpoint: String) -> Bool {
        // Only queue certain types of requests
        let queueableEndpoints = [
            "/chat/send",
        ]

        return queueableEndpoints.contains { endpoint.contains($0) }
    }

    // MARK: - Sync

    /// Sync all pending requests
    func syncPendingRequests() async {
        guard isOnline else {
            AppConfig.shared.debugLog("Cannot sync: offline")
            return
        }

        guard !requestQueue.isEmpty else {
            AppConfig.shared.debugLog("No pending requests to sync")
            return
        }

        guard !isSyncing else {
            AppConfig.shared.debugLog("Sync already in progress")
            return
        }

        isSyncing = true
        defer { isSyncing = false }

        AppConfig.shared.debugLog("Starting sync of \(requestQueue.count) pending requests")

        // Process queue in order
        var failedRequests: [QueuedRequest] = []

        for var request in requestQueue {
            // Skip expired requests
            if Date().timeIntervalSince(request.createdAt) > maxRequestAge {
                AppConfig.shared.debugLog("Skipping expired request: \(request.endpoint)")
                continue
            }

            // Skip requests that have exceeded retry limit
            if request.retryCount >= maxRetryAttempts {
                AppConfig.shared.debugLog("Skipping request after max retries: \(request.endpoint)")
                continue
            }

            do {
                try await executeQueuedRequest(request)
                AppConfig.shared.debugLog("Successfully synced request: \(request.endpoint)")
            } catch {
                AppConfig.shared.debugLog("Failed to sync request: \(request.endpoint) - \(error)")
                request.retryCount += 1
                failedRequests.append(request)
            }
        }

        // Update queue with failed requests
        requestQueue = failedRequests
        updateQueueState()
        persistQueue()

        AppConfig.shared.debugLog("Sync complete. \(failedRequests.count) requests remaining")
    }

    /// Execute a single queued request
    private func executeQueuedRequest(_ request: QueuedRequest) async throws {
        let url = AppConfig.shared.apiBaseURL.appendingPathComponent(request.endpoint)
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = request.method
        urlRequest.httpBody = request.body

        // Add headers via interceptor
        let interceptor = RequestInterceptor()
        urlRequest = try await interceptor.intercept(urlRequest, requiresAuth: true)

        let session = URLSession.pinnedSession()
        let (_, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw OfflineError.requestFailed
        }
    }

    // MARK: - Queue Management

    /// Clear all pending requests
    func clearQueue() {
        requestQueue.removeAll()
        updateQueueState()
        persistQueue()
        AppConfig.shared.debugLog("Cleared request queue")
    }

    /// Remove a specific request from the queue
    func removeRequest(_ id: UUID) {
        requestQueue.removeAll { $0.id == id }
        updateQueueState()
        persistQueue()
    }

    /// Get all pending requests
    func getPendingRequests() -> [QueuedRequest] {
        return requestQueue
    }

    // MARK: - Persistence

    /// Persist queue to UserDefaults
    private func persistQueue() {
        do {
            let data = try JSONEncoder().encode(requestQueue)
            UserDefaults.standard.set(data, forKey: queueKey)
        } catch {
            AppConfig.shared.debugLog("Failed to persist queue: \(error)")
        }
    }

    /// Load persisted queue from UserDefaults
    private func loadPersistedQueue() {
        guard let data = UserDefaults.standard.data(forKey: queueKey) else { return }

        do {
            requestQueue = try JSONDecoder().decode([QueuedRequest].self, from: data)
            // Remove expired requests
            let now = Date()
            requestQueue = requestQueue.filter { now.timeIntervalSince($0.createdAt) < maxRequestAge }
            updateQueueState()
        } catch {
            AppConfig.shared.debugLog("Failed to load persisted queue: \(error)")
        }
    }

    /// Update published state properties
    private func updateQueueState() {
        pendingRequestCount = requestQueue.count
        hasPendingRequests = !requestQueue.isEmpty
    }
}

// MARK: - Errors

enum OfflineError: LocalizedError {
    case offline
    case requestFailed
    case maxRetriesExceeded

    var errorDescription: String? {
        switch self {
        case .offline:
            return "No internet connection"
        case .requestFailed:
            return "Request failed"
        case .maxRetriesExceeded:
            return "Maximum retry attempts exceeded"
        }
    }
}

// MARK: - SwiftUI View Modifier

/// View modifier to show offline banner
struct OfflineBannerModifier: ViewModifier {
    @ObservedObject var offlineManager = OfflineManager.shared

    func body(content: Content) -> some View {
        VStack(spacing: 0) {
            // Offline banner
            if !offlineManager.isOnline {
                HStack {
                    Image(systemName: "wifi.slash")
                    Text("No internet connection")
                        .font(.footnote)

                    if offlineManager.hasPendingRequests {
                        Spacer()
                        Text("\(offlineManager.pendingRequestCount) pending")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                .padding(.horizontal)
                .padding(.vertical, 8)
                .frame(maxWidth: .infinity)
                .background(Color.orange.opacity(0.9))
                .foregroundColor(.white)
            }

            // Syncing banner
            if offlineManager.isSyncing {
                HStack {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(0.8)
                    Text("Syncing...")
                        .font(.footnote)
                }
                .padding(.horizontal)
                .padding(.vertical, 6)
                .frame(maxWidth: .infinity)
                .background(Color.blue.opacity(0.9))
                .foregroundColor(.white)
            }

            content
        }
    }
}

extension View {
    /// Add offline status banner to view
    func withOfflineBanner() -> some View {
        modifier(OfflineBannerModifier())
    }
}
