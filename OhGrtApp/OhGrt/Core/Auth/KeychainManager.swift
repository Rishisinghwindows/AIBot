import Foundation
import Security

/// Secure storage manager for authentication tokens using iOS Keychain
actor KeychainManager {
    /// Shared singleton instance
    static let shared = KeychainManager()

    private let accessTokenKey = "com.ohgrt.accessToken"
    private let refreshTokenKey = "com.ohgrt.refreshToken"
    private let userIdKey = "com.ohgrt.userId"
    private let oauthStatePrefix = "com.ohgrt.oauth.state."

    private init() {}

    // MARK: - Token Management

    /// Save both access and refresh tokens
    func saveTokens(access: String, refresh: String) throws {
        try save(key: accessTokenKey, value: access)
        try save(key: refreshTokenKey, value: refresh)
    }

    /// Get the access token
    func getAccessToken() throws -> String? {
        return try retrieve(key: accessTokenKey)
    }

    /// Get the refresh token
    func getRefreshToken() throws -> String? {
        return try retrieve(key: refreshTokenKey)
    }

    /// Clear all tokens (logout)
    func clearTokens() throws {
        try delete(key: accessTokenKey)
        try delete(key: refreshTokenKey)
        try delete(key: userIdKey)
    }

    /// Check if user has valid tokens stored
    func hasTokens() -> Bool {
        do {
            let accessToken = try retrieve(key: accessTokenKey)
            let refreshToken = try retrieve(key: refreshTokenKey)
            return accessToken != nil && refreshToken != nil
        } catch {
            return false
        }
    }

    // MARK: - User ID Management

    /// Save user ID
    func saveUserId(_ userId: String) throws {
        try save(key: userIdKey, value: userId)
    }

    /// Get user ID
    func getUserId() throws -> String? {
        return try retrieve(key: userIdKey)
    }

    // MARK: - OAuth State Management

    /// Save OAuth state for a provider (persists across app restarts)
    /// - Parameters:
    ///   - state: The OAuth state token
    ///   - provider: The provider name (e.g., "github", "slack")
    func saveOAuthState(_ state: String, for provider: String) throws {
        let key = oauthStatePrefix + provider.lowercased()
        try save(key: key, value: state)
    }

    /// Get OAuth state for a provider
    /// - Parameter provider: The provider name
    /// - Returns: The stored state, or nil if not found
    func getOAuthState(for provider: String) throws -> String? {
        let key = oauthStatePrefix + provider.lowercased()
        return try retrieve(key: key)
    }

    /// Remove OAuth state for a provider (call after OAuth completes)
    /// - Parameter provider: The provider name
    func removeOAuthState(for provider: String) throws {
        let key = oauthStatePrefix + provider.lowercased()
        try delete(key: key)
    }

    /// Validate OAuth state matches expected value and clean up
    /// - Parameters:
    ///   - state: The state received from OAuth callback
    ///   - provider: The provider name
    /// - Returns: True if state matches, false otherwise
    func validateAndClearOAuthState(_ state: String, for provider: String) throws -> Bool {
        guard let storedState = try getOAuthState(for: provider) else {
            return false
        }

        let isValid = storedState == state
        if isValid {
            try removeOAuthState(for: provider)
        }
        return isValid
    }

    // MARK: - Private Helpers

    private func save(key: String, value: String) throws {
        guard let data = value.data(using: .utf8) else {
            throw KeychainError.encodingFailed
        }

        // Delete existing item first
        let deleteQuery: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]
        SecItemDelete(deleteQuery as CFDictionary)

        // Add new item
        let addQuery: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        ]

        let status = SecItemAdd(addQuery as CFDictionary, nil)
        guard status == errSecSuccess else {
            throw KeychainError.saveFailed(status: status)
        }
    }

    private func retrieve(key: String) throws -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        switch status {
        case errSecSuccess:
            guard let data = result as? Data,
                  let string = String(data: data, encoding: .utf8) else {
                throw KeychainError.decodingFailed
            }
            return string
        case errSecItemNotFound:
            return nil
        default:
            throw KeychainError.retrieveFailed(status: status)
        }
    }

    private func delete(key: String) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]

        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw KeychainError.deleteFailed(status: status)
        }
    }
}

// MARK: - Keychain Errors

enum KeychainError: LocalizedError {
    case encodingFailed
    case decodingFailed
    case saveFailed(status: OSStatus)
    case retrieveFailed(status: OSStatus)
    case deleteFailed(status: OSStatus)

    var errorDescription: String? {
        switch self {
        case .encodingFailed:
            return "Failed to encode data for keychain"
        case .decodingFailed:
            return "Failed to decode data from keychain"
        case .saveFailed(let status):
            return "Failed to save to keychain: \(status)"
        case .retrieveFailed(let status):
            return "Failed to retrieve from keychain: \(status)"
        case .deleteFailed(let status):
            return "Failed to delete from keychain: \(status)"
        }
    }
}
