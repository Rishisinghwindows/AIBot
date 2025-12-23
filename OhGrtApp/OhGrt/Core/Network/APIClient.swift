import Foundation
import os.log

private let logger = Logger(subsystem: "com.d23.OhGrt", category: "APIClient")

/// Main API client for communicating with the backend
@MainActor
class APIClient {
    /// Shared singleton instance
    static let shared = APIClient()

    /// Base URL for the API
    private let baseURL: URL

    /// URLSession with SSL pinning
    private let session: URLSession

    /// Request interceptor for headers and auth
    private let interceptor: RequestInterceptor

    /// JSON decoder with date handling
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)

            // Try ISO8601 with fractional seconds
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            if let date = formatter.date(from: dateString) {
                return date
            }

            // Try without fractional seconds
            formatter.formatOptions = [.withInternetDateTime]
            if let date = formatter.date(from: dateString) {
                return date
            }

            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Cannot decode date: \(dateString)"
            )
        }
        return decoder
    }()

    /// JSON encoder
    private let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        return encoder
    }()

    /// Flag to prevent infinite refresh loops
    private var isRefreshing = false

    /// Maximum retry attempts for transient failures
    private let maxRetryAttempts: Int

    private init() {
        // Use environment-based configuration
        self.baseURL = AppConfig.shared.apiBaseURL
        self.maxRetryAttempts = AppConfig.shared.maxRetryAttempts

        // Use SSL pinning session with configured timeout
        self.session = URLSession.pinnedSession(timeoutInterval: AppConfig.shared.requestTimeout)
        self.interceptor = RequestInterceptor()

        AppConfig.shared.debugLog("APIClient initialized with base URL: \(baseURL)")
    }

    /// Calculate delay for exponential backoff
    private func retryDelay(attempt: Int) -> UInt64 {
        // Exponential backoff: 1s, 2s, 4s, etc. with jitter
        let baseDelay = pow(2.0, Double(attempt))
        let jitter = Double.random(in: 0...0.5)
        let delaySeconds = min(baseDelay + jitter, 30.0) // Max 30 seconds
        return UInt64(delaySeconds * 1_000_000_000)
    }

    /// Check if an error is retryable
    private func isRetryableError(_ error: Error) -> Bool {
        if let urlError = error as? URLError {
            switch urlError.code {
            case .timedOut, .networkConnectionLost, .notConnectedToInternet:
                return true
            default:
                return false
            }
        }
        return false
    }

    /// Check if an HTTP status code is retryable
    private func isRetryableStatus(_ statusCode: Int) -> Bool {
        // Retry on server errors (5xx) except 501 (Not Implemented)
        return statusCode >= 500 && statusCode != 501
    }

    /// Make an API request with automatic retry for transient failures
    /// - Parameters:
    ///   - endpoint: The API endpoint
    ///   - body: Optional request body (Encodable)
    ///   - requiresAuth: Whether auth is required (defaults to endpoint's setting)
    ///   - retryCount: Current retry attempt (internal use)
    /// - Returns: Decoded response
    func request<T: Decodable>(
        endpoint: APIEndpoint,
        body: (any Encodable)? = nil,
        requiresAuth: Bool? = nil,
        retryCount: Int = 0
    ) async throws -> T {
        // Check network connectivity before making request
        if !OfflineManager.shared.isOnline {
            logger.warning("Network unavailable for request to \(endpoint.path)")

            // Check if this request type can be queued for later
            if let encodedBody = try? body.flatMap({ try encoder.encode($0) }),
               OfflineManager.shared.shouldQueueRequest(endpoint: endpoint.path) {
                OfflineManager.shared.queueRequest(
                    endpoint: endpoint.path,
                    method: endpoint.method.rawValue,
                    body: encodedBody
                )
                throw APIError.offline(queued: true)
            }

            throw APIError.offline(queued: false)
        }

        let authRequired = requiresAuth ?? endpoint.requiresAuth

        // Build URL
        let url = baseURL.appendingPathComponent(endpoint.path)
        var request = URLRequest(url: url)
        request.httpMethod = endpoint.method.rawValue

        // Encode body if provided, or use empty JSON for POST/PUT
        if let body = body {
            do {
                request.httpBody = try encoder.encode(body)
            } catch {
                throw APIError.encodingError(error)
            }
        } else if endpoint.method == .post || endpoint.method == .put {
            // Some servers require a body for POST/PUT requests
            request.httpBody = "{}".data(using: .utf8)
        }

        // Add headers via interceptor
        do {
            request = try await interceptor.intercept(request, requiresAuth: authRequired)
        } catch {
            throw error
        }

        // Log request
        AppConfig.shared.debugLog("📤 REQUEST: \(endpoint.method.rawValue) \(url.absoluteString)")
        if let body = request.httpBody, let bodyString = String(data: body, encoding: .utf8) {
            AppConfig.shared.debugLog("📤 BODY: \(bodyString)")
        }

        // Make request with retry logic
        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            // Check if we should retry network errors
            if isRetryableError(error) && retryCount < maxRetryAttempts {
                AppConfig.shared.debugLog("Retrying request after network error (attempt \(retryCount + 1))")
                try await Task.sleep(nanoseconds: retryDelay(attempt: retryCount))
                return try await self.request(
                    endpoint: endpoint,
                    body: body,
                    requiresAuth: authRequired,
                    retryCount: retryCount + 1
                )
            }
            throw APIError.networkError(error)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        // Log response
        let responseString = String(data: data, encoding: .utf8) ?? "Unable to decode"
        AppConfig.shared.debugLog("📥 RESPONSE [\(httpResponse.statusCode)]: \(responseString)")

        // Handle 401 - try token refresh once
        if httpResponse.statusCode == 401 && authRequired && !isRefreshing {
            isRefreshing = true
            defer { isRefreshing = false }

            do {
                try await TokenRefresher.shared.refreshIfNeeded()
                // Retry the request (don't count this as a retry attempt)
                return try await self.request(endpoint: endpoint, body: body, requiresAuth: authRequired, retryCount: 0)
            } catch {
                throw APIError.tokenExpired
            }
        }

        // Check for retryable server errors
        if isRetryableStatus(httpResponse.statusCode) && retryCount < maxRetryAttempts {
            AppConfig.shared.debugLog("Retrying request after server error \(httpResponse.statusCode) (attempt \(retryCount + 1))")
            try await Task.sleep(nanoseconds: retryDelay(attempt: retryCount))
            return try await self.request(
                endpoint: endpoint,
                body: body,
                requiresAuth: authRequired,
                retryCount: retryCount + 1
            )
        }

        // Check for errors
        guard (200...299).contains(httpResponse.statusCode) else {
            // Try to decode error message
            if let errorResponse = try? decoder.decode(ServerErrorResponse.self, from: data) {
                throw APIError.serverError(message: errorResponse.errorMessage)
            }
            throw APIError.httpError(statusCode: httpResponse.statusCode, data: data)
        }

        // Decode response
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    /// Make a request without expecting a response body
    func requestVoid(
        endpoint: APIEndpoint,
        body: (any Encodable)? = nil,
        requiresAuth: Bool? = nil
    ) async throws {
        let _: EmptyResponse = try await request(endpoint: endpoint, body: body, requiresAuth: requiresAuth)
    }
}

