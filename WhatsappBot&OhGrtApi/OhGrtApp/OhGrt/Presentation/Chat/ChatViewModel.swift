import Foundation
import Combine
import SwiftUI
import SwiftData
import CoreLocation

/// ViewModel for chat screens
@MainActor
final class ChatViewModel: ObservableObject {
    // MARK: - Published Properties

    @Published private(set) var messages: [ChatMessage] = []
    @Published private(set) var isLoading = false
    @Published private(set) var isSending = false
    @Published private(set) var error: String?
    @Published var showError = false
    @Published var inputText = ""

    @Published private(set) var availableTools: [ToolInfo] = []
    @Published var selectedTools: Set<String> = []
    @Published private(set) var toolsLoading = false
    @Published private(set) var toolsError: String?

    @Published private(set) var providers: [ProviderInfo] = []
    @Published private(set) var providersLoading = false
    @Published var providerError: String?

    /// Trigger to show subscription modal
    @Published var shouldShowSubscription = false

    @Published private(set) var isLoadingMore = false
    @Published private(set) var hasMoreHistory = true

    // MARK: - Location Properties

    /// Whether to show the location sharing prompt
    @Published var showLocationPrompt = false

    /// User's current location (if shared)
    @Published private(set) var userLocation: CLLocationCoordinate2D?

    /// Location accuracy in meters
    @Published private(set) var locationAccuracy: Double?

    /// Pending message that requires location
    private var pendingLocationMessage: String?

    // MARK: - Computed Properties for Compatibility

    /// Alias for error to match ChatView expectations
    var errorMessage: String? { error }

    // MARK: - Legacy Compatibility Properties (for old ChatView)

    /// Legacy OAuth stub - returns empty OAuthStartResponse
    struct OAuthStartResponse {
        let authUrl: String
    }

    func startOAuth(for provider: Provider) async throws -> OAuthStartResponse {
        // Legacy OAuth stub - will be implemented in provider use cases
        throw DomainError.notImplemented("OAuth not yet implemented in Clean Architecture")
    }

    func startOAuth(for provider: ProviderInfo) async throws -> OAuthStartResponse {
        // Legacy OAuth stub - will be implemented in provider use cases
        throw DomainError.notImplemented("OAuth not yet implemented in Clean Architecture")
    }

    func completeOAuth(for provider: ProviderInfo, code: String, state: String) async {
        // Legacy OAuth stub - will be implemented in provider use cases
        providerError = "OAuth not yet implemented in Clean Architecture"
    }

    func friendlyErrorMessage(for error: Error) -> String {
        if let domainError = error as? DomainError {
            return domainError.localizedDescription
        }
        return error.localizedDescription
    }

    func retryMessage(_ message: Any) async {
        // Legacy stub - retry functionality will be implemented in use cases
    }

    /// Legacy property for old views - provides SwiftData Message compatibility
    /// Note: Old ChatView should migrate to use ChatMessage or @Query
    var legacyMessages: [Message] {
        // This returns empty since we can't easily convert ChatMessage to Message
        // Old views should use @Query directly
        []
    }

    // MARK: - Use Cases

    private let sendMessageUseCase: SendMessageUseCaseProtocol
    private let getMessagesUseCase: GetMessagesUseCaseProtocol
    private let getToolsUseCase: GetToolsUseCaseProtocol
    private let getProvidersUseCase: GetProvidersUseCaseProtocol
    private let createConversationUseCase: CreateConversationUseCaseProtocol

    // MARK: - Private Properties

    private var currentConversationId: UUID?
    private var oldestLoadedMessageDate: Date?
    private var cancellables = Set<AnyCancellable>()
    private var modelContext: ModelContext?
    private let pageSize = 30

    // MARK: - Computed Properties

    var canSend: Bool {
        !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isSending
    }

    var hasMessages: Bool {
        !messages.isEmpty
    }

    // MARK: - Initialization

    init(
        sendMessageUseCase: SendMessageUseCaseProtocol,
        getMessagesUseCase: GetMessagesUseCaseProtocol,
        getToolsUseCase: GetToolsUseCaseProtocol,
        getProvidersUseCase: GetProvidersUseCaseProtocol,
        createConversationUseCase: CreateConversationUseCaseProtocol
    ) {
        self.sendMessageUseCase = sendMessageUseCase
        self.getMessagesUseCase = getMessagesUseCase
        self.getToolsUseCase = getToolsUseCase
        self.getProvidersUseCase = getProvidersUseCase
        self.createConversationUseCase = createConversationUseCase
    }

