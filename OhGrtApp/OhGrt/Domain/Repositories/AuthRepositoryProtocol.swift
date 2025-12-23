import Foundation
import Combine

/// Protocol defining authentication repository operations
/// Implemented by Data layer, used by Domain Use Cases
protocol AuthRepositoryProtocol: Sendable {
    /// Current authentication state publisher
    var authStatePublisher: AnyPublisher<AuthState, Never> { get }

    /// Current authentication state
    var currentAuthState: AuthState { get }

    /// Sign in with Google
    /// - Returns: Authenticated user
    /// - Throws: DomainError on failure
    func signInWithGoogle() async throws -> User

    /// Sign in with Apple
    /// - Returns: Authenticated user
    /// - Throws: DomainError on failure
    func signInWithApple() async throws -> User

    /// Sign out current user
    /// - Throws: DomainError on failure
    func signOut() async throws

    /// Refresh authentication token
    /// - Returns: New credentials
    /// - Throws: DomainError on failure
    func refreshToken() async throws -> AuthCredentials

    /// Check if user is authenticated
    /// - Returns: true if authenticated
    func isAuthenticated() -> Bool

    /// Get current user
    /// - Returns: Current user or nil
    func getCurrentUser() -> User?
}
