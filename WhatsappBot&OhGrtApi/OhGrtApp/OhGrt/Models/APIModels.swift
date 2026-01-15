import Foundation

// MARK: - Auth Models

/// Request to authenticate with Google/Firebase
struct GoogleAuthRequest: Encodable {
    let firebaseIdToken: String
    let deviceInfo: String?
}

/// Request to refresh access token
struct RefreshTokenRequest: Encodable {
    let refreshToken: String
}

/// Token response from auth endpoints
struct TokenResponse: Decodable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String
    let expiresIn: Int
}

/// User profile response
struct UserResponse: Decodable {
    let id: String
    let email: String
    let displayName: String?
    let photoUrl: String?
    let bio: String?
    let preferences: [String: String]?
    let createdAt: Date?
}

/// Request to update profile
struct ProfileUpdateRequest: Encodable {
    let displayName: String?
    let bio: String?
    let photoUrl: String?
    let preferences: [String: String]?
}

// MARK: - Chat Models

/// Request to send a chat message
struct ChatSendRequest: Encodable {
    let message: String
    let conversationId: UUID?
    let tools: [String]?
}

/// Response from sending a chat message
struct ChatSendResponse: Decodable {
    let conversationId: UUID
    let userMessage: ChatMessageResponse
    let assistantMessage: ChatMessageResponse
}

/// A single chat message from API
struct ChatMessageResponse: Decodable, Identifiable {
    let id: UUID
    let role: String
    let content: String
    let metadata: [String: String]?
    let createdAt: Date

    private enum CodingKeys: String, CodingKey {
        case id
        case role
        case content
        case metadata = "message_metadata"
        case createdAt
    }
}

/// Chat history response
struct ChatHistoryResponse: Decodable {
    let messages: [ChatMessageResponse]
    let hasMore: Bool
}

/// Conversation summary
struct ConversationSummary: Decodable, Identifiable {
    let id: UUID
    let title: String?
    let messageCount: Int
    let lastMessageAt: Date
    let createdAt: Date
}

// MARK: - Tool Models

struct ToolInfo: Decodable, Identifiable {
    let name: String
    let description: String
    let category: String?

    var id: String { name }

    init(name: String, description: String, category: String? = nil) {
        self.name = name
        self.description = description
        self.category = category
    }

    private enum CodingKeys: String, CodingKey {
        case name
        case description
        case category
    }
}

// MARK: - Provider Models

struct ProviderInfo: Decodable, Identifiable {
    let name: String
    let displayName: String
    let authType: String
    let connected: Bool

    var id: String { name }

    init(name: String, displayName: String, authType: String, connected: Bool) {
        self.name = name
        self.displayName = displayName
        self.authType = authType
        self.connected = connected
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        name = try container.decode(String.self, forKey: .name)
        displayName = try container.decode(String.self, forKey: .displayName)
        authType = try container.decode(String.self, forKey: .authType)
        connected = try container.decode(Bool.self, forKey: .connected)
    }

    private enum CodingKeys: String, CodingKey {
        case name, displayName, authType, connected
    }
}

struct ProviderConnectRequest: Encodable {
    let provider: String
    let secret: String
    let displayName: String?
    let config: [String: String]?
}

struct OAuthStartResponse: Decodable {
    let authUrl: String
    let state: String
}

struct OAuthExchangeRequest: Encodable {
    let code: String
    let state: String
}

// MARK: - Birth Details Models

/// Request to save birth details
struct BirthDetailsRequest: Encodable {
    let fullName: String?
    let birthDate: String?
    let birthTime: String?
    let birthPlace: String?
    let zodiacSign: String?
}

/// Birth details response
struct BirthDetailsResponse: Decodable {
    let id: String
    let userId: String
    let fullName: String?
    let birthDate: String?
    let birthTime: String?
    let birthPlace: String?
    let zodiacSign: String?
    let moonSign: String?
    let nakshatra: String?
    let createdAt: Date?
    let updatedAt: Date?
}

// MARK: - Web Session Models (Anonymous, no auth required)

/// Response when creating a web session
struct WebSessionResponse: Decodable {
    let sessionId: String
    let expiresAt: Date
    let language: String
}

/// Request to send a web chat message
struct WebChatRequest: Encodable {
    let message: String
    let sessionId: String
    let language: String?
}

