import Foundation
import Combine

/// Protocol defining chat repository operations
protocol ChatRepositoryProtocol: Sendable {
    /// Send a message and get AI response
    /// - Parameters:
    ///   - message: User message content
    ///   - conversationId: Conversation ID
    ///   - tools: Selected tools for this message
    ///   - location: Optional user location
    /// - Returns: AI response message
    /// - Throws: DomainError on failure
    func sendMessage(
        _ message: String,
        conversationId: UUID,
        tools: [String],
        location: LocationDTO?
    ) async throws -> ChatMessage

    /// Stream AI response for a message
    /// - Parameters:
    ///   - message: User message content
    ///   - conversationId: Conversation ID
    ///   - tools: Selected tools
    /// - Returns: AsyncThrowingStream of response chunks
    func streamMessage(
        _ message: String,
        conversationId: UUID,
        tools: [String]
    ) -> AsyncThrowingStream<String, Error>

    /// Get available tools from server
    /// - Returns: List of available tools
    /// - Throws: DomainError on failure
    func getAvailableTools() async throws -> [Tool]

    /// Get available providers (MCP/external sources)
    /// - Returns: List of providers
    /// - Throws: DomainError on failure
    func getProviders() async throws -> [Provider]

    /// Connect to a provider
    /// - Parameter providerId: Provider ID to connect
    /// - Throws: DomainError on failure
    func connectProvider(_ providerId: String) async throws

    /// Disconnect from a provider
    /// - Parameter providerId: Provider ID to disconnect
    /// - Throws: DomainError on failure
    func disconnectProvider(_ providerId: String) async throws
}
