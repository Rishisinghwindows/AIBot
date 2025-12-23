import Foundation

/// HTTP methods
enum HTTPMethod: String {
    case get = "GET"
    case post = "POST"
    case put = "PUT"
    case delete = "DELETE"
}

/// API endpoint definitions
enum APIEndpoint {
    // Auth
    case googleAuth
    case refreshToken
    case logout
    case me
    case updateProfile
    case birthDetails
    case saveBirthDetails
    case deleteBirthDetails

    // Personas
    case personas
    case createPersona
    case persona(id: String)
    case updatePersona(id: String)
    case deletePersona(id: String)
    case checkHandle(handle: String)
    case personaDocuments(personaId: String)
    case uploadPersonaDocument(personaId: String)
    case deletePersonaDocument(personaId: String, docId: String)

    // Public Persona (no auth)
    case publicPersona(handle: String)
    case publicPersonaChat(handle: String)
    case publicPersonaChatHistory(handle: String, sessionId: String)

    // Chat
    case chatSend
    case chatHistory
    case conversations
    case tools
    case providers
    case connectProvider
    case disconnectProvider(provider: String)
    case deleteConversation(id: String)
    case githubOAuthStart
    case githubOAuthExchange
    case providerOAuthStart(provider: String)
    case providerOAuthExchange(provider: String)

    // Web session (anonymous, for development without auth)
    case webSession
    case webChat
    case webChatHistory(sessionId: String)
    case webTools
    case webProviders

    // Web scheduled tasks
    case webTasks(sessionId: String)
    case webCreateTask(sessionId: String)
    case webTask(taskId: String, sessionId: String)
    case webUpdateTask(taskId: String, sessionId: String)
    case webDeleteTask(taskId: String, sessionId: String)
    case webPauseTask(taskId: String, sessionId: String)
    case webResumeTask(taskId: String, sessionId: String)

    // Legacy
    case ask
    case weather(city: String)
    case pdfUpload
    case health

    var path: String {
        switch self {
        case .googleAuth:
            return "/auth/google"
        case .refreshToken:
            return "/auth/refresh"
        case .logout:
            return "/auth/logout"
        case .me:
            return "/auth/me"
        case .updateProfile:
            return "/auth/profile"
        case .birthDetails, .saveBirthDetails, .deleteBirthDetails:
            return "/auth/birth-details"

        // Personas
        case .personas, .createPersona:
            return "/personas"
        case .persona(let id), .updatePersona(let id), .deletePersona(let id):
            return "/personas/\(id)"
        case .checkHandle(let handle):
            return "/personas/check-handle/\(handle)"
        case .personaDocuments(let personaId), .uploadPersonaDocument(let personaId):
            return "/personas/\(personaId)/documents"
        case .deletePersonaDocument(let personaId, let docId):
            return "/personas/\(personaId)/documents/\(docId)"

        // Public Persona
        case .publicPersona(let handle):
            return "/p/\(handle)"
        case .publicPersonaChat(let handle):
            return "/p/\(handle)/chat"
        case .publicPersonaChatHistory(let handle, let sessionId):
            return "/p/\(handle)/chat/\(sessionId)"
        case .chatSend:
            return "/chat/send"
        case .chatHistory:
            return "/chat/history"
        case .conversations:
            return "/chat/conversations"
        case .tools:
            return "/chat/tools"
        case .providers:
            return "/auth/providers"
        case .connectProvider:
            return "/auth/providers/connect"
        case .disconnectProvider(let provider):
            return "/auth/providers/\(provider)"
        case .deleteConversation(let id):
            return "/chat/conversations/\(id)"
        case .githubOAuthStart:
            return "/auth/github/start"
        case .githubOAuthExchange:
            return "/auth/github/exchange"
        case .providerOAuthStart(let provider):
            let slug = provider.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? provider
            return "/auth/providers/\(slug)/start"
        case .providerOAuthExchange(let provider):
            let slug = provider.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? provider
            return "/auth/providers/\(slug)/exchange"
        case .webSession:
            return "/web/session"
        case .webChat:
            return "/web/chat"
        case .webChatHistory(let sessionId):
            return "/web/chat/history/\(sessionId)"
        case .webTools:
            return "/web/tools"
        case .webProviders:
            return "/web/providers"
        case .webTasks(let sessionId):
            return "/web/tasks?session_id=\(sessionId)"
        case .webCreateTask(let sessionId):
            return "/web/tasks?session_id=\(sessionId)"
        case .webTask(let taskId, let sessionId):
            return "/web/tasks/\(taskId)?session_id=\(sessionId)"
        case .webUpdateTask(let taskId, let sessionId):
            return "/web/tasks/\(taskId)?session_id=\(sessionId)"
        case .webDeleteTask(let taskId, let sessionId):
            return "/web/tasks/\(taskId)?session_id=\(sessionId)"
        case .webPauseTask(let taskId, let sessionId):
            return "/tasks/\(taskId)/pause?session_id=\(sessionId)"
        case .webResumeTask(let taskId, let sessionId):
            return "/tasks/\(taskId)/resume?session_id=\(sessionId)"
        case .ask:
            return "/ask"
        case .weather(let city):
            return "/weather?city=\(city.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? city)"
        case .pdfUpload:
            return "/pdf/upload"
        case .health:
            return "/health"
        }
    }

    var method: HTTPMethod {
        switch self {
        case .googleAuth, .refreshToken, .logout, .chatSend, .ask, .pdfUpload, .connectProvider, .githubOAuthExchange, .providerOAuthExchange, .saveBirthDetails, .webSession, .webChat, .webCreateTask, .webPauseTask, .webResumeTask, .createPersona, .uploadPersonaDocument, .publicPersonaChat:
            return .post
        case .me, .chatHistory, .conversations, .tools, .providers, .weather, .health, .githubOAuthStart, .providerOAuthStart, .birthDetails, .webChatHistory, .webTools, .webProviders, .webTasks, .webTask, .personas, .persona, .checkHandle, .personaDocuments, .publicPersona, .publicPersonaChatHistory:
            return .get
        case .deleteConversation, .disconnectProvider, .deleteBirthDetails, .webDeleteTask, .deletePersona, .deletePersonaDocument:
            return .delete
        case .webUpdateTask, .updateProfile, .updatePersona:
            return .put
        }
    }

    var requiresAuth: Bool {
        switch self {
        case .googleAuth, .refreshToken, .health, .webSession, .webChat, .webChatHistory, .webTools, .webProviders, .webTasks, .webCreateTask, .webTask, .webUpdateTask, .webDeleteTask, .webPauseTask, .webResumeTask, .publicPersona, .publicPersonaChat, .publicPersonaChatHistory, .checkHandle:
            return false
        default:
            return true
        }
    }
}
