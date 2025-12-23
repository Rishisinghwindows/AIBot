import Foundation

/// Protocol for remote chat data source
protocol ChatRemoteDataSourceProtocol: Sendable {
    func sendMessage(_ request: ChatRequestDTO) async throws -> ChatResponseDTO
    func streamMessage(_ request: ChatRequestDTO) -> AsyncThrowingStream<String, Error>
    func getTools() async throws -> ToolsResponseDTO
    func getProviders() async throws -> ProvidersResponseDTO
    func connectProvider(_ providerId: String) async throws
    func disconnectProvider(_ providerId: String) async throws
}

/// Web session response DTO
/// Note: APIClient uses .convertFromSnakeCase, so no CodingKeys needed
private struct WebSessionResponseDTO: Codable {
    let sessionId: String
    let expiresAt: String
    let language: String
}

/// Web chat request DTO
/// Note: APIClient uses .convertToSnakeCase for encoding
private struct WebChatRequestDTO: Codable {
    let message: String
    let sessionId: String
    let language: String?
    let location: LocationDTO?
}

/// Web chat response DTO
private struct WebChatResponseDTO: Codable {
    let userMessage: WebMessageDTO
    let assistantMessage: WebMessageDTO
    let detectedLanguage: String
    let requiresLocation: Bool?
}

/// Web message DTO
private struct WebMessageDTO: Codable {
    let id: String
    let role: String
    let content: String
    let timestamp: String
    let language: String
    let mediaUrl: String?
}

/// Remote data source for chat operations
final class ChatRemoteDataSource: ChatRemoteDataSourceProtocol, @unchecked Sendable {
    private let apiClient: APIClient

    /// Cached web session ID for development mode
    private static var webSessionId: String?

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    /// Check if we have a valid auth token
    private func hasAuthToken() async -> Bool {
        do {
            let token = try await KeychainManager.shared.getAccessToken()
            return token != nil
        } catch {
            return false
        }
    }

    /// Get or create a web session for anonymous chat
    private func getWebSessionId() async throws -> String {
        // Return cached session if available
        if let sessionId = ChatRemoteDataSource.webSessionId {
            return sessionId
        }

        // Create new web session (empty body)
        let response: WebSessionResponseDTO = try await apiClient.request(
            endpoint: .webSession
        )

        ChatRemoteDataSource.webSessionId = response.sessionId
        AppConfig.shared.debugLog("Created web session: \(response.sessionId)")
        return response.sessionId
    }

    func sendMessage(_ request: ChatRequestDTO) async throws -> ChatResponseDTO {
        AppConfig.shared.debugLog("🔵 sendMessage called with: \(request.message)")

        // In development mode without auth, use web chat endpoint
        if AppConfig.shared.isDevelopment {
            let hasToken = await hasAuthToken()
            AppConfig.shared.debugLog("🔵 Development mode, hasToken: \(hasToken)")
            if !hasToken {
                AppConfig.shared.debugLog("🔵 Using web chat endpoint")
                return try await sendWebMessage(request)
            }
        }

        // Use authenticated endpoint
        AppConfig.shared.debugLog("🔵 Using authenticated chat endpoint")
        let response: ChatResponseDTO = try await apiClient.request(
            endpoint: .chatSend,
            body: request
        )

        return response
    }

    /// Send message using anonymous web chat endpoint
    private func sendWebMessage(_ request: ChatRequestDTO) async throws -> ChatResponseDTO {
        AppConfig.shared.debugLog("🟢 sendWebMessage called")
        let sessionId = try await getWebSessionId()
        AppConfig.shared.debugLog("🟢 Got session ID: \(sessionId)")

        let webRequest = WebChatRequestDTO(
            message: request.message,
            sessionId: sessionId,
            language: nil,
            location: request.location
        )

        AppConfig.shared.debugLog("🟢 Sending web chat request...")
        let response: WebChatResponseDTO = try await apiClient.request(
            endpoint: .webChat,
            body: webRequest
        )
        AppConfig.shared.debugLog("🟢 Got response: \(response.assistantMessage.content)")

        // Convert web response to standard chat response
        return ChatResponseDTO(
            id: response.assistantMessage.id,
            content: response.assistantMessage.content,
            role: response.assistantMessage.role,
            createdAt: response.assistantMessage.timestamp,
            toolsUsed: nil,
            processingTime: nil,
            modelUsed: nil,
            mediaUrl: response.assistantMessage.mediaUrl,
            requiresLocation: response.requiresLocation
        )
    }

    func streamMessage(_ request: ChatRequestDTO) -> AsyncThrowingStream<String, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    // For now, fallback to regular request
                    // TODO: Implement SSE streaming
                    let response: ChatResponseDTO = try await apiClient.request(
                        endpoint: .chatSend,
                        body: request
                    )

                    continuation.yield(response.content)
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }

    func getTools() async throws -> ToolsResponseDTO {
        do {
            // Try authenticated endpoint first
            let response: ToolsResponseDTO = try await apiClient.request(
                endpoint: .tools
            )
            return response
        } catch {
            // Fall back to public endpoint for anonymous users
            AppConfig.shared.debugLog("🔧 Falling back to public tools endpoint")
            let response: ToolsResponseDTO = try await apiClient.request(
                endpoint: .webTools
            )
            return response
        }
    }

    func getProviders() async throws -> ProvidersResponseDTO {
        do {
            // Try authenticated endpoint first
            let response: ProvidersResponseDTO = try await apiClient.request(
                endpoint: .providers
            )
            return response
        } catch {
            // Fall back to public endpoint for anonymous users
            AppConfig.shared.debugLog("🔧 Falling back to public providers endpoint")
            let response: ProvidersResponseDTO = try await apiClient.request(
                endpoint: .webProviders
            )
            return response
        }
    }

    func connectProvider(_ providerId: String) async throws {
        let _: EmptyResponse = try await apiClient.request(
            endpoint: .connectProvider
        )
    }

    func disconnectProvider(_ providerId: String) async throws {
        let _: EmptyResponse = try await apiClient.request(
            endpoint: .disconnectProvider(provider: providerId)
        )
    }
}
