#!/bin/bash
# start.sh

# Run database migrations
echo "Running database migrations..."
python -c "
import asyncio
import asyncpg
import os

async def run_migrations():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Read and execute migration files
        with open('migrations/001_create_tables.sql', 'r') as f:
            await conn.execute(f.read())
        
        with open('migrations/002_create_indexes.sql', 'r') as f:
            await conn.execute(f.read())
        
        print('✅ Migrations completed')
    except Exception as e:
        print(f'⚠️  Migration error (may already exist): {e}')
    finally:
        await conn.close()

asyncio.run(run_migrations())
"

# Start the application
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
