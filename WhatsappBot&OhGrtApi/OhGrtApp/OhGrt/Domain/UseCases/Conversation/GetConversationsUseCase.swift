import Foundation
import Combine

/// Use case for getting all conversations
protocol GetConversationsUseCaseProtocol: Sendable {
    func execute() async throws -> [ChatConversation]
    func observe() -> AnyPublisher<[ChatConversation], Never>
}

final class GetConversationsUseCase: GetConversationsUseCaseProtocol, @unchecked Sendable {
    private let conversationRepository: ConversationRepositoryProtocol

    init(conversationRepository: ConversationRepositoryProtocol) {
        self.conversationRepository = conversationRepository
    }

    func execute() async throws -> [ChatConversation] {
        try await conversationRepository.getAllConversations()
    }

    func observe() -> AnyPublisher<[ChatConversation], Never> {
        conversationRepository.conversationsPublisher
    }
}
