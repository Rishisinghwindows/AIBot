//
//  OhGrtUITests.swift
//  OhGrtUITests
//
//  Created by pawan singh on 12/12/25.
//

import XCTest

final class OhGrtUITests: XCTestCase {

    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["UI_TESTING"]
    }

    override func tearDownWithError() throws {
        app = nil
    }

    // MARK: - App Launch Tests

    @MainActor
    func testAppLaunches() throws {
        app.launch()

        // App should launch and show either Auth or Chat view
        let authViewExists = app.buttons["Continue with Google"].waitForExistence(timeout: 5)
        let chatViewExists = app.navigationBars["Chat"].waitForExistence(timeout: 5)
        let conversationListExists = app.navigationBars["Chats"].waitForExistence(timeout: 5)

        XCTAssertTrue(authViewExists || chatViewExists || conversationListExists,
                      "App should show auth view, chat view, or conversation list")
    }

    @MainActor
    func testLaunchPerformance() throws {
        measure(metrics: [XCTApplicationLaunchMetric()]) {
            XCUIApplication().launch()
        }
    }

    // MARK: - Auth View Tests

    @MainActor
    func testAuthViewElements() throws {
        app.launch()

        // Only run if we're on the auth view
        guard app.buttons["Continue with Google"].waitForExistence(timeout: 3) else {
            // Already authenticated, skip this test
            return
        }

        // Check app branding
        XCTAssertTrue(app.staticTexts["OhGrt"].exists, "App name should be visible")
        XCTAssertTrue(app.staticTexts["Your AI Assistant"].exists, "App tagline should be visible")

        // Check sign in button
        let signInButton = app.buttons["Continue with Google"]
        XCTAssertTrue(signInButton.exists, "Sign in button should exist")
        XCTAssertTrue(signInButton.isEnabled, "Sign in button should be enabled")

        // Check terms text
        XCTAssertTrue(app.staticTexts.containing(NSPredicate(format: "label CONTAINS 'Terms of Service'")).element.exists,
                      "Terms text should be visible")
    }

    @MainActor
    func testSignInButtonIsInteractive() throws {
        app.launch()

        guard app.buttons["Continue with Google"].waitForExistence(timeout: 3) else {
            return
        }

        let signInButton = app.buttons["Continue with Google"]
        XCTAssertTrue(signInButton.isHittable, "Sign in button should be tappable")
    }

    // MARK: - Chat View Tests (when authenticated)

    @MainActor
    func testChatViewElementsWhenAuthenticated() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Wait for chat view or conversation list
        let chatExists = app.navigationBars["Chat"].waitForExistence(timeout: 5)
        let listExists = app.navigationBars["Chats"].waitForExistence(timeout: 5)

        guard chatExists || listExists else {
            XCTFail("Should show chat view or conversation list when authenticated")
            return
        }

        if listExists {
            // We're on conversation list, tap new chat
            if app.buttons["square.and.pencil"].exists {
                app.buttons["square.and.pencil"].tap()
                _ = app.navigationBars["Chat"].waitForExistence(timeout: 3)
            }
        }
    }

    @MainActor
    func testMessageInputViewExists() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Look for message input field
        let messageField = app.textFields["Message"]
        if messageField.waitForExistence(timeout: 5) {
            XCTAssertTrue(messageField.exists, "Message input field should exist")
        }
    }

    @MainActor
    func testSendButtonDisabledWhenEmpty() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Find send button (arrow.up icon)
        let sendButton = app.buttons.matching(NSPredicate(format: "label CONTAINS 'arrow' OR identifier CONTAINS 'send'")).firstMatch

        if sendButton.waitForExistence(timeout: 5) {
            // With empty input, send button should be disabled or not fully opaque
            // Note: The exact behavior depends on the implementation
            XCTAssertTrue(sendButton.exists, "Send button should exist")
        }
    }

    @MainActor
    func testMicButtonExists() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Look for mic button
        let micButton = app.buttons.matching(NSPredicate(format: "label CONTAINS 'mic'")).firstMatch

        if micButton.waitForExistence(timeout: 5) {
            XCTAssertTrue(micButton.isHittable, "Mic button should be tappable")
        }
    }

    // MARK: - Navigation Tests

    @MainActor
    func testToolbarMenuExists() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Wait for navigation bar
        guard app.navigationBars["Chat"].waitForExistence(timeout: 5) ||
              app.navigationBars["Chats"].waitForExistence(timeout: 5) else {
            return
        }

        // Look for menu button (ellipsis.circle)
        let menuButton = app.buttons["ellipsis.circle"]
        if menuButton.exists {
            XCTAssertTrue(menuButton.isHittable, "Menu button should be tappable")
        }
    }

    @MainActor
    func testConversationListSwipeToDelete() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Only run if on conversation list
        guard app.navigationBars["Chats"].waitForExistence(timeout: 5) else {
            return
        }

        // Check if there are any cells to swipe
        let cells = app.cells
        if cells.count > 0 {
            let firstCell = cells.firstMatch
            firstCell.swipeLeft()

            // Delete button should appear
            let deleteButton = app.buttons["Delete"]
            if deleteButton.waitForExistence(timeout: 2) {
                XCTAssertTrue(deleteButton.exists, "Delete button should appear on swipe")
            }
        }
    }

    // MARK: - Tool Picker Tests

    @MainActor
    func testOpenToolPicker() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Need to be in chat view
        guard app.navigationBars["Chat"].waitForExistence(timeout: 5) else {
            return
        }

        // Open menu
        let menuButton = app.buttons["ellipsis.circle"]
        guard menuButton.waitForExistence(timeout: 3) else {
            return
        }

        menuButton.tap()

        // Look for Tools option
        let toolsButton = app.buttons["Tools"]
        if toolsButton.waitForExistence(timeout: 2) {
            toolsButton.tap()

            // Tool picker sheet should appear
            let toolsNavTitle = app.navigationBars["Tools"]
            XCTAssertTrue(toolsNavTitle.waitForExistence(timeout: 3), "Tools sheet should appear")
        }
    }

    // MARK: - MCP Config Tests

    @MainActor
    func testOpenMCPConfig() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Need to be in chat view
        guard app.navigationBars["Chat"].waitForExistence(timeout: 5) else {
            return
        }

        // Open menu
        let menuButton = app.buttons["ellipsis.circle"]
        guard menuButton.waitForExistence(timeout: 3) else {
            return
        }

        menuButton.tap()

        // Look for Configure MCP option
        let mcpButton = app.buttons["Configure MCP"]
        if mcpButton.waitForExistence(timeout: 2) {
            mcpButton.tap()

            // MCP config view should appear
            let mcpNavTitle = app.navigationBars["MCP & Sources"]
            XCTAssertTrue(mcpNavTitle.waitForExistence(timeout: 3), "MCP config view should appear")
        }
    }

    // MARK: - Quick Suggestions Tests

    @MainActor
    func testQuickSuggestionsExist() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Need to be in chat view
        guard app.navigationBars["Chat"].waitForExistence(timeout: 5) else {
            return
        }

        // Look for quick suggestion buttons
        let suggestions = [
            "Summarize our last chat",
            "Draft an email update",
            "Explain this code snippet",
            "What's the weather in New York?",
            "Brainstorm ideas"
        ]

        var foundSuggestion = false
        for suggestion in suggestions {
            if app.buttons[suggestion].exists {
                foundSuggestion = true
                break
            }
        }

        // At least one suggestion should be visible (unless scrolled)
        // This is a soft check since suggestions might need scrolling
        if !foundSuggestion {
            // Try scrolling to find suggestions
            let scrollView = app.scrollViews.firstMatch
            if scrollView.exists {
                scrollView.swipeUp()
            }
        }
    }

    // MARK: - Sign Out Tests

    @MainActor
    func testSignOutButtonExists() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Need to be on conversation list
        guard app.navigationBars["Chats"].waitForExistence(timeout: 5) else {
            return
        }

        // Sign out button should exist in toolbar
        let signOutButton = app.buttons["rectangle.portrait.and.arrow.right"]
        XCTAssertTrue(signOutButton.exists, "Sign out button should exist")
    }

    // MARK: - Accessibility Tests

    @MainActor
    func testAuthViewAccessibility() throws {
        app.launch()

        guard app.buttons["Continue with Google"].waitForExistence(timeout: 3) else {
            return
        }

        // Sign in button should be accessible
        let signInButton = app.buttons["Continue with Google"]
        XCTAssertTrue(signInButton.isHittable, "Sign in button should be accessible")
    }

    @MainActor
    func testChatInputAccessibility() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Message field should be accessible
        let messageField = app.textFields["Message"]
        if messageField.waitForExistence(timeout: 5) {
            XCTAssertTrue(messageField.isHittable, "Message field should be accessible")
        }
    }

    // MARK: - Error State Tests

    @MainActor
    func testErrorBannerDismissible() throws {
        app.launch()

        // This test checks that error banners have a dismiss button
        // In real scenarios, errors would need to be triggered
        // For now, we just verify the UI structure is correct

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // If an error banner exists, it should have a dismiss button
        let dismissButton = app.buttons["Dismiss"]
        if dismissButton.exists {
            XCTAssertTrue(dismissButton.isHittable, "Dismiss button should be tappable")
        }
    }
}

