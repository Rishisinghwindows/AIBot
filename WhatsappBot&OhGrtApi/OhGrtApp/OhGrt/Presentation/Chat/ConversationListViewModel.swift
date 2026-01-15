import Foundation
import Combine
import SwiftUI

/// ViewModel for conversation list screen
@MainActor
final class ConversationListViewModel: ObservableObject {
    // MARK: - Published Properties

    @Published private(set) var conversations: [ChatConversation] = []
    @Published private(set) var isLoading = false
    @Published private(set) var error: String?
    @Published var showError = false
    @Published var searchText = ""

    // MARK: - Use Cases

    private let getConversationsUseCase: GetConversationsUseCaseProtocol
    private let createConversationUseCase: CreateConversationUseCaseProtocol
    private let deleteConversationUseCase: DeleteConversationUseCaseProtocol

    // MARK: - Private Properties

    private var cancellables = Set<AnyCancellable>()

    // MARK: - Computed Properties

    var filteredConversations: [ChatConversation] {
        if searchText.isEmpty {
            return conversations
        }
        return conversations.filter {
            $0.title.localizedCaseInsensitiveContains(searchText) ||
            ($0.lastMessagePreview?.localizedCaseInsensitiveContains(searchText) ?? false)
        }
    }

    var hasConversations: Bool {
        !conversations.isEmpty
    }

    // MARK: - Initialization

    init(
        getConversationsUseCase: GetConversationsUseCaseProtocol,
        createConversationUseCase: CreateConversationUseCaseProtocol,
        deleteConversationUseCase: DeleteConversationUseCaseProtocol
    ) {
        self.getConversationsUseCase = getConversationsUseCase
        self.createConversationUseCase = createConversationUseCase
        self.deleteConversationUseCase = deleteConversationUseCase

        setupObservers()
    }

    // MARK: - Public Methods

    func loadConversations() {
        Task {
            await performLoadConversations()
        }
    }

    func createConversation() async -> ChatConversation? {
        do {
            let conversation = try await createConversationUseCase.execute(
                title: "New Conversation",
                tools: []
            )
            return conversation
        } catch let domainError as DomainError {
            error = domainError.localizedDescription
            showError = true
            return nil
        } catch {
            self.error = error.localizedDescription
            showError = true
            return nil
        }
    }

    func deleteConversation(_ conversation: ChatConversation) {
        Task {
            await performDeleteConversation(conversation.id)
        }
    }

    func deleteConversation(at offsets: IndexSet) {
        for index in offsets {
            let conversation = filteredConversations[index]
            deleteConversation(conversation)
        }
    }

    func clearError() {
        error = nil
        showError = false
    }

    // MARK: - Private Methods

    private func setupObservers() {
        getConversationsUseCase.observe()
            .receive(on: DispatchQueue.main)
            .sink { [weak self] conversations in
                self?.conversations = conversations
            }
            .store(in: &cancellables)
    }

    private func performLoadConversations() async {
        isLoading = true

        do {
            conversations = try await getConversationsUseCase.execute()
        } catch let domainError as DomainError {
            error = domainError.localizedDescription
            showError = true
        } catch {
            self.error = error.localizedDescription
            showError = true
        }

        isLoading = false
    }

    private func performDeleteConversation(_ id: UUID) async {
        do {
            try await deleteConversationUseCase.execute(conversationId: id)
            // Remove from local list (will also be updated via observer)
            conversations.removeAll { $0.id == id }
        } catch let domainError as DomainError {
            error = domainError.localizedDescription
            showError = true
        } catch {
            self.error = error.localizedDescription
            showError = true
        }
    }
}
