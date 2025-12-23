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
    private var cancellables = Set<AnyCancellable>()
    private var modelContext: ModelContext?

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
            messages = try await getMessagesUseCase.execute(conversationId: conversationId)
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
            availableTools = tools.map { tool in
                ToolInfo(name: tool.name, description: tool.description)
            }
        } catch let domainError as DomainError {
            toolsError = domainError.localizedDescription
        } catch {
            toolsError = error.localizedDescription
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
            messages = try await getMessagesUseCase.execute(conversationId: conversationId)
        } catch let domainError as DomainError {
            error = domainError.localizedDescription
            showError = true
        } catch {
            self.error = error.localizedDescription
            showError = true
        }

        isLoading = false
    }

    private func performCreateConversation() async {
        do {
            let conversation = try await createConversationUseCase.execute(
                title: "New Conversation",
                tools: Array(selectedTools)
            )
            currentConversationId = conversation.id
            messages = []
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
}