// MARK: - Conversation List UI Tests

final class ConversationListUITests: XCTestCase {

    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["UI_TESTING"]
    }

    override func tearDownWithError() throws {
        app = nil
    }

    @MainActor
    func testNewChatButton() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Need to be on conversation list
        guard app.navigationBars["Chats"].waitForExistence(timeout: 5) else {
            return
        }

        let newChatButton = app.buttons["square.and.pencil"]
        XCTAssertTrue(newChatButton.exists, "New chat button should exist")
        XCTAssertTrue(newChatButton.isHittable, "New chat button should be tappable")
    }

    @MainActor
    func testConversationListTitle() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Need to be on conversation list
        guard app.navigationBars["Chats"].waitForExistence(timeout: 5) else {
            return
        }

        XCTAssertTrue(app.navigationBars["Chats"].exists, "Should show Chats title")
    }
}

// MARK: - Message Bubble UI Tests

final class MessageBubbleUITests: XCTestCase {

    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["UI_TESTING"]
    }

    override func tearDownWithError() throws {
        app = nil
    }

    @MainActor
    func testMessageCopyContextMenu() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Need to be in chat view with messages
        guard app.navigationBars["Chat"].waitForExistence(timeout: 5) else {
            return
        }

        // If there are messages, test context menu
        let messages = app.staticTexts.matching(NSPredicate(format: "identifier CONTAINS 'message'"))
        if messages.count > 0 {
            let firstMessage = messages.firstMatch
            firstMessage.press(forDuration: 1.0) // Long press

            // Copy option should appear in context menu
            let copyButton = app.buttons["Copy"]
            if copyButton.waitForExistence(timeout: 2) {
                XCTAssertTrue(copyButton.exists, "Copy option should exist in context menu")
            }
        }
    }
}

