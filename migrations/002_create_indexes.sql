
-- User lookups
CREATE INDEX idx_users_email ON users(email);

-- Follow graph queries
CREATE INDEX idx_follows_follower ON follows(follower_id);
CREATE INDEX idx_follows_followee ON follows(followee_id);

-- Story queries (most important for performance)
CREATE INDEX idx_stories_author ON stories(author_id, created_at DESC);
CREATE INDEX idx_stories_expires ON stories(expires_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_stories_active ON stories(created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_stories_visibility ON stories(visibility) WHERE deleted_at IS NULL;

-- Views and reactions
CREATE INDEX idx_story_views_story ON story_views(story_id);
CREATE INDEX idx_reactions_story ON reactions(story_id);
CREATE INDEX idx_reactions_user ON reactions(user_id);
