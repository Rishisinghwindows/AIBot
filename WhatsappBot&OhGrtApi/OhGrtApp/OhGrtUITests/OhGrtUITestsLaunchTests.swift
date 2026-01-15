//
//  OhGrtUITestsLaunchTests.swift
//  OhGrtUITests
//
//  Created by pawan singh on 12/12/25.
//

import XCTest

final class OhGrtUITestsLaunchTests: XCTestCase {

    override class var runsForEachTargetApplicationUIConfiguration: Bool {
        true
    }

    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    @MainActor
    func testLaunch() throws {
        let app = XCUIApplication()
        app.launch()

        // Capture launch screen
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = "Launch Screen"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    @MainActor
    func testLaunchAuthView() throws {
        let app = XCUIApplication()
        app.launch()

        // Wait for auth view to appear
        if app.buttons["Continue with Google"].waitForExistence(timeout: 5) {
            let attachment = XCTAttachment(screenshot: app.screenshot())
            attachment.name = "Auth View"
            attachment.lifetime = .keepAlways
            add(attachment)
        }
    }

    @MainActor
    func testLaunchChatView() throws {
        let app = XCUIApplication()
        app.launch()

        // Wait for chat view or conversation list
        let chatExists = app.navigationBars["Chat"].waitForExistence(timeout: 5)
        let listExists = app.navigationBars["Chats"].waitForExistence(timeout: 5)

        if chatExists || listExists {
            let attachment = XCTAttachment(screenshot: app.screenshot())
            attachment.name = "Main View (Authenticated)"
            attachment.lifetime = .keepAlways
            add(attachment)
        }
    }

    @MainActor
    func testLaunchDarkMode() throws {
        let app = XCUIApplication()
        app.launchArguments += ["-UIUserInterfaceStyle", "Dark"]
        app.launch()

        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = "Dark Mode Launch"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    @MainActor
    func testLaunchLightMode() throws {
        let app = XCUIApplication()
        app.launchArguments += ["-UIUserInterfaceStyle", "Light"]
        app.launch()

        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = "Light Mode Launch"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    @MainActor
    func testLaunchLandscape() throws {
        let app = XCUIApplication()
        app.launch()

        XCUIDevice.shared.orientation = .landscapeLeft

        // Wait for orientation change
        Thread.sleep(forTimeInterval: 0.5)

        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = "Landscape Launch"
        attachment.lifetime = .keepAlways
        add(attachment)

        // Reset to portrait
        XCUIDevice.shared.orientation = .portrait
    }

    @MainActor
    func testLaunchWithLargeText() throws {
        let app = XCUIApplication()
        app.launchArguments += ["-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXXXL"]
        app.launch()

        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = "Large Text Launch"
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
