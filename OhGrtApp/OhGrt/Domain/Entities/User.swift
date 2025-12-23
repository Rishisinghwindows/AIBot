import Foundation

/// Domain entity representing a user
struct User: Equatable, Sendable {
    let id: String
    let email: String
    let displayName: String?
    let photoURL: URL?
    let createdAt: Date

    init(
        id: String,
        email: String,
        displayName: String? = nil,
        photoURL: URL? = nil,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.email = email
        self.displayName = displayName
        self.photoURL = photoURL
        self.createdAt = createdAt
    }
}

/// Authentication state
enum AuthState: Equatable, Sendable {
    case unknown
    case authenticated(User)
    case unauthenticated
}

/// Authentication credentials
struct AuthCredentials: Sendable {
    let accessToken: String
    let refreshToken: String?
    let expiresAt: Date?
}