    // MARK: - Public Methods

    func loadConversation(_ conversationId: UUID) {
        currentConversationId = conversationId
        resetPagination()
        Task {
            await loadMessages()
        }
    }

    func createNewConversation() {
        Task {
            await performCreateConversation()
        }
    }

    func sendMessage() async {
        AppConfig.shared.debugLog("🟣 sendMessage called, canSend: \(canSend)")
        guard canSend else {
            AppConfig.shared.debugLog("🟣 Cannot send - canSend is false")
            return
        }

        let messageText = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        AppConfig.shared.debugLog("🟣 Sending message: \(messageText)")
        inputText = ""

        await performSendMessage(messageText)
    }

    func toggleTool(_ toolId: String) {
        if selectedTools.contains(toolId) {
            selectedTools.remove(toolId)
        } else {
            selectedTools.insert(toolId)
        }
    }

    func clearError() {
        error = nil
        showError = false
    }

    func clearConversation() {
        messages = []
        currentConversationId = nil
        resetPagination()
    }

    /// Alias for createNewConversation() to match ChatView expectations
    func startNewConversation() {
        createNewConversation()
    }

    // MARK: - Location Methods

    /// Handle location shared by user
    func handleLocationShare(_ coordinate: CLLocationCoordinate2D, accuracy: Double?) {
        userLocation = coordinate
        locationAccuracy = accuracy
        showLocationPrompt = false

        // If there's a pending message, resend it with location
        if let pendingMessage = pendingLocationMessage {
            pendingLocationMessage = nil
            inputText = pendingMessage
            Task {
                await sendMessage()
            }
        }
    }

    /// Dismiss location prompt without sharing
    func dismissLocationPrompt() {
        showLocationPrompt = false
        pendingLocationMessage = nil
    }

    /// Build LocationDTO from current user location
    private func buildLocationDTO() -> LocationDTO? {
        guard let location = userLocation else { return nil }
        return LocationDTO(
            latitude: location.latitude,
            longitude: location.longitude,
            accuracy: locationAccuracy,
            address: nil
        )
    }

    /// Set the SwiftData model context for local persistence
    func setModelContext(_ context: ModelContext) {
        self.modelContext = context
    }

    /// Load chat history from server
    func loadHistoryFromServer() async {
        guard let conversationId = currentConversationId else { return }

        isLoading = true
        defer { isLoading = false }

        do {
            let fetched = try await getMessagesUseCase.execute(
                conversationId: conversationId,
                before: nil,
                limit: pageSize
            )
            let ordered = fetched.sorted { $0.createdAt < $1.createdAt }
            messages = ordered
            oldestLoadedMessageDate = messages.first?.createdAt
            hasMoreHistory = fetched.count == pageSize
        } catch let domainError as DomainError {
            error = domainError.localizedDescription
            showError = true
        } catch {
            self.error = error.localizedDescription
            showError = true
        }
    }

    /// Load available tools from server (async version)
    func loadTools() async {
        toolsLoading = true
        toolsError = nil

        do {
            let tools = try await getToolsUseCase.execute()
            // Convert Tool domain entities to ToolInfo for the view
            let serverTools = tools.map { tool in
                ToolInfo(
                    name: tool.name,
                    description: tool.description,
                    category: tool.category.rawValue
                )
            }
            availableTools = ToolCatalog.mergedTools(from: serverTools)
        } catch let domainError as DomainError {
            toolsError = domainError.localizedDescription
            availableTools = ToolCatalog.mergedTools(from: [])
        } catch {
            toolsError = error.localizedDescription
            availableTools = ToolCatalog.mergedTools(from: [])
        }

        toolsLoading = false
    }

    /// Load available providers/integrations from server
    func loadProviders() async {
        providersLoading = true
        providerError = nil

        do {
            let providerList = try await getProvidersUseCase.execute()
            // Convert Provider domain entities to ProviderInfo for the view
            providers = providerList.map { provider in
                ProviderInfo(
                    name: provider.name,
                    displayName: provider.displayName,
                    authType: provider.authType,
                    connected: provider.connected
                )
            }
        } catch let domainError as DomainError {
            providerError = domainError.localizedDescription
        } catch {
            providerError = error.localizedDescription
        }

        providersLoading = false
    }

    /// Connect a provider with API key/credentials
    func connectProvider(_ provider: ProviderInfo, secret: String, displayName: String, config: [String: String]?) async {
        providerError = nil

        do {
            // TODO: Implement ConnectProviderUseCase when ready
            throw DomainError.notImplemented("Provider connection not yet implemented in Clean Architecture")
        } catch let domainError as DomainError {
            providerError = domainError.localizedDescription
        } catch {
            providerError = error.localizedDescription
        }
    }

