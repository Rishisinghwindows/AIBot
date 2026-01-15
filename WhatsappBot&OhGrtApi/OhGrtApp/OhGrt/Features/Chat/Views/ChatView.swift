import SwiftUI
import SwiftData
import Combine
import Speech
import AVFoundation
import AuthenticationServices
import UIKit

/// Main chat view
struct ChatView: View {
    @Environment(\.modelContext) private var modelContext
    @StateObject private var viewModel = DependencyContainer.shared.makeChatViewModel()
    @ObservedObject private var usageTracker = UsageTracker.shared
    @EnvironmentObject var authManager: AuthManager

    let conversationId: UUID?
    @State private var showingTools = false
    @State private var showingConfigPage = false
    @State private var showingBirthDetails = false
    @State private var showingSubscription = false
    @StateObject private var speechRecognizer = SpeechRecognizer()
    @State private var showingConnectSheet = false
    @State private var providerToConnect: ProviderInfo?
    @State private var providerSecret: String = ""
    @State private var providerDisplayName: String = ""
    @State private var providerBaseURL: String = ""
    @State private var providerUser: String = ""
    @State private var providerProjectKey: String = ""
    @State private var providerOwner: String = ""
    @State private var providerRepo: String = ""
    @State private var authSession: ASWebAuthenticationSession?
    @State private var anchorProvider = PresentationAnchorProvider()
    // Quick suggestions with icons and colors
    private let quickSuggestions: [(text: String, icon: String, color: Color)] = [
        ("Aries horoscope", "sparkles", .purple),
        ("Check PNR", "ticket.fill", .blue),
        ("Weather in Delhi", "cloud.sun.fill", .cyan),
        ("Latest news", "newspaper.fill", .red),
        ("Generate image", "wand.and.stars", .pink),
        ("Set reminder", "bell.badge.fill", .teal),
        ("Nearby places", "location.fill", .green),
        ("Live cricket scores", "sportscourt.fill", .orange),
        ("Govt jobs", "briefcase.fill", .mint),
        ("Draw tarot card", "suit.diamond.fill", .indigo),
        ("Today's Panchang", "calendar", .teal),
        ("Train status", "train.side.front.car", .blue),
        ("Numerology", "number.circle.fill", .orange)
    ]

    @State private var showScrollToBottom = false
    @State private var scrollOffset: CGFloat = 0
    @State private var lastHistoryTrigger = Date.distantPast

    init(conversationId: UUID? = nil) {
        self.conversationId = conversationId
    }

