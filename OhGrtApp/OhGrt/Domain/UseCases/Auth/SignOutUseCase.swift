import Foundation

/// Use case for signing out
protocol SignOutUseCaseProtocol: Sendable {
    func execute() async throws
}

final class SignOutUseCase: SignOutUseCaseProtocol, @unchecked Sendable {
    private let authRepository: AuthRepositoryProtocol

    init(authRepository: AuthRepositoryProtocol) {
        self.authRepository = authRepository
    }

    func execute() async throws {
        try await authRepository.signOut()
    }
}
