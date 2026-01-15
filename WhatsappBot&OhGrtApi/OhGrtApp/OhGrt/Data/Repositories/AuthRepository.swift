import Foundation
import Combine

/// Implementation of AuthRepositoryProtocol
final class AuthRepository: AuthRepositoryProtocol, @unchecked Sendable {
    private let remoteDataSource: AuthRemoteDataSourceProtocol
    private let keychainManager: KeychainManager

    private let authStateSubject = CurrentValueSubject<AuthState, Never>(.unknown)
    private var currentUser: User?
    private var credentials: AuthCredentials?

    var authStatePublisher: AnyPublisher<AuthState, Never> {
        authStateSubject.eraseToAnyPublisher()
    }

    var currentAuthState: AuthState {
        authStateSubject.value
    }

    init(
        remoteDataSource: AuthRemoteDataSourceProtocol,
        keychainManager: KeychainManager
    ) {
        self.remoteDataSource = remoteDataSource
        self.keychainManager = keychainManager

        Task {
            await checkStoredCredentials()
        }
    }

    func signInWithGoogle() async throws -> User {
        let response = try await remoteDataSource.signInWithGoogle()

        let user = AuthMapper.toDomain(response.user)
        let credentials = AuthMapper.toCredentials(response)

        self.currentUser = user
        self.credentials = credentials

        // Store tokens in keychain
        try await keychainManager.saveTokens(
            access: credentials.accessToken,
            refresh: credentials.refreshToken ?? ""
        )

        authStateSubject.send(.authenticated(user))
        return user
    }

    func signInWithApple() async throws -> User {
        let response = try await remoteDataSource.signInWithApple()

        let user = AuthMapper.toDomain(response.user)
        let credentials = AuthMapper.toCredentials(response)

        self.currentUser = user
        self.credentials = credentials

        authStateSubject.send(.authenticated(user))
        return user
    }

    func signOut() async throws {
        try await remoteDataSource.signOut()

        currentUser = nil
        credentials = nil

        // Clear keychain
        try await keychainManager.clearTokens()

        authStateSubject.send(.unauthenticated)
    }

    func refreshToken() async throws -> AuthCredentials {
        guard let refreshToken = try await keychainManager.getRefreshToken() else {
            throw DomainError.tokenExpired
        }

        let response = try await remoteDataSource.refreshToken(refreshToken: refreshToken)
        let newCredentials = AuthMapper.toCredentials(response)

        self.credentials = newCredentials

        // Update keychain
        try await keychainManager.saveTokens(
            access: newCredentials.accessToken,
            refresh: newCredentials.refreshToken ?? refreshToken
        )

        return newCredentials
    }

    func isAuthenticated() -> Bool {
        if case .authenticated = currentAuthState {
            return true
        }
        return false
    }

    func getCurrentUser() -> User? {
        currentUser
    }

    // MARK: - Private

    private func checkStoredCredentials() async {
        let hasTokens = await keychainManager.hasTokens()
        if hasTokens {
            // We have stored credentials, assume valid for now
            // Actual validation would check with server
            authStateSubject.send(.unauthenticated)
        } else {
            authStateSubject.send(.unauthenticated)
        }
    }
}
