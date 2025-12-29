-- =============================================================================
-- D23Bot Database Initialization Script
-- =============================================================================
-- This script runs automatically when PostgreSQL container starts
-- =============================================================================

-- Create schema
CREATE SCHEMA IF NOT EXISTS agentic;

-- Set search path
SET search_path TO agentic, public;

-- =============================================================================
-- USER PROFILES TABLE
-- =============================================================================
-- Stores user birth details and preferences for personalized features

CREATE TABLE IF NOT EXISTS user_profiles (
    phone_number VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    birth_date VARCHAR(20),
    birth_time VARCHAR(20),
    birth_place VARCHAR(100),

    -- Cached astrology data
    moon_sign VARCHAR(20),
    sun_sign VARCHAR(20),
    ascendant VARCHAR(20),
    moon_nakshatra VARCHAR(30),

    -- Preferences
    preferred_language VARCHAR(10) DEFAULT 'en',
    notification_enabled BOOLEAN DEFAULT false,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_updated
    ON user_profiles(updated_at DESC);

-- =============================================================================
-- CONVERSATION CONTEXT TABLE
-- =============================================================================
-- Stores temporary conversation context for multi-turn flows

CREATE TABLE IF NOT EXISTS conversation_context (
    phone_number VARCHAR(20),
    context_type VARCHAR(50),
    context_data JSONB,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (phone_number, context_type)
);

-- Index for expired context cleanup
CREATE INDEX IF NOT EXISTS idx_conversation_context_expires
    ON conversation_context(expires_at);

-- Auto-cleanup expired contexts (run periodically)
CREATE OR REPLACE FUNCTION cleanup_expired_contexts()
RETURNS void AS $$
BEGIN
    DELETE FROM conversation_context
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- REMINDERS TABLE
-- =============================================================================
-- Stores user-created reminders

CREATE TABLE IF NOT EXISTS reminders (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    remind_at TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP,

    CONSTRAINT reminders_status_check
        CHECK (status IN ('pending', 'sent', 'cancelled', 'failed'))
);

-- Index for pending reminders
CREATE INDEX IF NOT EXISTS idx_reminders_pending
    ON reminders(remind_at)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_reminders_phone
    ON reminders(phone_number);

-- =============================================================================
-- QUERY HISTORY TABLE (Optional - for analytics)
-- =============================================================================
-- Stores anonymized query history for improving the bot

CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    phone_hash VARCHAR(64),  -- Hashed phone number for privacy
    intent VARCHAR(50),
    domain VARCHAR(30),
    query_length INTEGER,
    response_time_ms INTEGER,
    success BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for analytics queries
CREATE INDEX IF NOT EXISTS idx_query_history_created
    ON query_history(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_query_history_intent
    ON query_history(intent, created_at DESC);

-- =============================================================================
-- RATE LIMITING TABLE (Optional - for persistent rate limits)
-- =============================================================================

CREATE TABLE IF NOT EXISTS rate_limits (
    phone_number VARCHAR(20) PRIMARY KEY,
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMP DEFAULT NOW(),
    cooldown_until TIMESTAMP
);

-- =============================================================================
-- LANGGRAPH CHECKPOINT TABLES
-- =============================================================================
-- These are created automatically by langgraph-checkpoint-postgres
-- but we ensure the schema exists

-- Note: LangGraph will create these tables automatically:
-- - checkpoints
-- - checkpoint_blobs
-- - checkpoint_writes

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for user_profiles
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- SEED DATA (Optional - for testing)
-- =============================================================================

-- Uncomment to add test data:
/*
INSERT INTO user_profiles (phone_number, name, birth_date, birth_time, birth_place)
VALUES
    ('919876543210', 'Test User', '15-08-1990', '10:30 AM', 'Delhi'),
    ('919876543211', 'Demo User', '22-03-1992', '14:00', 'Mumbai')
ON CONFLICT (phone_number) DO NOTHING;
*/

-- =============================================================================
-- GRANTS
-- =============================================================================

-- Grant permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON SCHEMA agentic TO postgres;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agentic TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agentic TO postgres;

-- =============================================================================
-- COMPLETION
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE 'D23Bot database initialization complete!';
    RAISE NOTICE 'Schema: agentic';
    RAISE NOTICE 'Tables created: user_profiles, conversation_context, reminders, query_history, rate_limits';
END $$;
