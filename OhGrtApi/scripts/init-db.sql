-- OhGrt Database Initialization Script
-- Creates schema and enables required extensions

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Create application schema
CREATE SCHEMA IF NOT EXISTS agentic;

-- Grant permissions
GRANT ALL ON SCHEMA agentic TO postgres;
