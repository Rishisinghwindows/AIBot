//
//  AppConfigTests.swift
//  OhGrtTests
//
//  Tests for AppConfig functionality
//

import Testing
import Foundation
@testable import OhGrt

// MARK: - AppConfig Tests

struct AppConfigTests {

    @Test func sharedInstanceExists() async throws {
        let config = AppConfig.shared
        #expect(config != nil)
    }

    @Test func apiBaseURLIsValid() async throws {
        let config = AppConfig.shared
        let url = config.apiBaseURL

        // Should be a valid URL
        #expect(url.scheme == "http" || url.scheme == "https")
        #expect(url.host != nil)
    }

    @Test func apiBaseURLHasHost() async throws {
        let config = AppConfig.shared
        let url = config.apiBaseURL

        // Host should not be empty
        #expect(url.host != nil)
        #expect(!url.host!.isEmpty)
    }

    @Test func environmentIsSet() async throws {
        let config = AppConfig.shared
        let env = config.environment

        // Environment should be one of the valid values
        let validEnvironments: [AppEnvironment] = [.debug, .staging, .release]
        #expect(validEnvironments.contains(env))
    }

    @Test func requestTimeoutIsPositive() async throws {
        let config = AppConfig.shared
        let timeout = config.requestTimeout

        #expect(timeout > 0)
    }

    @Test func maxRetryAttemptsIsPositive() async throws {
        let config = AppConfig.shared
        let retries = config.maxRetryAttempts

        #expect(retries >= 0)
    }
}

// MARK: - AppEnvironment Tests

struct AppEnvironmentTests {

    @Test func debugEnvironmentExists() async throws {
        let env = AppEnvironment.debug
        #expect(env == .debug)
    }

    @Test func stagingEnvironmentExists() async throws {
        let env = AppEnvironment.staging
        #expect(env == .staging)
    }

    @Test func releaseEnvironmentExists() async throws {
        let env = AppEnvironment.release
        #expect(env == .release)
    }

    @Test func environmentsAreDistinct() async throws {
        #expect(AppEnvironment.debug != AppEnvironment.staging)
        #expect(AppEnvironment.staging != AppEnvironment.release)
        #expect(AppEnvironment.debug != AppEnvironment.release)
    }
}
