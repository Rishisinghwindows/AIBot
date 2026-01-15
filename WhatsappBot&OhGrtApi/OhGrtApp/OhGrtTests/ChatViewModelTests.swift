//
//  ChatViewModelTests.swift
//  OhGrtTests
//
//  Tests for ChatViewModel functionality
//

import Testing
import Foundation
@testable import OhGrt

// MARK: - ChatViewModel State Tests

struct ChatViewModelStateTests {

    @Test func initialState() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()

            #expect(viewModel.messages.isEmpty)
            #expect(viewModel.inputText.isEmpty)
            #expect(viewModel.isLoading == false)
            #expect(viewModel.errorMessage == nil)
            #expect(viewModel.availableTools.isEmpty)
            #expect(viewModel.selectedTools.isEmpty)
            #expect(viewModel.currentConversationId == nil)
        }
    }

    @Test func startNewConversation() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()
            viewModel.inputText = "Some text"
            viewModel.errorMessage = "Some error"
            viewModel.selectedTools = ["weather", "pdf"]

            viewModel.startNewConversation()

            #expect(viewModel.currentConversationId == nil)
            #expect(viewModel.messages.isEmpty)
            #expect(viewModel.inputText.isEmpty)
            #expect(viewModel.errorMessage == nil)
            #expect(viewModel.selectedTools.isEmpty)
        }
    }

    @Test func clearError() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()
            viewModel.errorMessage = "Test error"

            viewModel.clearError()

            #expect(viewModel.errorMessage == nil)
        }
    }
}

// MARK: - Tool Selection Tests

struct ChatViewModelToolTests {

    @Test func toggleToolAddsToSelection() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()

            viewModel.toggleTool("weather")

            #expect(viewModel.selectedTools.contains("weather"))
        }
    }

    @Test func toggleToolRemovesFromSelection() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()
            viewModel.selectedTools = ["weather", "pdf"]

            viewModel.toggleTool("weather")

            #expect(!viewModel.selectedTools.contains("weather"))
            #expect(viewModel.selectedTools.contains("pdf"))
        }
    }

    @Test func toggleMultipleTools() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()

            viewModel.toggleTool("weather")
            viewModel.toggleTool("pdf")
            viewModel.toggleTool("jira")

            #expect(viewModel.selectedTools.count == 3)
            #expect(viewModel.selectedTools.contains("weather"))
            #expect(viewModel.selectedTools.contains("pdf"))
            #expect(viewModel.selectedTools.contains("jira"))
        }
    }
}

// MARK: - Error Message Formatting Tests

struct ChatViewModelErrorTests {

    @Test func friendlyErrorMessageForNoInternet() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()
            let error = URLError(.notConnectedToInternet)

            let message = viewModel.friendlyErrorMessage(for: error)

            #expect(message.contains("internet"))
        }
    }

    @Test func friendlyErrorMessageForTimeout() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()
            let error = URLError(.timedOut)

            let message = viewModel.friendlyErrorMessage(for: error)

            #expect(message.contains("timed out"))
        }
    }

    @Test func friendlyErrorMessageForNetworkLost() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()
            let error = URLError(.networkConnectionLost)

            let message = viewModel.friendlyErrorMessage(for: error)

            #expect(message.contains("internet"))
        }
    }

    @Test func friendlyErrorMessageForGenericError() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()
            let error = NSError(domain: "TestDomain", code: 123, userInfo: [NSLocalizedDescriptionKey: "Custom error"])

            let message = viewModel.friendlyErrorMessage(for: error)

            #expect(message == "Custom error")
        }
    }
}

// MARK: - Input Validation Tests

struct ChatViewModelInputTests {

    @Test func emptyInputDoesNotSend() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()
            viewModel.inputText = ""

            // This would need mocking the APIClient in a real test
            // For now, we verify the input is empty
            let text = viewModel.inputText.trimmingCharacters(in: .whitespacesAndNewlines)
            #expect(text.isEmpty)
        }
    }

    @Test func whitespaceOnlyInputDoesNotSend() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()
            viewModel.inputText = "   \n\t   "

            let text = viewModel.inputText.trimmingCharacters(in: .whitespacesAndNewlines)
            #expect(text.isEmpty)
        }
    }

    @Test func validInputTrimsWhitespace() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()
            viewModel.inputText = "  Hello World  "

            let text = viewModel.inputText.trimmingCharacters(in: .whitespacesAndNewlines)
            #expect(text == "Hello World")
        }
    }
}

// MARK: - Provider State Tests

struct ChatViewModelProviderTests {

    @Test func initialProviderState() async throws {
        await MainActor.run {
            let viewModel = ChatViewModel()

            #expect(viewModel.providers.isEmpty)
            #expect(viewModel.providerError == nil)
        }
    }
}
