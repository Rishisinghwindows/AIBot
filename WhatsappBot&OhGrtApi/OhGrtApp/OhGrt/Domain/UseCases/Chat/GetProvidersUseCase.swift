import Foundation

/// Use case for getting available providers/integrations
protocol GetProvidersUseCaseProtocol: Sendable {
    func execute() async throws -> [Provider]
}

final class GetProvidersUseCase: GetProvidersUseCaseProtocol, @unchecked Sendable {
    private let chatRepository: ChatRepositoryProtocol

    init(chatRepository: ChatRepositoryProtocol) {
        self.chatRepository = chatRepository
    }

    func execute() async throws -> [Provider] {
        return try await chatRepository.getProviders()
    }
}