    var body: some View {
        VStack(spacing: 0) {
            // Messages list or welcome screen
            if viewModel.messages.isEmpty && !viewModel.isLoading {
                welcomeView
            } else {
                ZStack(alignment: .bottomTrailing) {
                    ScrollViewReader { proxy in
                        ZStack(alignment: .bottomTrailing) {
                            ScrollView {
                                LazyVStack(spacing: 12) {
                                    TopHistorySentinel()

                                    if viewModel.hasMoreHistory || viewModel.isLoadingMore {
                                        LoadingHistoryShimmerRow(isLoading: viewModel.isLoadingMore)
                                            .transition(.opacity)
                                    }

                                    ForEach(viewModel.messages, id: \.id) { message in
                                        MessageBubble(
                                            message: message,
                                            onRetry: {
                                                Task {
                                                    await viewModel.retryMessage(message)
                                                }
                                            }
                                        )
                                        .id(message.id)
                                    }

                                    if viewModel.isSending {
                                        TypingIndicator()
                                            .id("typing")
                                    }

                                    // Spacer for scroll detection
                                    Color.clear
                                        .frame(height: 1)
                                        .id("bottom")
                                }
                                .padding()
                                .background(
                                    GeometryReader { geo in
                                        Color.clear.preference(
                                            key: ScrollOffsetPreferenceKey.self,
                                            value: geo.frame(in: .named("scroll")).minY
                                        )
                                    }
                                )
                            }
                            .background(chatBackground)
                            .coordinateSpace(name: "scroll")
                            .onPreferenceChange(ScrollOffsetPreferenceKey.self) { value in
                                let threshold: CGFloat = -200
                                withAnimation(.easeInOut(duration: 0.2)) {
                                    showScrollToBottom = value < threshold
                                }
                            }
                            .onPreferenceChange(TopHistoryPreferenceKey.self) { value in
                                guard value > -40 else { return }
                                guard viewModel.hasMoreHistory, !viewModel.isLoadingMore else { return }
                                let now = Date()
                                guard now.timeIntervalSince(lastHistoryTrigger) > 1 else { return }
                                lastHistoryTrigger = now
                                Task {
                                    await viewModel.loadMoreHistory()
                                }
                            }
                            .onChange(of: viewModel.messages.count) { _, _ in
                                if !viewModel.isLoadingMore {
                                    scrollToBottom(proxy: proxy)
                                }
                            }
                            .onChange(of: viewModel.isSending) { _, isSending in
                                if isSending {
                                    scrollToBottom(proxy: proxy, toTyping: true)
                                }
                            }

                            // Scroll to bottom FAB
                            if showScrollToBottom {
                                ScrollToBottomButton(action: {
                                    scrollToBottom(proxy: proxy)
                                }, unreadCount: 0)
                                .padding(.trailing, 16)
                                .padding(.bottom, 16)
                                .transition(.scale.combined(with: .opacity))
                            }
                        }
                    }
                }
            }

            suggestionBar

            // Usage indicator for free tier users
            if !SubscriptionManager.shared.subscriptionStatus.isActive {
                usageIndicatorBar
            }

            if !viewModel.selectedTools.isEmpty {
                selectedToolsBar
            }

            // Error banner
            if let error = viewModel.errorMessage {
                ChatErrorBanner(
                    message: error,
                    onDismiss: { viewModel.clearError() },
                    onRetry: {
                        Task {
                            if let lastMessage = viewModel.messages.last(where: { $0.isUser && !$0.isSynced }) {
                                await viewModel.retryMessage(lastMessage)
                            }
                        }
                    }
                )
                .transition(.move(edge: .top).combined(with: .opacity))
            }

            // Location prompt
            if viewModel.showLocationPrompt {
                LocationPromptView(
                    onShareLocation: { coordinate, accuracy in
                        viewModel.handleLocationShare(coordinate, accuracy: accuracy)
                    },
                    onDismiss: {
                        viewModel.dismissLocationPrompt()
                    }
                )
                .padding(.horizontal)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }

            Divider()

            // Input area
            MessageInputView(
                text: $viewModel.inputText,
                isLoading: viewModel.isSending,
                onMic: {
                    Task {
                        await startVoiceInput()
                    }
                },
                onSend: {
                    Task {
                        await viewModel.sendMessage()
                    }
                }
            )
        }
        .background(chatBackground.ignoresSafeArea())
        .overlay(alignment: .bottomLeading) {
            if speechRecognizer.isRecording {
                listeningBanner
                    .padding(.leading, 16)
                    .padding(.bottom, 92)
            }
        }
        .navigationTitle("Chat")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Menu {
                    Button(action: {
                        viewModel.startNewConversation()
                    }) {
                        Label("New Chat", systemImage: "plus.message")
                    }

                    Button(action: {
                        showingTools = true
                    }) {
                        Label("Tools", systemImage: "wrench.and.screwdriver")
                    }

                    Button(action: {
                        showingConfigPage = true
                    }) {
                        Label("Configure MCP", systemImage: "slider.horizontal.3")
                    }

                    Divider()

                    Button(action: {
                        showingBirthDetails = true
                    }) {
                        Label("Birth Details", systemImage: "sparkles")
                    }

                    Button(action: {
                        showingSubscription = true
                    }) {
                        Label("Premium", systemImage: "crown.fill")
                    }

                    Divider()

                    Button(action: {
                        Task {
                            await viewModel.loadHistoryFromServer()
                        }
                    }) {
                        Label("Refresh", systemImage: "arrow.clockwise")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                }
            }
        }
        // Inline navigation destination to avoid overlay hacks
        .background(
            NavigationLink(
                destination: MCPConfigView(
                    providers: viewModel.providers,
                    providerError: viewModel.providerError,
                    onConnectProvider: { provider in
                        if provider.authType == "oauth" {
                            Task { await startOAuth(provider: provider) }
                        } else {
                            providerToConnect = provider
                            providerSecret = ""
                            providerDisplayName = provider.displayName
                            providerBaseURL = ""
                            providerUser = ""
                            providerProjectKey = ""
                            providerOwner = ""
                            providerRepo = ""
                            showingConnectSheet = true
                        }
                    },
                    onDisconnectProvider: { provider in
                        Task { await viewModel.disconnectProvider(provider) }
                    },
                    onRefresh: {
                        await viewModel.loadProviders()
                    }
                ),
                isActive: $showingConfigPage
            ) {
                EmptyView()
            }
            .hidden()
        )
        .onAppear {
            viewModel.setModelContext(modelContext)
            if let convId = conversationId {
                viewModel.loadConversation(convId)
            }
            Task {
                if viewModel.availableTools.isEmpty {
                    await viewModel.loadTools()
                }
                await viewModel.loadProviders()
            }
        }
        .sheet(isPresented: $showingTools) {
            ToolPickerView(
                availableTools: viewModel.availableTools,
                selectedTools: $viewModel.selectedTools,
                errorMessage: viewModel.toolsError,
                onRefresh: {
                    await viewModel.loadTools()
                },
                onToggle: { name in
                    viewModel.toggleTool(name)
                }
            )
        }
        .sheet(isPresented: $showingConnectSheet) {
            if let provider = providerToConnect {
                ProviderConnectSheet(
                    provider: provider,
                    secret: $providerSecret,
                    displayName: $providerDisplayName,
                    baseURL: $providerBaseURL,
                    userField: $providerUser,
                    projectKey: $providerProjectKey,
                    ownerField: $providerOwner,
                    repoField: $providerRepo,
                    onCancel: { showingConnectSheet = false },
                    onConnect: {
                        showingConnectSheet = false
                        Task {
                            var config: [String: String] = [:]
                            if !providerBaseURL.isEmpty {
                                config["base_url"] = providerBaseURL
                            }
                            if !providerUser.isEmpty {
                                config["user"] = providerUser
                            }
                            if !providerProjectKey.isEmpty {
                                config["project_key"] = providerProjectKey
                            }
                            if !providerOwner.isEmpty {
                                config["owner"] = providerOwner
                            }
                            if !providerRepo.isEmpty {
                                config["repo"] = providerRepo
                            }
                            await viewModel.connectProvider(provider, secret: providerSecret, displayName: providerDisplayName, config: config.isEmpty ? nil : config)
                        }
                    }
                )
                .presentationDetents([.medium])
            }
        }
        .sheet(isPresented: $showingBirthDetails) {
            BirthDetailsView()
        }
        .sheet(isPresented: $showingSubscription) {
            SubscriptionView()
        }
        .onChange(of: speechRecognizer.transcript) { _, newValue in
            if speechRecognizer.isRecording {
                viewModel.inputText = newValue
            }
        }
        .onChange(of: viewModel.shouldShowSubscription) { _, shouldShow in
            if shouldShow {
                showingSubscription = true
                viewModel.shouldShowSubscription = false
            }
        }
    }

    private var chatBackground: some View {
        LinearGradient(
            colors: [
                Color(red: 0.05, green: 0.03, blue: 0.08),
                Color(red: 0.02, green: 0.02, blue: 0.05),
                Color.black
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    private func scrollToBottom(proxy: ScrollViewProxy, toTyping: Bool = false) {
        withAnimation(.easeOut(duration: 0.2)) {
            if toTyping {
                proxy.scrollTo("typing", anchor: .bottom)
            } else if let lastMessage = viewModel.messages.last {
                proxy.scrollTo(lastMessage.id, anchor: .bottom)
            }
        }
    }
    
    private var suggestionBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                ForEach(quickSuggestions, id: \.text) { suggestion in
                    SuggestionChip(
                        text: suggestion.text,
                        icon: suggestion.icon,
                        color: suggestion.color
                    ) {
                        guard !viewModel.isLoading else { return }
                        Task {
                            viewModel.inputText = suggestion.text
                            await viewModel.sendMessage()
                        }
                    }
                    .disabled(viewModel.isLoading)
                    .opacity(viewModel.isLoading ? 0.6 : 1.0)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
        }
        .background(
            LinearGradient(
                colors: [Color(.systemBackground), Color(.systemBackground).opacity(0.95)],
                startPoint: .top,
                endPoint: .bottom
            )
        )
    }
    
    private var selectedToolsBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(Array(viewModel.selectedTools), id: \.self) { tool in
                    HStack(spacing: 6) {
                        Image(systemName: "wrench.adjustable")
                        Text(tool)
                    }
                    .font(.caption)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Color.blue.opacity(0.1))
                    .foregroundColor(.blue)
                    .cornerRadius(12)
                }
            }
            .padding(.horizontal)
            .padding(.bottom, 4)
        }
    }

    private var usageIndicatorBar: some View {
        Button {
            showingSubscription = true
        } label: {
            HStack(spacing: 8) {
                Image(systemName: usageTracker.isAtLimit ? "exclamationmark.triangle.fill" : "sparkles")
                    .foregroundColor(usageTracker.isAtLimit ? .orange : .purple)

                Text(usageTracker.usageDescription)
                    .font(.caption)
                    .foregroundColor(.secondary)

                Spacer()

                Text("Upgrade")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.white)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(Color.purple)
                    .cornerRadius(8)
            }
            .padding(.horizontal)
            .padding(.vertical, 6)
            .background(usageTracker.isAtLimit ? Color.orange.opacity(0.1) : Color.purple.opacity(0.05))
        }
        .buttonStyle(.plain)
    }

    private var listeningBanner: some View {
        HStack(spacing: 8) {
            ProgressView()
                .progressViewStyle(CircularProgressViewStyle(tint: .white))
            Text("Listening... speak now")
                .font(.footnote)
                .foregroundColor(.white)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(.blue)
        .cornerRadius(14)
        .shadow(radius: 4)
    }

    private var welcomeView: some View {
        WelcomeScreen(
            selectedToolsCount: viewModel.selectedTools.count,
            connectedProvidersCount: viewModel.providers.filter { $0.connected }.count,
            onCardTapped: { prompt in
                // Set the input text and send the message
                viewModel.inputText = prompt
                Task {
                    await viewModel.sendMessage()
                }
            }
        )
    }
    
    private func startVoiceInput() async {
        // Voice input is a premium feature
        if !SubscriptionManager.shared.subscriptionStatus.isActive {
            showingSubscription = true
            return
        }

        await speechRecognizer.toggle()
        if !speechRecognizer.isRecording, !speechRecognizer.transcript.isEmpty {
            viewModel.inputText = speechRecognizer.transcript
        }
    }

    private func startOAuth(provider: ProviderInfo) async {
        do {
            let start = try await viewModel.startOAuth(for: provider)
            guard let url = URL(string: start.authUrl) else {
                await MainActor.run { viewModel.providerError = "Invalid auth URL" }
                return
            }
            let callbackScheme = "ohgrt"
            if let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
               let redirect = components.queryItems?.first(where: { $0.name == "redirect_uri" })?.value,
               let redirectURL = URL(string: redirect),
               redirectURL.scheme?.lowercased() != callbackScheme {
                await MainActor.run {
                    viewModel.providerError = "\(provider.displayName) auth misconfigured: redirect_uri must use \(callbackScheme)://"
                }
                return
            }
            let session = ASWebAuthenticationSession(url: url, callbackURLScheme: callbackScheme) { [weak viewModel] callbackURL, error in
                // Clear session reference on completion to avoid retain cycles
                Task { @MainActor in
                    self.authSession = nil
                }

                if let error = error {
                    print("[OAuth] \(provider.name) auth cancelled/error: \(error)")
                    return
                }
                guard let callbackURL = callbackURL,
                      let components = URLComponents(url: callbackURL, resolvingAgainstBaseURL: false),
                      let queryItems = components.queryItems else {
                    Task { @MainActor in viewModel?.providerError = "\(provider.displayName) auth failed: invalid callback" }
                    return
                }
                let code = queryItems.first(where: { $0.name == "code" })?.value
                let state = queryItems.first(where: { $0.name == "state" })?.value
                guard let code = code, let state = state else {
                    Task { @MainActor in viewModel?.providerError = "\(provider.displayName) auth failed: missing code/state" }
                    return
                }
                Task { await viewModel?.completeOAuth(for: provider, code: code, state: state) }
            }
            session.prefersEphemeralWebBrowserSession = true
            session.presentationContextProvider = anchorProvider
            authSession = session
            session.start()
        } catch {
            let friendly = viewModel.friendlyErrorMessage(for: error)
            await MainActor.run { viewModel.providerError = friendly }
        }
    }
}

private struct TopHistorySentinel: View {
    var body: some View {
        GeometryReader { geo in
            Color.clear.preference(
                key: TopHistoryPreferenceKey.self,
                value: geo.frame(in: .named("scroll")).minY
            )
        }
        .frame(height: 1)
    }
}

