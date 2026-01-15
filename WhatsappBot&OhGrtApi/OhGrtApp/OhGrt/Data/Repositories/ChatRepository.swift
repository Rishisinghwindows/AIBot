import Foundation
import Combine

/// Implementation of ChatRepositoryProtocol
final class ChatRepository: ChatRepositoryProtocol, @unchecked Sendable {
    private let remoteDataSource: ChatRemoteDataSourceProtocol

    init(remoteDataSource: ChatRemoteDataSourceProtocol) {
        self.remoteDataSource = remoteDataSource
    }

    func sendMessage(
        _ message: String,
        conversationId: UUID,
        tools: [String],
        location: LocationDTO? = nil
    ) async throws -> ChatMessage {
        let request = ChatRequestDTO(
            message: message,
            conversationId: conversationId.uuidString,
            tools: tools,
            sessionId: nil,
            location: location
        )

        let response = try await remoteDataSource.sendMessage(request)
        return ChatMapper.toDomain(response, conversationId: conversationId)
    }

    func streamMessage(
        _ message: String,
        conversationId: UUID,
        tools: [String]
    ) -> AsyncThrowingStream<String, Error> {
        let request = ChatRequestDTO(
            message: message,
            conversationId: conversationId.uuidString,
            tools: tools,
            sessionId: nil,
            location: nil
        )

        return remoteDataSource.streamMessage(request)
    }

    func getAvailableTools() async throws -> [Tool] {
        let response = try await remoteDataSource.getTools()
        return ChatMapper.toDomain(response.tools)
    }

    func getProviders() async throws -> [Provider] {
        let response = try await remoteDataSource.getProviders()
        return ChatMapper.toDomain(response.providers)
    }

    func connectProvider(_ providerId: String) async throws {
        try await remoteDataSource.connectProvider(providerId)
    }

    func disconnectProvider(_ providerId: String) async throws {
        try await remoteDataSource.disconnectProvider(providerId)
    }
}
