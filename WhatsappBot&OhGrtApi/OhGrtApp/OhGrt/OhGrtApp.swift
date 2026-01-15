//
//  OhGrtApp.swift
//  OhGrt
//
//  Created by pawan singh on 12/12/25.
//

import SwiftUI
import SwiftData
import Combine
import FirebaseCore
import GoogleSignIn
import os.log

private let logger = Logger(subsystem: "com.d23.OhGrt", category: "App")

@main
struct OhGrtApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var delegate
    @StateObject private var themeManager = ThemeManager.shared
    @State private var showDatabaseError = false
    @State private var databaseErrorMessage = ""

    let sharedModelContainer: ModelContainer

    init() {
        // Create ModelContainer
        let schema = Schema([
            Message.self,
            Conversation.self,
        ])
        let modelConfiguration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)

        let container: ModelContainer
        do {
            container = try ModelContainer(for: schema, configurations: [modelConfiguration])
        } catch {
            logger.error("Failed to create ModelContainer: \(error.localizedDescription)")
            // Fallback to in-memory storage to prevent crash
            do {
                let fallbackConfig = ModelConfiguration(schema: schema, isStoredInMemoryOnly: true)
                logger.warning("Using in-memory storage as fallback")
                container = try ModelContainer(for: schema, configurations: [fallbackConfig])
            } catch {
                // Last resort - this should never happen with in-memory config
                logger.critical("Critical: Even in-memory ModelContainer failed: \(error.localizedDescription)")
                fatalError("Could not create ModelContainer: \(error)")
            }
        }

        self.sharedModelContainer = container

        // Configure DI container BEFORE any views are created
        DependencyContainer.shared.configure(with: container.mainContext)
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(themeManager)
                .environmentObject(AuthManager.shared)
                .preferredColorScheme(themeManager.colorScheme)
        }
        .modelContainer(sharedModelContainer)
    }
}

/// Root view that switches between splash, onboarding, auth, and main content
struct RootView: View {
    @Environment(\.modelContext) private var modelContext
    @EnvironmentObject private var theme: ThemeManager
    @StateObject private var authViewModel = DependencyContainer.shared.makeAuthViewModel()

    /// Track if splash screen has finished
    @State private var showSplash = true

    /// Track if onboarding has been completed
    @AppStorage("hasCompletedOnboarding") private var hasCompletedOnboarding = false

    /// In development mode, bypass auth and show main content
    private var shouldShowMainContent: Bool {
        AppConfig.shared.isDevelopment || authViewModel.isAuthenticated
    }

    var body: some View {
        ZStack {
            theme.appBackground
                .ignoresSafeArea()

            // Main content (behind splash)
            Group {
                if !hasCompletedOnboarding {
                    // Show onboarding for first-time users
                    OnboardingView()
                        .transition(.opacity.combined(with: .scale(scale: 1.02)))
                } else if shouldShowMainContent {
                    // Show main content for authenticated users
                    MainTabView()
                        .transition(.opacity)
                } else {
                    // Show auth screen for non-authenticated users
                    AuthView(viewModel: authViewModel)
                        .transition(.opacity.combined(with: .move(edge: .trailing)))
                }
            }
            .animation(.easeInOut(duration: 0.4), value: hasCompletedOnboarding)
            .animation(.easeInOut(duration: 0.3), value: shouldShowMainContent)

            // Splash screen overlay
            if showSplash {
                SplashScreenView {
                    withAnimation(.easeInOut(duration: 0.4)) {
                        showSplash = false
                    }
                }
                .transition(.opacity)
                .zIndex(1)
            }
        }
        .withDependencies()
    }
}

/// Main tab view after authentication
struct MainTabView: View {
    @StateObject private var conversationListVM = DependencyContainer.shared.makeConversationListViewModel()
    @EnvironmentObject private var theme: ThemeManager

    var body: some View {
        TabView {
            NavigationStack {
                ChatView(conversationId: nil)
            }
            .tabItem {
                Label("Chat", systemImage: "bubble.left.and.bubble.right.fill")
            }

            NavigationStack {
                ConversationListView(viewModel: conversationListVM)
            }
            .tabItem {
                Label("Chats", systemImage: "tray.full.fill")
            }

            NavigationStack {
                SettingsView()
            }
            .tabItem {
                Label("Settings", systemImage: "gearshape.fill")
            }
        }
        .tint(theme.primaryColor)
    }
}

#Preview {
    RootView()
        .environmentObject(ThemeManager.shared)
        .modelContainer(for: [Message.self, Conversation.self], inMemory: true)
}
