/**
 * API Client for D23Web
 *
 * Handles communication with OhGrtApi backend for anonymous chat sessions.
 */

// API Base URL - use relative path to go through Next.js proxy (see next.config.mjs rewrites)
// This allows the app to work when accessed from external networks
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api";

// Session storage key
const SESSION_KEY = "d23_chat_session";

export interface WebSession {
  session_id: string;
  expires_at: string;
  language: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  language: string;
  media_url?: string;  // For image responses
  intent?: string;  // Detected intent (pnr_status, weather, etc.)
  structured_data?: Record<string, unknown>;  // Structured data for rich UI rendering
}

export interface ChatResponse {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  detected_language: string;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
  session_id: string;
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Get or create a session
   */
  async getOrCreateSession(): Promise<WebSession> {
    // Check for existing session in localStorage
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(SESSION_KEY);
      if (stored) {
        try {
          const session = JSON.parse(stored) as WebSession;
          // Check if session is still valid
          if (new Date(session.expires_at) > new Date()) {
            // Verify session is still valid on server
            try {
              const verified = await this.verifySession(session.session_id);
              return verified;
            } catch {
              // Session expired on server, create new one
              localStorage.removeItem(SESSION_KEY);
            }
          }
        } catch {
          localStorage.removeItem(SESSION_KEY);
        }
      }
    }

    // Create new session
    return this.createSession();
  }

  /**
   * Create a new anonymous session
   */
  async createSession(): Promise<WebSession> {
    const response = await fetch(`${this.baseURL}/web/session`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept-Language": navigator.language || "en",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to create session");
    }

    const session = (await response.json()) as WebSession;

    // Store in localStorage
    if (typeof window !== "undefined") {
      localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    }

    return session;
  }

  /**
   * Verify an existing session
   */
  async verifySession(sessionId: string): Promise<WebSession> {
    const response = await fetch(`${this.baseURL}/web/session/${sessionId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Session not found or expired");
    }

    return response.json();
  }

  /**
   * Send a chat message
   */
  async sendMessage(
    sessionId: string,
    message: string,
    language?: string
  ): Promise<ChatResponse> {
    const response = await fetch(`${this.baseURL}/web/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: message,
        language: language,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Failed to send message");
    }

    const data = await response.json();
    // Debug: log the response to see if media_url is present
    console.log("[API] Chat response:", JSON.stringify(data, null, 2));
    if (data.assistant_message?.media_url) {
      console.log("[API] Media URL found:", data.assistant_message.media_url);
    }
    return data;
  }

  /**
   * Get chat history
   */
  async getChatHistory(
    sessionId: string,
    limit: number = 50
  ): Promise<ChatHistoryResponse> {
    const response = await fetch(
      `${this.baseURL}/web/chat/history/${sessionId}?limit=${limit}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error("Failed to fetch chat history");
    }

    return response.json();
  }

  /**
   * Delete session (clear chat)
   */
  async deleteSession(sessionId: string): Promise<void> {
    const response = await fetch(`${this.baseURL}/web/session/${sessionId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to delete session");
    }

    // Clear local storage
    if (typeof window !== "undefined") {
      localStorage.removeItem(SESSION_KEY);
    }
  }

  /**
   * Clear local session without server call
   */
  clearLocalSession(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem(SESSION_KEY);
    }
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export class for custom instances
export { APIClient };
