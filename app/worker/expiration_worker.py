import asyncio
import asyncpg
from datetime import datetime
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import settings


class ExpirationWorker:
    """Background worker to expire stories automatically"""
    
    def __init__(self):
        self.pool: asyncpg.Pool = None
        self.running = False
    
    async def connect_db(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=5,
            command_timeout=60
        )
        print(f"✅ Worker connected to database")
    
    async def disconnect_db(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            print("❌ Worker disconnected from database")
    
    async def expire_stories(self) -> dict:
        """
        Soft-delete expired stories
        
        Returns:
            dict with count and duration
        """
        start_time = datetime.utcnow()
        
        query = """
            UPDATE stories 
            SET deleted_at = NOW() 
            WHERE expires_at < NOW() 
              AND deleted_at IS NULL
            RETURNING id, author_id, created_at, expires_at
        """
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query)
                
                expired_count = len(rows)
                end_time = datetime.utcnow()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                # Structured logging
                log_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "stories_expired",
                    "count": expired_count,
                    "duration_ms": round(duration_ms, 2),
                    "worker": "expiration_worker"
                }
                
                # Log expired story IDs if any
                if expired_count > 0:
                    log_data["expired_story_ids"] = [str(row["id"]) for row in rows]
                
                # Emit structured JSON log
                print(json.dumps(log_data))
                
                return {
                    "count": expired_count,
                    "duration_ms": duration_ms,
                    "timestamp": start_time
                }
        
        except Exception as e:
            error_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "event": "expiration_error",
                "error": str(e),
                "worker": "expiration_worker"
            }
            print(json.dumps(error_log), file=sys.stderr)
            raise
    
    async def run_once(self):
        """Run expiration check once (for testing)"""
        if not self.pool:
            await self.connect_db()
        
        result = await self.expire_stories()
        return result
    
    async def run(self):
        """Main worker loop - runs every minute"""
        self.running = True
        
        print("🚀 Starting Expiration Worker...")
        print(f"⏰ Scanning interval: 60 seconds")
        print(f"📊 Database: {settings.DATABASE_URL.split('@')[1]}")
        
        await self.connect_db()
        
        iteration = 0
        
        try:
            while self.running:
                iteration += 1
                
                # Log iteration start
                start_log = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "worker_iteration_start",
                    "iteration": iteration,
                    "worker": "expiration_worker"
                }
                print(json.dumps(start_log))
                
                # Run expiration
                await self.expire_stories()
                
                # Wait 60 seconds
                await asyncio.sleep(60)
        
        except KeyboardInterrupt:
            print("\n⚠️  Received interrupt signal, shutting down gracefully...")
        except Exception as e:
            error_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "event": "worker_fatal_error",
                "error": str(e),
                "worker": "expiration_worker"
            }
            print(json.dumps(error_log), file=sys.stderr)
            raise
        finally:
            self.running = False
            await self.disconnect_db()
            print("✅ Worker shutdown complete")
    
    def stop(self):
        """Stop the worker gracefully"""
        self.running = False


async def main():
    """Entry point for worker"""
    worker = ExpirationWorker()
    
    try:
        await worker.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    # Run the worker
    asyncio.run(main())
