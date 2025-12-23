import SwiftUI
import Combine

/// View for chatting with a public persona
struct PublicPersonaChatView: View {
    let handle: String
    @StateObject private var viewModel: PublicPersonaChatViewModel
    @Environment(\.dismiss) private var dismiss

    init(handle: String) {
        self.handle = handle
        self._viewModel = StateObject(wrappedValue: PublicPersonaChatViewModel(handle: handle))
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if viewModel.isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if viewModel.notFound {
                    notFoundView
                } else {
                    personaChatContent
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark")
                    }
                }
                ToolbarItem(placement: .principal) {
                    if let persona = viewModel.persona {
                        HStack(spacing: 8) {
                            AsyncImage(url: URL(string: persona.avatarUrl ?? "")) { image in
                                image
                                    .resizable()
                                    .scaledToFill()
                            } placeholder: {
                                Circle()
                                    .fill(LinearGradient(
                                        colors: [.purple, .pink],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    ))
                                    .overlay(
                                        Text(persona.displayName.prefix(1).uppercased())
                                            .font(.caption)
                                            .foregroundColor(.white)
                                    )
                            }
                            .frame(width: 32, height: 32)
                            .clipShape(Circle())

                            VStack(alignment: .leading, spacing: 0) {
                                Text(persona.displayName)
                                    .font(.headline)
                                Text("@\(persona.handle)")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
            }
            .task {
                await viewModel.loadPersona()
            }
        }
    }

    private var notFoundView: some View {
        VStack(spacing: 16) {
            Image(systemName: "person.slash")
                .font(.system(size: 60))
                .foregroundColor(.secondary)

            Text("Persona Not Found")
                .font(.title2)
                .fontWeight(.semibold)

            Text("@\(handle) doesn't exist or is private")
                .font(.subheadline)
                .foregroundColor(.secondary)

            Button("Go Back") {
                dismiss()
            }
            .buttonStyle(.bordered)
        }
    }

    private var personaChatContent: some View {
        VStack(spacing: 0) {
            // Persona header info
            if let persona = viewModel.persona {
                personaHeader(persona)
            }

            Divider()

            // Messages
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        if viewModel.messages.isEmpty {
                            emptyMessagesView
                        } else {
                            ForEach(viewModel.messages) { message in
                                PersonaMessageBubble(
                                    message: message,
                                    personaName: viewModel.persona?.displayName ?? "",
                                    personaAvatar: viewModel.persona?.avatarUrl
                                )
                            }
                        }

                        if viewModel.isSending {
                            HStack {
                                typingIndicator
                                Spacer()
                            }
                            .padding(.horizontal)
                        }
                    }
                    .padding()
                    .id("bottom")
                }
                .onChange(of: viewModel.messages.count) { _, _ in
                    withAnimation {
                        proxy.scrollTo("bottom", anchor: .bottom)
                    }
                }
            }

            // Input bar
            inputBar
        }
    }

    private func personaHeader(_ persona: PersonaPublicResponse) -> some View {
        VStack(spacing: 8) {
            if let tagline = persona.tagline, !tagline.isEmpty {
                Text(tagline)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }

            HStack(spacing: 16) {
                if let jobTitle = persona.jobTitle {
                    Label(jobTitle, systemImage: "briefcase")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                if let expertise = persona.expertiseArea {
                    Label(expertise, systemImage: "sparkles")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            if let topics = persona.topics, !topics.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack {
                        ForEach(topics.prefix(5), id: \.self) { topic in
                            Text(topic)
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color(.systemGray6))
                                .cornerRadius(8)
                        }
                    }
                }
            }
        }
        .padding()
        .background(
            LinearGradient(
                colors: [Color.purple.opacity(0.1), Color.clear],
                startPoint: .top,
                endPoint: .bottom
            )
        )
    }

    private var emptyMessagesView: some View {
        VStack(spacing: 16) {
            Image(systemName: "bubble.left.and.bubble.right")
                .font(.system(size: 40))
                .foregroundColor(.secondary)

            Text("Start a conversation")
                .font(.headline)

            if let persona = viewModel.persona {
                Text("Ask \(persona.displayName) anything about their expertise")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
        }
        .padding(.top, 60)
    }

    private var typingIndicator: some View {
        HStack(spacing: 4) {
            ForEach(0..<3) { i in
                Circle()
                    .fill(Color.secondary)
                    .frame(width: 8, height: 8)
                    .opacity(0.5)
            }
        }
        .padding(12)
        .background(Color(.systemGray6))
        .cornerRadius(16)
    }

    private var inputBar: some View {
        HStack(spacing: 12) {
            TextField("Message \(viewModel.persona?.displayName ?? "")...", text: $viewModel.inputText)
                .textFieldStyle(.roundedBorder)
                .disabled(viewModel.isSending)

            Button {
                Task { await viewModel.sendMessage() }
            } label: {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.system(size: 32))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [.purple, .pink],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            }
            .disabled(viewModel.inputText.trimmingCharacters(in: .whitespaces).isEmpty || viewModel.isSending)
        }
        .padding()
        .background(Color(.systemBackground))
        .shadow(color: .black.opacity(0.05), radius: 5, y: -2)
    }
}

