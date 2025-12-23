import Foundation
import GoogleSignIn
import FirebaseAuth
import UIKit

/// Protocol for remote authentication data source
protocol AuthRemoteDataSourceProtocol: Sendable {
    func signInWithGoogle() async throws -> AuthResponseDTO
    func signInWithApple() async throws -> AuthResponseDTO
    func signOut() async throws
    func refreshToken(refreshToken: String) async throws -> TokenRefreshResponseDTO
}

/// Remote data source for authentication operations
final class AuthRemoteDataSource: AuthRemoteDataSourceProtocol, @unchecked Sendable {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func signInWithGoogle() async throws -> AuthResponseDTO {
        // Get root view controller
        guard let windowScene = await MainActor.run(body: {
            UIApplication.shared.connectedScenes.first as? UIWindowScene
        }) else {
            throw DomainError.authenticationFailed("No window scene")
        }

        guard let rootViewController = await MainActor.run(body: {
            windowScene.windows.first?.rootViewController
        }) else {
            throw DomainError.authenticationFailed("No root view controller")
        }

        // Perform Google Sign-In
        let result = try await GIDSignIn.sharedInstance.signIn(withPresenting: rootViewController)

        guard let idToken = result.user.idToken?.tokenString else {
            throw DomainError.authenticationFailed("No ID token received")
        }

        // Create Firebase credential
        let credential = GoogleAuthProvider.credential(
            withIDToken: idToken,
            accessToken: result.user.accessToken.tokenString
        )

        // Sign in to Firebase
        let authResult = try await Auth.auth().signIn(with: credential)
        let firebaseToken = try await authResult.user.getIDToken()

        // Create response DTO
        let userDTO = UserDTO(
            id: authResult.user.uid,
            email: authResult.user.email ?? "",
            displayName: authResult.user.displayName,
            photoURL: authResult.user.photoURL?.absoluteString,
            createdAt: nil
        )

        return AuthResponseDTO(
            accessToken: firebaseToken,
            refreshToken: authResult.user.refreshToken,
            expiresIn: 3600,
            user: userDTO
        )
    }

    func signInWithApple() async throws -> AuthResponseDTO {
        // TODO: Implement Apple Sign-In
        throw DomainError.authenticationFailed("Apple Sign-In not implemented")
    }

    func signOut() async throws {
        try Auth.auth().signOut()
        GIDSignIn.sharedInstance.signOut()
    }

    func refreshToken(refreshToken: String) async throws -> TokenRefreshResponseDTO {
        guard let currentUser = Auth.auth().currentUser else {
            throw DomainError.notAuthenticated
        }

        let newToken = try await currentUser.getIDToken(forcingRefresh: true)

        return TokenRefreshResponseDTO(
            accessToken: newToken,
            refreshToken: currentUser.refreshToken,
            expiresIn: 3600
        )
    }
}
