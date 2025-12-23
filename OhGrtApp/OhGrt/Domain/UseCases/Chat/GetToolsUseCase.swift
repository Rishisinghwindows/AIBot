import Foundation

/// Use case for getting available AI tools
protocol GetToolsUseCaseProtocol: Sendable {
    func execute() async throws -> [Tool]
}

final class GetToolsUseCase: GetToolsUseCaseProtocol, @unchecked Sendable {
    private let chatRepository: ChatRepositoryProtocol

    init(chatRepository: ChatRepositoryProtocol) {
        self.chatRepository = chatRepository
    }

    func execute() async throws -> [Tool] {
        try await chatRepository.getAvailableTools()
    }
}
