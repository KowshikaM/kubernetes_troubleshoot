-- Create investigations table for storing investigation history
CREATE TABLE investigations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  namespace VARCHAR(255),
  root_cause TEXT NOT NULL,
  explanation TEXT,
  confidence INTEGER DEFAULT 0,
  status VARCHAR(50) DEFAULT 'pending',
  diagnosis_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable row-level security
ALTER TABLE investigations ENABLE ROW LEVEL SECURITY;

-- RLS policy: users can only see their own investigations
CREATE POLICY "Users can see their own investigations" ON investigations
  FOR SELECT
  USING (auth.uid() = user_id);

-- RLS policy: users can only insert their own investigations
CREATE POLICY "Users can insert their own investigations" ON investigations
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Index for efficient queries
CREATE INDEX idx_investigations_user_created 
  ON investigations(user_id, created_at DESC);
