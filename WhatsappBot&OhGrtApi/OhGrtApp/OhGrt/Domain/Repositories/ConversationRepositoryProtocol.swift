import Foundation
import Combine

/// Protocol defining conversation repository operations (local storage)
protocol ConversationRepositoryProtocol: Sendable {
    /// Publisher for all conversations
    var conversationsPublisher: AnyPublisher<[ChatConversation], Never> { get }

    /// Get all conversations
    /// - Returns: List of conversations sorted by updatedAt
    /// - Throws: DomainError on failure
    func getAllConversations() async throws -> [ChatConversation]

    /// Get a specific conversation by ID
    /// - Parameter id: Conversation ID
    /// - Returns: Conversation if found
    /// - Throws: DomainError.notFound if not found
    func getConversation(id: UUID) async throws -> ChatConversation

    /// Create a new conversation
    /// - Parameter title: Conversation title
    /// - Returns: Created conversation
    /// - Throws: DomainError on failure
    func createConversation(title: String, tools: [String]) async throws -> ChatConversation

    /// Update conversation
    /// - Parameter conversation: Updated conversation
    /// - Throws: DomainError on failure
    func updateConversation(_ conversation: ChatConversation) async throws

    /// Delete a conversation
    /// - Parameter id: Conversation ID to delete
    /// - Throws: DomainError on failure
    func deleteConversation(id: UUID) async throws

    /// Get messages for a conversation
    /// - Parameter conversationId: Conversation ID
    /// - Returns: List of messages sorted by createdAt
    /// - Throws: DomainError on failure
    func getMessages(conversationId: UUID) async throws -> [ChatMessage]

    /// Get messages for a conversation with pagination
    /// - Parameters:
    ///   - conversationId: Conversation ID
    ///   - before: Load messages created before this date (for pagination)
    ///   - limit: Maximum number of messages to return
    /// - Returns: List of messages sorted by createdAt (newest first)
    /// - Throws: DomainError on failure
    func getMessages(conversationId: UUID, before: Date?, limit: Int) async throws -> [ChatMessage]

    /// Save a message to local storage
    /// - Parameter message: Message to save
    /// - Throws: DomainError on failure
    func saveMessage(_ message: ChatMessage) async throws

    /// Delete all messages in a conversation
    /// - Parameter conversationId: Conversation ID
    /// - Throws: DomainError on failure
    func deleteMessages(conversationId: UUID) async throws
}