private struct LoadingHistoryShimmerRow: View {
    let isLoading: Bool
    @State private var shimmerPhase: CGFloat = -0.6

    var body: some View {
        RoundedRectangle(cornerRadius: 12)
            .fill(Color.white.opacity(0.06))
            .frame(height: 36)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .fill(
                        LinearGradient(
                            colors: [
                                Color.white.opacity(0.05),
                                Color.white.opacity(0.18),
                                Color.white.opacity(0.05)
                            ],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .rotationEffect(.degrees(12))
                    .offset(x: shimmerPhase * 220)
                    .opacity(isLoading ? 1 : 0.3)
            )
            .overlay(
                HStack(spacing: 8) {
                    if isLoading {
                        ProgressView()
                            .tint(.white.opacity(0.8))
                    }
                    Text(isLoading ? "Loading earlier messages..." : "Pull up to load older messages")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.65))
                }
            )
            .onAppear {
                withAnimation(.linear(duration: 1.3).repeatForever(autoreverses: false)) {
                    shimmerPhase = 0.6
                }
            }
    }
}

private struct TopHistoryPreferenceKey: PreferenceKey {
    static var defaultValue: CGFloat = 0
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) {
        value = nextValue()
    }
}

// Helper to provide presentation anchor for ASWebAuthenticationSession
final class PresentationAnchorProvider: NSObject, ASWebAuthenticationPresentationContextProviding {
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        return UIApplication.shared.connectedScenes
            .compactMap { ($0 as? UIWindowScene)?.keyWindow }
            .first ?? ASPresentationAnchor()
    }
}

@MainActor
final class SpeechRecognizer: NSObject, ObservableObject {
    @Published var transcript: String = ""
    @Published var isRecording = false

    private let audioEngine = AVAudioEngine()
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let recognizer = SFSpeechRecognizer()

    deinit {
        // Ensure cleanup on deallocation
        if audioEngine.isRunning {
            audioEngine.stop()
        }
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()
    }

    private func cleanup() {
        if audioEngine.isRunning {
            audioEngine.stop()
        }
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        recognitionTask?.cancel()
        recognitionTask = nil
    }

    func toggle() async {
        if isRecording {
            stop()
        } else {
            await start()
        }
    }

    private func start() async {
        let authorized = await requestAuthorization()
        guard authorized else {
            transcript = "Speech permission denied."
            return
        }

        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.playAndRecord, mode: .default, options: [.duckOthers])
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)

            recognitionTask?.cancel()
            recognitionTask = nil

            let request = SFSpeechAudioBufferRecognitionRequest()
            request.shouldReportPartialResults = true
            recognitionRequest = request

            let inputNode = audioEngine.inputNode
            let recordingFormat = inputNode.outputFormat(forBus: 0)
            inputNode.removeTap(onBus: 0)
            inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
                self?.recognitionRequest?.append(buffer)
            }

            audioEngine.prepare()
            try audioEngine.start()

            recognitionTask = recognizer?.recognitionTask(with: request) { [weak self] result, error in
                guard let self else { return }
                if let result {
                    self.transcript = result.bestTranscription.formattedString
                }
                if error != nil || (result?.isFinal ?? false) {
                    self.stop()
                }
            }

            isRecording = true
        } catch {
            stop()
            transcript = "Voice capture failed."
        }
    }

    private func stop() {
        cleanup()
        isRecording = false
    }

    private func requestAuthorization() async -> Bool {
        await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status == .authorized)
            }
        }
    }
}

// MARK: - Conversation List View

/// View showing list of conversations
private enum ConversationDestination: Hashable {
    case conversation(UUID)
    case new
}

struct LegacyConversationListView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \Conversation.updatedAt, order: .reverse) private var conversations: [Conversation]
    @EnvironmentObject var authManager: AuthManager

    @State private var selection: ConversationDestination?
    @State private var mcpActive = false
    @State private var listAppeared = false
    @State private var searchText = ""
    @State private var showingNewChatAnimation = false
    @State private var showingSettings = false

    private var filteredConversations: [Conversation] {
        if searchText.isEmpty {
            return conversations
        }
        return conversations.filter { conversation in
            (conversation.title?.localizedCaseInsensitiveContains(searchText) ?? false) ||
            conversation.preview.localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        NavigationSplitView {
            Group {
                if conversations.isEmpty {
                    AnimatedEmptyStateView(onNewChat: {
                        withAnimation(.spring(response: 0.4, dampingFraction: 0.7)) {
                            showingNewChatAnimation = true
                        }
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                            selection = .new
                            showingNewChatAnimation = false
                        }
                    })
                } else {
                    conversationList
                }
            }
            .navigationTitle("Chats")
            .searchable(text: $searchText, prompt: "Search conversations")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    HStack(spacing: 16) {
                        Button(action: {
                            let feedback = UIImpactFeedbackGenerator(style: .light)
                            feedback.impactOccurred()
                            showingSettings = true
                        }) {
                            Image(systemName: "gearshape.fill")
                                .foregroundStyle(
                                    LinearGradient(
                                        colors: ThemeManager.shared.accentTheme.primaryColors,
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                        }

                        Button(action: {
                            Task {
                                await authManager.signOut()
                            }
                        }) {
                            Image(systemName: "rectangle.portrait.and.arrow.right")
                                .foregroundStyle(
                                    LinearGradient(
                                        colors: [.red.opacity(0.8), .orange],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                        }
                    }
                }

                ToolbarItem(placement: .navigationBarTrailing) {
                    newChatButton
                }
            }
            .sheet(isPresented: $showingSettings) {
                SettingsView()
            }
            .navigationDestination(item: $selection) { destination in
                switch destination {
                case .conversation(let id):
                    ChatView(conversationId: id)
                case .new:
                    ChatView(conversationId: nil)
                }
            }
        } detail: {
            switch selection {
            case .conversation(let id):
                ChatView(conversationId: id)
            case .new:
                ChatView(conversationId: nil)
            case .none:
                AnimatedDetailEmptyView(onNewChat: { selection = .new })
            }
        }
        .onAppear {
            ensureSelection()
            withAnimation(.easeOut(duration: 0.5).delay(0.2)) {
                listAppeared = true
            }
        }
        .onChange(of: conversations.count) { _, _ in
            ensureSelection()
        }
    }

    // MARK: - New Chat Button

    private var newChatButton: some View {
        Button(action: {
            let feedback = UIImpactFeedbackGenerator(style: .medium)
            feedback.impactOccurred()
            withAnimation(.spring(response: 0.4, dampingFraction: 0.7)) {
                showingNewChatAnimation = true
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                selection = .new
                showingNewChatAnimation = false
            }
        }) {
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [.blue, .purple],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 32, height: 32)
                    .shadow(color: .blue.opacity(0.3), radius: 4, y: 2)
                    .scaleEffect(showingNewChatAnimation ? 1.2 : 1.0)

                Image(systemName: "plus")
                    .font(.system(size: 14, weight: .bold))
                    .foregroundColor(.white)
                    .rotationEffect(.degrees(showingNewChatAnimation ? 90 : 0))
            }
        }
    }

    // MARK: - Conversation List

    private var conversationList: some View {
        List(selection: $selection) {
            // Header stats
            if !searchText.isEmpty {
                searchResultsHeader
            }

            ForEach(Array(filteredConversations.enumerated()), id: \.element.id) { index, conversation in
                NavigationLink(value: ConversationDestination.conversation(conversation.id)) {
                    AnimatedConversationRow(
                        conversation: conversation,
                        index: index,
                        isVisible: listAppeared
                    )
                }
                .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                    Button(role: .destructive) {
                        withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                            deleteConversation(conversation)
                        }
                    } label: {
                        Label("Delete", systemImage: "trash.fill")
                    }
                }
                .swipeActions(edge: .leading, allowsFullSwipe: false) {
                    Button {
                        // Pin action (future feature)
                        let feedback = UIImpactFeedbackGenerator(style: .light)
                        feedback.impactOccurred()
                    } label: {
                        Label("Pin", systemImage: "pin.fill")
                    }
                    .tint(.orange)
                }
            }
        }
        .listStyle(.insetGrouped)
        .animation(.spring(response: 0.4, dampingFraction: 0.8), value: filteredConversations.count)
    }

    private var searchResultsHeader: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)
            Text("\(filteredConversations.count) result\(filteredConversations.count == 1 ? "" : "s")")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .listRowBackground(Color.clear)
    }

    private func deleteConversation(_ conversation: Conversation) {
        if case .conversation(conversation.id) = selection {
            selection = nil
        }
        modelContext.delete(conversation)
        try? modelContext.save()
    }

    private func deleteConversations(at offsets: IndexSet) {
        for index in offsets {
            let conversation = filteredConversations[index]
            deleteConversation(conversation)
        }
    }

    private func ensureSelection() {
        guard selection == nil else { return }
        if let first = conversations.first {
            selection = .conversation(first.id)
        } else {
            selection = .new
        }
    }
}

