import Foundation

/// DTO for user location
struct LocationDTO: Codable {
    let latitude: Double
    let longitude: Double
    let accuracy: Double?
    let address: String?
}

/// DTO for chat message request
struct ChatRequestDTO: Codable {
    let message: String
    let conversationId: String
    let tools: [String]
    let sessionId: String?
    let location: LocationDTO?

    enum CodingKeys: String, CodingKey {
        case message
        case conversationId = "conversation_id"
        case tools
        case sessionId = "session_id"
        case location
    }
}

/// DTO for chat message response
struct ChatResponseDTO: Codable {
    let id: String
    let content: String
    let role: String
    let createdAt: String?
    let toolsUsed: [String]?
    let processingTime: Double?
    let modelUsed: String?
    let mediaUrl: String?
    let requiresLocation: Bool?

    enum CodingKeys: String, CodingKey {
        case id
        case content
        case role
        case createdAt = "created_at"
        case toolsUsed = "tools_used"
        case processingTime = "processing_time"
        case modelUsed = "model_used"
        case mediaUrl = "media_url"
        case requiresLocation = "requires_location"
    }
}

/// DTO for tool information
struct ToolDTO: Codable {
    let id: String
    let name: String
    let description: String
    let category: String?
}

/// DTO for tools list response
struct ToolsResponseDTO: Codable {
    let tools: [ToolDTO]
}

/// DTO for provider information
struct ProviderDTO: Codable {
    let id: String
    let name: String
    let displayName: String?
    let authType: String?
    let isConnected: Bool
    let iconName: String?

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case displayName = "display_name"
        case authType = "auth_type"
        case isConnected = "is_connected"
        case iconName = "icon_name"
    }
}

/// DTO for providers list response
struct ProvidersResponseDTO: Codable {
    let providers: [ProviderDTO]
}
