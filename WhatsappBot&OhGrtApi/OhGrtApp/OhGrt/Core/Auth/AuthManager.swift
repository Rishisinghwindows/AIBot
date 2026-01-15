import Foundation
import SwiftUI
import Combine // Move after SwiftUI
import SwiftData
import FirebaseCore
import FirebaseAuth
import GoogleSignIn
import os.log

private let logger = Logger(subsystem: "com.d23.OhGrt", category: "AuthManager")

/// Main authentication manager for the app
@MainActor
class AuthManager: ObservableObject {
    /// Shared singleton instance
    static let shared = AuthManager()

    /// Whether the user is authenticated
    @Published var isAuthenticated = false

    /// Current user information
    @Published var currentUser: UserInfo?

    /// Loading state for auth operations
    @Published var isLoading = false

    /// Error message to display
    @Published var errorMessage: String?

    private init() {
        checkAuthState()
    }

    /// Check if user has valid stored tokens
    func checkAuthState() {
        // In development mode, skip auth checks (backend requires database)
        if AppConfig.shared.isDevelopment {
            logger.info("Skipping auth check in development mode")
            return
        }

        Task {
            let hasTokens = await KeychainManager.shared.hasTokens()
            await MainActor.run {
                self.isAuthenticated = hasTokens
            }

            if hasTokens {
                // Try to fetch user profile
                await fetchUserProfile()
            }
        }
    }

    /// Sign in with Google via Firebase
    func signInWithGoogle() async {
        // In development mode, skip sign in (backend requires database)
        if AppConfig.shared.isDevelopment {
            logger.warning("Sign in not available in development mode - using anonymous session")
            await MainActor.run {
                self.errorMessage = "Sign in is disabled in development mode. Chat works without authentication."
            }
            return
        }

        isLoading = true
        errorMessage = nil

        defer {
            Task { @MainActor in
                self.isLoading = false
            }
        }

        do {
            // Get the presenting view controller
            guard let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
                  let rootVC = windowScene.windows.first?.rootViewController else {
                throw AuthError.noRootViewController
            }

            // Get Firebase client ID
            guard let clientID = FirebaseApp.app()?.options.clientID else {
                throw AuthError.missingFirebaseConfig
            }

            // Configure Google Sign-In
            let config = GIDConfiguration(clientID: clientID)
            GIDSignIn.sharedInstance.configuration = config

            // Present Google Sign-In
            let result = try await GIDSignIn.sharedInstance.signIn(withPresenting: rootVC)

            guard let idToken = result.user.idToken?.tokenString else {
                throw AuthError.missingIdToken
            }

            // Create Firebase credential
            let credential = GoogleAuthProvider.credential(
                withIDToken: idToken,
                accessToken: result.user.accessToken.tokenString
            )

            // Sign in to Firebase
            let authResult = try await Auth.auth().signIn(with: credential)

            // Get Firebase ID token
            let firebaseIdToken = try await authResult.user.getIDToken()

            // Exchange Firebase token for our JWT
            try await exchangeFirebaseToken(firebaseIdToken)

            await MainActor.run {
                self.isAuthenticated = true
            }

            // Fetch user profile
            await fetchUserProfile()

            logger.info("Sign in successful")

        } catch {
            logger.error("Sign in failed: \(error.localizedDescription)")
            await MainActor.run {
                self.errorMessage = error.localizedDescription
            }
        }
    }

    /// Exchange Firebase token for our backend JWT tokens
    private func exchangeFirebaseToken(_ firebaseToken: String) async throws {
        let deviceInfo = UIDevice.current.identifierForVendor?.uuidString

        let response = try await APIClient.shared.authenticateWithGoogle(
            firebaseToken: firebaseToken,
            deviceInfo: deviceInfo
        )

        // Save tokens to keychain
        try await KeychainManager.shared.saveTokens(
            access: response.accessToken,
            refresh: response.refreshToken
        )

        logger.debug("Tokens saved to keychain")
    }

    /// Fetch current user profile from backend
    func fetchUserProfile() async {
        // In development mode, skip profile fetch (backend requires database)
        if AppConfig.shared.isDevelopment {
            logger.info("Skipping profile fetch in development mode")
            return
        }

        do {
            let user: UserResponse = try await APIClient.shared.request(endpoint: .me)
            await MainActor.run {
                self.currentUser = UserInfo(
                    id: user.id,
                    email: user.email,
                    displayName: user.displayName,
                    photoUrl: user.photoUrl
                )
            }
            logger.debug("User profile fetched successfully")
        } catch {
            logger.error("Failed to fetch user profile: \(error.localizedDescription)")
        }
    }

    /// Sign out
    func signOut() async {
        isLoading = true

        do {
            // Get refresh token for logout request
            if let refreshToken = try await KeychainManager.shared.getRefreshToken() {
                // Notify backend - log errors but continue with local cleanup
                let request = RefreshTokenRequest(refreshToken: refreshToken)
                do {
                    try await APIClient.shared.requestVoid(endpoint: .logout, body: request)
                    logger.debug("Backend logout successful")
                } catch {
                    // SECURITY: Log the error for debugging but continue with local cleanup
                    // User should still be logged out locally even if backend call fails
                    logger.warning("Backend logout failed: \(error.localizedDescription). Continuing with local cleanup.")
                }
            }

            // Sign out of Firebase
            try Auth.auth().signOut()

            // Sign out of Google
            GIDSignIn.sharedInstance.signOut()

            // Clear local tokens
            try await KeychainManager.shared.clearTokens()
            clearLocalData()

            await MainActor.run {
                self.isAuthenticated = false
                self.currentUser = nil
                self.isLoading = false
            }

            logger.info("Sign out successful")

        } catch {
            logger.error("Sign out error: \(error.localizedDescription)")
            await MainActor.run {
                self.isLoading = false
                self.errorMessage = error.localizedDescription
            }
        }
    }

    private func clearLocalData() {
        do {
            let container = try ModelContainer(for: Message.self, Conversation.self)
            let context = ModelContext(container)
            let messages = try context.fetch(FetchDescriptor<Message>())
            let conversations = try context.fetch(FetchDescriptor<Conversation>())
            messages.forEach { context.delete($0) }
            conversations.forEach { context.delete($0) }
            try context.save()
            logger.debug("Cleared local chat data")
        } catch {
            logger.error("Failed to clear local data: \(error.localizedDescription)")
        }
    }
}

// MARK: - Supporting Types

/// User information
struct UserInfo: Identifiable {
    let id: String
    let email: String
    let displayName: String?
    let photoUrl: String?
}

/// Authentication errors
enum AuthError: LocalizedError {
    case noRootViewController
    case missingFirebaseConfig
    case missingIdToken
    case exchangeFailed

    var errorDescription: String? {
        switch self {
        case .noRootViewController:
            return "Could not find root view controller"
        case .missingFirebaseConfig:
            return "Firebase configuration is missing"
        case .missingIdToken:
            return "Could not get ID token from Google"
        case .exchangeFailed:
            return "Failed to exchange token with server"
        }
    }
}