/// A web chat message
struct WebChatMessage: Decodable, Identifiable {
    let id: String
    let role: String
    let content: String
    let timestamp: Date
    let language: String
}

/// Response from web chat endpoint
struct WebChatResponse: Decodable {
    let userMessage: WebChatMessage
    let assistantMessage: WebChatMessage
    let detectedLanguage: String
}

/// Web chat history response
struct WebChatHistoryResponse: Decodable {
    let messages: [WebChatMessage]
    let sessionId: String
}

// MARK: - Legacy Models

/// Legacy ask request
struct AskRequest: Encodable {
    let message: String
}

/// Legacy ask response
struct AskResponse: Decodable {
    let category: String
    let response: String
    let routeLog: [String]
    let metadata: [String: String]
}

/// Weather response
struct WeatherResponse: Decodable {
    let city: String
    let temperature: Double
    let description: String
    let humidity: Int?
    let windSpeed: Double?
}

/// Health check response
struct HealthResponse: Decodable {
    let status: String
    let version: String
}

// MARK: - Persona Models

/// Personality questionnaire data
struct PersonalityData: Codable {
    var communicationStyle: String?
    var expertiseArea: String?
    var topics: [String]?
    var outsideExpertiseResponse: String?
    var responseLength: String?
    var useHumor: String?
}

/// Professional questionnaire data
struct ProfessionalData: Codable {
    var jobTitle: String?
    var industry: String?
    var yearsExperience: Int?
    var skills: [String]?
    var achievements: String?
    var problemsSolved: String?
}

/// Request to create a persona
struct PersonaCreateRequest: Encodable {
    let handle: String
    let displayName: String
    let tagline: String?
    let avatarUrl: String?
    let personality: PersonalityData?
    let professional: ProfessionalData?
    let isPublic: Bool
}

/// Request to update a persona
struct PersonaUpdateRequest: Encodable {
    let displayName: String?
    let tagline: String?
    let avatarUrl: String?
    let personality: PersonalityData?
    let professional: ProfessionalData?
    let isPublic: Bool?
}

/// Persona response (for owner)
struct PersonaResponse: Decodable, Identifiable {
    let id: String
    let handle: String
    let displayName: String
    let tagline: String?
    let avatarUrl: String?
    let personality: [String: AnyCodable]?
    let professional: [String: AnyCodable]?
    let isPublic: Bool
    let totalChats: Int
    let createdAt: Date
    let updatedAt: Date
}

/// Public persona response (for visitors)
struct PersonaPublicResponse: Decodable {
    let handle: String
    let displayName: String
    let tagline: String?
    let avatarUrl: String?
    let expertiseArea: String?
    let topics: [String]?
    let jobTitle: String?
    let industry: String?
}

/// Persona document response
struct PersonaDocumentResponse: Decodable, Identifiable {
    let id: String
    let filename: String
    let fileSize: Int
    let chunkCount: Int
    let createdAt: Date
}

/// Handle check response
struct HandleCheckResponse: Decodable {
    let handle: String
    let available: Bool
}

/// Persona chat request
struct PersonaChatRequest: Encodable {
    let message: String
    let sessionId: String?
    let visitorName: String?
}

/// Persona chat response
struct PersonaChatResponse: Decodable {
    let sessionId: String
    let response: String
}

/// Persona chat history response
struct PersonaChatHistoryResponse: Decodable {
    let sessionId: String
    let personaHandle: String
    let messages: [PersonaChatMessageResponse]
    let createdAt: Date
}

/// Individual persona chat message
struct PersonaChatMessageResponse: Decodable {
    let role: String
    let content: String
    let createdAt: String
}

// MARK: - Helper for dynamic JSON

/// Type-erased codable for dynamic JSON values
struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let string = try? container.decode(String.self) {
            value = string
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dict = try? container.decode([String: AnyCodable].self) {
            value = dict.mapValues { $0.value }
        } else {
            value = NSNull()
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch value {
        case let string as String:
            try container.encode(string)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let bool as Bool:
            try container.encode(bool)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dict as [String: Any]:
            try container.encode(dict.mapValues { AnyCodable($0) })
        default:
            try container.encodeNil()
        }
    }
}