/// Empty response for endpoints that don't return data
struct EmptyResponse: Decodable {}

// MARK: - Convenience Methods

extension APIClient {
    /// Send a chat message
    func sendMessage(
        _ message: String,
        conversationId: UUID? = nil,
        tools: [String]? = nil
    ) async throws -> ChatSendResponse {
        let request = ChatSendRequest(message: message, conversationId: conversationId, tools: tools)
        return try await self.request(endpoint: .chatSend, body: request)
    }

    /// Get chat history
    func getChatHistory(conversationId: String? = nil, limit: Int = 50) async throws -> ChatHistoryResponse {
        let historyURL = baseURL.appendingPathComponent("/chat/history")
        guard var urlComponents = URLComponents(string: historyURL.absoluteString) else {
            throw APIError.invalidURL
        }

        var queryItems: [URLQueryItem] = [URLQueryItem(name: "limit", value: String(limit))]
        if let convId = conversationId {
            queryItems.append(URLQueryItem(name: "conversation_id", value: convId))
        }
        urlComponents.queryItems = queryItems

        guard let url = urlComponents.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = HTTPMethod.get.rawValue

        request = try await interceptor.intercept(request, requiresAuth: true)

        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIError.networkError(error)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            if let errorResponse = try? decoder.decode(ServerErrorResponse.self, from: data) {
                throw APIError.serverError(message: errorResponse.errorMessage)
            }
            throw APIError.httpError(statusCode: httpResponse.statusCode, data: data)
        }

