import Foundation

/// Use case for creating a new conversation
protocol CreateConversationUseCaseProtocol: Sendable {
    func execute(title: String, tools: [String]) async throws -> ChatConversation
}

final class CreateConversationUseCase: CreateConversationUseCaseProtocol, @unchecked Sendable {
    private let conversationRepository: ConversationRepositoryProtocol

    init(conversationRepository: ConversationRepositoryProtocol) {
        self.conversationRepository = conversationRepository
    }

    func execute(title: String, tools: [String]) async throws -> ChatConversation {
        let finalTitle = title.isEmpty ? "New Conversation" : title
        return try await conversationRepository.createConversation(title: finalTitle, tools: tools)
    }
}
