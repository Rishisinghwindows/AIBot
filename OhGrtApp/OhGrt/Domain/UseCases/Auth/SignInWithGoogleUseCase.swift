import Foundation

/// Use case for signing in with Google
protocol SignInWithGoogleUseCaseProtocol: Sendable {
    func execute() async throws -> User
}

final class SignInWithGoogleUseCase: SignInWithGoogleUseCaseProtocol, @unchecked Sendable {
    private let authRepository: AuthRepositoryProtocol

    init(authRepository: AuthRepositoryProtocol) {
        self.authRepository = authRepository
    }

    func execute() async throws -> User {
        try await authRepository.signInWithGoogle()
    }
}
