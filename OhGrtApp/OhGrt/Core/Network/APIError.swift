import Foundation

/// API error types for the OhGrt application
enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int, data: Data?)
    case decodingError(Error)
    case encodingError(Error)
    case networkError(Error)
    case notAuthenticated
    case tokenExpired
    case sslPinningFailed
    case serverError(message: String)
    case offline(queued: Bool)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid server response"
        case .httpError(let statusCode, _):
            return "HTTP error: \(statusCode)"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .encodingError(let error):
            return "Failed to encode request: \(error.localizedDescription)"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .notAuthenticated:
            return "Not authenticated"
        case .tokenExpired:
            return "Session expired. Please sign in again."
        case .sslPinningFailed:
            return "SSL certificate verification failed"
        case .serverError(let message):
            return message
        case .offline(let queued):
            return queued
                ? "No internet connection. Your message will be sent when you're back online."
                : "No internet connection. Please check your network and try again."
        }
    }

    /// Whether this error indicates the device is offline
    var isOfflineError: Bool {
        if case .offline = self { return true }
        if case .networkError(let error) = self {
            if let urlError = error as? URLError {
                return urlError.code == .notConnectedToInternet || urlError.code == .networkConnectionLost
            }
        }
        return false
    }

    var isAuthError: Bool {
        switch self {
        case .notAuthenticated, .tokenExpired:
            return true
        case .httpError(let statusCode, _):
            return statusCode == 401
        default:
            return false
        }
    }
}

/// Server error response structure matching API format
struct ServerErrorResponse: Decodable {
    let error: String?
    let message: String?
    let details: ErrorDetails?
    let detail: String? // Legacy format support

    struct ErrorDetails: Decodable {
        let errors: [FieldError]?
        let field: String?
        let statusCode: Int?

        private enum CodingKeys: String, CodingKey {
            case errors
            case field
            case statusCode = "status_code"
        }
    }

    struct FieldError: Decodable {
        let field: String?
        let message: String?
    }

    var errorMessage: String {
        // Use new API format first
        if let message = message, !message.isEmpty {
            // Include field-level errors if present
            if let fieldErrors = details?.errors, !fieldErrors.isEmpty {
                let fieldMessages = fieldErrors.compactMap { error -> String? in
                    guard let field = error.field, let msg = error.message else { return nil }
                    return "\(field): \(msg)"
                }
                if !fieldMessages.isEmpty {
                    return "\(message): \(fieldMessages.joined(separator: ", "))"
                }
            }
            return message
        }
        // Fall back to legacy format
        return detail ?? "Unknown error"
    }

    var errorCode: String {
        error ?? "UNKNOWN_ERROR"
    }

    var isValidationError: Bool {
        error == "VALIDATION_ERROR"
    }

    var isRateLimitError: Bool {
        error == "RATE_LIMIT_EXCEEDED"
    }

    var isAuthError: Bool {
        error == "AUTH_ERROR" || error == "TOKEN_EXPIRED" || error == "INVALID_TOKEN"
    }
}
