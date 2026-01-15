import Foundation
import os.log

private let logger = Logger(subsystem: "com.d23.OhGrt", category: "TokenRefresher")

/// Handles automatic token refresh
actor TokenRefresher {
    /// Shared singleton instance
    static let shared = TokenRefresher()

    /// Flag to prevent concurrent refresh attempts
    private var isRefreshing = false

    /// Continuation for waiting requests during refresh
    private var refreshContinuations: [CheckedContinuation<Void, Error>] = []

    /// Store the last refresh error to propagate to waiting continuations
    private var lastRefreshError: Error?

    private init() {}

    /// Refresh the access token if needed
    /// If a refresh is already in progress, waits for it to complete
    func refreshIfNeeded() async throws {
        // If already refreshing, wait for it to complete
        if isRefreshing {
            try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
                refreshContinuations.append(continuation)
            }
            // After waiting, check if the refresh failed
            if let error = lastRefreshError {
                throw error
            }
            return
        }

        isRefreshing = true
        lastRefreshError = nil

        do {
            try await performRefresh()
            resumeWaitingContinuations(with: nil)
        } catch {
            lastRefreshError = error
            resumeWaitingContinuations(with: error)
            throw error
        }

        isRefreshing = false
    }

    /// Actually perform the token refresh
    private func performRefresh() async throws {
        // Get refresh token
        guard let refreshToken = try await KeychainManager.shared.getRefreshToken() else {
            throw TokenRefreshError.noRefreshToken
        }

        // Call refresh endpoint
        do {
            let response = try await APIClient.shared.refreshAccessToken(refreshToken: refreshToken)

            // Save new tokens
            try await KeychainManager.shared.saveTokens(
                access: response.accessToken,
                refresh: response.refreshToken
            )

            logger.info("Token refreshed successfully")
        } catch {
            logger.error("Failed to refresh token: \(error.localizedDescription)")

            // Clear tokens on refresh failure - user needs to re-authenticate
            do {
                try await KeychainManager.shared.clearTokens()
            } catch {
                logger.error("Failed to clear tokens after refresh failure: \(error.localizedDescription)")
            }
            throw TokenRefreshError.refreshFailed(error)
        }
    }

    /// Resume all waiting continuations with optional error
    private func resumeWaitingContinuations(with error: Error?) {
        let continuations = refreshContinuations
        refreshContinuations.removeAll()
        for continuation in continuations {
            if let error = error {
                continuation.resume(throwing: error)
            } else {
                continuation.resume()
            }
        }
    }

    /// Force a token refresh
    /// Cancels any waiting continuations and starts a fresh refresh
    func forceRefresh() async throws {
        // If already refreshing, cancel waiting continuations with an error
        if isRefreshing {
            let cancelError = TokenRefreshError.refreshCancelled
            resumeWaitingContinuations(with: cancelError)
            isRefreshing = false
        }

        try await refreshIfNeeded()
    }
}

// MARK: - Token Refresh Errors

enum TokenRefreshError: LocalizedError {
    case noRefreshToken
    case refreshFailed(Error)
    case refreshCancelled

    var errorDescription: String? {
        switch self {
        case .noRefreshToken:
            return "No refresh token available. Please sign in again."
        case .refreshFailed(let error):
            return "Failed to refresh token: \(error.localizedDescription)"
        case .refreshCancelled:
            return "Token refresh was cancelled. Please try again."
        }
    }
}
