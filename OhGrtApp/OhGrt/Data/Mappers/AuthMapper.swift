import Foundation

/// Mapper for authentication DTOs to Domain entities
enum AuthMapper {
    /// Map UserDTO to User domain entity
    static func toDomain(_ dto: UserDTO) -> User {
        let createdAt: Date
        if let createdAtString = dto.createdAt {
            createdAt = ISO8601DateFormatter().date(from: createdAtString) ?? Date()
        } else {
            createdAt = Date()
        }

        return User(
            id: dto.id,
            email: dto.email,
            displayName: dto.displayName,
            photoURL: dto.photoURL.flatMap { URL(string: $0) },
            createdAt: createdAt
        )
    }

    /// Map AuthResponseDTO to AuthCredentials
    static func toCredentials(_ dto: AuthResponseDTO) -> AuthCredentials {
        let expiresAt: Date?
        if let expiresIn = dto.expiresIn {
            expiresAt = Date().addingTimeInterval(TimeInterval(expiresIn))
        } else {
            expiresAt = nil
        }

        return AuthCredentials(
            accessToken: dto.accessToken,
            refreshToken: dto.refreshToken,
            expiresAt: expiresAt
        )
    }

    /// Map TokenRefreshResponseDTO to AuthCredentials
    static func toCredentials(_ dto: TokenRefreshResponseDTO) -> AuthCredentials {
        let expiresAt: Date?
        if let expiresIn = dto.expiresIn {
            expiresAt = Date().addingTimeInterval(TimeInterval(expiresIn))
        } else {
            expiresAt = nil
        }

        return AuthCredentials(
            accessToken: dto.accessToken,
            refreshToken: dto.refreshToken,
            expiresAt: expiresAt
        )
    }
}