/// Message bubble for persona chat
struct PersonaMessageBubble: View {
    let message: PersonaChatMessage
    let personaName: String
    let personaAvatar: String?

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            if message.role == "assistant" {
                // Persona avatar
                AsyncImage(url: URL(string: personaAvatar ?? "")) { image in
                    image
                        .resizable()
                        .scaledToFill()
                } placeholder: {
                    Circle()
                        .fill(LinearGradient(
                            colors: [.purple, .pink],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ))
                        .overlay(
                            Text(personaName.prefix(1).uppercased())
                                .font(.caption)
                                .foregroundColor(.white)
                        )
                }
                .frame(width: 28, height: 28)
                .clipShape(Circle())
            }

            VStack(alignment: message.role == "user" ? .trailing : .leading, spacing: 4) {
                if message.role == "assistant" {
                    Text(personaName)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Text(message.content)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(
                        message.role == "user"
                            ? AnyShapeStyle(LinearGradient(
                                colors: [.purple, .pink],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                              ))
                            : AnyShapeStyle(Color(.systemGray6))
                    )
                    .foregroundColor(message.role == "user" ? .white : .primary)
                    .cornerRadius(16)
            }

            if message.role == "user" {
                Spacer(minLength: 40)
            } else {
                Spacer()
            }
        }
        .padding(.horizontal, message.role == "user" ? 0 : 0)
        .frame(maxWidth: .infinity, alignment: message.role == "user" ? .trailing : .leading)
    }
}

/// Chat message model
struct PersonaChatMessage: Identifiable {
    let id = UUID()
    let role: String
    let content: String
}

/// ViewModel for public persona chat
@MainActor
class PublicPersonaChatViewModel: ObservableObject {
    let handle: String

    @Published var persona: PersonaPublicResponse?
    @Published var messages: [PersonaChatMessage] = []
    @Published var inputText = ""
    @Published var isLoading = false
    @Published var isSending = false
    @Published var notFound = false
    @Published var sessionId: String?

    init(handle: String) {
        self.handle = handle
    }

    func loadPersona() async {
        isLoading = true
        do {
            persona = try await APIClient.shared.getPublicPersona(handle: handle)
        } catch {
            notFound = true
        }
        isLoading = false
    }

    func sendMessage() async {
        let text = inputText.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty else { return }

        inputText = ""
        messages.append(PersonaChatMessage(role: "user", content: text))
        isSending = true

        do {
            let request = PersonaChatRequest(message: text, sessionId: sessionId, visitorName: nil)
            let response = try await APIClient.shared.chatWithPersona(handle: handle, request: request)
            sessionId = response.sessionId
            messages.append(PersonaChatMessage(role: "assistant", content: response.response))
        } catch {
            messages.append(PersonaChatMessage(
                role: "assistant",
                content: "Sorry, I'm having trouble responding right now. Please try again."
            ))
        }

        isSending = false
    }
}

#Preview {
    PublicPersonaChatView(handle: "johndoe")
}
