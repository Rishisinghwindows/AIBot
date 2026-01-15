import Foundation
import SwiftData
import Combine

/// Protocol for local conversation data source
@MainActor
protocol ConversationLocalDataSourceProtocol {
    var conversationsPublisher: AnyPublisher<[ChatConversation], Never> { get }

    func getAllConversations() throws -> [ChatConversation]
    func getConversation(id: UUID) throws -> ChatConversation?
    func saveConversation(_ conversation: ChatConversation) throws
    func deleteConversation(id: UUID) throws
    func getMessages(conversationId: UUID) throws -> [ChatMessage]
    func getMessages(conversationId: UUID, before: Date?, limit: Int) throws -> [ChatMessage]
    func saveMessage(_ message: ChatMessage) throws
    func deleteMessages(conversationId: UUID) throws
}

/// Local data source using SwiftData for persistence
@MainActor
final class ConversationLocalDataSource: ConversationLocalDataSourceProtocol {
    private let modelContext: ModelContext
    private let conversationsSubject = CurrentValueSubject<[ChatConversation], Never>([])

    var conversationsPublisher: AnyPublisher<[ChatConversation], Never> {
        conversationsSubject.eraseToAnyPublisher()
    }

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
        refreshConversations()
    }

    func getAllConversations() throws -> [ChatConversation] {
        let descriptor = FetchDescriptor<Conversation>(
            sortBy: [SortDescriptor(\.updatedAt, order: .reverse)]
        )

        let conversations = try modelContext.fetch(descriptor)
        let domainConversations = conversations.map { mapToDomain($0) }

        conversationsSubject.send(domainConversations)
        return domainConversations
    }

    func getConversation(id: UUID) throws -> ChatConversation? {
        let targetId = id
        let descriptor = FetchDescriptor<Conversation>(
            predicate: #Predicate { conversation in
                conversation.id == targetId
            }
        )

        guard let conversation = try modelContext.fetch(descriptor).first else {
            return nil
        }

        return mapToDomain(conversation)
    }

    func saveConversation(_ conversation: ChatConversation) throws {
        let targetId = conversation.id
        let descriptor = FetchDescriptor<Conversation>(
            predicate: #Predicate { conv in
                conv.id == targetId
            }
        )

        if let existing = try modelContext.fetch(descriptor).first {
            // Update existing
            existing.title = conversation.title
            existing.updatedAt = conversation.updatedAt
            existing.tools = conversation.tools
        } else {
            // Create new
            let newConversation = Conversation(
                id: conversation.id,
                title: conversation.title,
                createdAt: conversation.createdAt,
                tools: conversation.tools
            )
            newConversation.updatedAt = conversation.updatedAt
            modelContext.insert(newConversation)
        }

        try modelContext.save()
        refreshConversations()
    }

    func deleteConversation(id: UUID) throws {
        let targetId = id
        let descriptor = FetchDescriptor<Conversation>(
            predicate: #Predicate { conversation in
                conversation.id == targetId
            }
        )

        if let conversation = try modelContext.fetch(descriptor).first {
            modelContext.delete(conversation)
            try modelContext.save()
            refreshConversations()
        }
    }

    func getMessages(conversationId: UUID) throws -> [ChatMessage] {
        let targetConversationId = conversationId
        let descriptor = FetchDescriptor<Message>(
            predicate: #Predicate { message in
                message.conversationId == targetConversationId
            },
            sortBy: [SortDescriptor(\.createdAt, order: .forward)]
        )

        let messages = try modelContext.fetch(descriptor)
        return messages.map { mapToDomain($0) }
    }

    func getMessages(conversationId: UUID, before: Date?, limit: Int) throws -> [ChatMessage] {
        guard limit > 0 else { return [] }

        let targetConversationId = conversationId
        var descriptor: FetchDescriptor<Message>

        if let before = before {
            descriptor = FetchDescriptor<Message>(
                predicate: #Predicate { message in
                    message.conversationId == targetConversationId && message.createdAt < before
                },
                sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
            )
        } else {
            descriptor = FetchDescriptor<Message>(
                predicate: #Predicate { message in
                    message.conversationId == targetConversationId
                },
                sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
            )
        }

        descriptor.fetchLimit = limit
        let messages = try modelContext.fetch(descriptor)
        return messages.map { mapToDomain($0) }
    }

    func saveMessage(_ message: ChatMessage) throws {
        let newMessage = Message(
            id: message.id,
            conversationId: message.conversationId,
            role: message.role.rawValue,
            content: message.content,
            createdAt: message.createdAt
        )
        modelContext.insert(newMessage)
        try modelContext.save()
    }

    func deleteMessages(conversationId: UUID) throws {
        let targetConversationId = conversationId
        let descriptor = FetchDescriptor<Message>(
            predicate: #Predicate { message in
                message.conversationId == targetConversationId
            }
        )

        let messages = try modelContext.fetch(descriptor)
        for message in messages {
            modelContext.delete(message)
        }
        try modelContext.save()
    }

    // MARK: - Private Helpers

    private func refreshConversations() {
        do {
            _ = try getAllConversations()
        } catch {
            conversationsSubject.send([])
        }
    }

    private func mapToDomain(_ conversation: Conversation) -> ChatConversation {
        // Get message count and last message preview
        let targetId = conversation.id
        let messageDescriptor = FetchDescriptor<Message>(
            predicate: #Predicate { message in
                message.conversationId == targetId
            },
            sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
        )

        let messages = (try? modelContext.fetch(messageDescriptor)) ?? []
        let lastMessage = messages.first

        return ChatConversation(
            id: conversation.id,
            title: conversation.title ?? "New Conversation",
            createdAt: conversation.createdAt,
            updatedAt: conversation.updatedAt,
            messageCount: messages.count,
            lastMessagePreview: lastMessage.map { String($0.content.prefix(100)) },
            tools: conversation.tools
        )
    }

    private func mapToDomain(_ message: Message) -> ChatMessage {
        let role: MessageRole
        switch message.role {
        case "user":
            role = .user
        case "system":
            role = .system
        default:
            role = .assistant
        }

        return ChatMessage(
            id: message.id,
            conversationId: message.conversationId,
            content: message.content,
            role: role,
            createdAt: message.createdAt,
            metadata: nil
        )
    }
}