// MARK: - Animated Conversation Row

struct AnimatedConversationRow: View {
    let conversation: Conversation
    let index: Int
    let isVisible: Bool

    @State private var appeared = false
    @State private var isPressed = false

    private var categoryIcon: String {
        // Detect category from title or preview
        let text = (conversation.title ?? "").lowercased() + conversation.preview.lowercased()
        if text.contains("horoscope") || text.contains("astrology") || text.contains("zodiac") {
            return "sparkles"
        } else if text.contains("weather") {
            return "cloud.sun.fill"
        } else if text.contains("pnr") || text.contains("train") {
            return "train.side.front.car"
        } else if text.contains("news") {
            return "newspaper.fill"
        } else if text.contains("tarot") {
            return "suit.diamond.fill"
        }
        return "bubble.left.fill"
    }

    private var categoryColor: Color {
        let text = (conversation.title ?? "").lowercased() + conversation.preview.lowercased()
        if text.contains("horoscope") || text.contains("astrology") || text.contains("zodiac") {
            return .purple
        } else if text.contains("weather") {
            return .cyan
        } else if text.contains("pnr") || text.contains("train") {
            return .blue
        } else if text.contains("news") {
            return .red
        } else if text.contains("tarot") {
            return .indigo
        }
        return .blue
    }

    var body: some View {
        HStack(spacing: 14) {
            // Category Icon
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [categoryColor.opacity(0.2), categoryColor.opacity(0.1)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 48, height: 48)

                Image(systemName: categoryIcon)
                    .font(.system(size: 20, weight: .medium))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [categoryColor, categoryColor.opacity(0.7)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            }

            // Content
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(conversation.title ?? "New Chat")
                        .font(.headline)
                        .fontWeight(.semibold)
                        .lineLimit(1)

                    Spacer()

                    // Time badge with animation
                    TimeBadge(date: conversation.updatedAt)
                }

                Text(conversation.preview)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(2)

                // Stats row
                HStack(spacing: 10) {
                    StatBadge(
                        icon: "message.fill",
                        text: "\(conversation.messageCount)",
                        color: .secondary
                    )

                    if !conversation.tools.isEmpty {
                        StatBadge(
                            icon: "wrench.adjustable.fill",
                            text: "\(conversation.tools.count)",
                            color: .blue
                        )
                    }

                    Spacer()

                    // Unread indicator (visual enhancement)
                    if isRecent(conversation.updatedAt) {
                        Circle()
                            .fill(Color.green)
                            .frame(width: 8, height: 8)
                    }
                }
            }
        }
        .padding(.vertical, 8)
        .scaleEffect(isPressed ? 0.98 : 1.0)
        .opacity(appeared ? 1.0 : 0)
        .offset(x: appeared ? 0 : -30)
        .onAppear {
            let delay = Double(min(index, 10)) * 0.05
            withAnimation(.spring(response: 0.5, dampingFraction: 0.7).delay(delay)) {
                appeared = true
            }
        }
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    withAnimation(.easeInOut(duration: 0.1)) {
                        isPressed = true
                    }
                }
                .onEnded { _ in
                    withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                        isPressed = false
                    }
                }
        )
    }

    private func isRecent(_ date: Date) -> Bool {
        Date().timeIntervalSince(date) < 300 // 5 minutes
    }
}

// MARK: - Supporting Views

struct TimeBadge: View {
    let date: Date

    var body: some View {
        Text(date, style: .relative)
            .font(.caption2)
            .fontWeight(.medium)
            .foregroundColor(.secondary)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(
                Capsule()
                    .fill(Color(.tertiarySystemBackground))
            )
    }
}

struct StatBadge: View {
    let icon: String
    let text: String
    let color: Color

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.system(size: 10))
            Text(text)
                .font(.caption2)
                .fontWeight(.medium)
        }
        .foregroundColor(color)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            Capsule()
                .fill(color.opacity(0.1))
        )
    }
}

// MARK: - Animated Empty State

struct AnimatedEmptyStateView: View {
    let onNewChat: () -> Void

    @State private var iconScale: CGFloat = 0.5
    @State private var iconOpacity: Double = 0
    @State private var textOpacity: Double = 0
    @State private var buttonOpacity: Double = 0
    @State private var floatingOffset: CGFloat = 0
    @State private var pulseAnimation = false
    @State private var rotationAngle: Double = 0

    var body: some View {
        VStack(spacing: 28) {
            Spacer()

            // Animated icon
            ZStack {
                // Outer pulse rings
                ForEach(0..<3, id: \.self) { i in
                    Circle()
                        .stroke(
                            LinearGradient(
                                colors: [.blue.opacity(0.3), .purple.opacity(0.3)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 2
                        )
                        .frame(width: 100 + CGFloat(i * 30), height: 100 + CGFloat(i * 30))
                        .scaleEffect(pulseAnimation ? 1.2 : 1.0)
                        .opacity(pulseAnimation ? 0 : 0.5)
                        .animation(
                            .easeInOut(duration: 2)
                            .repeatForever(autoreverses: false)
                            .delay(Double(i) * 0.4),
                            value: pulseAnimation
                        )
                }

                // Main circle
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [.blue.opacity(0.2), .purple.opacity(0.2)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 120, height: 120)
                    .offset(y: floatingOffset)

                // Icon
                Image(systemName: "bubble.left.and.bubble.right.fill")
                    .font(.system(size: 50, weight: .medium))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.blue, .purple],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .rotationEffect(.degrees(rotationAngle))
                    .offset(y: floatingOffset)
            }
            .scaleEffect(iconScale)
            .opacity(iconOpacity)

            // Text content
            VStack(spacing: 12) {
                Text("No Conversations Yet")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.primary, .primary.opacity(0.8)],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )

                Text("Start your first chat with OhGrt\nand explore AI-powered features")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            .opacity(textOpacity)

            // Animated button
            Button(action: {
                let feedback = UIImpactFeedbackGenerator(style: .medium)
                feedback.impactOccurred()
                onNewChat()
            }) {
                HStack(spacing: 8) {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 18))
                    Text("Start New Chat")
                        .fontWeight(.semibold)
                }
                .foregroundColor(.white)
                .padding(.horizontal, 28)
                .padding(.vertical, 14)
                .background(
                    LinearGradient(
                        colors: [.blue, .purple],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .cornerRadius(16)
                .shadow(color: .blue.opacity(0.4), radius: 12, y: 6)
            }
            .opacity(buttonOpacity)
            .scaleEffect(buttonOpacity)

            Spacer()
        }
        .frame(maxWidth: .infinity)
        .onAppear {
            startAnimations()
        }
    }

    private func startAnimations() {
        withAnimation(.spring(response: 0.8, dampingFraction: 0.6).delay(0.1)) {
            iconScale = 1.0
            iconOpacity = 1.0
        }

        withAnimation(.easeOut(duration: 0.6).delay(0.4)) {
            textOpacity = 1.0
        }

        withAnimation(.spring(response: 0.6, dampingFraction: 0.7).delay(0.6)) {
            buttonOpacity = 1.0
        }

        pulseAnimation = true

        withAnimation(.easeInOut(duration: 3).repeatForever(autoreverses: true)) {
            floatingOffset = -10
        }

        withAnimation(.easeInOut(duration: 4).repeatForever(autoreverses: true)) {
            rotationAngle = 5
        }
    }
}

// MARK: - Animated Detail Empty View

struct AnimatedDetailEmptyView: View {
    let onNewChat: () -> Void

    @State private var appeared = false
    @State private var iconRotation: Double = 0
    @State private var shimmerOffset: CGFloat = -200
    @State private var particleOpacity: [Double] = Array(repeating: 0, count: 5)

