import Foundation

/// Domain entity representing a chat message
struct ChatMessage: Identifiable, Equatable, Sendable {
    let id: UUID
    let conversationId: UUID
    let content: String
    let role: MessageRole
    let createdAt: Date
    let metadata: MessageMetadata?

    /// Whether the message has been synced to the server (for optimistic updates)
    var isSynced: Bool = true

    init(
        id: UUID = UUID(),
        conversationId: UUID,
        content: String,
        role: MessageRole,
        createdAt: Date = Date(),
        metadata: MessageMetadata? = nil,
        isSynced: Bool = true
    ) {
        self.id = id
        self.conversationId = conversationId
        self.content = content
        self.role = role
        self.createdAt = createdAt
        self.metadata = metadata
        self.isSynced = isSynced
    }

    /// Convenience property to check if this is a user message
    var isUser: Bool {
        role == .user
    }

    /// Convenience property to check if this is an assistant message
    var isAssistant: Bool {
        role == .assistant
    }
}

/// Message role (user or assistant)
enum MessageRole: String, Codable, Sendable {
    case user
    case assistant
    case system
}

/// Additional metadata for messages
struct MessageMetadata: Equatable, Sendable {
    let toolsUsed: [String]?
    let processingTime: TimeInterval?
    let modelUsed: String?
    let category: String?
    let mediaUrl: String?
    let requiresLocation: Bool?

    init(
        toolsUsed: [String]? = nil,
        processingTime: TimeInterval? = nil,
        modelUsed: String? = nil,
        category: String? = nil,
        mediaUrl: String? = nil,
        requiresLocation: Bool? = nil
    ) {
        self.toolsUsed = toolsUsed
        self.processingTime = processingTime
        self.modelUsed = modelUsed
        self.category = category
        self.mediaUrl = mediaUrl
        self.requiresLocation = requiresLocation
    }
}
