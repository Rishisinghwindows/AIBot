import Foundation
import SwiftData

/// Chat message stored locally
@Model
final class Message {
    /// Unique identifier
    var id: UUID

    /// Conversation this message belongs to
    var conversationId: UUID

    /// Role: "user" or "assistant"
    var role: String

    /// Message content
    var content: String

    /// Additional metadata from the AI response
    var category: String?

    /// When the message was created
    var createdAt: Date

    /// Whether this message has been synced with the server
    var isSynced: Bool

    /// Inverse relationship to conversation
    var conversation: Conversation?

    init(
        id: UUID = UUID(),
        conversationId: UUID,
        role: String,
        content: String,
        category: String? = nil,
        createdAt: Date = Date(),
        isSynced: Bool = false
    ) {
        self.id = id
        self.conversationId = conversationId
        self.role = role
        self.content = content
        self.category = category
        self.createdAt = createdAt
        self.isSynced = isSynced
    }

    /// Whether this is a user message
    var isUser: Bool {
        role == "user"
    }

    /// Whether this is an assistant message
    var isAssistant: Bool {
        role == "assistant"
    }
}

// MARK: - DisplayableMessage Conformance

extension Message: DisplayableMessage {
    var displayCategory: String? {
        category
    }

    var displaySynced: Bool {
        isSynced
    }
}

// MARK: - Factory Methods

extension Message {
    /// Create a user message
    static func userMessage(
        conversationId: UUID,
        content: String
    ) -> Message {
        Message(
            conversationId: conversationId,
            role: "user",
            content: content
        )
    }

    /// Create an assistant message
    static func assistantMessage(
        conversationId: UUID,
        content: String,
        category: String? = nil
    ) -> Message {
        Message(
            conversationId: conversationId,
            role: "assistant",
            content: content,
            category: category
        )
    }

    /// Create from API response
    static func from(response: ChatMessageResponse, conversationId: UUID) -> Message {
        Message(
            id: response.id,
            conversationId: conversationId,
            role: response.role,
            content: response.content,
            category: response.metadata?["category"],
            createdAt: response.createdAt,
            isSynced: true
        )
    }
}