    var body: some View {
        ZStack {
            // Background particles
            ForEach(0..<5, id: \.self) { i in
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [.purple.opacity(0.3), .blue.opacity(0.3)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: CGFloat.random(in: 20...40))
                    .offset(
                        x: CGFloat.random(in: -100...100),
                        y: CGFloat.random(in: -150...150)
                    )
                    .opacity(particleOpacity[i])
                    .blur(radius: 10)
            }

            VStack(spacing: 28) {
                // Animated logo
                ZStack {
                    Circle()
                        .fill(
                            RadialGradient(
                                colors: [.blue.opacity(0.15), .clear],
                                center: .center,
                                startRadius: 0,
                                endRadius: 80
                            )
                        )
                        .frame(width: 160, height: 160)

                    Circle()
                        .stroke(
                            AngularGradient(
                                colors: [.blue, .purple, .pink, .blue],
                                center: .center
                            ),
                            lineWidth: 3
                        )
                        .frame(width: 130, height: 130)
                        .rotationEffect(.degrees(iconRotation))

                    Image(systemName: "sparkles")
                        .font(.system(size: 55, weight: .medium))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [.blue, .purple],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .symbolEffect(.pulse, options: .repeating)
                }

                VStack(spacing: 12) {
                    Text("Welcome to OhGrt")
                        .font(.title)
                        .fontWeight(.bold)
                        .foregroundStyle(
                            LinearGradient(
                                colors: [.primary, .primary.opacity(0.8)],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )

                    Text("Select a conversation or start a new chat\nto begin your AI-powered journey")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                }

                // Feature chips
                HStack(spacing: 12) {
                    FeatureChip(icon: "sparkles", text: "Astrology", color: .purple)
                    FeatureChip(icon: "train.side.front.car", text: "Travel", color: .blue)
                    FeatureChip(icon: "newspaper.fill", text: "News", color: .red)
                }

                Button(action: {
                    let feedback = UIImpactFeedbackGenerator(style: .medium)
                    feedback.impactOccurred()
                    onNewChat()
                }) {
                    HStack(spacing: 8) {
                        Image(systemName: "plus.message.fill")
                        Text("Start New Chat")
                    }
                    .fontWeight(.semibold)
                    .foregroundColor(.white)
                    .padding(.horizontal, 32)
                    .padding(.vertical, 16)
                    .background(
                        LinearGradient(
                            colors: [.blue, .purple],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .cornerRadius(16)
                    .shadow(color: .blue.opacity(0.4), radius: 15, y: 8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .fill(
                                LinearGradient(
                                    colors: [.white.opacity(0.3), .clear],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .offset(x: shimmerOffset)
                            .mask(RoundedRectangle(cornerRadius: 16))
                    )
                }
            }
            .scaleEffect(appeared ? 1.0 : 0.9)
            .opacity(appeared ? 1.0 : 0)
        }
        .onAppear {
            withAnimation(.spring(response: 0.6, dampingFraction: 0.7)) {
                appeared = true
            }

            withAnimation(.linear(duration: 10).repeatForever(autoreverses: false)) {
                iconRotation = 360
            }

            withAnimation(.linear(duration: 2).repeatForever(autoreverses: false).delay(0.5)) {
                shimmerOffset = 300
            }

            // Animate particles
            for i in 0..<5 {
                withAnimation(.easeInOut(duration: 2).repeatForever(autoreverses: true).delay(Double(i) * 0.3)) {
                    particleOpacity[i] = Double.random(in: 0.3...0.7)
                }
            }
        }
    }
}

struct FeatureChip: View {
    let icon: String
    let text: String
    let color: Color

    var body: some View {
        HStack(spacing: 6) {
            Image(systemName: icon)
                .font(.caption)
            Text(text)
                .font(.caption)
                .fontWeight(.medium)
        }
        .foregroundColor(color)
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(
            Capsule()
                .fill(color.opacity(0.12))
                .overlay(
                    Capsule()
                        .stroke(color.opacity(0.2), lineWidth: 1)
                )
        )
    }
}

/// Get icon for tool
func toolIcon(for name: String) -> String {
    switch name.lowercased() {
    case "weather": return "cloud.sun.fill"
    case "pdf": return "doc.text.fill"
    case "sql": return "cylinder.split.1x2.fill"
    case "gmail": return "envelope.fill"
    case "google_drive_list": return "folder.fill"
    case "jira_search", "jira_create", "jira_add_watchers", "jira_remove_watcher": return "checkmark.circle.fill"
    case "slack_post": return "bubble.left.and.bubble.right.fill"
    case "github_search", "github_create": return "chevron.left.forwardslash.chevron.right"
    case "confluence_search": return "doc.richtext.fill"
    case "custom_mcp": return "server.rack"
    case "web_crawl": return "globe"
    case "chat": return "text.bubble.fill"
    case "image": return "photo.fill.on.rectangle.fill"
    case "image_analysis": return "viewfinder.circle.fill"
    case "local_search": return "location.magnifyingglass"
    case "set_reminder", "reminder": return "bell.fill"
    case "subscription": return "bell.badge.fill"
    case "help": return "questionmark.circle.fill"
    case "cricket_score": return "sportscourt.fill"
    case "govt_jobs": return "briefcase.fill"
    case "govt_schemes": return "building.columns.fill"
    case "farmer_schemes": return "leaf.fill"
    case "free_audio_sources": return "speaker.wave.2.fill"
    case "fact_check": return "checkmark.shield.fill"
    case "event", "events": return "calendar.circle.fill"
    case "food", "food_order": return "fork.knife.circle.fill"
    case "word_game": return "puzzlepiece.extension.fill"
    // D23Bot Astrology tools
    case "horoscope": return "sparkles"
    case "kundli": return "star.circle.fill"
    case "kundli_matching": return "heart.circle.fill"
    case "dosha", "dosha_check": return "exclamationmark.triangle.fill"
    case "life_prediction": return "crystal.ball.fill"
    case "panchang": return "calendar.badge.clock"
    case "numerology": return "number.circle.fill"
    case "tarot": return "suit.diamond.fill"
    case "ask_astrologer": return "person.wave.2.fill"
    // D23Bot Travel tools
    case "pnr_status": return "ticket.fill"
    case "train_status": return "train.side.front.car"
    case "metro_info", "metro_ticket": return "tram.fill"
    // D23Bot News tool
    case "news": return "newspaper.fill"
    default: return "wrench.and.screwdriver.fill"
    }
}

/// Get color for tool
func toolColor(for name: String) -> Color {
    switch name.lowercased() {
    case "weather": return .orange
    case "pdf": return .red
    case "sql": return .purple
    case "gmail": return .red
    case "google_drive_list": return .green
    case "jira_search", "jira_create", "jira_add_watchers", "jira_remove_watcher": return .blue
    case "slack_post": return .purple
    case "github_search", "github_create": return .gray
    case "confluence_search": return .blue
    case "custom_mcp": return .orange
    case "web_crawl": return .teal
    case "chat": return .green
    case "image": return .pink
    case "image_analysis": return .indigo
    case "local_search": return .teal
    case "set_reminder", "reminder": return .orange
    case "subscription": return .purple
    case "help": return .blue
    case "cricket_score": return .green
    case "govt_jobs": return .blue
    case "govt_schemes": return .teal
    case "farmer_schemes": return .green
    case "free_audio_sources": return .orange
    case "fact_check": return .indigo
    case "event", "events": return .purple
    case "food", "food_order": return .orange
    case "word_game": return .pink
    // D23Bot Astrology tools
    case "horoscope", "kundli", "life_prediction", "ask_astrologer": return .purple
    case "kundli_matching": return .pink
    case "dosha", "dosha_check": return .red
    case "panchang": return .teal
    case "numerology": return .orange
    case "tarot": return .indigo
    // D23Bot Travel tools
    case "pnr_status", "train_status", "metro_info", "metro_ticket": return .blue
    // D23Bot News tool
    case "news": return .red
    default: return .blue
    }
}

/// Get category for tool
func toolCategory(for tool: ToolInfo) -> String {
    if let category = tool.category?.lowercased() {
        switch category {
        case "astrology": return "Astrology"
        case "travel": return "Travel"
        case "utility", "search": return "Utilities"
        case "news": return "News & Info"
        case "govt": return "Government"
        case "food": return "Food & Local"
        case "games": return "Games"
        case "integration": return "Integrations"
        case "general": return "General"
        default: break
        }
    }

    switch tool.name.lowercased() {
    case "weather", "web_crawl": return "Web & Data"
    case "news", "cricket_score", "fact_check", "event", "events": return "News & Info"
    case "image", "image_analysis", "local_search", "set_reminder", "reminder": return "Utilities"
    case "pdf", "sql": return "Documents & Database"
    case "gmail", "google_drive_list": return "Google"
    case "jira_search", "jira_create", "jira_add_watchers", "jira_remove_watcher", "confluence_search": return "Atlassian"
    case "slack_post": return "Communication"
    case "github_search", "github_create": return "Development"
    case "custom_mcp": return "Custom"
    case "chat", "help", "subscription": return "General"
    case "horoscope", "kundli", "kundli_matching", "dosha", "dosha_check", "life_prediction", "panchang", "numerology", "tarot", "ask_astrologer": return "Astrology"
    case "pnr_status", "train_status", "metro_info", "metro_ticket": return "Travel"
    case "govt_jobs", "govt_schemes", "farmer_schemes", "free_audio_sources": return "Government"
    case "food", "food_order": return "Food & Local"
    case "word_game": return "Games"
    default: return "Other"
    }
}

/// Tool picker sheet
struct ToolPickerView: View {
    let availableTools: [ToolInfo]
    @Binding var selectedTools: Set<String>
    let errorMessage: String?
    let onRefresh: () async -> Void
    let onToggle: (String) -> Void

    private var groupedTools: [(String, [ToolInfo])] {
        let grouped = Dictionary(grouping: availableTools) { toolCategory(for: $0) }
        let order = [
            "General",
            "Astrology",
            "Travel",
            "News & Info",
            "Utilities",
            "Government",
            "Food & Local",
            "Games",
            "Web & Data",
            "Documents & Database",
            "Google",
            "Atlassian",
            "Communication",
            "Development",
            "Integrations",
            "Custom",
            "Other",
        ]
        return order.compactMap { category in
            guard let tools = grouped[category], !tools.isEmpty else { return nil }
            return (category, tools.sorted { $0.name < $1.name })
        }
    }

    var body: some View {
        NavigationStack {
            List {
                // Selection summary
                Section {
                    HStack {
                        Image(systemName: "checkmark.seal.fill")
                            .foregroundColor(selectedTools.isEmpty ? .secondary : .green)
                        Text("\(selectedTools.count) of \(availableTools.count) tools selected")
                            .font(.subheadline)
                        Spacer()
                        if !selectedTools.isEmpty {
                            Button("Clear All") {
                                for tool in selectedTools {
                                    onToggle(tool)
                                }
                            }
                            .font(.caption)
                            .foregroundColor(.red)
                        }
                    }
                }

                if let errorMessage {
                    Section {
                        HStack(spacing: 12) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.orange)
                            Text(errorMessage)
                                .font(.subheadline)
                        }
                    }
                }

                if availableTools.isEmpty {
                    Section {
                        VStack(spacing: 12) {
                            Image(systemName: "wrench.and.screwdriver")
                                .font(.largeTitle)
                                .foregroundColor(.secondary)
                            Text("No tools available")
                                .font(.headline)
                            Text("Pull to refresh or check your server connection")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                                .multilineTextAlignment(.center)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 32)
                    }
                } else {
                    ForEach(groupedTools, id: \.0) { category, tools in
                        Section(header: Text(category)) {
                            ForEach(tools) { tool in
                                ToolRow(
                                    tool: tool,
                                    isSelected: selectedTools.contains(tool.name),
                                    onToggle: { onToggle(tool.name) }
                                )
                            }
                        }
                    }
                }
            }
            .navigationTitle("Tools")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        Task {
                            await onRefresh()
                        }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .refreshable {
                await onRefresh()
            }
            .task {
                await onRefresh()
            }
        }
        .presentationDetents([.medium, .large])
    }
}

/// Row for a single tool
struct ToolRow: View {
    let tool: ToolInfo
    let isSelected: Bool
    let onToggle: () -> Void

    var body: some View {
        Button(action: onToggle) {
            HStack(spacing: 12) {
                // Tool icon
                ZStack {
                    RoundedRectangle(cornerRadius: 8)
                        .fill(toolColor(for: tool.name).opacity(0.15))
                        .frame(width: 36, height: 36)
                    Image(systemName: toolIcon(for: tool.name))
                        .font(.system(size: 16))
                        .foregroundColor(toolColor(for: tool.name))
                }

                // Tool info
                VStack(alignment: .leading, spacing: 2) {
                    Text(tool.name.replacingOccurrences(of: "_", with: " ").capitalized)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.primary)
                    Text(tool.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                }

                Spacer()

                // Selection indicator
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .font(.title3)
                    .foregroundColor(isSelected ? .blue : .secondary.opacity(0.5))
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Previews

#Preview("Chat View") {
    NavigationStack {
        ChatView()
            .environmentObject(AuthManager.shared)
    }
}

#Preview("Conversation List") {
    LegacyConversationListView()
        .environmentObject(AuthManager.shared)
        .modelContainer(for: [Conversation.self, Message.self], inMemory: true)
}

#Preview("Capability Card") {
    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
        CapabilityCard(
            icon: "sparkles",
            title: "Astrology",
            description: "Horoscope, Kundli & more",
            color: .purple
        )
        CapabilityCard(
            icon: "train.side.front.car",
            title: "Travel",
            description: "PNR & train status",
            color: .blue
        )
        CapabilityCard(
            icon: "newspaper.fill",
            title: "News",
            description: "Latest headlines",
            color: .red
        )
        CapabilityCard(
            icon: "cloud.sun.fill",
            title: "Weather",
            description: "Live weather updates",
            color: .cyan
        )
    }
    .padding()
}

#Preview("Tool Row - Selected") {
    ToolRow(
        tool: ToolInfo(name: "horoscope", description: "Get daily horoscope predictions"),
        isSelected: true,
        onToggle: {}
    )
    .padding()
}

#Preview("Tool Row - Unselected") {
    ToolRow(
        tool: ToolInfo(name: "pnr_status", description: "Check PNR status for Indian Railways"),
        isSelected: false,
        onToggle: {}
    )
    .padding()
}

#Preview("Provider Row - Connected") {
    ProviderRow(
        provider: ProviderInfo(name: "slack", displayName: "Slack", authType: "oauth", connected: true),
        onConnect: {},
        onDisconnect: {}
    )
    .padding()
}

