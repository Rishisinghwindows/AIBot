//
//  NetworkLayerTests.swift
//  OhGrtTests
//
//  Tests for network layer components
//

import Testing
import Foundation
@testable import OhGrt

// MARK: - RequestInterceptor Extended Tests

struct RequestInterceptorExtendedTests {

    @Test func multipleNoncesAreUnique() async throws {
        let interceptor = RequestInterceptor()
        var nonces: Set<String> = []

        for _ in 0..<100 {
            let nonce = await interceptor.generateNonce()
            nonces.insert(nonce)
        }

        // All 100 nonces should be unique
        #expect(nonces.count == 100)
    }

    @Test func multipleRequestIdsAreUnique() async throws {
        let interceptor = RequestInterceptor()
        var ids: Set<String> = []

        for _ in 0..<100 {
            let requestId = await interceptor.generateRequestId()
            ids.insert(requestId)
        }

        // All 100 IDs should be unique
        #expect(ids.count == 100)
    }

    @Test func timestampIsReasonable() async throws {
        let interceptor = RequestInterceptor()
        let timestamp = await interceptor.currentTimestamp()
        let timestampValue = Double(timestamp)!

        // Should be after January 1, 2020
        let jan2020: TimeInterval = 1577836800
        #expect(timestampValue > jan2020)

        // Should be before January 1, 2100
        let jan2100: TimeInterval = 4102444800
        #expect(timestampValue < jan2100)
    }
}

// MARK: - APIClient Configuration Tests

struct APIClientConfigTests {

    @Test func sharedInstanceExists() async throws {
        let client = APIClient.shared
        #expect(client != nil)
    }
}

// MARK: - URLSession Pinning Tests

struct URLSessionPinningTests {

    @Test func pinnedSessionHasCorrectConfiguration() async throws {
        let session = URLSession.pinnedSession()

        // Check timeout settings
        #expect(session.configuration.timeoutIntervalForRequest == 30)
        #expect(session.configuration.timeoutIntervalForResource == 60)
    }

    @Test func pinnedSessionWithCustomTimeout() async throws {
        let customTimeout: TimeInterval = 45
        let session = URLSession.pinnedSession(timeoutInterval: customTimeout)

        #expect(session.configuration.timeoutIntervalForRequest == customTimeout)
    }

    @Test func multiplePinnedSessionsAreIndependent() async throws {
        let session1 = URLSession.pinnedSession(timeoutInterval: 10)
        let session2 = URLSession.pinnedSession(timeoutInterval: 20)

        #expect(session1.configuration.timeoutIntervalForRequest == 10)
        #expect(session2.configuration.timeoutIntervalForRequest == 20)
    }
}

// MARK: - HTTPMethod Tests

struct HTTPMethodExtendedTests {

    @Test func allMethodsExist() async throws {
        let methods: [HTTPMethod] = [.get, .post, .put, .delete]

        #expect(methods.count == 4)
    }

    @Test func methodsAreUppercase() async throws {
        #expect(HTTPMethod.get.rawValue == HTTPMethod.get.rawValue.uppercased())
        #expect(HTTPMethod.post.rawValue == HTTPMethod.post.rawValue.uppercased())
        #expect(HTTPMethod.put.rawValue == HTTPMethod.put.rawValue.uppercased())
        #expect(HTTPMethod.delete.rawValue == HTTPMethod.delete.rawValue.uppercased())
    }
}

// MARK: - API Endpoint Extended Tests

struct APIEndpointExtendedTests {

    @Test func allEndpointsHavePaths() async throws {
        let endpoints: [APIEndpoint] = [
            .googleAuth,
            .refreshToken,
            .logout,
            .me,
            .chatSend,
            .chatHistory,
            .conversations,
            .tools,
            .providers,
            .health
        ]

        for endpoint in endpoints {
            #expect(!endpoint.path.isEmpty)
            #expect(endpoint.path.hasPrefix("/"))
        }
    }

    @Test func postEndpointsUsePostMethod() async throws {
        let postEndpoints: [APIEndpoint] = [
            .googleAuth,
            .refreshToken,
            .logout,
            .chatSend,
            .providerConnect
        ]

        for endpoint in postEndpoints {
            #expect(endpoint.method == .post)
        }
    }

    @Test func getEndpointsUseGetMethod() async throws {
        let getEndpoints: [APIEndpoint] = [
            .me,
            .chatHistory,
            .conversations,
            .tools,
            .providers,
            .health
        ]

        for endpoint in getEndpoints {
            #expect(endpoint.method == .get)
        }
    }

    @Test func authEndpointsDontRequireAuth() async throws {
        #expect(APIEndpoint.googleAuth.requiresAuth == false)
        #expect(APIEndpoint.refreshToken.requiresAuth == false)
        #expect(APIEndpoint.health.requiresAuth == false)
    }

    @Test func protectedEndpointsRequireAuth() async throws {
        #expect(APIEndpoint.me.requiresAuth == true)
        #expect(APIEndpoint.chatSend.requiresAuth == true)
        #expect(APIEndpoint.conversations.requiresAuth == true)
        #expect(APIEndpoint.tools.requiresAuth == true)
        #expect(APIEndpoint.providers.requiresAuth == true)
    }
}

// MARK: - Server Error Response Extended Tests

struct ServerErrorResponseExtendedTests {

    @Test func emptyJSONReturnsUnknown() async throws {
        let json = "{}".data(using: .utf8)!
        let decoder = JSONDecoder()
        let response = try decoder.decode(ServerErrorResponse.self, from: json)

        #expect(response.errorMessage == "Unknown error")
    }

    @Test func detailTakesPrecedenceOverMessage() async throws {
        let json = """
        {"detail": "Specific error", "message": "General error"}
        """.data(using: .utf8)!

        let decoder = JSONDecoder()
        let response = try decoder.decode(ServerErrorResponse.self, from: json)

        #expect(response.errorMessage == "Specific error")
    }

    @Test func messageFallbackWhenNoDetail() async throws {
        let json = """
        {"message": "Only message present"}
        """.data(using: .utf8)!

        let decoder = JSONDecoder()
        let response = try decoder.decode(ServerErrorResponse.self, from: json)

        #expect(response.errorMessage == "Only message present")
    }
}

// MARK: - APIError Extended Tests

struct APIErrorExtendedTests {

    @Test func httpErrorWithData() async throws {
        let errorData = """
        {"detail": "Not found"}
        """.data(using: .utf8)

        let error = APIError.httpError(statusCode: 404, data: errorData)

        #expect(error.errorDescription?.contains("404") == true)
    }

    @Test func is4xxError() async throws {
        for statusCode in 400..<500 {
            let error = APIError.httpError(statusCode: statusCode, data: nil)
            // 401 is auth error
            if statusCode == 401 {
                #expect(error.isAuthError == true)
            } else {
                #expect(error.isAuthError == false)
            }
        }
    }

    @Test func is5xxNotAuthError() async throws {
        for statusCode in 500..<600 {
            let error = APIError.httpError(statusCode: statusCode, data: nil)
            #expect(error.isAuthError == false)
        }
    }
}
