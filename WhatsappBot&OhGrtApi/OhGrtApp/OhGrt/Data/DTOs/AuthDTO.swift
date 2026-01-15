import Foundation

/// DTO for user data from API
struct UserDTO: Codable {
    let id: String
    let email: String
    let displayName: String?
    let photoURL: String?
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id
        case email
        case displayName = "display_name"
        case photoURL = "photo_url"
        case createdAt = "created_at"
    }
}

/// DTO for authentication response
struct AuthResponseDTO: Codable {
    let accessToken: String
    let refreshToken: String?
    let expiresIn: Int?
    let user: UserDTO

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case user
    }
}

/// DTO for token refresh response
struct TokenRefreshResponseDTO: Codable {
    let accessToken: String
    let refreshToken: String?
    let expiresIn: Int?

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
    }
}