#Preview("Provider Row - Disconnected") {
    ProviderRow(
        provider: ProviderInfo(name: "github", displayName: "GitHub", authType: "api_key", connected: false),
        onConnect: {},
        onDisconnect: {}
    )
    .padding()
}

#Preview("Animated Conversation Row") {
    let container = try! ModelContainer(for: Conversation.self, Message.self, configurations: ModelConfiguration(isStoredInMemoryOnly: true))
    let conversation = Conversation(title: "Weather & Horoscope")
    return AnimatedConversationRow(conversation: conversation, index: 0, isVisible: true)
        .padding()
        .modelContainer(container)
}

#Preview("Empty State") {
    AnimatedEmptyStateView(onNewChat: {})
}

#Preview("Detail Empty State") {
    AnimatedDetailEmptyView(onNewChat: {})
}

#Preview("Stat Badge") {
    HStack(spacing: 12) {
        StatBadge(icon: "message.fill", text: "5", color: .secondary)
        StatBadge(icon: "wrench.adjustable.fill", text: "3", color: .blue)
        TimeBadge(date: Date())
    }
    .padding()
}

#Preview("Feature Chips") {
    HStack(spacing: 12) {
        FeatureChip(icon: "sparkles", text: "Astrology", color: .purple)
        FeatureChip(icon: "train.side.front.car", text: "Travel", color: .blue)
        FeatureChip(icon: "newspaper.fill", text: "News", color: .red)
    }
    .padding()
}

#Preview("Tool Picker") {
    ToolPickerView(
        availableTools: [
            ToolInfo(name: "horoscope", description: "Get daily horoscope predictions"),
            ToolInfo(name: "pnr_status", description: "Check PNR status for Indian Railways"),
            ToolInfo(name: "weather", description: "Get current weather information"),
            ToolInfo(name: "news", description: "Get latest news headlines")
        ],
        selectedTools: .constant(Set(["horoscope", "weather"])),
        errorMessage: nil,
        onRefresh: {},
        onToggle: { _ in }
    )
}

#Preview("MCP Config View") {
    NavigationStack {
        MCPConfigView(
            providers: [
                ProviderInfo(name: "slack", displayName: "Slack", authType: "oauth", connected: true),
                ProviderInfo(name: "github", displayName: "GitHub", authType: "api_key", connected: false),
                ProviderInfo(name: "jira", displayName: "Jira", authType: "api_key", connected: false)
            ],
            providerError: nil,
            onConnectProvider: { _ in },
            onDisconnectProvider: { _ in },
            onRefresh: {}
        )
    }
}

#Preview("Provider Connect Sheet") {
    ProviderConnectSheet(
        provider: ProviderInfo(name: "github", displayName: "GitHub", authType: "api_key", connected: false),
        secret: .constant(""),
        displayName: .constant("My GitHub"),
        baseURL: .constant(""),
        userField: .constant(""),
        projectKey: .constant(""),
        ownerField: .constant("octocat"),
        repoField: .constant("hello-world"),
        onCancel: {},
        onConnect: {}
    )
}

