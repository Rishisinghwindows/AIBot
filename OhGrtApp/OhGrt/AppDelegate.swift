//
//  AppDelegate.swift
//  OhGrt
//
//  Created by pawan singh on 13/12/25.
//

import UIKit
import FirebaseCore
import GoogleSignIn
import os.log

private let logger = Logger(subsystem: "com.d23.OhGrt", category: "AppDelegate")

class AppDelegate: NSObject, UIApplicationDelegate {

    /// Flag to track Firebase configuration status
    private(set) var isFirebaseConfigured = false

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil) -> Bool {
        configureFirebase()
        return true
    }

    func application(_ app: UIApplication,
                     open url: URL,
                     options: [UIApplication.OpenURLOptionsKey : Any] = [:]) -> Bool {
        return GIDSignIn.sharedInstance.handle(url)
    }

    // MARK: - Firebase Configuration

    /// Configure Firebase with validation
    private func configureFirebase() {
        // Check if GoogleService-Info.plist exists
        guard let plistPath = Bundle.main.path(forResource: "GoogleService-Info", ofType: "plist") else {
            logger.error("Firebase configuration failed: GoogleService-Info.plist not found in bundle")
            return
        }

        // Validate plist can be read
        guard let plistData = FileManager.default.contents(atPath: plistPath),
              let plistDict = try? PropertyListSerialization.propertyList(from: plistData, format: nil) as? [String: Any] else {
            logger.error("Firebase configuration failed: Unable to read GoogleService-Info.plist")
            return
        }

        // Validate required keys exist
        let requiredKeys = ["API_KEY", "GCM_SENDER_ID", "GOOGLE_APP_ID", "PROJECT_ID"]
        var missingKeys: [String] = []

        for key in requiredKeys {
            if plistDict[key] == nil {
                missingKeys.append(key)
            }
        }

        if !missingKeys.isEmpty {
            logger.error("Firebase configuration failed: Missing required keys: \(missingKeys.joined(separator: ", "))")
            return
        }

        // Validate key values are not empty
        var emptyKeys: [String] = []
        for key in requiredKeys {
            if let value = plistDict[key] as? String, value.isEmpty {
                emptyKeys.append(key)
            }
        }

        if !emptyKeys.isEmpty {
            logger.error("Firebase configuration failed: Empty values for keys: \(emptyKeys.joined(separator: ", "))")
            return
        }

        // Configure Firebase
        do {
            FirebaseApp.configure()
            isFirebaseConfigured = true
            logger.info("Firebase configured successfully")
        } catch {
            logger.error("Firebase configuration failed: \(error.localizedDescription)")
        }
    }
}
