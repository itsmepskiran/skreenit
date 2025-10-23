CREATE TABLE IF NOT EXISTS candidate_drafts (
  candidate_id UUID PRIMARY KEY,
  draft JSONB NOT NULL DEFAULT '{}',
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_candidate FOREIGN KEY (candidate_id) REFERENCES auth.users (id) ON DELETE CASCADE,
  CONSTRAINT unique_draft UNIQUE (candidate_id)
);

-- Create index on candidate_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_candidate_drafts_id ON candidate_drafts(candidate_id);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_candidate_drafts_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to call the update function
CREATE TRIGGER trigger_update_candidate_drafts_timestamp
  BEFORE UPDATE ON candidate_drafts
  FOR EACH ROW
  EXECUTE FUNCTION update_candidate_drafts_timestamp();

-- Grant access to authenticated users (will need to re-run after each RLS change)
ALTER TABLE candidate_drafts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own drafts"
  ON candidate_drafts FOR SELECT
  USING (auth.uid() = candidate_id);

CREATE POLICY "Users can insert their own drafts"
  ON candidate_drafts FOR INSERT
  WITH CHECK (auth.uid() = candidate_id);

CREATE POLICY "Users can update their own drafts"
  ON candidate_drafts FOR UPDATE
  USING (auth.uid() = candidate_id)
  WITH CHECK (auth.uid() = candidate_id);

-- Grant permissions to authenticated users
GRANT ALL ON candidate_drafts TO authenticated;

-- If using service_role key access as well:
GRANT ALL ON candidate_drafts TO service_role;