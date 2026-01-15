import Foundation

/// Use case for getting messages in a conversation
protocol GetMessagesUseCaseProtocol: Sendable {
    func execute(conversationId: UUID, before: Date?, limit: Int) async throws -> [ChatMessage]
}

final class GetMessagesUseCase: GetMessagesUseCaseProtocol, @unchecked Sendable {
    private let conversationRepository: ConversationRepositoryProtocol

    init(conversationRepository: ConversationRepositoryProtocol) {
        self.conversationRepository = conversationRepository
    }

    func execute(conversationId: UUID, before: Date?, limit: Int) async throws -> [ChatMessage] {
        try await conversationRepository.getMessages(conversationId: conversationId, before: before, limit: limit)
    }
}
