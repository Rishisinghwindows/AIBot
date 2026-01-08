/**
 * Tests for the API client
 *
 * Run with: npm test
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

// Mock fetch
const mockFetch = vi.fn()

beforeEach(() => {
  vi.stubGlobal('localStorage', localStorageMock)
  vi.stubGlobal('fetch', mockFetch)
  localStorageMock.clear()
  mockFetch.mockReset()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('APIClient', () => {
  describe('Session Management', () => {
    it('should create a new session when none exists', async () => {
      const mockSession = {
        session_id: 'test-session-123',
        expires_at: new Date(Date.now() + 86400000).toISOString(),
        language: 'en',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSession,
      })

      // Dynamically import to get fresh instance
      const { APIClient } = await import('../lib/api-client')
      const client = new APIClient()

      const session = await client.createSession()

      expect(session.session_id).toBe('test-session-123')
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/web/session'),
        expect.objectContaining({
          method: 'POST',
        })
      )
    })

    it('should return existing valid session from localStorage', async () => {
      const futureDate = new Date(Date.now() + 86400000).toISOString()
      const existingSession = {
        session_id: 'existing-session',
        expires_at: futureDate,
        language: 'en',
      }

      localStorageMock.setItem('d23_chat_session', JSON.stringify(existingSession))

      // Mock the verify endpoint
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => existingSession,
      })

      const { APIClient } = await import('../lib/api-client')
      const client = new APIClient()

      const session = await client.getOrCreateSession()

      expect(session.session_id).toBe('existing-session')
    })

    it('should create new session when existing session is expired', async () => {
      const pastDate = new Date(Date.now() - 86400000).toISOString()
      const expiredSession = {
        session_id: 'expired-session',
        expires_at: pastDate,
        language: 'en',
      }

      localStorageMock.setItem('d23_chat_session', JSON.stringify(expiredSession))

      const newSession = {
        session_id: 'new-session',
        expires_at: new Date(Date.now() + 86400000).toISOString(),
        language: 'en',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => newSession,
      })

      const { APIClient } = await import('../lib/api-client')
      const client = new APIClient()

      const session = await client.getOrCreateSession()

      expect(session.session_id).toBe('new-session')
    })

    it('should clear local session', async () => {
      const session = {
        session_id: 'test-session',
        expires_at: new Date(Date.now() + 86400000).toISOString(),
        language: 'en',
      }

      localStorageMock.setItem('d23_chat_session', JSON.stringify(session))

      const { APIClient } = await import('../lib/api-client')
      const client = new APIClient()

      client.clearLocalSession()

      expect(localStorageMock.getItem('d23_chat_session')).toBeNull()
    })
  })

  describe('Chat Operations', () => {
    it('should send a message and receive response', async () => {
      const mockResponse = {
        user_message: {
          id: 'user-msg-1',
          role: 'user',
          content: 'Hello',
          timestamp: new Date().toISOString(),
          language: 'en',
        },
        assistant_message: {
          id: 'assistant-msg-1',
          role: 'assistant',
          content: 'Hi there!',
          timestamp: new Date().toISOString(),
          language: 'en',
        },
        detected_language: 'en',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const { APIClient } = await import('../lib/api-client')
      const client = new APIClient()

      const response = await client.sendMessage('test-session', 'Hello')

      expect(response.user_message.content).toBe('Hello')
      expect(response.assistant_message.content).toBe('Hi there!')
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/web/chat'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('Hello'),
        })
      )
    })

    it('should get chat history', async () => {
      const mockHistory = {
        messages: [
          {
            id: 'msg-1',
            role: 'user',
            content: 'First message',
            timestamp: new Date().toISOString(),
            language: 'en',
          },
          {
            id: 'msg-2',
            role: 'assistant',
            content: 'Response',
            timestamp: new Date().toISOString(),
            language: 'en',
          },
        ],
        session_id: 'test-session',
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistory,
      })

      const { APIClient } = await import('../lib/api-client')
      const client = new APIClient()

      const history = await client.getChatHistory('test-session')

      expect(history.messages).toHaveLength(2)
      expect(history.messages[0].content).toBe('First message')
    })
  })

  describe('Error Handling', () => {
    it('should throw error on failed request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      })

      const { APIClient } = await import('../lib/api-client')
      const client = new APIClient()

      await expect(client.createSession()).rejects.toThrow()
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const { APIClient } = await import('../lib/api-client')
      const client = new APIClient()

      await expect(client.createSession()).rejects.toThrow('Network error')
    })

    it('should handle 401 session expired', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
      })

      const { APIClient } = await import('../lib/api-client')
      const client = new APIClient()

      await expect(client.sendMessage('expired-session', 'test')).rejects.toThrow()
    })

    it('should handle 429 rate limit', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        statusText: 'Too Many Requests',
      })

      const { APIClient } = await import('../lib/api-client')
      const client = new APIClient()

      await expect(client.sendMessage('test-session', 'test')).rejects.toThrow()
    })
  })
})

describe('Session Storage', () => {
  it('should store session in localStorage', async () => {
    const mockSession = {
      session_id: 'stored-session',
      expires_at: new Date(Date.now() + 86400000).toISOString(),
      language: 'en',
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSession,
    })

    const { APIClient } = await import('../lib/api-client')
    const client = new APIClient()

    await client.createSession()

    const stored = localStorageMock.getItem('d23_chat_session')
    expect(stored).not.toBeNull()
    expect(JSON.parse(stored!).session_id).toBe('stored-session')
  })
})
