import Foundation
import SwiftData
import SwiftUI

/// Dependency Injection Container - Single source of truth for all dependencies
@MainActor
final class DependencyContainer {
    // MARK: - Singleton

    static let shared = DependencyContainer()

    // MARK: - Core Dependencies

    private(set) var apiClient: APIClient
    private(set) var keychainManager: KeychainManager
    private var modelContext: ModelContext?

    // MARK: - Data Sources

    private var authRemoteDataSource: AuthRemoteDataSourceProtocol!
    private var chatRemoteDataSource: ChatRemoteDataSourceProtocol!
    private var conversationLocalDataSource: ConversationLocalDataSourceProtocol?

    // MARK: - Repositories

    private var authRepository: AuthRepositoryProtocol!
    private var chatRepository: ChatRepositoryProtocol!
    private var conversationRepository: ConversationRepositoryProtocol?

    // MARK: - Initialization

    private init() {
        // Use existing singletons
        apiClient = APIClient.shared
        keychainManager = KeychainManager.shared

        setupDataSources()
        setupRepositories()
    }

    // MARK: - Setup Methods

    private func setupDataSources() {
        authRemoteDataSource = AuthRemoteDataSource(apiClient: apiClient)
        chatRemoteDataSource = ChatRemoteDataSource(apiClient: apiClient)
    }

    private func setupRepositories() {
        authRepository = AuthRepository(
            remoteDataSource: authRemoteDataSource,
            keychainManager: keychainManager
        )
        chatRepository = ChatRepository(remoteDataSource: chatRemoteDataSource)
    }

    /// Configure with ModelContext for SwiftData (called from App)
    func configure(with modelContext: ModelContext) {
        self.modelContext = modelContext
        conversationLocalDataSource = ConversationLocalDataSource(modelContext: modelContext)
        conversationRepository = ConversationRepository(localDataSource: conversationLocalDataSource!)
    }

    // MARK: - Use Case Factories

    // Auth Use Cases
    func makeSignInWithGoogleUseCase() -> SignInWithGoogleUseCaseProtocol {
        SignInWithGoogleUseCase(authRepository: authRepository)
    }

    func makeSignOutUseCase() -> SignOutUseCaseProtocol {
        SignOutUseCase(authRepository: authRepository)
    }

    func makeObserveAuthStateUseCase() -> ObserveAuthStateUseCaseProtocol {
        ObserveAuthStateUseCase(authRepository: authRepository)
    }

    // Chat Use Cases
    func makeSendMessageUseCase() -> SendMessageUseCaseProtocol {
        guard let conversationRepository = conversationRepository else {
            fatalError("ConversationRepository not configured. Call configure(with:) first.")
        }
        return SendMessageUseCase(
            chatRepository: chatRepository,
            conversationRepository: conversationRepository
        )
    }

    func makeGetToolsUseCase() -> GetToolsUseCaseProtocol {
        GetToolsUseCase(chatRepository: chatRepository)
    }

    func makeGetProvidersUseCase() -> GetProvidersUseCaseProtocol {
        GetProvidersUseCase(chatRepository: chatRepository)
    }

    // Conversation Use Cases
    func makeGetConversationsUseCase() -> GetConversationsUseCaseProtocol {
        guard let conversationRepository = conversationRepository else {
            fatalError("ConversationRepository not configured. Call configure(with:) first.")
        }
        return GetConversationsUseCase(conversationRepository: conversationRepository)
    }

    func makeCreateConversationUseCase() -> CreateConversationUseCaseProtocol {
        guard let conversationRepository = conversationRepository else {
            fatalError("ConversationRepository not configured. Call configure(with:) first.")
        }
        return CreateConversationUseCase(conversationRepository: conversationRepository)
    }

    func makeDeleteConversationUseCase() -> DeleteConversationUseCaseProtocol {
        guard let conversationRepository = conversationRepository else {
            fatalError("ConversationRepository not configured. Call configure(with:) first.")
        }
        return DeleteConversationUseCase(conversationRepository: conversationRepository)
    }

    func makeGetMessagesUseCase() -> GetMessagesUseCaseProtocol {
        guard let conversationRepository = conversationRepository else {
            fatalError("ConversationRepository not configured. Call configure(with:) first.")
        }
        return GetMessagesUseCase(conversationRepository: conversationRepository)
    }

    // MARK: - ViewModel Factories

    func makeAuthViewModel() -> AuthViewModel {
        AuthViewModel(
            signInWithGoogleUseCase: makeSignInWithGoogleUseCase(),
            signOutUseCase: makeSignOutUseCase(),
            observeAuthStateUseCase: makeObserveAuthStateUseCase()
        )
    }

    func makeChatViewModel() -> ChatViewModel {
        ChatViewModel(
            sendMessageUseCase: makeSendMessageUseCase(),
            getMessagesUseCase: makeGetMessagesUseCase(),
            getToolsUseCase: makeGetToolsUseCase(),
            getProvidersUseCase: makeGetProvidersUseCase(),
            createConversationUseCase: makeCreateConversationUseCase()
        )
    }

    func makeConversationListViewModel() -> ConversationListViewModel {
        ConversationListViewModel(
            getConversationsUseCase: makeGetConversationsUseCase(),
            createConversationUseCase: makeCreateConversationUseCase(),
            deleteConversationUseCase: makeDeleteConversationUseCase()
        )
    }
}

// MARK: - Environment Key

private struct DependencyContainerKey: EnvironmentKey {
    @MainActor static let defaultValue = DependencyContainer.shared
}

extension EnvironmentValues {
    var dependencyContainer: DependencyContainer {
        get { self[DependencyContainerKey.self] }
        set { self[DependencyContainerKey.self] = newValue }
    }
}

// MARK: - View Extension

extension View {
    @MainActor
    func withDependencies() -> some View {
        self.environment(\.dependencyContainer, DependencyContainer.shared)
    }
}
