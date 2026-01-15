import Foundation
import Combine

/// Use case for observing authentication state changes
protocol ObserveAuthStateUseCaseProtocol: Sendable {
    func execute() -> AnyPublisher<AuthState, Never>
}

final class ObserveAuthStateUseCase: ObserveAuthStateUseCaseProtocol, @unchecked Sendable {
    private let authRepository: AuthRepositoryProtocol

    init(authRepository: AuthRepositoryProtocol) {
        self.authRepository = authRepository
    }

    func execute() -> AnyPublisher<AuthState, Never> {
        authRepository.authStatePublisher
    }
}
