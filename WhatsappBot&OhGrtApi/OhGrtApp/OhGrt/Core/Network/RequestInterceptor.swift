import Foundation
import Security

/// Intercepts requests to add security headers and authentication
actor RequestInterceptor {

    /// Generate a cryptographically secure nonce
    func generateNonce() -> String {
        var bytes = [UInt8](repeating: 0, count: 32)
        _ = SecRandomCopyBytes(kSecRandomDefault, bytes.count, &bytes)
        return Data(bytes).base64EncodedString()
    }

    /// Generate a unique request ID
    func generateRequestId() -> String {
        UUID().uuidString
    }

    /// Get current Unix timestamp
    func currentTimestamp() -> String {
        String(Date().timeIntervalSince1970)
    }

    /// Intercept and modify a request with security headers and auth
    func intercept(_ request: URLRequest, requiresAuth: Bool) async throws -> URLRequest {
        var modifiedRequest = request

        // Add security headers
        let requestId = generateRequestId()
        let nonce = generateNonce()
        let timestamp = currentTimestamp()

        modifiedRequest.setValue(requestId, forHTTPHeaderField: "X-Request-ID")
        modifiedRequest.setValue(nonce, forHTTPHeaderField: "X-Nonce")
        modifiedRequest.setValue(timestamp, forHTTPHeaderField: "X-Timestamp")

        // Add content type for JSON
        if modifiedRequest.httpMethod == "POST" || modifiedRequest.httpMethod == "PUT" {
            modifiedRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        modifiedRequest.setValue("application/json", forHTTPHeaderField: "Accept")

        // Add auth header if required
        if requiresAuth {
            do {
                if let accessToken = try await KeychainManager.shared.getAccessToken() {
                    modifiedRequest.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
                } else {
                    throw APIError.notAuthenticated
                }
            } catch {
                throw APIError.notAuthenticated
            }
        }

        return modifiedRequest
    }
}
