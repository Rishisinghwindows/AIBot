import Foundation

/// Domain entity representing a chat conversation
struct ChatConversation: Identifiable, Equatable, Hashable, Sendable {
    let id: UUID
    let title: String
    let createdAt: Date
    let updatedAt: Date
    let messageCount: Int
    let lastMessagePreview: String?
    let tools: [String]

    init(
        id: UUID = UUID(),
        title: String,
        createdAt: Date = Date(),
        updatedAt: Date = Date(),
        messageCount: Int = 0,
        lastMessagePreview: String? = nil,
        tools: [String] = []
    ) {
        self.id = id
        self.title = title
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.messageCount = messageCount
        self.lastMessagePreview = lastMessagePreview
        self.tools = tools
    }
}

/// Tool information for chat
struct Tool: Identifiable, Equatable, Sendable {
    let id: String
    let name: String
    let description: String
    let category: ToolCategory

    var identifier: String { id }
}

enum ToolCategory: String, Codable, Sendable {
    case search
    case utility
    case integration
    case astrology
    case travel
    case unknown
}

/// Provider information (MCP/External sources)
struct Provider: Identifiable, Equatable, Sendable {
    let id: String
    let name: String
    let displayName: String
    let authType: String
    let isConnected: Bool
    let iconName: String?

    /// Backward compatibility alias for isConnected
    var connected: Bool { isConnected }
}
