import Foundation
import Combine

/// Implementation of ConversationRepositoryProtocol
@MainActor
final class ConversationRepository: ConversationRepositoryProtocol {
    private let localDataSource: ConversationLocalDataSourceProtocol

    var conversationsPublisher: AnyPublisher<[ChatConversation], Never> {
        localDataSource.conversationsPublisher
    }

    nonisolated init(localDataSource: ConversationLocalDataSourceProtocol) {
        self.localDataSource = localDataSource
    }

    nonisolated func getAllConversations() async throws -> [ChatConversation] {
        try await MainActor.run {
            try localDataSource.getAllConversations()
        }
    }

    nonisolated func getConversation(id: UUID) async throws -> ChatConversation {
        try await MainActor.run {
            guard let conversation = try localDataSource.getConversation(id: id) else {
                throw DomainError.conversationNotFound
            }
            return conversation
        }
    }

    nonisolated func createConversation(title: String, tools: [String]) async throws -> ChatConversation {
        try await MainActor.run {
            let conversation = ChatConversation(
                title: title,
                tools: tools
            )
            try localDataSource.saveConversation(conversation)
            return conversation
        }
    }

    nonisolated func updateConversation(_ conversation: ChatConversation) async throws {
        try await MainActor.run {
            try localDataSource.saveConversation(conversation)
        }
    }

    nonisolated func deleteConversation(id: UUID) async throws {
        try await MainActor.run {
            try localDataSource.deleteConversation(id: id)
        }
    }

    nonisolated func getMessages(conversationId: UUID) async throws -> [ChatMessage] {
        try await MainActor.run {
            try localDataSource.getMessages(conversationId: conversationId)
        }
    }

    nonisolated func getMessages(conversationId: UUID, before: Date?, limit: Int) async throws -> [ChatMessage] {
        try await MainActor.run {
            try localDataSource.getMessages(conversationId: conversationId, before: before, limit: limit)
        }
    }

    nonisolated func saveMessage(_ message: ChatMessage) async throws {
        try await MainActor.run {
            try localDataSource.saveMessage(message)
        }
    }

    nonisolated func deleteMessages(conversationId: UUID) async throws {
        try await MainActor.run {
            try localDataSource.deleteMessages(conversationId: conversationId)
        }
    }
}
