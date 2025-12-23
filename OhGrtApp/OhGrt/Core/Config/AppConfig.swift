import Foundation

/// Application configuration based on build environment
enum AppEnvironment: String {
    case development
    case staging
    case production

    /// Current environment based on build configuration
    static var current: AppEnvironment {
        #if DEBUG
        return .development
        #else
        // Check for staging flag in Info.plist or use production
        if let envString = Bundle.main.infoDictionary?["APP_ENVIRONMENT"] as? String,
           let env = AppEnvironment(rawValue: envString.lowercased()) {
            return env
        }
        return .production
        #endif
    }

    /// Validate that current environment is appropriate for release
    /// Call this during app startup to catch configuration errors
    static func validateForRelease() {
        #if !DEBUG
        let env = current
        if env == .development {
            // Log critical warning - development mode in release build
            print("⚠️ CRITICAL: Development environment detected in release build!")
            print("⚠️ This may expose sensitive debugging features.")
            // In production, we could also send this to crash reporting
            assertionFailure("Development environment should not be used in release builds")
        }
        #endif
    }
}

/// Centralized application configuration
struct AppConfig {
    /// Shared singleton instance
    static let shared = AppConfig()

    /// Current environment
    let environment: AppEnvironment

    /// API base URL
    let apiBaseURL: URL

    /// Whether SSL pinning is strictly enforced
    let enforceSSLPinning: Bool

    /// Whether to allow debug logging
    let allowDebugLogging: Bool

    /// Request timeout interval
    let requestTimeout: TimeInterval

    /// Maximum retry attempts for failed requests
    let maxRetryAttempts: Int

    private init() {
        self.environment = AppEnvironment.current

        switch environment {
        case .development:
            // Development configuration
            // Use 127.0.0.1 (IPv4) for simulator since API binds to IPv4 only
            // For physical device, use your Mac's IP address
            self.apiBaseURL = URL(string: "http://127.0.0.1:8000")!
            self.enforceSSLPinning = false  // Allow debugging with proxies
            self.allowDebugLogging = true
            self.requestTimeout = 60
            self.maxRetryAttempts = 3

        case .staging:
            // Staging configuration
            self.apiBaseURL = URL(string: "https://staging-api.d23.ai")!
            self.enforceSSLPinning = true
            self.allowDebugLogging = true
            self.requestTimeout = 30
            self.maxRetryAttempts = 3

        case .production:
            // Production configuration - strictest settings
            self.apiBaseURL = URL(string: "https://api.d23.ai")!
            self.enforceSSLPinning = true
            self.allowDebugLogging = false
            self.requestTimeout = 30
            self.maxRetryAttempts = 2
        }
    }

    /// Whether the app is running in development mode
    var isDevelopment: Bool {
        environment == .development
    }

    /// Whether the app is running in production mode
    var isProduction: Bool {
        environment == .production
    }

    /// Log a message if debug logging is enabled
    func debugLog(_ message: String, file: String = #file, function: String = #function, line: Int = #line) {
        guard allowDebugLogging else { return }
        let fileName = (file as NSString).lastPathComponent
        print("[\(fileName):\(line)] \(function) - \(message)")
    }
}

// MARK: - Feature Flags

extension AppConfig {
    /// Feature flags for gradual rollout
    struct FeatureFlags {
        /// Whether offline mode is enabled
        static var offlineModeEnabled: Bool {
            // Can be controlled via remote config in the future
            return true
        }

        /// Whether voice input is enabled
        static var voiceInputEnabled: Bool {
            return true
        }

        /// Whether to show MCP configuration UI
        static var mcpConfigEnabled: Bool {
            return true
        }

        /// Maximum message length
        static var maxMessageLength: Int {
            return 10000
        }
    }
}

// MARK: - Security Configuration

extension AppConfig {
    /// Security-related configuration
    struct Security {
        /// Keychain service identifier
        static let keychainService = "com.ohgrt.keychain"

        /// Access token keychain key
        static let accessTokenKey = "com.ohgrt.accessToken"

        /// Refresh token keychain key
        static let refreshTokenKey = "com.ohgrt.refreshToken"

        /// User ID keychain key
        static let userIdKey = "com.ohgrt.userId"

        /// Token refresh threshold (refresh when less than this many seconds remain)
        static let tokenRefreshThreshold: TimeInterval = 300 // 5 minutes

        /// Maximum failed auth attempts before lockout
        static let maxFailedAuthAttempts = 5

        /// Lockout duration after max failed attempts
        static let authLockoutDuration: TimeInterval = 300 // 5 minutes
    }
}
