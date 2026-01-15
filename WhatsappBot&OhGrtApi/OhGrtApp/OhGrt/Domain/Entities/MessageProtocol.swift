import Foundation

/// Protocol for message display - enables both SwiftData Message and domain ChatMessage to be used in views
protocol DisplayableMessage {
    var id: UUID { get }
    var content: String { get }
    var createdAt: Date { get }
    var isUser: Bool { get }
    var isAssistant: Bool { get }
    var displayCategory: String? { get }
    var displayMediaURL: String? { get }
    var displayStructuredDataJSON: String? { get }
    var displaySynced: Bool { get }
}

// MARK: - ChatMessage Conformance

extension ChatMessage: DisplayableMessage {
    var displayCategory: String? {
        metadata?.category
    }

    var displayMediaURL: String? {
        metadata?.mediaUrl
    }

    var displayStructuredDataJSON: String? {
        metadata?.structuredDataJSON
    }

    var displaySynced: Bool {
        isSynced
    }
}
