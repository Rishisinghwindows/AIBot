import Foundation

/// Domain-level errors
enum DomainError: Error, Equatable, Sendable {
    // Authentication errors
    case notAuthenticated
    case authenticationFailed(String)
    case tokenExpired
    case invalidCredentials

    // Network errors
    case networkUnavailable
    case serverError(String)
    case requestTimeout
    case invalidResponse

    // Data errors
    case notFound
    case dataCorrupted
    case saveFailed(String)
    case deleteFailed(String)

    // Chat errors
    case messageEmpty
    case conversationNotFound
    case rateLimitExceeded
    case usageLimitReached

    // General errors
    case unknown(String)
    case notImplemented(String)

    var localizedDescription: String {
        switch self {
        case .notAuthenticated:
            return "Please sign in to continue"
        case .authenticationFailed(let message):
            return "Authentication failed: \(message)"
        case .tokenExpired:
            return "Session expired. Please sign in again"
        case .invalidCredentials:
            return "Invalid credentials"
        case .networkUnavailable:
            return "No internet connection"
        case .serverError(let message):
            return "Server error: \(message)"
        case .requestTimeout:
            return "Request timed out"
        case .invalidResponse:
            return "Invalid response from server"
        case .notFound:
            return "Resource not found"
        case .dataCorrupted:
            return "Data is corrupted"
        case .saveFailed(let message):
            return "Failed to save: \(message)"
        case .deleteFailed(let message):
            return "Failed to delete: \(message)"
        case .messageEmpty:
            return "Message cannot be empty"
        case .conversationNotFound:
            return "Conversation not found"
        case .rateLimitExceeded:
            return "Too many requests. Please wait"
        case .usageLimitReached:
            return "Usage limit reached. Please upgrade"
        case .unknown(let message):
            return message
        case .notImplemented(let feature):
            return "\(feature) is not yet implemented"
        }
    }
}
