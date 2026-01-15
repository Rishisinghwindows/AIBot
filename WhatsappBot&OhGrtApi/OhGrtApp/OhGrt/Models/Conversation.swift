import Foundation
import SwiftData

/// A chat conversation containing multiple messages
@Model
final class Conversation {
    /// Unique identifier
    var id: UUID

    /// Conversation title (derived from first message)
    var title: String?

    /// When the conversation was created
    var createdAt: Date

    /// When the conversation was last updated
    var updatedAt: Date

    /// Messages in this conversation
    @Relationship(deleteRule: .cascade, inverse: \Message.conversation)
    var messages: [Message]

    /// Enabled tools for this conversation
    var tools: [String]

    init(
        id: UUID = UUID(),
        title: String? = nil,
        createdAt: Date = Date(),
        tools: [String] = []
    ) {
        self.id = id
        self.title = title
        self.createdAt = createdAt
        self.updatedAt = createdAt
        self.messages = []
        self.tools = tools
    }

    /// Number of messages in this conversation
    var messageCount: Int {
        messages.count
    }

    /// The most recent message
    var lastMessage: Message? {
        messages.sorted { $0.createdAt > $1.createdAt }.first
    }

    /// Preview text for conversation list
    var preview: String {
        if let last = lastMessage {
            let prefix = last.isUser ? "You: " : ""
            let content = last.content
            if content.count > 50 {
                return prefix + String(content.prefix(50)) + "..."
            }
            return prefix + content
        }
        return "No messages"
    }

    /// Update the title from the first user message
    func updateTitleIfNeeded() {
        guard title == nil else { return }

        let firstUserMessage = messages
            .filter { $0.isUser }
            .sorted { $0.createdAt < $1.createdAt }
            .first

        if let message = firstUserMessage {
            let content = message.content
            title = content.count > 40 ? String(content.prefix(40)) + "..." : content
        }
    }

    /// Mark as updated
    func markUpdated() {
        updatedAt = Date()
    }
}

// MARK: - Factory Methods

extension Conversation {
    /// Create from API summary
    static func from(summary: ConversationSummary) -> Conversation {
        Conversation(
            id: summary.id,
            title: summary.title,
            createdAt: summary.createdAt
        )
    }
}
