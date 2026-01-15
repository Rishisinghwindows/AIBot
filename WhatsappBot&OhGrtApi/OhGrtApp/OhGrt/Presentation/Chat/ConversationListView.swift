import SwiftUI

/// List of all conversations
struct ConversationListView: View {
    @ObservedObject var viewModel: ConversationListViewModel
    @ObservedObject private var theme = ThemeManager.shared

    @State private var showNewChat = false
    @State private var selectedConversation: ChatConversation?

    var body: some View {
        NavigationStack {
            ZStack {
                // Adaptive background for light/dark mode
                AdaptiveBackground()

                if viewModel.isLoading && !viewModel.hasConversations {
                    // Loading state
                    ProgressView("Loading conversations...")
                } else if !viewModel.hasConversations {
                    // Empty state
                    emptyStateView
                } else {
                    // Conversation list
                    conversationList
                }
            }
            .navigationTitle("Conversations")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button(action: createNewConversation) {
                        Image(systemName: "square.and.pencil")
                            .font(.system(size: 18, weight: .medium))
                            .foregroundStyle(
                                LinearGradient(
                                    colors: [theme.primaryColor, theme.secondaryColor],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                    }
                }

                ToolbarItem(placement: .topBarLeading) {
                    HStack(spacing: 16) {
                        NavigationLink(destination: SettingsView()) {
                            Image(systemName: "gearshape.fill")
                                .font(.system(size: 18, weight: .medium))
                                .foregroundColor(.secondary)
                        }
                        NavigationLink(destination: TasksView()) {
                            Image(systemName: "calendar.badge.clock")
                                .font(.system(size: 18, weight: .medium))
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            .searchable(text: $viewModel.searchText, prompt: "Search conversations")
            .refreshable {
                viewModel.loadConversations()
            }
            .navigationDestination(item: $selectedConversation) { conversation in
                ChatView(conversationId: conversation.id)
            }
        }
        .onAppear {
            viewModel.loadConversations()
        }
        .alert("Error", isPresented: $viewModel.showError) {
            Button("OK") {
                viewModel.clearError()
            }
        } message: {
            Text(viewModel.error ?? "An error occurred")
        }
    }

    // MARK: - Empty State

    private var emptyStateView: some View {
        VStack(spacing: 24) {
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [theme.primaryColor.opacity(0.15), theme.secondaryColor.opacity(0.1)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 100, height: 100)

                Image(systemName: "bubble.left.and.bubble.right")
                    .font(.system(size: 40, weight: .medium))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [theme.primaryColor, theme.secondaryColor],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            }

            VStack(spacing: 8) {
                Text("No Conversations Yet")
                    .font(.title2)
                    .fontWeight(.bold)

                Text("Start a new conversation with D23 AI")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }

            Button(action: createNewConversation) {
                HStack(spacing: 8) {
                    Image(systemName: "plus.circle.fill")
                    Text("New Conversation")
                }
                .font(.headline)
                .foregroundColor(.white)
                .padding(.horizontal, 24)
                .padding(.vertical, 14)
                .background(
                    LinearGradient(
                        colors: [theme.primaryColor, theme.secondaryColor],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .cornerRadius(14)
                .shadow(color: theme.primaryColor.opacity(0.3), radius: 10, y: 5)
            }
        }
        .padding()
    }

    // MARK: - Conversation List

    private var conversationList: some View {
        List {
            ForEach(viewModel.filteredConversations) { conversation in
                ConversationRow(conversation: conversation)
                    .contentShape(Rectangle())
                    .onTapGesture {
                        selectedConversation = conversation
                    }
            }
            .onDelete { offsets in
                viewModel.deleteConversation(at: offsets)
            }
        }
        .listStyle(.plain)
    }

    // MARK: - Actions

    private func createNewConversation() {
        Task {
            if let conversation = await viewModel.createConversation() {
                selectedConversation = conversation
            }
        }
    }
}

/// Row item for conversation list
private struct ConversationRow: View {
    let conversation: ChatConversation
    @ObservedObject private var theme = ThemeManager.shared

    var body: some View {
        HStack(spacing: 14) {
            // Icon
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: [theme.primaryColor.opacity(0.15), theme.secondaryColor.opacity(0.1)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 48, height: 48)

                Image(systemName: "bubble.left.fill")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [theme.primaryColor, theme.secondaryColor],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            }

            // Content
            VStack(alignment: .leading, spacing: 4) {
                Text(conversation.title)
                    .font(.headline)
                    .lineLimit(1)

                if let preview = conversation.lastMessagePreview {
                    Text(preview)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                }

                HStack(spacing: 8) {
                    Text(conversation.updatedAt.formatted(.relative(presentation: .named)))
                        .font(.caption)
                        .foregroundColor(.secondary)

                    if conversation.messageCount > 0 {
                        Text("•")
                            .foregroundColor(.secondary)
                        Text("\(conversation.messageCount) messages")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 8)
    }
}

/// Chat detail view for a specific conversation
struct ChatDetailView: View {
    let conversation: ChatConversation
    @StateObject private var viewModel = DependencyContainer.shared.makeChatViewModel()
    @ObservedObject private var theme = ThemeManager.shared

    var body: some View {
        VStack(spacing: 0) {
            // Messages list
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 16) {
                        ForEach(viewModel.messages) { message in
                            MessageBubbleView(message: message)
                                .id(message.id)
                        }

                        if viewModel.isSending {
                            HStack {
                                ProgressView()
                                    .scaleEffect(0.8)
                                Text("Thinking...")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            .padding()
                        }
                    }
                    .padding()
                }
                .onChange(of: viewModel.messages.count) { _, _ in
                    if let lastMessage = viewModel.messages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }

            Divider()

            // Input area
            MessageInputArea(
                text: $viewModel.inputText,
                isSending: viewModel.isSending,
                onSend: {
                    Task {
                        await viewModel.sendMessage()
                    }
                }
            )
        }
        .navigationTitle(conversation.title)
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            viewModel.loadConversation(conversation.id)
            Task {
                await viewModel.loadTools()
            }
        }
        .alert("Error", isPresented: $viewModel.showError) {
            Button("OK") {
                viewModel.clearError()
            }
        } message: {
            Text(viewModel.error ?? "An error occurred")
        }
    }
}

/// Message bubble view
private struct MessageBubbleView: View {
    let message: ChatMessage
    @ObservedObject private var theme = ThemeManager.shared

    var isUser: Bool {
        message.role == .user
    }

    var body: some View {
        HStack {
            if isUser { Spacer(minLength: 60) }

            VStack(alignment: isUser ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .font(.body)
                    .foregroundColor(isUser ? .white : .primary)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                    .background(
                        isUser
                        ? AnyShapeStyle(LinearGradient(
                            colors: [theme.primaryColor, theme.secondaryColor],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ))
                        : AnyShapeStyle(Color(.secondarySystemBackground))
                    )
                    .cornerRadius(18)

                Text(message.createdAt.formatted(date: .omitted, time: .shortened))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }

            if !isUser { Spacer(minLength: 60) }
        }
    }
}

/// Message input area
private struct MessageInputArea: View {
    @Binding var text: String
    let isSending: Bool
    let onSend: () -> Void

    @ObservedObject private var theme = ThemeManager.shared
    @FocusState private var isFocused: Bool

    var body: some View {
        HStack(spacing: 12) {
            TextField("Message", text: $text, axis: .vertical)
                .textFieldStyle(.plain)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(Color(.secondarySystemBackground))
                .cornerRadius(24)
                .focused($isFocused)
                .lineLimit(1...5)

            Button(action: onSend) {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.system(size: 32, weight: .medium))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [theme.primaryColor, theme.secondaryColor],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            }
            .disabled(text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSending)
            .opacity(text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? 0.5 : 1)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color(.systemBackground))
    }
}

// Preview requires model container to be configured
// Use the main app preview instead