/// Sheet to collect API key/secret for a provider
struct ProviderConnectSheet: View {
    let provider: ProviderInfo
    @Binding var secret: String
    @Binding var displayName: String
    @Binding var baseURL: String
    @Binding var userField: String
    @Binding var projectKey: String
    @Binding var ownerField: String
    @Binding var repoField: String
    let onCancel: () -> Void
    let onConnect: () -> Void

    var body: some View {
        NavigationStack {
            Form {
                Section(header: Text("Connect \(provider.displayName)")) {
                    SecureField("API key or token", text: $secret)
                    TextField("Display name (optional)", text: $displayName)
                    if requiresBaseURL {
                        TextField("Base URL (e.g. https://your-domain.atlassian.net)", text: $baseURL)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                    }
                    if requiresUserField {
                        TextField("User/Email", text: $userField)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                    }
                    if requiresProjectKey {
                        TextField("Project Key (e.g. ABC)", text: $projectKey)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                    }
                    if requiresOwnerRepo {
                        TextField("Owner/Org (e.g. octocat)", text: $ownerField)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                        TextField("Repo (e.g. hello-world)", text: $repoField)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                    }
                }
            }
            .navigationTitle("Connect")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel", action: onCancel)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save", action: onConnect)
                        .disabled(secret.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
        .presentationDetents([.medium])
    }

    private var requiresBaseURL: Bool {
        provider.name == "confluence" || provider.name == "jira" || provider.name == "custom_mcp"
    }

    private var requiresUserField: Bool {
        provider.name == "confluence" || provider.name == "jira"
    }

    private var requiresProjectKey: Bool {
        provider.name == "jira"
    }

    private var requiresOwnerRepo: Bool {
        provider.name == "github"
    }
}

/// Capability card for welcome screen
struct CapabilityCard: View {
    let icon: String
    let title: String
    let description: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)
                Spacer()
            }
            Text(title)
                .font(.subheadline)
                .fontWeight(.semibold)
            Text(description)
                .font(.caption)
                .foregroundColor(.secondary)
                .lineLimit(2)
        }
        .padding(12)
        .background(Color(.secondarySystemBackground))
        .cornerRadius(12)
    }
}

/// Get icon for provider
func providerIcon(for name: String) -> String {
    switch name.lowercased() {
    case "slack": return "bubble.left.and.bubble.right.fill"
    case "jira": return "checkmark.circle.fill"
    case "confluence": return "doc.richtext.fill"
    case "github": return "chevron.left.forwardslash.chevron.right"
    case "gmail": return "envelope.fill"
    case "google_drive": return "folder.fill"
    case "custom_mcp": return "server.rack"
    default: return "puzzlepiece.fill"
    }
}

/// Get color for provider
func providerColor(for name: String) -> Color {
    switch name.lowercased() {
    case "slack": return .purple
    case "jira": return .blue
    case "confluence": return .blue
    case "github": return .gray
    case "gmail": return .red
    case "google_drive": return .green
    case "custom_mcp": return .orange
    default: return .blue
    }
}

/// Dedicated MCP/Provider configuration screen
struct MCPConfigView: View {
    let providers: [ProviderInfo]
    let providerError: String?
    let onConnectProvider: (ProviderInfo) -> Void
    let onDisconnectProvider: (ProviderInfo) -> Void
    let onRefresh: () async -> Void

    var body: some View {
        List {
            if let providerError {
                Section {
                    HStack(spacing: 12) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundColor(.orange)
                        Text(providerError)
                            .font(.subheadline)
                    }
                    .padding(.vertical, 4)
                }
            }

            // Connected providers
            let connected = providers.filter { $0.connected }
            if !connected.isEmpty {
                Section {
                    ForEach(connected) { provider in
                        ProviderRow(
                            provider: provider,
                            onConnect: { onConnectProvider(provider) },
                            onDisconnect: { onDisconnectProvider(provider) }
                        )
                    }
                } header: {
                    HStack {
                        Image(systemName: "checkmark.seal.fill")
                            .foregroundColor(.green)
                        Text("Connected")
                    }
                }
            }

            // Available providers
            let available = providers.filter { !$0.connected }
            if !available.isEmpty {
                Section {
                    ForEach(available) { provider in
                        ProviderRow(
                            provider: provider,
                            onConnect: { onConnectProvider(provider) },
                            onDisconnect: { onDisconnectProvider(provider) }
                        )
                    }
                } header: {
                    HStack {
                        Image(systemName: "puzzlepiece.extension")
                            .foregroundColor(.secondary)
                        Text("Available Integrations")
                    }
                }
            }

            if providers.isEmpty {
                Section {
                    VStack(spacing: 12) {
                        Image(systemName: "tray")
                            .font(.largeTitle)
                            .foregroundColor(.secondary)
                        Text("No integrations available")
                            .font(.headline)
                        Text("Pull to refresh or check your server configuration")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 32)
                }
            }
        }
        .navigationTitle("MCP & Sources")
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    Task { await onRefresh() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
            }
        }
        .refreshable {
            await onRefresh()
        }
        .task {
            await onRefresh()
        }
    }
}

/// Row for a single provider
struct ProviderRow: View {
    let provider: ProviderInfo
    let onConnect: () -> Void
    let onDisconnect: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            // Provider icon
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(providerColor(for: provider.name).opacity(0.15))
                    .frame(width: 40, height: 40)
                Image(systemName: providerIcon(for: provider.name))
                    .font(.system(size: 18))
                    .foregroundColor(providerColor(for: provider.name))
            }

            // Provider info
            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 6) {
                    Text(provider.displayName)
                        .font(.headline)
                    if provider.authType == "oauth" {
                        Text("OAuth")
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.blue.opacity(0.1))
                            .foregroundColor(.blue)
                            .cornerRadius(4)
                    }
                }
                Text(provider.connected ? "Connected" : "Not connected")
                    .font(.caption)
                    .foregroundColor(provider.connected ? .green : .secondary)
            }

            Spacer()

            // Action button
            Button {
                if provider.connected {
                    onDisconnect()
                } else {
                    onConnect()
                }
            } label: {
                HStack(spacing: 4) {
                    Image(systemName: provider.connected ? "xmark" : "plus")
                        .font(.caption)
                    Text(provider.connected ? "Remove" : "Add")
                        .font(.caption)
                        .fontWeight(.medium)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(provider.connected ? Color.red.opacity(0.1) : Color.blue.opacity(0.1))
                .foregroundColor(provider.connected ? .red : .blue)
                .cornerRadius(8)
            }
            .buttonStyle(.plain)
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Scroll Offset Preference Key

struct ScrollOffsetPreferenceKey: PreferenceKey {
    static var defaultValue: CGFloat = 0

    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) {
        value = nextValue()
    }
}

// MARK: - Welcome Screen with Animations

struct WelcomeScreen: View {
    let selectedToolsCount: Int
    let connectedProvidersCount: Int
    var onCardTapped: ((String) -> Void)?

    @State private var logoScale: CGFloat = 1
    @State private var logoOpacity: Double = 1
    @State private var titleOpacity: Double = 1
    @State private var titleOffset: CGFloat = 0
    @State private var subtitleOpacity: Double = 1
    @State private var pulseAnimation = false
    @State private var rotationAngle: Double = 0
    @State private var gradientRotation: Double = 0
    @State private var floatingOffset: CGFloat = 0
    @State private var shimmerOffset: CGFloat = 0

    private let capabilities: [(icon: String, title: String, description: String, color: Color, prompt: String)] = [
        ("sparkles", "Astrology", "Horoscope, Kundli & more", .purple, "What's my horoscope for today? I'm an Aries."),
        ("train.side.front.car", "Travel", "PNR & train status", .blue, "Check PNR status for my train booking"),
        ("newspaper.fill", "News", "Latest headlines", .red, "What are today's top news headlines in India?"),
        ("suit.diamond.fill", "Tarot", "Get tarot readings", .indigo, "Give me a tarot card reading for today"),
        ("briefcase.fill", "Govt Jobs", "Latest government jobs", .mint, "Show me the latest government job openings"),
        ("sportscourt.fill", "Cricket", "Live scores & updates", .orange, "Get the live cricket score right now"),
        ("wand.and.stars", "Image", "Generate AI images", .pink, "Generate an image of a futuristic city skyline"),
        ("bell.badge.fill", "Reminders", "Set & manage reminders", .teal, "Set a reminder to drink water every 2 hours"),
        ("location.fill", "Nearby", "Find places near you", .green, "Find cafes near me"),
        ("number.circle.fill", "Numerology", "Name & number analysis", .orange, "What does my name mean in numerology?"),
        ("calendar.badge.clock", "Panchang", "Daily Hindu calendar", .teal, "What's today's Panchang and auspicious timings?"),
        ("cloud.sun.fill", "Weather", "Live weather updates", .cyan, "What's the weather like today in my city?"),
        ("message.fill", "Chat", "Ask anything", .green, "Hello! What can you help me with?")
    ]

