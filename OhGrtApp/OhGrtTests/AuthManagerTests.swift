//
//  AuthManagerTests.swift
//  OhGrtTests
//
//  Tests for AuthManager functionality
//

import Testing
import Foundation
@testable import OhGrt

// MARK: - AuthManager State Tests

struct AuthManagerStateTests {

    @Test func sharedInstanceExists() async throws {
        await MainActor.run {
            let manager = AuthManager.shared
            #expect(manager != nil)
        }
    }

    @Test func initialLoadingState() async throws {
        await MainActor.run {
            let manager = AuthManager.shared
            // isLoading should be false when no operation is in progress
            #expect(manager.isLoading == false)
        }
    }

    @Test func errorMessageInitiallyNil() async throws {
        await MainActor.run {
            let manager = AuthManager.shared
            // Clear any previous error for test
            manager.errorMessage = nil
            #expect(manager.errorMessage == nil)
        }
    }
}

// MARK: - UserInfo Tests

struct UserInfoModelTests {

    @Test func userInfoInitialization() async throws {
        let user = UserInfo(
            id: "user-123",
            email: "test@example.com",
            displayName: "Test User",
            photoUrl: "https://example.com/photo.jpg"
        )

        #expect(user.id == "user-123")
        #expect(user.email == "test@example.com")
        #expect(user.displayName == "Test User")
        #expect(user.photoUrl == "https://example.com/photo.jpg")
    }

    @Test func userInfoWithNilOptionals() async throws {
        let user = UserInfo(
            id: "user-456",
            email: "minimal@example.com",
            displayName: nil,
            photoUrl: nil
        )

        #expect(user.id == "user-456")
        #expect(user.email == "minimal@example.com")
        #expect(user.displayName == nil)
        #expect(user.photoUrl == nil)
    }

    @Test func userInfoIdentifiable() async throws {
        let user = UserInfo(
            id: "unique-id",
            email: "test@example.com",
            displayName: nil,
            photoUrl: nil
        )

        // Identifiable protocol requires id property
        #expect(user.id == "unique-id")
    }
}

// MARK: - AuthError Tests (extended from OhGrtTests.swift)

struct AuthErrorExtendedTests {

    @Test func allAuthErrorsHaveDescriptions() async throws {
        let errors: [AuthError] = [
            .noRootViewController,
            .missingFirebaseConfig,
            .missingIdToken,
            .exchangeFailed
        ]

        for error in errors {
            #expect(error.errorDescription != nil)
            #expect(!error.errorDescription!.isEmpty)
        }
    }

    @Test func authErrorConformsToLocalizedError() async throws {
        let error: LocalizedError = AuthError.noRootViewController
        #expect(error.errorDescription != nil)
    }
}