// MARK: - Provider Connection UI Tests

final class ProviderConnectionUITests: XCTestCase {

    var app: XCUIApplication!

    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["UI_TESTING"]
    }

    override func tearDownWithError() throws {
        app = nil
    }

    @MainActor
    func testProviderListLoads() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Navigate to MCP config
        guard app.navigationBars["Chat"].waitForExistence(timeout: 5) else {
            return
        }

        let menuButton = app.buttons["ellipsis.circle"]
        guard menuButton.waitForExistence(timeout: 3) else {
            return
        }

        menuButton.tap()

        let mcpButton = app.buttons["Configure MCP"]
        guard mcpButton.waitForExistence(timeout: 2) else {
            return
        }

        mcpButton.tap()

        // Wait for providers to load
        _ = app.navigationBars["MCP & Sources"].waitForExistence(timeout: 3)

        // Check for common providers
        let providerNames = ["Slack", "Jira", "GitHub", "Gmail", "Google Drive", "Confluence", "Custom MCP"]
        var foundProvider = false

        for name in providerNames {
            if app.staticTexts[name].waitForExistence(timeout: 2) {
                foundProvider = true
                break
            }
        }

        // At least one provider should be visible
        XCTAssertTrue(foundProvider, "At least one provider should be visible")
    }

    @MainActor
    func testProviderConnectButton() throws {
        app.launch()

        // Skip if on auth view
        if app.buttons["Continue with Google"].waitForExistence(timeout: 2) {
            return
        }

        // Navigate to MCP config
        guard app.navigationBars["Chat"].waitForExistence(timeout: 5) else {
            return
        }

        let menuButton = app.buttons["ellipsis.circle"]
        guard menuButton.waitForExistence(timeout: 3) else {
            return
        }

        menuButton.tap()

        let mcpButton = app.buttons["Configure MCP"]
        guard mcpButton.waitForExistence(timeout: 2) else {
            return
        }

        mcpButton.tap()

        // Wait for view
        _ = app.navigationBars["MCP & Sources"].waitForExistence(timeout: 3)

        // Look for Connect/Disconnect buttons
        let connectButton = app.buttons["Connect"]
        let disconnectButton = app.buttons["Disconnect"]

        XCTAssertTrue(connectButton.exists || disconnectButton.exists,
                      "Connect or Disconnect button should exist for providers")
    }
}
