import Foundation

/// Use case for deleting a conversation
protocol DeleteConversationUseCaseProtocol: Sendable {
    func execute(conversationId: UUID) async throws
}

final class DeleteConversationUseCase: DeleteConversationUseCaseProtocol, @unchecked Sendable {
    private let conversationRepository: ConversationRepositoryProtocol

    init(conversationRepository: ConversationRepositoryProtocol) {
        self.conversationRepository = conversationRepository
    }

    func execute(conversationId: UUID) async throws {
        // Delete all messages first
        try await conversationRepository.deleteMessages(conversationId: conversationId)
        // Then delete the conversation
        try await conversationRepository.deleteConversation(id: conversationId)
    }
}