    var body: some View {
        ScrollView {
            ZStack {
                // Animated Background
                animatedBackground

                VStack(spacing: 28) {
                    Spacer(minLength: 30)

                    // Animated Logo
                    animatedLogo

                    // Title with Animation
                    titleSection

                    // Animated Capabilities Grid
                    capabilitiesSection

                    // Status Badges
                    statusBadges

                    // Animated Hint
                    hintSection

                    Spacer(minLength: 20)
                }
            }
        }
    }

    // MARK: - Animated Background

    private var animatedBackground: some View {
        AdaptiveBackground()
    }

    // MARK: - Animated Logo

    private var animatedLogo: some View {
        ZStack {
            // Outer Glow Ring
            Circle()
                .stroke(
                    AngularGradient(
                        colors: [.purple, .blue, .cyan, .purple],
                        center: .center,
                        startAngle: .degrees(gradientRotation),
                        endAngle: .degrees(gradientRotation + 360)
                    ),
                    lineWidth: 3
                )
                .frame(width: 110, height: 110)
                .blur(radius: 4)

            // Pulse Ring
            Circle()
                .stroke(
                    LinearGradient(
                        colors: [.purple.opacity(0.5), .blue.opacity(0.5)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: 2
                )
                .frame(width: 100, height: 100)
                .scaleEffect(pulseAnimation ? 1.3 : 1.0)
                .opacity(pulseAnimation ? 0 : 0.8)

            // Main Logo Circle
            Circle()
                .fill(
                    LinearGradient(
                        colors: [
                            Color(red: 0.5, green: 0.2, blue: 0.9),
                            Color(red: 0.3, green: 0.4, blue: 0.95)
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 90, height: 90)
                .shadow(color: .purple.opacity(0.5), radius: 20, y: 10)

            // Icon with Rotation
            Image(systemName: "sparkles")
                .font(.system(size: 40, weight: .medium))
                .foregroundStyle(
                    LinearGradient(
                        colors: [.white, .white.opacity(0.8)],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )
                .rotationEffect(.degrees(rotationAngle))
        }
        .scaleEffect(logoScale)
        .opacity(logoOpacity)
    }

    // MARK: - Title Section

    private var titleSection: some View {
        VStack(spacing: 12) {
            // Main Title with Gradient
            Text("Welcome to OhGrt")
                .font(.system(size: 32, weight: .bold, design: .rounded))
                .foregroundStyle(
                    LinearGradient(
                        colors: [.primary, .primary.opacity(0.8)],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )

            // Animated Subtitle
            Text("Your AI-powered assistant for India")
                .font(.subheadline)
                .foregroundColor(.secondary)

            // Feature Pills
            HStack(spacing: 8) {
                FeaturePill(text: "11+ Languages", icon: "globe")
                FeaturePill(text: "Voice AI", icon: "waveform")
            }
            .padding(.top, 4)
        }
        .opacity(titleOpacity)
        .offset(y: titleOffset)
    }

    // MARK: - Capabilities Section

    private var capabilitiesSection: some View {
        VStack(spacing: 16) {
            Text("What I can help with")
                .font(.headline)
                .foregroundColor(.secondary)
                .opacity(subtitleOpacity)

            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                ForEach(Array(capabilities.enumerated()), id: \.offset) { index, capability in
                    CapabilityCard(
                        icon: capability.icon,
                        title: capability.title,
                        description: capability.description,
                        color: capability.color
                    )
                    .onTapGesture {
                        onCardTapped?(capability.prompt)
                    }
                }
            }
            .padding(.horizontal)
        }
    }

    // MARK: - Status Badges

    private var statusBadges: some View {
        VStack(spacing: 10) {
            if selectedToolsCount > 0 {
                AnimatedBadge(
                    icon: "checkmark.seal.fill",
                    text: "\(selectedToolsCount) tools enabled",
                    color: .green,
                    delay: 0.8
                )
            }

            if connectedProvidersCount > 0 {
                AnimatedBadge(
                    icon: "link.circle.fill",
                    text: "\(connectedProvidersCount) integrations connected",
                    color: .blue,
                    delay: 0.9
                )
            }
        }
        .padding(.top, 8)
    }

    // MARK: - Hint Section

    private var hintSection: some View {
        HStack(spacing: 6) {
            Image(systemName: "hand.tap.fill")
                .font(.caption)
            Text("Type a message or tap a suggestion to start")
                .font(.caption)
        }
        .foregroundColor(.secondary)
        .padding(.vertical, 10)
        .padding(.horizontal, 16)
        .background(
            Capsule()
                .fill(Color(.secondarySystemBackground))
                .overlay(
                    Capsule()
                        .fill(
                            LinearGradient(
                                colors: [.white.opacity(0.5), .clear, .clear],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .offset(x: shimmerOffset)
                        .mask(Capsule())
                )
        )
        .opacity(subtitleOpacity)
    }

}

// MARK: - Supporting Views

struct FeaturePill: View {
    let text: String
    let icon: String

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.caption2)
            Text(text)
                .font(.caption2)
                .fontWeight(.medium)
        }
        .foregroundColor(.purple)
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(
            Capsule()
                .fill(Color.purple.opacity(0.12))
        )
    }
}

struct AnimatedCapabilityCard: View {
    let icon: String
    let title: String
    let description: String
    let color: Color
    let delay: Double
    let isVisible: Bool
    var onTap: (() -> Void)?

    @Environment(\.colorScheme) var colorScheme
    @State private var isPressed = false
    @State private var appeared = false

    private let impactFeedback = UIImpactFeedbackGenerator(style: .medium)

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Icon with gradient background
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(
                        LinearGradient(
                            colors: [color.opacity(0.2), color.opacity(0.1)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 40, height: 40)

                Image(systemName: icon)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [color, color.opacity(0.7)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(.primary)

                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(colorScheme == .light ? Color.white : Color(.secondarySystemBackground))
                .shadow(
                    color: colorScheme == .light
                        ? Color.black.opacity(isPressed ? 0.12 : 0.06)
                        : color.opacity(isPressed ? 0.3 : 0.1),
                    radius: isPressed ? 14 : 8,
                    y: isPressed ? 6 : 4
                )
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(
                    colorScheme == .light
                        ? color.opacity(isPressed ? 0.3 : 0.1)
                        : color.opacity(isPressed ? 0.4 : 0.15),
                    lineWidth: 1
                )
        )
        .scaleEffect(isPressed ? 0.96 : 1.0)
        .scaleEffect(appeared ? 1.0 : 0.8)
        .opacity(appeared ? 1.0 : 0)
        .onTapGesture {
            // Haptic feedback
            impactFeedback.impactOccurred()

            withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                isPressed = true
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                    isPressed = false
                }
                // Call the tap handler after animation
                onTap?()
            }
        }
        .onChange(of: isVisible) { _, visible in
            if visible {
                withAnimation(.spring(response: 0.6, dampingFraction: 0.7).delay(delay)) {
                    appeared = true
                }
            }
        }
    }
}

struct AnimatedBadge: View {
    let icon: String
    let text: String
    let color: Color
    let delay: Double

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .foregroundColor(color)
            Text(text)
                .font(.footnote)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 10)
        .padding(.horizontal, 18)
        .background(
            Capsule()
                .fill(color.opacity(0.1))
                .overlay(
                    Capsule()
                        .stroke(color.opacity(0.2), lineWidth: 1)
                )
        )
    }
}

// MARK: - Welcome Screen Preview

#Preview("Welcome Screen") {
    WelcomeScreen(selectedToolsCount: 3, connectedProvidersCount: 2)
}

#Preview("Welcome Screen - Empty") {
    WelcomeScreen(selectedToolsCount: 0, connectedProvidersCount: 0)
}

#Preview("Animated Capability Card") {
    AnimatedCapabilityCard(
        icon: "sparkles",
        title: "Astrology",
        description: "Horoscope, Kundli & more",
        color: .purple,
        delay: 0,
        isVisible: true
    )
    .padding()
}

#Preview("Feature Pills") {
    HStack {
        FeaturePill(text: "11+ Languages", icon: "globe")
        FeaturePill(text: "Voice AI", icon: "waveform")
    }
    .padding()
}
