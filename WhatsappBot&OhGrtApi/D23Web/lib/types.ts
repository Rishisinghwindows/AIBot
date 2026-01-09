export interface Tool {
  id: string;
  name: string;
  description?: string;
  type: string;
  config: Record<string, string>;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface Provider {
  name: string;
  display_name: string;
  auth_type: string;
  connected: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  message_count: number;
  last_message_at: string;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  message_metadata?: Record<string, unknown>;
  created_at: string;
  conversation_id?: string;
  media_url?: string;
  intent?: string;
  structured_data?: Record<string, unknown>;
}

export interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  photo_url: string | null;
  created_at: string;
}
