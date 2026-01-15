import Foundation

/// Mapper for chat DTOs to Domain entities
enum ChatMapper {
    /// Map ChatResponseDTO to ChatMessage domain entity
    static func toDomain(_ dto: ChatResponseDTO, conversationId: UUID) -> ChatMessage {
        let createdAt: Date
        if let createdAtString = dto.createdAt {
            createdAt = ISO8601DateFormatter().date(from: createdAtString) ?? Date()
        } else {
            createdAt = Date()
        }

        let role: MessageRole
        switch dto.role.lowercased() {
        case "user":
            role = .user
        case "assistant":
            role = .assistant
        case "system":
            role = .system
        default:
            role = .assistant
        }

        let structuredDataJSON: String?
        if let structuredData = dto.structuredData,
           let jsonData = try? JSONEncoder().encode(structuredData) {
            structuredDataJSON = String(data: jsonData, encoding: .utf8)
        } else {
            structuredDataJSON = nil
        }

        let metadata = MessageMetadata(
            toolsUsed: dto.toolsUsed,
            processingTime: dto.processingTime,
            modelUsed: dto.modelUsed,
            category: dto.intent,
            mediaUrl: dto.mediaUrl,
            requiresLocation: dto.requiresLocation,
            intent: dto.intent,
            structuredDataJSON: structuredDataJSON
        )

        return ChatMessage(
            id: UUID(uuidString: dto.id) ?? UUID(),
            conversationId: conversationId,
            content: dto.content,
            role: role,
            createdAt: createdAt,
            metadata: metadata
        )
    }

    /// Map ToolDTO to Tool domain entity
    static func toDomain(_ dto: ToolDTO) -> Tool {
        let category: ToolCategory
        switch dto.category?.lowercased() {
        case "search":
            category = .search
        case "utility":
            category = .utility
        case "integration":
            category = .integration
        case "astrology":
            category = .astrology
        case "travel":
            category = .travel
        default:
            category = .unknown
        }

        return Tool(
            id: dto.id,
            name: dto.name,
            description: dto.description,
            category: category
        )
    }

    /// Map ProviderDTO to Provider domain entity
    static func toDomain(_ dto: ProviderDTO) -> Provider {
        Provider(
            id: dto.id,
            name: dto.name,
            displayName: dto.displayName ?? dto.name.capitalized,
            authType: dto.authType ?? "api_key",
            isConnected: dto.isConnected,
            iconName: dto.iconName
        )
    }

    /// Map array of ToolDTOs to Tools
    static func toDomain(_ dtos: [ToolDTO]) -> [Tool] {
        dtos.map { toDomain($0) }
    }

    /// Map array of ProviderDTOs to Providers
    static func toDomain(_ dtos: [ProviderDTO]) -> [Provider] {
        dtos.map { toDomain($0) }
    }
}