    /// Disconnect a provider
    func disconnectProvider(_ provider: ProviderInfo) async {
        providerError = nil

        do {
            // TODO: Implement DisconnectProviderUseCase when ready
            throw DomainError.notImplemented("Provider disconnection not yet implemented in Clean Architecture")
        } catch let domainError as DomainError {
            providerError = domainError.localizedDescription
        } catch {
            providerError = error.localizedDescription
        }
    }

    // MARK: - Private Methods

    private func loadMessages() async {
        guard let conversationId = currentConversationId else { return }

        isLoading = true

        do {
            let fetched = try await getMessagesUseCase.execute(
                conversationId: conversationId,
                before: nil,
                limit: pageSize
            )
            let ordered = fetched.sorted { $0.createdAt < $1.createdAt }
            messages = ordered
            oldestLoadedMessageDate = messages.first?.createdAt
            hasMoreHistory = fetched.count == pageSize
        } catch let domainError as DomainError {
            error = domainError.localizedDescription
            showError = true
        } catch {
            self.error = error.localizedDescription
            showError = true
        }

        isLoading = false
    }

    func loadMoreHistory() async {
        guard let conversationId = currentConversationId else { return }
        guard hasMoreHistory, !isLoadingMore else { return }

        isLoadingMore = true
        defer { isLoadingMore = false }

        do {
            let fetched = try await getMessagesUseCase.execute(
                conversationId: conversationId,
                before: oldestLoadedMessageDate,
                limit: pageSize
            )
            let ordered = fetched.sorted { $0.createdAt < $1.createdAt }
            if !ordered.isEmpty {
                messages.insert(contentsOf: ordered, at: 0)
                oldestLoadedMessageDate = messages.first?.createdAt
            }
            if fetched.count < pageSize {
                hasMoreHistory = false
            }
        } catch let domainError as DomainError {
            error = domainError.localizedDescription
            showError = true
        } catch {
            self.error = error.localizedDescription
            showError = true
        }
    }

    private func performCreateConversation() async {
        do {
            let conversation = try await createConversationUseCase.execute(
                title: "New Conversation",
                tools: Array(selectedTools)
            )
            currentConversationId = conversation.id
            messages = []
            resetPagination()
        } catch let domainError as DomainError {
            error = domainError.localizedDescription
            showError = true
        } catch {
            self.error = error.localizedDescription
            showError = true
        }
    }

    private func performSendMessage(_ text: String) async {
        AppConfig.shared.debugLog("🟣 performSendMessage called with: \(text)")

        // Create conversation if needed
        if currentConversationId == nil {
            AppConfig.shared.debugLog("🟣 No conversation ID, creating new conversation")
            await performCreateConversation()
        }

        guard let conversationId = currentConversationId else {
            AppConfig.shared.debugLog("🟣 ERROR: Still no conversation ID after creation")
            return
        }

        AppConfig.shared.debugLog("🟣 Using conversation ID: \(conversationId)")
        isSending = true

        // Add user message to UI immediately
        let userMessage = ChatMessage(
            conversationId: conversationId,
            content: text,
            role: .user
        )
        messages.append(userMessage)
        AppConfig.shared.debugLog("🟣 Added user message to UI, total messages: \(messages.count)")
        if oldestLoadedMessageDate == nil {
            oldestLoadedMessageDate = messages.first?.createdAt
        }

        do {
            AppConfig.shared.debugLog("🟣 Calling sendMessageUseCase.execute...")
            let response = try await sendMessageUseCase.execute(
                message: text,
                conversationId: conversationId,
                tools: Array(selectedTools),
                location: buildLocationDTO()
            )

            // Add AI response
            AppConfig.shared.debugLog("🟣 Got AI response: \(response.content.prefix(50))...")
            messages.append(response)
        AppConfig.shared.debugLog("🟣 Added AI response to UI, total messages: \(messages.count)")
        if oldestLoadedMessageDate == nil {
            oldestLoadedMessageDate = messages.first?.createdAt
        }

            // Check if AI needs location
            if response.metadata?.requiresLocation == true && userLocation == nil {
                pendingLocationMessage = text
                showLocationPrompt = true
                AppConfig.shared.debugLog("🟣 AI requires location, showing prompt")
            }
        } catch let domainError as DomainError {
            // Remove optimistic user message on error
            AppConfig.shared.debugLog("🟣 ERROR (DomainError): \(domainError.localizedDescription)")
            messages.removeLast()
            error = domainError.localizedDescription
            showError = true
        } catch {
            AppConfig.shared.debugLog("🟣 ERROR: \(error.localizedDescription)")
            messages.removeLast()
            self.error = error.localizedDescription
            showError = true
        }

        isSending = false
        AppConfig.shared.debugLog("🟣 performSendMessage completed")
    }

