-- Seed script for local Postgres + pgvector.
-- Run with: psql -h <host> -U <user> -d <database> -f data/db/seed.sql

CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS agentic;
SET search_path TO agentic;

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  amount NUMERIC(10,2) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Example data
INSERT INTO users (email, created_at) VALUES
  ('alice@example.com', NOW() - INTERVAL '9 days'),
  ('bob@example.com', NOW() - INTERVAL '6 days'),
  ('carol@example.com', NOW() - INTERVAL '3 days')
ON CONFLICT DO NOTHING;

INSERT INTO orders (user_id, amount, created_at) VALUES
  (1, 120.50, NOW() - INTERVAL '8 days'),
  (1, 75.00, NOW() - INTERVAL '7 days'),
  (2, 200.00, NOW() - INTERVAL '5 days'),
  (3, 50.00, NOW() - INTERVAL '2 days')
ON CONFLICT DO NOTHING;
