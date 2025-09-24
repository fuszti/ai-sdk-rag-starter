-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create resources table
CREATE TABLE IF NOT EXISTS resources (
    id VARCHAR(191) PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id VARCHAR(191) PRIMARY KEY,
    resource_id VARCHAR(191) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL
);

-- Insert pre-defined test memories for evaluation
-- These memories will be available for all simulations to test retrieval

INSERT INTO resources (id, content) VALUES
('test-memory-1', 'I had a wonderful sunset dinner at Cafe Luna with my college friend Sarah last Tuesday. We talked about her new job in marketing and reminisced about our study abroad trip to Italy.'),
('test-memory-2', 'Bought groceries at Whole Foods yesterday: organic bananas, quinoa, Greek yogurt, spinach, and dark chocolate. Spent about $65 total.'),
('test-memory-3', 'Meeting with Dr. Johnson about my knee injury is scheduled for next Friday at 2 PM. Need to bring previous X-rays and insurance card.'),
('test-memory-4', 'Mom''s birthday is coming up on March 15th. She mentioned wanting a new garden hose and some kitchen towels. Budget around $50.'),
('test-memory-5', 'Started reading "The Seven Husbands of Evelyn Hugo" by Taylor Jenkins Reid. Really enjoying it so far - finished chapter 3 last night.');

-- Note: Embeddings will be generated dynamically when the application starts
-- This ensures they use the same embedding model as the running application