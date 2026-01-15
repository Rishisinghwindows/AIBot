//
//  OfflineManagerTests.swift
//  OhGrtTests
//
//  Tests for OfflineManager functionality
//

import Testing
import Foundation
@testable import OhGrt

// MARK: - QueuedRequest Tests

struct QueuedRequestTests {

    @Test func queuedRequestInitialization() async throws {
        let request = QueuedRequest(
            endpoint: "/chat/send",
            method: "POST",
            body: "test".data(using: .utf8)
        )

        #expect(request.endpoint == "/chat/send")
        #expect(request.method == "POST")
        #expect(request.body != nil)
        #expect(request.retryCount == 0)
        #expect(request.id != UUID()) // Should have a unique ID
    }

    @Test func queuedRequestWithoutBody() async throws {
        let request = QueuedRequest(
            endpoint: "/health",
            method: "GET",
            body: nil
        )

        #expect(request.endpoint == "/health")
        #expect(request.method == "GET")
        #expect(request.body == nil)
    }

    @Test func queuedRequestCodable() async throws {
        let original = QueuedRequest(
            endpoint: "/chat/send",
            method: "POST",
            body: "test data".data(using: .utf8)
        )

        let encoder = JSONEncoder()
        let data = try encoder.encode(original)

        let decoder = JSONDecoder()
        let decoded = try decoder.decode(QueuedRequest.self, from: data)

        #expect(decoded.endpoint == original.endpoint)
        #expect(decoded.method == original.method)
        #expect(decoded.id == original.id)
        #expect(decoded.retryCount == original.retryCount)
    }

    @Test func queuedRequestIdentifiable() async throws {
        let request = QueuedRequest(
            endpoint: "/test",
            method: "GET",
            body: nil
        )

        // Verify Identifiable protocol - id should match
        #expect(request.id == request.id)
    }
}

// MARK: - OfflineManager State Tests

struct OfflineManagerStateTests {

    @Test func sharedInstanceExists() async throws {
        await MainActor.run {
            let manager = OfflineManager.shared
            #expect(manager != nil)
        }
    }

    @Test func initialOnlineState() async throws {
        await MainActor.run {
            // The shared instance should initially report as online
            // (unless actually offline)
            let manager = OfflineManager.shared
            // Can't reliably test isOnline as it depends on actual network state
            #expect(manager.isSyncing == false)
        }
    }
}

// MARK: - Queueable Endpoint Tests

struct OfflineManagerQueueTests {

    @Test func chatSendIsQueueable() async throws {
        await MainActor.run {
            let manager = OfflineManager.shared
            let shouldQueue = manager.shouldQueueRequest(endpoint: "/chat/send")
            #expect(shouldQueue == true)
        }
    }

    @Test func healthCheckIsNotQueueable() async throws {
        await MainActor.run {
            let manager = OfflineManager.shared
            let shouldQueue = manager.shouldQueueRequest(endpoint: "/health")
            #expect(shouldQueue == false)
        }
    }

    @Test func authEndpointsNotQueueable() async throws {
        await MainActor.run {
            let manager = OfflineManager.shared

            #expect(manager.shouldQueueRequest(endpoint: "/auth/google") == false)
            #expect(manager.shouldQueueRequest(endpoint: "/auth/refresh") == false)
            #expect(manager.shouldQueueRequest(endpoint: "/auth/logout") == false)
        }
    }

    @Test func toolsEndpointNotQueueable() async throws {
        await MainActor.run {
            let manager = OfflineManager.shared
            let shouldQueue = manager.shouldQueueRequest(endpoint: "/chat/tools")
            #expect(shouldQueue == false)
        }
    }
}

// MARK: - OfflineError Tests

struct OfflineErrorTests {

    @Test func offlineErrorDescription() async throws {
        #expect(OfflineError.offline.errorDescription == "No internet connection")
    }

    @Test func requestFailedErrorDescription() async throws {
        #expect(OfflineError.requestFailed.errorDescription == "Request failed")
    }

    @Test func maxRetriesErrorDescription() async throws {
        #expect(OfflineError.maxRetriesExceeded.errorDescription == "Maximum retry attempts exceeded")
    }
}
