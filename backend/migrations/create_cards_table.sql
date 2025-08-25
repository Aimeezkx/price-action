-- Create cards table for flashcard storage
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    deck TEXT,
    due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for efficient due date queries
CREATE INDEX IF NOT EXISTS idx_cards_due ON cards(due_at);

-- Create index for deck filtering
CREATE INDEX IF NOT EXISTS idx_cards_deck ON cards(deck);

-- Sample data for testing (optional)
INSERT INTO cards (front, back, deck, due_at) VALUES 
    ('What is FastAPI?', 'FastAPI is a modern, fast web framework for building APIs with Python', 'Programming', NOW() - INTERVAL '1 day'),
    ('What is React?', 'React is a JavaScript library for building user interfaces', 'Programming', NOW() + INTERVAL '1 day'),
    ('What is PostgreSQL?', 'PostgreSQL is a powerful, open source object-relational database system', 'Database', NOW())
ON CONFLICT DO NOTHING;