        return try decoder.decode(ChatHistoryResponse.self, from: data)
    }

    /// Get conversations list
    func getConversations(limit: Int = 20) async throws -> [ConversationSummary] {
        return try await request(endpoint: .conversations)
    }

    /// List available tools
    func getTools() async throws -> [ToolInfo] {
        return try await request(endpoint: .tools)
    }

    /// List external providers
    func getProviders() async throws -> [ProviderInfo] {
        return try await request(endpoint: .providers)
    }

    /// Start GitHub OAuth
    func startGitHubOAuth() async throws -> OAuthStartResponse {
        return try await request(endpoint: .githubOAuthStart)
    }

    /// Exchange GitHub OAuth code
    func exchangeGitHubOAuth(code: String, state: String) async throws -> ProviderInfo {
        let body = OAuthExchangeRequest(code: code, state: state)
        return try await request(endpoint: .githubOAuthExchange, body: body)
    }

    /// Start OAuth for any provider (reuses GitHub endpoint when applicable)
    func startProviderOAuth(provider: String) async throws -> OAuthStartResponse {
        if provider.lowercased() == "github" {
            return try await startGitHubOAuth()
        }
        return try await request(endpoint: .providerOAuthStart(provider: provider))
    }

    /// Exchange OAuth code for any provider (reuses GitHub endpoint when applicable)
    func exchangeProviderOAuth(provider: String, code: String, state: String) async throws -> ProviderInfo {
        if provider.lowercased() == "github" {
            return try await exchangeGitHubOAuth(code: code, state: state)
        }
        let body = OAuthExchangeRequest(code: code, state: state)
        return try await request(endpoint: .providerOAuthExchange(provider: provider), body: body)
    }

    /// Connect to a provider
    func connectProvider(_ payload: ProviderConnectRequest) async throws -> ProviderInfo {
        return try await request(endpoint: .connectProvider, body: payload)
    }

    /// Disconnect a provider
    func disconnectProvider(_ provider: String) async throws {
        try await requestVoid(endpoint: .disconnectProvider(provider: provider))
    }

    /// Authenticate with Google/Firebase
    func authenticateWithGoogle(firebaseToken: String, deviceInfo: String?) async throws -> TokenResponse {
        let request = GoogleAuthRequest(firebaseIdToken: firebaseToken, deviceInfo: deviceInfo)
        return try await self.request(endpoint: .googleAuth, body: request, requiresAuth: false)
    }

    /// Refresh access token
    func refreshAccessToken(refreshToken: String) async throws -> TokenResponse {
        let request = RefreshTokenRequest(refreshToken: refreshToken)
        return try await self.request(endpoint: .refreshToken, body: request, requiresAuth: false)
    }

    /// Get user's birth details
    func getBirthDetails() async throws -> BirthDetailsResponse? {
        do {
            return try await request(endpoint: .birthDetails)
        } catch let error as APIError {
            // Return nil if not found (404)
            if case .httpError(let statusCode, _) = error, statusCode == 404 {
                return nil
            }
            throw error
        }
    }

    /// Save user's birth details
    func saveBirthDetails(_ details: BirthDetailsRequest) async throws -> BirthDetailsResponse {
        return try await request(endpoint: .saveBirthDetails, body: details)
    }

    /// Delete user's birth details
    func deleteBirthDetails() async throws {
        try await requestVoid(endpoint: .deleteBirthDetails)
    }

    // MARK: - Web Session (Anonymous, for development)

    /// Create a new anonymous web session
    func createWebSession() async throws -> WebSessionResponse {
        return try await request(endpoint: .webSession)
    }

    /// Send a message using web session (no auth required)
    func sendWebMessage(_ message: String, sessionId: String, language: String? = nil) async throws -> WebChatResponse {
        let request = WebChatRequest(message: message, sessionId: sessionId, language: language)
        return try await self.request(endpoint: .webChat, body: request)
    }

    /// Get web chat history
    func getWebChatHistory(sessionId: String) async throws -> WebChatHistoryResponse {
        return try await request(endpoint: .webChatHistory(sessionId: sessionId))
    }

    // MARK: - Profile

    /// Get current user profile
    func getProfile() async throws -> UserResponse {
        return try await request(endpoint: .me)
    }

    /// Update user profile
    func updateProfile(_ profile: ProfileUpdateRequest) async throws -> UserResponse {
        return try await request(endpoint: .updateProfile, body: profile)
    }

    // MARK: - Personas

    /// Get all user's personas
    func getPersonas() async throws -> [PersonaResponse] {
        return try await request(endpoint: .personas)
    }

    /// Create a new persona
    func createPersona(_ request: PersonaCreateRequest) async throws -> PersonaResponse {
        return try await self.request(endpoint: .createPersona, body: request)
    }

    /// Get a persona by ID
    func getPersona(id: String) async throws -> PersonaResponse {
        return try await request(endpoint: .persona(id: id))
    }

    /// Update a persona
    func updatePersona(id: String, request: PersonaUpdateRequest) async throws -> PersonaResponse {
        return try await self.request(endpoint: .updatePersona(id: id), body: request)
    }

    /// Delete a persona
    func deletePersona(id: String) async throws {
        try await requestVoid(endpoint: .deletePersona(id: id))
    }

    /// Check if a handle is available
    func checkHandle(_ handle: String) async throws -> HandleCheckResponse {
        return try await request(endpoint: .checkHandle(handle: handle), requiresAuth: false)
    }

    /// Get persona documents
    func getPersonaDocuments(personaId: String) async throws -> [PersonaDocumentResponse] {
        return try await request(endpoint: .personaDocuments(personaId: personaId))
    }

    /// Delete a persona document
    func deletePersonaDocument(personaId: String, docId: String) async throws {
        try await requestVoid(endpoint: .deletePersonaDocument(personaId: personaId, docId: docId))
    }

    // MARK: - Public Persona Chat

    /// Get public persona profile
    func getPublicPersona(handle: String) async throws -> PersonaPublicResponse {
        return try await request(endpoint: .publicPersona(handle: handle), requiresAuth: false)
    }

    /// Chat with a public persona
    func chatWithPersona(handle: String, request: PersonaChatRequest) async throws -> PersonaChatResponse {
        return try await self.request(endpoint: .publicPersonaChat(handle: handle), body: request, requiresAuth: false)
    }

    /// Get persona chat history
    func getPersonaChatHistory(handle: String, sessionId: String) async throws -> PersonaChatHistoryResponse {
        return try await request(endpoint: .publicPersonaChatHistory(handle: handle, sessionId: sessionId), requiresAuth: false)
    }
}