    private func resetPagination() {
        oldestLoadedMessageDate = nil
        hasMoreHistory = true
        isLoadingMore = false
    }
}

/// Curated tool catalog for WhatsApp + web chat parity.
enum ToolCatalog {
    static let curatedTools: [ToolInfo] = [
        // General + web tools
        ToolInfo(name: "chat", description: "General conversation and help", category: "general"),
        ToolInfo(name: "weather", description: "Get current weather for a city or location", category: "utility"),
        ToolInfo(name: "news", description: "Get the latest headlines and updates", category: "news"),
        ToolInfo(name: "image", description: "Generate AI images from text", category: "utility"),
        ToolInfo(name: "image_analysis", description: "Analyze images and describe contents", category: "utility"),
        ToolInfo(name: "local_search", description: "Find nearby places and services", category: "utility"),
        ToolInfo(name: "set_reminder", description: "Set a reminder for later", category: "utility"),
        ToolInfo(name: "reminder", description: "Create and manage reminders", category: "utility"),
        ToolInfo(name: "help", description: "See what the assistant can do", category: "general"),
        ToolInfo(name: "subscription", description: "Manage subscriptions and daily updates", category: "general"),
        ToolInfo(name: "db_query", description: "Run database-style queries", category: "utility"),

        // Astrology
        ToolInfo(name: "horoscope", description: "Daily horoscope for zodiac signs", category: "astrology"),
        ToolInfo(name: "kundli", description: "Generate kundli or birth chart insights", category: "astrology"),
        ToolInfo(name: "dosha", description: "Check dosha and related insights", category: "astrology"),
        ToolInfo(name: "dosha_check", description: "Check dosha and related insights", category: "astrology"),
        ToolInfo(name: "life_prediction", description: "Life prediction for career, marriage, and more", category: "astrology"),
        ToolInfo(name: "numerology", description: "Numerology analysis", category: "astrology"),
        ToolInfo(name: "panchang", description: "Hindu calendar and auspicious timings", category: "astrology"),
        ToolInfo(name: "tarot", description: "Tarot card readings", category: "astrology"),
        ToolInfo(name: "ask_astrologer", description: "Astrology guidance and Q&A", category: "astrology"),

        // Travel
        ToolInfo(name: "pnr_status", description: "Check Indian Railways PNR status", category: "travel"),
        ToolInfo(name: "train_status", description: "Live train running status", category: "travel"),
        ToolInfo(name: "metro_ticket", description: "Metro ticket info and booking guidance", category: "travel"),
        ToolInfo(name: "metro_info", description: "Metro schedules and fares", category: "travel"),

        // News + info
        ToolInfo(name: "cricket_score", description: "Live cricket scores and match info", category: "news"),
        ToolInfo(name: "fact_check", description: "Verify claims and check facts", category: "news"),
        ToolInfo(name: "event", description: "Upcoming events and festivals", category: "news"),

        // Government + schemes
        ToolInfo(name: "govt_jobs", description: "Government job updates and alerts", category: "govt"),
        ToolInfo(name: "govt_schemes", description: "Government schemes and benefits", category: "govt"),
        ToolInfo(name: "farmer_schemes", description: "Agriculture and farmer schemes", category: "govt"),
        ToolInfo(name: "free_audio_sources", description: "Free audio sources and listening links", category: "govt"),

        // Food + local
        ToolInfo(name: "food", description: "Recipes, nutrition, and food help", category: "food"),
        ToolInfo(name: "food_order", description: "Food ordering assistance", category: "food"),

        // Games
        ToolInfo(name: "word_game", description: "Play word games", category: "games"),
    ]

    static func mergedTools(from serverTools: [ToolInfo]) -> [ToolInfo] {
        var byName: [String: ToolInfo] = [:]
        for tool in serverTools {
            byName[tool.name.lowercased()] = tool
        }
        for tool in curatedTools {
            let key = tool.name.lowercased()
            if byName[key] == nil {
                byName[key] = tool
            }
        }
        let all = Array(byName.values)
        return all.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
    }
}
