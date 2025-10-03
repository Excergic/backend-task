import asyncio
import asyncpg
from faker import Faker
import random
from uuid import uuid4

fake = Faker()

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/stories_db"


async def seed_database():
    """Seed database with test data"""
    print("Seeding database...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Create users
        print("Creating users...")
        user_ids = []
        
        for i in range(10):
            user_id = uuid4()
            email = fake.email()
            password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqCQ9P6oka"  # "password123"
            
            await conn.execute("""
                INSERT INTO users (id, email, password_hash)
                VALUES ($1, $2, $3)
                ON CONFLICT (email) DO NOTHING
            """, user_id, email, password_hash)
            
            user_ids.append(user_id)
        
        print(f"Created {len(user_ids)} users")
        
        # Create follows
        print("Creating follows...")
        follow_count = 0
        
        for user_id in user_ids:
            # Each user follows 2-5 random other users
            num_follows = random.randint(2, 5)
            targets = random.sample([uid for uid in user_ids if uid != user_id], num_follows)
            
            for target_id in targets:
                await conn.execute("""
                    INSERT INTO follows (follower_id, followee_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                """, user_id, target_id)
                follow_count += 1
        
        print(f"Created {follow_count} follows")
        
        # Create stories
        print("Creating stories...")
        story_ids = []
        visibilities = ['public', 'friends', 'private']
        
        for user_id in user_ids:
            # Each user creates 3-8 stories
            num_stories = random.randint(3, 8)
            
            for _ in range(num_stories):
                story_id = uuid4()
                text = fake.sentence(nb_words=10)
                visibility = random.choice(visibilities)
                
                await conn.execute("""
                    INSERT INTO stories (id, author_id, text, visibility, expires_at)
                    VALUES ($1, $2, $3, $4, NOW() + INTERVAL '24 hours')
                """, story_id, user_id, text, visibility)
                
                story_ids.append((story_id, user_id))
        
        print(f"Created {len(story_ids)} stories")
        
        # Create views
        print("Creating views...")
        view_count = 0
        
        for story_id, author_id in story_ids:
            # Random 2-7 users view each story
            num_viewers = random.randint(2, 7)
            viewers = random.sample([uid for uid in user_ids if uid != author_id], 
                                   min(num_viewers, len(user_ids) - 1))
            
            for viewer_id in viewers:
                await conn.execute("""
                    INSERT INTO story_views (story_id, viewer_id, viewed_at)
                    VALUES ($1, $2, NOW() - INTERVAL '1 hour' * random() * 24)
                    ON CONFLICT DO NOTHING
                """, story_id, viewer_id)
                view_count += 1
        
        print(f"Created {view_count} views")
        
        # Create reactions
        print("Creating reactions...")
        emojis = ['👍', '❤️', '😂', '😮', '😢', '🔥']
        reaction_count = 0
        
        for story_id, author_id in story_ids:
            # Random 1-5 reactions per story
            num_reactions = random.randint(1, 5)
            reactors = random.sample([uid for uid in user_ids if uid != author_id], 
                                    min(num_reactions, len(user_ids) - 1))
            
            for reactor_id in reactors:
                reaction_id = uuid4()
                emoji = random.choice(emojis)
                
                await conn.execute("""
                    INSERT INTO reactions (id, story_id, user_id, emoji)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT DO NOTHING
                """, reaction_id, story_id, reactor_id, emoji)
                reaction_count += 1
        
        print(f"Created {reaction_count} reactions")
        
        # Print summary
        print("\nDatabase seeded successfully!")
        print(f"   Users: {len(user_ids)}")
        print(f"   Follows: {follow_count}")
        print(f"   Stories: {len(story_ids)}")
        print(f"   Views: {view_count}")
        print(f"   Reactions: {reaction_count}")
        
        # Print sample credentials
        print("\nSample login credentials:")
        print("   Email: (any from above)")
        print("   Password: password123")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
